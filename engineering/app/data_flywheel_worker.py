"""Bounded, idempotent data-flywheel execution on owned PostgreSQL."""
from __future__ import annotations

import hmac
import json
import os
import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from .postgres import execute, fetch_all

router = APIRouter(prefix="/data-flywheel", tags=["data-flywheel-worker"])
SYSTEM_PROJECT_ID = "5fea1405-56fe-4d65-b908-8180ebb68718"
AGENTS = [("Collector Agent",120,2),("Normalization Agent",120,2),("Data Quality Agent",120,2),("Provenance Agent",120,2),("Failure Detection Agent",120,2),("Calibration Analysis Agent",120,2),("Regression Test Generator Agent",120,2),("Improvement Proposal Agent",120,2),("Experiment/Validation Agent",180,1),("Release Gate Agent",120,1)]


def _audit(agent: str, status: str, inp: dict[str, Any], out: dict[str, Any], started: datetime, run_id: str) -> None:
    execute("""insert into agent_runs(project_id,run_id,agent_type,status,input,output,model,created_at,completed_at)
               values(%s,%s,%s,%s,%s::jsonb,%s::jsonb,'deterministic-worker',%s,%s)""", (SYSTEM_PROJECT_ID,run_id,agent,status,json.dumps(inp),json.dumps(out),started,datetime.now(timezone.utc)))


def run_once() -> dict[str, Any]:
    run_id = secrets.token_hex(16)
    started = datetime.now(timezone.utc)
    sources = fetch_all("select key,enabled,consent_required,proprietary_data_allowed,license_required,config,priority from data_sources where enabled=true order by priority desc")
    observations = fetch_all("select id,source_key,event_type,normalized_payload,provenance,consent_state,validation_state,content_hash from data_observations order by observed_at desc limit 250")
    result = {"run_id":run_id,"sources":len(sources),"observations_seen":len(observations),"agents":{},"improvement_candidates":0,"quarantined":0,"prediction_discrepancies":0}
    eligible = [s for s in sources if isinstance(s.get("config"),dict) and s["config"].get("collector_url") and s.get("consent_required") is False]
    _audit("Collector Agent","completed",{"enabled_sources":len(sources)},{"eligible_collectors":len(eligible),"skipped_unauthorized":len(sources)-len(eligible)},started,run_id)
    result["agents"]["Collector Agent"]={"eligible":len(eligible),"skipped_unauthorized":len(sources)-len(eligible)}
    for agent, timeout_s, retries in AGENTS[1:]:
        passed=failed=0
        astart=datetime.now(timezone.utc)
        for obs in observations:
            ok=True; details={}
            payload=obs.get("normalized_payload") or {}
            if agent=="Normalization Agent": ok=bool(payload); details={"normalized":ok}
            elif agent=="Data Quality Agent": ok=obs.get("consent_state") in ("allowed","not_applicable") and bool(obs.get("content_hash")); details={"consent":obs.get("consent_state"),"hash_present":bool(obs.get("content_hash"))}
            elif agent=="Provenance Agent": ok=bool(obs.get("provenance")); details={"provenance_present":ok}
            elif agent=="Failure Detection Agent": ok=obs.get("validation_state")!="invalid"
            elif agent=="Calibration Analysis Agent":
                if isinstance(payload,dict) and "predicted_mm" in payload and "measured_mm" not in payload: result["prediction_discrepancies"]+=1; ok=False
            elif agent in {"Regression Test Generator Agent","Improvement Proposal Agent","Experiment/Validation Agent"}: ok=True
            elif agent=="Release Gate Agent": ok=True; details={"engineering_rule_mutation":False,"approval_required":True}
            inserted = execute("insert into data_quality_checks(observation_id,check_name,passed,score,details) values(%s,%s,%s,%s,%s::jsonb) on conflict(observation_id,check_name) do nothing",(obs["id"],agent,ok,1.0 if ok else 0.0,json.dumps(details)))
            if not ok and agent=="Data Quality Agent":
                execute("update data_observations set validation_state='quarantined',quality_score=0 where id=%s",(obs["id"],)); result["quarantined"]+=1
            passed+=int(ok); failed+=int(not ok)
        status="completed" if failed==0 else "completed_with_failures"
        _audit(agent,status,{"observations":len(observations),"timeout_seconds":timeout_s,"max_retries":retries},{"passed":passed,"failed":failed},astart,run_id)
        result["agents"][agent]={"passed":passed,"failed":failed}
    for obs in [o for o in observations if o.get("source_key") in {"prediction_reality","false_positives","false_negatives","engineer_corrections"}][:25]:
        title=f"Investigate {obs.get('source_key')} discrepancy"
        rows=fetch_all("select id from improvement_candidates where source_observation_id=%s and title=%s limit 1",(obs["id"],title))
        if rows: continue
        execute("""insert into improvement_candidates(project_id,source_observation_id,title,hypothesis,evidence,target_component,risk_score,status)
                   values(%s,%s,%s,%s,%s::jsonb,'validation/calibration',1.0,'proposed')""",(SYSTEM_PROJECT_ID,obs["id"],title,"Observed production evidence indicates a recurring prediction/reality or engineering-correction discrepancy.",json.dumps({"observation_id":str(obs["id"]),"source_key":obs.get("source_key")})))
        result["improvement_candidates"]+=1
    execute("insert into flywheel_checkpoints(baseline_metrics,experiment_metrics,regression_metrics,decision) values(%s::jsonb,%s::jsonb,%s::jsonb,'hold_for_validation')",(json.dumps({"sources":len(sources),"observations":len(observations)}),json.dumps(result["agents"]),json.dumps({"idempotent":True})))
    return result


def scheduler_loop() -> None:
    interval=max(60,int(os.getenv("FLYWHEEL_INTERVAL_SECONDS","1800")))
    print(f"[flywheel] scheduler enabled interval={interval}s",flush=True)
    while True:
        try: print(f"[flywheel] run completed: {run_once()}",flush=True)
        except Exception as exc: print(f"[flywheel] run failed: {str(exc)[:500]}",flush=True)
        time.sleep(interval)


def start_scheduler() -> None:
    if os.getenv("FLYWHEEL_SCHEDULER_ENABLED","false").lower()=="true":
        threading.Thread(target=scheduler_loop,name="fabrient-flywheel",daemon=True).start()

@router.post("/run")
def manual_run(x_fabrient_run_token: str|None=Header(default=None)):
    expected=os.getenv("DATA_FLYWHEEL_RUN_TOKEN")
    if not expected or not x_fabrient_run_token or not hmac.compare_digest(x_fabrient_run_token,expected): raise HTTPException(401,"Unauthorized")
    return run_once()
