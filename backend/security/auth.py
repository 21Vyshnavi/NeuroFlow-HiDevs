# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "super-secret-key-for-neuroflow"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

class TokenData(BaseModel):
    client_id: str | None = None
    scopes: list[str] = []

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("sub")
        scopes: list[str] = payload.get("scopes", [])
        if client_id is None:
            raise credentials_exception
        token_data = TokenData(client_id=client_id, scopes=scopes)
    except JWTError:
        raise credentials_exception
    return token_data

class ScopeRequired:
    def __init__(self, required_scope: str) -> None:
        self.required_scope = required_scope

    async def __call__(self, current_user: TokenData = Depends(get_current_user)):
        if self.required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions, {self.required_scope} scope required"
            )
        return current_user
