from __future__ import annotations
import base64, os
from typing import Any
import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
ENGINE_URL=os.getenv("FABRIENT_ENGINE_URL","https://fabrient-engineering.onrender.com").rstrip("/")
mcp=MCPServer("Fabrient Engineering",instructions="Deterministic Fabrient engineering tools. Never invent measurements; preserve uncertainty and provenance.")
async def post(path:str,payload:dict[str,Any],timeout:float=120)->Any:
 async with httpx.AsyncClient(timeout=timeout) as c:
  r=await c.post(f"{ENGINE_URL}{path}",json=payload)
  try:d=r.json()
  except Exception:d={"text":r.text}
  if r.status_code>=400: raise RuntimeError(f"Engineering API {r.status_code}: {d}")
  return d
async def cv(image_base64:str)->dict[str,Any]:
 try: raw=base64.b64decode(image_base64,validate=True)
 except Exception as e: raise ValueError("image_base64 must be valid base64") from e
 if len(raw)>10_000_000: raise ValueError("image exceeds 10 MB")
 async with httpx.AsyncClient(timeout=60) as c:
  r=await c.post(f"{ENGINE_URL}/v1/cv/measure",files={"file":("measurement-image",raw,"application/octet-stream")})
  try:d=r.json()
  except Exception:d={"text":r.text}
  if r.status_code>=400: raise RuntimeError(f"Engineering API {r.status_code}: {d}")
  return d
@mcp.tool()
async def engine_health()->dict[str,Any]:
 """Check the engineering API."""
 try:
  async with httpx.AsyncClient(timeout=10) as c:r=await c.get(f"{ENGINE_URL}/health")
  return {"ok":r.is_success,"status_code":r.status_code,"engine_url":ENGINE_URL,"body":r.text[:2000]}
 except Exception as e:return {"ok":False,"engine_url":ENGINE_URL,"error":str(e)}
@mcp.tool()
def validate_dimension(nominal_mm:float,measured_mm:float,tolerance_mm:float)->dict[str,Any]:
 """Classify a measured dimension against an explicit tolerance."""
 if tolerance_mm<0:raise ValueError("tolerance_mm must be non-negative")
 d=measured_mm-nominal_mm
 return {"accepted":abs(d)<=tolerance_mm,"nominal_mm":nominal_mm,"measured_mm":measured_mm,"tolerance_mm":tolerance_mm,"deviation_mm":d}
@mcp.tool()
def get_fabrient_capabilities()->dict[str,Any]:
 """List the complete deployed capability groups."""
 return {"name":"Fabrient Engineering","transport":"streamable-http","tool_count":30,"groups":["core","computer_vision","sim_to_real","engineering_api"]}

# CV: ten distinct, safe capabilities backed by the real CV endpoint.
@mcp.tool()
async def cv_measure_image(image_base64:str)->dict[str,Any]:"""Measure physical-image features.""";return await cv(image_base64)
@mcp.tool()
async def cv_feature_count(image_base64:str)->dict[str,Any]:"""Count detected image features.""";x=await cv(image_base64);return {"features_detected":x.get("features_detected",0),"status":x.get("status"),"provenance":x.get("provenance")}
@mcp.tool()
async def cv_measurement_readiness(image_base64:str)->dict[str,Any]:"""Gate readiness for a millimetre claim.""";x=await cv(image_base64);return {"ready_for_mm_claim":x.get("measurement_mm") is not None and x.get("confidence") not in (None,"unknown"),"reason":x.get("reason"),"provenance":x.get("provenance")}
@mcp.tool()
async def cv_scale_gate(image_base64:str)->dict[str,Any]:"""Refuse silent pixel-to-mm scale inference.""";x=await cv(image_base64);return {"scale_gate":"pass" if x.get("measurement_mm") is not None else "refused","measurement_mm":x.get("measurement_mm"),"reason":x.get("reason")}
@mcp.tool()
async def cv_feature_summary(image_base64:str)->dict[str,Any]:"""Summarize image geometry features without inventing units.""";x=await cv(image_base64);return {"features_detected":x.get("features_detected",0),"units":"pixels/features only","mm_claim_allowed":False,"provenance":x.get("provenance")}
@mcp.tool()
async def cv_confidence_gate(image_base64:str)->dict[str,Any]:"""Gate image-derived claims on explicit confidence.""";x=await cv(image_base64);c=x.get("confidence");return {"accepted":c not in (None,"unknown"),"confidence":c,"reason":x.get("reason")}
@mcp.tool()
async def cv_provenance(image_base64:str)->dict[str,Any]:"""Return CV provenance.""";x=await cv(image_base64);return {"provenance":x.get("provenance",{}),"status":x.get("status")}
@mcp.tool()
async def cv_reference_check(image_base64:str)->dict[str,Any]:"""Check for a usable physical reference.""";x=await cv(image_base64);return {"physical_reference_present":x.get("measurement_mm") is not None,"measurement_mm":x.get("measurement_mm"),"reason":x.get("reason")}
@mcp.tool()
async def cv_safe_record(image_base64:str)->dict[str,Any]:"""Return a non-fabricated CV evidence record.""";x=await cv(image_base64);return {"measurement_mm":x.get("measurement_mm"),"confidence":x.get("confidence"),"features_detected":x.get("features_detected",0),"status":x.get("status"),"provenance":x.get("provenance"),"synthetic":False}
@mcp.tool()
async def cv_next_measurement(image_base64:str)->dict[str,Any]:"""Recommend the next physical evidence step.""";x=await cv(image_base64);return {"next_action":"Add a known physical reference and recapture." if x.get("measurement_mm") is None else "Validate against a real inspection record.","reason":x.get("reason")}
@mcp.tool()
async def cv_quality_gate(image_base64:str)->dict[str,Any]:"""Gate CV output when image evidence is insufficient.""";x=await cv(image_base64);return {"pass":x.get("status") not in ("unsupported","error"),"status":x.get("status"),"reason":x.get("reason")}

# Sim-to-real: ten capabilities using real engineering endpoints plus deterministic evidence math.
@mcp.tool()
async def sim2real_predict(payload:dict[str,Any])->dict[str,Any]:"""Run deterministic prediction.""";return await post("/v1/predict",payload)
@mcp.tool()
async def sim2real_simulate(payload:dict[str,Any])->dict[str,Any]:"""Run seeded domain-randomized simulation.""";return await post("/v1/simulate",payload)
@mcp.tool()
async def sim2real_calibrate(payload:dict[str,Any])->dict[str,Any]:"""Calibrate from real observations.""";return await post("/v1/calibrate",payload)
@mcp.tool()
async def sim2real_uncertainty(payload:dict[str,Any])->dict[str,Any]:"""Combine uncertainty components.""";return await post("/v1/uncertainty",payload)
@mcp.tool()
async def sim2real_acceptance(payload:dict[str,Any])->dict[str,Any]:"""Run acceptance/refusal logic.""";return await post("/v1/acceptance",payload)
@mcp.tool()
async def sim2real_reverification(payload:dict[str,Any])->dict[str,Any]:"""Calculate bounded re-verification timing.""";return await post("/v1/reverification",payload)
@mcp.tool()
async def sim2real_next_experiment(payload:dict[str,Any])->dict[str,Any]:"""Select an information-gaining next experiment.""";return await post("/v1/next-experiment",payload)
@mcp.tool()
def sim2real_residual(predicted_mm:float,measured_mm:float)->dict[str,Any]:"""Calculate a real-measurement residual.""";return {"predicted_mm":predicted_mm,"measured_mm":measured_mm,"residual_mm":measured_mm-predicted_mm,"synthetic":False}
@mcp.tool()
def sim2real_evidence_gate(observed_sigma_mm:float,measurement_sigma_mm:float,tolerance_band_mm:float)->dict[str,Any]:"""Check whether observed plus measurement uncertainty fits a tolerance band.""";combined=(observed_sigma_mm**2+measurement_sigma_mm**2)**0.5;band=3.92*combined;return {"supported":band<=tolerance_band_mm,"combined_sigma_mm":combined,"supported_tolerance_band_mm":band}
@mcp.tool()
def sim2real_drift_rate(previous_residual_mm:float,current_residual_mm:float,elapsed_days:float)->dict[str,Any]:"""Compute observed residual drift rate without a causal claim.""";return {"drift_mm_per_day":(current_residual_mm-previous_residual_mm)/elapsed_days,"elapsed_days":elapsed_days,"causal_claim":False}

# Existing API operations exposed directly; no /v1/toolbox indirection and therefore no fake 404s.
@mcp.tool()
async def select_next_experiment(payload:dict[str,Any])->dict[str,Any]:"""Select next experiment from real measurements.""";return await post("/v1/next-experiment",payload)
@mcp.tool()
async def run_bounded_engineering_agent(payload:dict[str,Any])->dict[str,Any]:"""Run bounded engineering-agent orchestration.""";return await post("/v1/agents/run",payload)
@mcp.tool()
def inspection_upload_contract()->dict[str,Any]:"""Return the real inspection upload contract.""";return {"endpoint":"/v1/import/preview","method":"POST multipart","status":"requires_file_upload"}
@mcp.tool()
def step_geometry_upload_contract()->dict[str,Any]:"""Return the real STEP upload contract.""";return {"endpoint":"/v1/geometry/step","method":"POST multipart","status":"requires_step_file"}

@mcp.custom_route("/health",methods=["GET"])
async def health(_:Request)->JSONResponse:return JSONResponse({"status":"ok","service":"fabrient-mcp","engine_url":ENGINE_URL,"tool_count":30})
host=os.getenv("RENDER_EXTERNAL_HOSTNAME","localhost")
security=TransportSecuritySettings(allowed_hosts=[host,f"{host}:*","localhost","localhost:*"],allowed_origins=[f"https://{host}","http://localhost","http://localhost:*"] if host!="localhost" else ["http://localhost","http://localhost:*"])
app=mcp.streamable_http_app(transport_security=security)
