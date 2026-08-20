from .main import app
from .advanced import router as advanced_router
from .real_cv_sim2real import router as real_cv_sim2real_router
from .cv_json import router as cv_json_router
from .risk_map import router as risk_map_router
from .validate_dimension import router as validate_dimension_router
from .manufacturing import router as manufacturing_router
from .cad_routes import router as cad_router
from .final_pipeline import router as final_router
from .quality import router as quality_router
from .compat_routes import router as compat_router
from .universal_quality import install as install_universal_quality

# Compose the complete engineering API surface used by both the web app and MCP.
# Every lifecycle surface is exposed from this same application boundary to
# prevent app/MCP behavior drift.
app.include_router(advanced_router)
app.include_router(real_cv_sim2real_router)
app.include_router(cv_json_router)
app.include_router(risk_map_router)
app.include_router(validate_dimension_router)
app.include_router(manufacturing_router)
app.include_router(cad_router)
app.include_router(final_router)
app.include_router(quality_router)
app.include_router(compat_router)
install_universal_quality(app)
