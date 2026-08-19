from .main import app
from .advanced import router as advanced_router
from .validate_dimension import router as validate_dimension_router
from .manufacturing import router as manufacturing_router

# Compose the full engineering API surface used by the MCP gateway.
# The deterministic validate_dimension route is registered before the generic
# manufacturing toolbox router so the operation can never fall through to
# "unknown_operation".
app.include_router(advanced_router)
app.include_router(validate_dimension_router)
app.include_router(manufacturing_router)
