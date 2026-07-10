# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.security.auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenRequest(BaseModel):
    client_id: str
    client_secret: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(payload: TokenRequest):
    # Mock authentication validation
    if not payload.client_id or not payload.client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client credentials cannot be empty"
        )
        
    # Standard dummy credentials check
    if payload.client_secret != "supersecretpassword":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client secret",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Assign scopes depending on client_id for testing
    if "admin" in payload.client_id.lower():
        scopes = ["query", "ingest", "admin"]
    elif "ingest" in payload.client_id.lower():
        scopes = ["ingest"]
    else:
        scopes = ["query"]

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": payload.client_id, "scopes": scopes},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
