"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.admin.routes import router as admin_router
from backend.api.auth.routes import router as auth_router
from backend.api.routes.analytics import router as analytics_router
from backend.api.routes.constituencies import router as constituencies_router
from backend.api.routes.contributions import router as contributions_router
from backend.api.routes.metadata import router as metadata_router
from backend.api.routes.hansard import router as hansard_router
from backend.api.routes.mps import router as mps_router
from backend.api.routes.narrative import router as narrative_router
from backend.api.routes.search import router as search_router
from backend.api.routes.status import router as status_router

DEV_JWT_SECRET = 'ba-reng-dev-secret-do-not-use-in-production'

if os.environ.get('JWT_SECRET_KEY', DEV_JWT_SECRET) == DEV_JWT_SECRET:
    import warnings
    warnings.warn(
        'JWT_SECRET_KEY is the dev default. '
        'Set JWT_SECRET_KEY to a strong random value in production.',
    )

app = FastAPI(
    title='Ba Reng?',
    description='Botswana Parliament MP Monitor',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(mps_router)
app.include_router(contributions_router)
app.include_router(constituencies_router)
app.include_router(metadata_router)
app.include_router(hansard_router)
app.include_router(analytics_router)
app.include_router(narrative_router)
app.include_router(search_router)
app.include_router(status_router)


@app.get('/api/v1/health')
def health() -> dict:
    """Return system health check."""
    return {'status': 'ok', 'version': '0.1.0'}
