from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .postgres import execute, fetch_all, transaction

router = APIRouter(prefix="/data-flywheel", tags=["data-flywheel"])
INGEST_SECRET = os.getenv("DATA_FLYWHEEL_INGEST_SECRET")
SOURCES = """user_requirements board_dimensions enclosure_dimensions component_locations connector_locations mounting_holes clearance_requirements wall_thickness fastener_selection material_selection manufacturing_method printer_parameters design_revisions validation_results failed_validations engineer_overrides engineer_corrections accepted_recommendations rejected_recommendations manual_edits print_outcomes measured_dimensions warping_measurements fit_tests assembly_results connector_accessibility fastener_fit pcb_insertion component_interference cable_routing thermal_results vibration_results structural_results manufacturing_defects rework_records scrap_records prototype_iterations time_to_success production_results prediction_measurement_delta step_geometry stl_geometry cad_features hole_patterns fillet_patterns wall_distributions clearance_distributions overhang_distributions interference_patterns assembly_relationships successful_geometry_patterns failure_geometry_patterns manufacturing_geometry_patterns cad_version_diffs feature_failure_locations mcp_success mcp_failure mcp_latency mcp_retries mcp_inputs mcp_outputs invalid_inputs workflow_failures app_crashes ui_abandonment repeated_actions unused_features used_features common_workflows error_messages support_requests feature_requests customer_complaints customer_corrections consented_workflow_events reported_manufacturing_problems reported_time_savings reported_accuracy retention expansion public_standards manufacturer_datasheets application_notes manufacturing_guidelines engineering_papers public_cad_examples open_hardware failure_case_studies printing_research materials_data prediction_reality false_positives false_negatives regression_tests edge_case_discovery confidence_calibration failure_clustering version_comparison new_checks closed_loop""".split()

class Observation(BaseModel):
    source_key: str
    event_type: str
    project_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    normalized_payload: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    consent_state: str = "unknown"
    observed_at: datetime | None = None


def _auth(secret: str | None) -> None:
    if not INGEST_SECRET:
        raise HTTPException(503, "Data flywheel ingestion is not configured")
    if not secret or not hmac.compare_digest(secret, INGEST_SECRET):
        raise HTTPException(401, "Invalid ingestion secret")


def _content_hash(source_key: str, event_type: str, payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps({"s": source_key, "e": event_type, "p": payload}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _insert_observation(source_key: str, event_type: str, payload: dict[str, Any], project_id: str | None = None, entity_type: str = "product_request", entity_id: str | None = None, provenance: dict[str, Any] | None = None) -> tuple[str, bool]:
    content_hash = _content_hash(source_key, event_type, payload)
    with transaction() as conn:
        inserted = conn.execute("""insert into data_observations(project_id,source_key,observed_at,entity_type,entity_id,event_type,raw_payload,normalized_payload,provenance,consent_state,validation_state,quality_score,content_hash)
            values(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,'validated',1.0,%s)
            on conflict(source_key,event_type,content_hash) do nothing returning id""", (project_id, source_key, datetime.now(timezone.utc), entity_type, entity_id, event_type, json.dumps(payload), json.dumps(payload), json.dumps(provenance or {}), "not_applicable", content_hash)).fetchone()
        if inserted:
            return str(inserted["id"]), False
        existing = conn.execute("select id from data_observations where source_key=%s and event_type=%s and content_hash=%s", (source_key, event_type, content_hash)).fetchone()
        if not existing:
            raise RuntimeError("Observation conflict could not be resolved")
        return str(existing["id"]), True


def post(source_key: str, observation: dict[str, Any]) -> dict[str, Any]:
    if source_key not in SOURCES:
        return {"accepted": False, "reason": "unknown_source"}
    event_type = str(observation.get("event_type", "internal_event"))
    observation_id, deduplicated = _insert_observation(source_key, event_type, dict(observation), project_id=observation.get("project_id"), entity_type=str(observation.get("entity_type", "product_request")), entity_id=observation.get("entity_id"), provenance=observation.get("provenance"))
    return {"accepted": True, "observation_id": observation_id, "deduplicated": deduplicated}


def query(table: str, filters: dict[str, Any] | None = None, limit: int = 1000) -> list[dict[str, Any]]:
    allowed_tables = {"data_observations", "data_sources"}
    allowed_filters = {
        "data_observations": {"id", "project_id", "source_key", "observed_at", "entity_type", "entity_id", "event_type", "validation_state", "content_hash"},
        "data_sources": {"id", "key", "category", "collection_mode", "enabled", "consent_required", "priority"},
    }
    if table not in allowed_tables:
        raise ValueError("Unsupported flywheel table")
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")
    filters = filters or {}
    if any(k not in allowed_filters[table] for k in filters):
        raise ValueError("Unsupported filter")
    if not filters:
        return fetch_all(f"select * from {table} limit %s", (limit,))
    clauses = " and ".join(f"{k}=%s" for k in filters)
    return fetch_all(f"select * from {table} where {clauses} limit %s", (*filters.values(), limit))


def _seed() -> int:
    for key in SOURCES:
        execute("""insert into data_sources(key,name,category,description,collection_mode,enabled,consent_required,priority)
            values(%s,%s,'data_flywheel',%s,'event',true,true,%s)
            on conflict(key) do update set name=excluded.name,updated_at=now()""", (key, key.replace("_", " ").title(), f"Fabrient data source: {key}", 90 if key in {"prediction_reality", "closed_loop", "engineer_corrections", "print_outcomes", "measured_dimensions", "false_negatives"} else 50))
    return len(SOURCES)

@router.get("/catalog")
def catalog():
    rows = fetch_all("select key from data_sources where enabled=true order by priority desc, key")
    keys = [str(row["key"]) for row in rows]
    return {"count": len(keys), "sources": keys, "configured": bool(keys)}

@router.post("/ingest")
def ingest(o: Observation, x_fabrient_ingest_secret: str | None = Header(default=None)):
    _auth(x_fabrient_ingest_secret)
    if o.source_key not in SOURCES:
        raise HTTPException(400, "Unknown source_key")
    if o.consent_state not in {"allowed", "not_applicable"}:
        raise HTTPException(400, "Consent required")
    payload = o.normalized_payload or o.raw_payload
    observation_id, deduplicated = _insert_observation(o.source_key, o.event_type, payload, project_id=o.project_id, entity_type=o.entity_type or "product_request", entity_id=o.entity_id, provenance=o.provenance)
    return {"accepted": True, "observation_id": observation_id, "source_key": o.source_key, "deduplicated": deduplicated}

@router.post("/seed-catalog")
def seed_catalog(x_fabrient_ingest_secret: str | None = Header(default=None)):
    _auth(x_fabrient_ingest_secret)
    return {"count": _seed()}
