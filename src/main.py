from fastapi import FastAPI
from src.parser.router import router as parser_router

app = FastAPI(
    title="Wildberries parser",
    version="0.1"
)

app.include_router(
    parser_router
)