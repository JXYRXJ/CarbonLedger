from app.api.v1.routers.admin import router as admin_router
from app.api.v1.routers.admin_blockchain import router as admin_blockchain_router
from app.api.v1.routers.analytics import router as analytics_router
from app.api.v1.routers.exports import router as exports_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.batches import router as batches_router
from app.api.v1.routers.companies import router as companies_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.marketplace import router as marketplace_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.ownerships import router as ownerships_router, company_ownership_router, batch_ownership_router
from app.api.v1.routers.portfolios import router as portfolios_router
from app.api.v1.routers.projects import router as projects_router, document_router
from app.api.v1.routers.registries import router as registries_router
from app.api.v1.routers.retirements import router as retirements_router
from app.api.v1.routers.transactions import router as transactions_router
from app.api.v1.routers.users import router as users_router

# List of all routes and their respective prefixes for simple iteration
routers_list = [
    (health_router, ""),
    (auth_router, ""),
    (users_router, ""),
    (companies_router, ""),
    (registries_router, ""),
    (projects_router, ""),
    (document_router, ""),
    (batches_router, ""),
    (ownerships_router, ""),
    (company_ownership_router, ""),
    (batch_ownership_router, ""),
    (portfolios_router, ""),

    (marketplace_router, ""),
    (orders_router, ""),
    (transactions_router, ""),
    (retirements_router, ""),
    (analytics_router, ""),
    (admin_router, ""),
    (admin_blockchain_router, ""),
    (exports_router, ""),
]
