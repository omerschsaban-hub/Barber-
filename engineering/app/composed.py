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
from .integration_gateway import router as integration_gateway_router
from .product_intelligence import install_product_intelligence
from .competitive_product_loop import router as competitive_product_loop_router
from .customer_obsession import router as customer_obsession_router

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
app.include_router(moat_intelligence_router)
app.include_router(integration_gateway_router)
app.include_router(competitive_product_loop_router)
app.include_router(customer_obsession_router)
install_product_intelligence(app)
install_universal_quality(app)
