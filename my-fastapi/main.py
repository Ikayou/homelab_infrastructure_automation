from fastapi import FastAPI
import threading

from database import init_db
from services.monitor_service import background_monitor

from routers import containers
from routers import keycloak_users
from routers import history
from routers import monitor
from routers import metrics


app = FastAPI(
    title="Container API",
    swagger_ui_init_oauth={
        "clientId": "container-api-client",
        "usePkceWithAuthorizationCodeGrant": True,
    }
)


@app.on_event("startup")
def startup():
    init_db()

    monitor_thread = threading.Thread(
        target=background_monitor,
        daemon=True
    )
    monitor_thread.start()


@app.get("/")
def root():
    return {"message": "Container API läuft"}


app.include_router(containers.router)
app.include_router(keycloak_users.router)
app.include_router(history.router)
app.include_router(monitor.router)
app.include_router(metrics.router)