from .main import app
from .advanced import router as advanced_router
from .real_cv_sim2real import router as real_cv_sim2real_router
from .cv_json import router as cv_json_router
from .risk_map import router as risk_map_router
from .validate_dimension import router as validate_dimension_router
from .manufacturing import router as manufacturing_router

# Compose the full engineering API surface used by the MCP gateway.
app.include_router(advanced_router)
app.include_router(real_cv_sim2real_router)
app.include_router(cv_json_router)
app.include_router(risk_map_router)
app.include_router(validate_dimension_router)
app.include_router(manufacturing_router)
