from .main import app
from .advanced import router as advanced_router
from .manufacturing import router as manufacturing_router

# Compose the full engineering API surface used by the MCP gateway.
# Keep all feature implementations in the engineering service; the MCP only
# exposes callable adapters to these existing capabilities.
app.include_router(advanced_router)
app.include_router(manufacturing_router)
