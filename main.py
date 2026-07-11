"""JetPakt AI — AI Front Desk for 80134-area local service businesses

24/7 AI phone answering, booking, one-page sites, and review automation for
salons, dry cleaners, roofers, plumbers, and other trades that don't have
automated front-office tooling today. See docs/AI_AGENCY_PLAN.md.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes.services import router as services_router
from api.routes.webhooks import router as webhooks_router

app = FastAPI(
    title="JetPakt AI",
    description="AI Front Desk automation for local service businesses",
    version="0.1.0",
)

# CORS — allow the marketing site to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gojetpakt.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services_router)
app.include_router(webhooks_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "jetpakt-ai"}


# Serve static marketing site
site_dir = os.path.join(os.path.dirname(__file__), "site")
if os.path.isdir(site_dir):
    app.mount("/", StaticFiles(directory=site_dir, html=True), name="site")


@app.get("/api/openapi.json")
async def openapi():
    return app.openapi()
