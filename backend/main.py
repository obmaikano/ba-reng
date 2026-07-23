"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get('/api/v1/health')
def health() -> dict:
    """Return system health check."""
    return {'status': 'ok', 'version': '0.1.0'}
