from datetime import datetime, timedelta
from typing import Union
from jose import JWTError, jwt

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Verifica que "sub" contenga el email del usuario o un valor válido
    if "sub" not in to_encode or to_encode["sub"] is None:
        raise ValueError("The token payload must contain a valid 'sub' field")
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        print(f"Payload: {payload}")  # Agregar para debug
        if email is None:
            raise credentials_exception
        return email
    except JWTError as e:
        print(f"JWTError: {e}")  # Agregar para debug
        raise credentials_exception
