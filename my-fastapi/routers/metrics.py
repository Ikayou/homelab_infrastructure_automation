from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type="text/plain"
    )