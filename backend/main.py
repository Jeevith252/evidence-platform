# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from database.mongo import check_connection
from routes.analysis import router as analysis_router
from routes.evidence import router as evidence_router
from routes.network import router as network_router
from routes.reports import router as reports_router
from routes.suspects import router as suspects_router
from routes.image_analysis import router as image_router
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs when server STARTS
    print("Starting Evidence Platform...")
    await check_connection()
    yield
    # Runs when server STOPS
    print("Shutting down...")

app = FastAPI(
    title="Digital Evidence & Social Media Intelligence Platform",
    description="AI-powered platform for analyzing social media evidence",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(evidence_router)
app.include_router(network_router)
app.include_router(reports_router)
app.include_router(suspects_router)
app.include_router(image_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return {
        "message": "Welcome to the Evidence Platform API",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}