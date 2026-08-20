from .main import app
from .advanced import router as advanced_router
from .real_cv_sim2real import router as real_cv_sim2real_router
from .cv_json import router as cv_json_router
from .risk_map import router as risk_map_router
from .validate_dimension import router as validate_dimension_router
from .mcp_compat_fixes import router as mcp_compat_fixes_router
from .manufacturing import router as manufacturing_router
from .cad_routes import router as cad_router
from .final_pipeline import router as final_router
from .quality import router as quality_router
from .compat_routes import router as compat_router
from .universal_quality import install as install_universal_quality
from .data_flywheel import router as data_flywheel_router
from .data_flywheel_worker import router as data_flywheel_worker_router
from .moat_intelligence import router as moat_intelligence_router

app.include_router(advanced_router)
app.include_router(real_cv_sim2real_router)
app.include_router(cv_json_router)
app.include_router(risk_map_router)
app.include_router(validate_dimension_router)
app.include_router(mcp_compat_fixes_router)
app.include_router(manufacturing_router)
app.include_router(cad_router)
app.include_router(final_router)
app.include_router(quality_router)
app.include_router(compat_router)
app.include_router(data_flywheel_router)
app.include_router(data_flywheel_worker_router)
# Product-facing moat intelligence: health, priorities, and the evidence-backed
# engineering feedback graph are available to the app and MCP through the same
# API boundary as the existing engineering surfaces.
app.include_router(moat_intelligence_router)
install_universal_quality(app)
