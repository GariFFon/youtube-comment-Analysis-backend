from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import init_db
from app.api.endpoints import router as analysis_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the server starts
    await init_db()
    yield
    # This runs when the server stops
    print("Shutting down...")

app = FastAPI(
    title="YouTube Comment Analysis API",
    lifespan=lifespan
)

# Configure CORS (Important for your frontend to communicate with backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register our massive new Analysis endpoint!
app.include_router(analysis_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the YouTube Comment Analysis API! MongoDB is connected."}
