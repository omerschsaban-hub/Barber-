from __future__ import annotations
import asyncio, os, base64
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from server import CAPABILITY_NAMES, CAPABILITY_REGISTRY

def args_for(name: str, path: str) -> dict:
    if path.startswith("/v1/toolbox/"): return {"payload": {}}
    if name == "validate_dimension": return {"nominal_mm":10.0,"measured_mm":10.0,"tolerance_mm":0.1}
    if name in {"physics_predict","physics_interval","physics_provenance"}: return {"nominal_mm":10.0,"material":"PLA","machine":"test","process_temperature_c":200.0}
    if name in {"simulation_run","simulation_domain_randomization"}: return {"nominal_mm":10.0,"shrinkage_pct":0.5,"shrinkage_sigma_pct":0.1,"temperature_c":200.0,"temperature_sigma_c":5.0,"n":100}
    if name in {"calibration_fit","ml_residual_fit","ml_residual_validation"}: return {"observations":[{"predicted_mm":10.0,"measured_mm":10.01},{"predicted_mm":10.1,"measured_mm":10.11},{"predicted_mm":10.2,"measured_mm":10.21}]}
    if name in {"uncertainty_calculate","ml_prediction_uncertainty"}: return {"physics_sigma_mm":0.1,"measurement_sigma_mm":0.05,"model_sigma_mm":0.05,"n_observations":3}
    if name == "residual_uncertainty": return {"physics_sigma_mm":0.1,"measurement_sigma_mm":0.05,"model_sigma_mm":0.05,"n_real_observations":3,"residuals_mm":[0.01,0.02,0.01]}
    if name in {"acceptance_gate","deterministic_acceptance"}: return {"nominal_mm":10.0,"lower_tol_mm":-0.5,"upper_tol_mm":0.5,"observed_sigma_mm":0.05,"measurement_sigma_mm":0.02,"n_observations":3}
    if name in {"reverification_calculate","deterministic_reverification"}: return {"tolerance_band_mm":1.0,"uses_per_week":5,"environment_severity":0.2,"observed_drift_mm_per_day":0.01,"consequence_severity":0.2}
    if name in {"next_experiment","deterministic_next_experiment"}: return {"features":[{"name":"test","uncertainty_mm":0.1}],"budget":1}
    if name == "engineering_agent_run": return {"project_id":"mcp-smoke","objective":"validate routing","max_iterations":1}
    if name == "agent_graph": return {"project_id":"mcp-smoke","max_iterations":1,"approval_required":True}
    if name == "agent_step": return {"objective":"validate routing","max_iterations":1,"approved":False}
    if name == "risk_estimate": return {"nominal_mm":10.0,"predicted_mm":10.0,"uncertainty_mm":0.05,"lower_tol_mm":-0.5,"upper_tol_mm":0.5}
    if name == "final_system_identification": return {"observations":[],"min_points":6}
    if name == "system_identification": return {"observations":[]}
    if name == "inspection_confirm": return {"filename":"smoke.csv","content_sha256":"0"*64,"mapping":{"a":"serial","b":"feature","c":"measured_mm"},"rows":[],"unit":"mm"}
    if name == "inspection_preview": return {"file_base64":base64.b64encode(b"a,b\n1,2\n").decode(),"filename":"smoke.csv"}
    if name in {"inspection_report_csv","inspection_report_pdf"}: return {"serial":"smoke","gauge_name":"test","machine":"test","inspected_at":"2026-08-19T00:00:00Z","acceptance_criteria":"test","measurements":[{"feature":"x","nominal_mm":10,"measured_mm":10}],"provenance":{}}
    if name == "cad_step_extract":
        s="ISO-10303-21;HEADER;ENDSEC;DATA;#1=CARTESIAN_POINT('',(0.,0.,0.));#2=CARTESIAN_POINT('',(10.,5.,2.));ENDSEC;END-ISO-10303-21;"; return {"file_base64":base64.b64encode(s.encode()).decode(),"filename":"smoke.step"}
    if name == "cv_measure":
        png=bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360606000000004000109c9a7e20000000049454e44ae426082"); return {"file_base64":base64.b64encode(png).decode(),"filename":"smoke.png"}
    return {"payload":{}}

async def main():
    url=os.getenv("MCP_URL","http://127.0.0.1:8000/mcp")
    async with streamable_http_client(url) as (r,w,_):
      async with ClientSession(r,w) as s:
        await s.initialize(); listed=await s.list_tools(); names=[t.name for t in listed.tools]
        assert names==CAPABILITY_NAMES and len(names)==100 and len(set(names))==100
        failures=[]
        for name,_,path in CAPABILITY_REGISTRY:
          try:
            result=await s.call_tool(name,arguments=args_for(name,path))
            if getattr(result,"isError",False) or not result.content: failures.append(f"{name}: error/empty")
          except Exception as e: failures.append(f"{name}: {type(e).__name__}: {e}")
        if failures: raise AssertionError("REAL MCP smoke failures:\n"+"\n".join(failures))
        print("REAL MCP smoke OK: tools/list=100, tools/call=100")

if __name__=="__main__": asyncio.run(main())
