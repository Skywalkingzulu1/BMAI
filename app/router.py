from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .main import get_current_active_user, User, app

router = APIRouter()


@router.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint returning service status and version information.
    """
    return {
        "status": "ok",
        "service": app.title,
        "version": app.version,
    }


# Example protected endpoint
@router.get(
    "/protected",
    tags=["Protected"],
    dependencies=[Depends(get_current_active_user)],
)
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """A route that requires a valid JWT token."""
    return {"message": f"Hello, {current_user.username}! This is a protected endpoint."}


# ----------------------------------------------------------------------
# Prediction endpoint
# ----------------------------------------------------------------------


class PredictRequest(BaseModel):
    """Schema for prediction requests.

    Adjust fields as needed for the actual model. For demonstration, we accept a
    simple text input.
    """

    input_text: str


class PredictResponse(BaseModel):
    """Schema for prediction responses."""

    prediction: str
    model_version: str


@router.post(
    "/api/predict",
    tags=["Prediction"],
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
)
async def predict(request: PredictRequest):
    """Mock inference endpoint.

    In a real implementation this would load a trained model and generate a
    prediction based on ``request.input_text``. Here we simply reverse the input
    string to simulate a deterministic transformation.
    """
    # Mock inference logic – replace with actual model call as needed.
    mock_prediction = request.input_text[::-1]

    return PredictResponse(
        prediction=mock_prediction,
        model_version=app.version,
    )