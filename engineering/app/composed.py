from .main import app
from .advanced import router as advanced_router
from .real_cv_sim2real import router as real_cv_sim2real_router
from .sim2real_loop import router as sim2real_loop_router
from .cv_json import router as cv_json_router
from .risk_map import router as risk_map_router
from .validate_dimension import router as validate_dimension_router
from .mcp_compat_fixes import router as mcp_compat_fixes_router
from .manufacturing import router as manufacturing_router
from .cad_routes import router as cad_router
from .final_pipeline import router as final_pipeline_router
from .quality import router as quality_router
from .compat_routes import router as compat_router
from .universal_quality import install as install_universal_quality
from .data_flywheel import router as data_flywheel_router
from .data_flywheel_worker import router as data_flywheel_worker_router
from .moat_intelligence import router as moat_intelligence_router
from .integration_gateway import router as integration_gateway_router
from .product_intelligence import install_product_intelligence
from .competitive_product_loop import router as competitive_product_loop_router
from .customer_obsession import router as customer_obsession_router
from .owned_auth import router as owned_auth_router
from .billing import router as billing_router

for router in (advanced_router, real_cv_sim2real_router, sim2real_loop_router, cv_json_router, risk_map_router, validate_dimension_router, mcp_compat_fixes_router, manufacturing_router, cad_router, final_pipeline_router, quality_router, compat_router, data_flywheel_router, data_flywheel_worker_router, moat_intelligence_router, integration_gateway_router, competitive_product_loop_router, customer_obsession_router, owned_auth_router, billing_router):
    app.include_router(router)
install_product_intelligence(app)
install_universal_quality(app)

# The MCP registry is the single source of truth for the 100-tool compatibility surface.
# Parse only its literal registry so the engineering runtime does not depend on the MCP SDK.
import ast
from pathlib import Path
from fastapi import Request

_registry_path = Path(__file__).resolve().parents[2] / "services" / "mcp" / "server.py"
_registry_tree = ast.parse(_registry_path.read_text(encoding="utf-8"), filename=str(_registry_path))
CAPABILITY_REGISTRY = None
for node in _registry_tree.body:
    targets=[]; value=None
    if isinstance(node, ast.Assign): targets=node.targets; value=node.value
    elif isinstance(node, ast.AnnAssign): targets=[node.target]; value=node.value
    if value is not None and any(isinstance(t, ast.Name) and t.id=="CAPABILITY_REGISTRY" for t in targets):
        CAPABILITY_REGISTRY=ast.literal_eval(value); break
if not isinstance(CAPABILITY_REGISTRY, tuple) or len(CAPABILITY_REGISTRY)!=100:
    raise RuntimeError("Authoritative MCP registry could not be loaded with exactly 100 tools")
if len({name for name,_,_ in CAPABILITY_REGISTRY})!=100:
    raise RuntimeError("Authoritative MCP registry contains duplicate tool names")

_existing_paths={route.path for route in app.routes if hasattr(route,"path")}
def _make_mcp_compat_handler(operation: str):
    async def _handler(request: Request):
        try: payload=await request.json()
        except Exception: payload={}
        return {"status":"reviewable","operation":operation,"inputs_received":sorted(payload.keys()) if isinstance(payload,dict) else [],"next_step":"Provide operation-specific evidence; the compatibility boundary never invents measurements or confidence.","human_gate":True,"provenance":{"source":"mcp_registry_compatibility_boundary","synthetic":False}}
    return _handler
for _name,_description,_path in CAPABILITY_REGISTRY:
    if _path not in _existing_paths:
        app.add_api_route(_path,_make_mcp_compat_handler(_name),methods=["POST"],name=f"mcp_compat_{_name}")
