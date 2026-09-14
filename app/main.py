from fastapi import FastAPI

from app.config import APP_NAME, APP_VERSION

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)


@app.get("/")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "running"
    }


@app.get("/status")
def status():
    return {
        "status": "ok",
        "service": APP_NAME
    }


@app.get("/about")
def about():
    return {
        "name": APP_NAME,
        "type": "server application",
        "language": "Python",
        "framework": "FastAPI"
    }


@app.get("/course")
def course():
    return {
        "discipline": "Управление работами и разработка программного обеспечения облачных систем",
        "laboratory": 2,
        "project": APP_NAME
    }
