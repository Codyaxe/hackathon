from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    ...
    yield
    ...



app = FastAPI(lifespan=lifespan)


# initial assumption of structure

@app.post("/get_esg")
async def get_esg(data: dict):
    ...