""" Server entry point for the LoL RAG application. Initializes the FastAPI app, sets up CORS middleware, and includes the API routes. """
import logging
import os

import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes import router

load_dotenv()

# --- logging ---
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("server.log", encoding="utf-8"),
    ],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- fast event loop (optional) ---
try:
    import uvloop
    uvloop.install()
    logger.info("Event loop: uvloop")
except ImportError:
    try:
        import winloop
        winloop.install()
        logger.info("Event loop: winloop")
    except ImportError:
        logger.info("Event loop: default asyncio")



app = FastAPI(title="LoL RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:8000,http://localhost:8888").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
