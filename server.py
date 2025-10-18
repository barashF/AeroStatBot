from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent


@app.get('/')
async def root():
    return {'status': 'ok'}


@app.get('/webapp')
async def webapp():
    return FileResponse(BASE_DIR / 'static/index.html')