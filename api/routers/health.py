from fastapi import APIRouter, Request

from api.schemas.models import HealthResponse
from config.settings import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def health_check(request: Request):
    state = request.app.state
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        classifier_ready=getattr(state, "classifier", None) is not None,
        predictor_ready=getattr(state, "predictor", None) is not None,
        classifier_error=getattr(state, "classifier_error", None),
    )
