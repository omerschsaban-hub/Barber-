from __future__ import annotations

"""Invisible product-learning hooks connected to the existing data flywheel."""

import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any

from .data_flywheel import SOURCES, post

ROUTE_SOURCES = {
    "/v1/predict": "prediction_reality",
    "/v1/calibrate": "confidence_calibration",
    "/v1/uncertainty": "confidence_calibration",
    "/v1/acceptance": "validation_results",
    "/v1/reverification": "validation_results",
    "/v1/next-experiment": "common_workflows",
    "/v1/import/preview": "measured_dimensions",
    "/v1/geometry/step": "step_geometry",
    "/v1/final/risk": "validation_results",
    "/v1/final/system-identification": "prediction_reality",
    "/v1/final/import/confirm": "measured_dimensions",
    "/v1/cv/measure": "measured_dimensions",
}


def _write(source_key: str, event_type: str, payload: dict[str, Any], project_id: str | None, entity_id: str | None) -> None:
    if source_key not in SOURCES:
        return
    try:
        post("data_observations", {
            "project_id": project_id,
            "source_key": source_key,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "entity_type": "product_request",
            "entity_id": entity_id,
            "event_type": event_type,
            "raw_payload": payload,
            "normalized_payload": payload,
            "provenance": {"source": "fabrient_product_runtime", "route": payload.get("route"), "app_version": payload.get("app_version")},
            "consent_state": "not_applicable",
            "validation_state": "validated",
            "quality_score": 1.0,
            "content_hash": hashlib.sha256(json.dumps({"s": source_key, "e": event_type, "p": payload}, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        })
    except Exception:
        pass


def record(source_key: str, event_type: str, payload: dict[str, Any], project_id: str | None = None, entity_id: str | None = None) -> None:
    threading.Thread(target=_write, args=(source_key, event_type, payload, project_id, entity_id), daemon=True).start()


def install_product_intelligence(app: Any) -> None:
    @app.middleware("http")
    async def product_learning_middleware(request: Any, call_next: Any):
        started = time.perf_counter()
        response = None
        error = None
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error = exc
            raise
        finally:
            path = request.url.path
            if path.startswith("/data-flywheel") or path in {"/health", "/docs", "/openapi.json", "/redoc"}:
                continue_recording = False
            else:
                continue_recording = True
            if continue_recording:
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                status = getattr(response, "status_code", 500 if error else 200)
                project_id = request.headers.get("x-project-id")
                entity_id = request.headers.get("x-entity-id")
                route_source = ROUTE_SOURCES.get(path)
                if route_source:
                    record(route_source, "product_outcome", {"route": path, "status_code": status, "latency_ms": elapsed_ms, "app_version": "1.0.0"}, project_id, entity_id)
                record("common_workflows", "workflow_event", {"route": path, "status_code": status, "latency_ms": elapsed_ms, "app_version": "1.0.0"}, project_id, entity_id)
                record("mcp_latency", "runtime_latency", {"route": path, "latency_ms": elapsed_ms, "status_code": status}, project_id, entity_id)
                record("mcp_success" if 200 <= status < 400 else "mcp_failure", "runtime_result", {"route": path, "status_code": status, "latency_ms": elapsed_ms}, project_id, entity_id)
                if status >= 400:
                    record("failure_clustering", "product_failure", {"route": path, "status_code": status, "latency_ms": elapsed_ms}, project_id, entity_id)
