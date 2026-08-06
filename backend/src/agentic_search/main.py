from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_search.api.routes import router

app = FastAPI(title="Agentic Search with Memory")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
