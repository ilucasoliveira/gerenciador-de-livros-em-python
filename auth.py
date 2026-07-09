import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from secrets import compare_digest

security = HTTPBasic()

USUARIO = os.getenv("MEU_USUARIO")
SENHA = os.getenv("MINHA_SENHA")

def user_authenticate(credentials: HTTPBasicCredentials=Depends(security)):
    is_username_correct = compare_digest(credentials.username, USUARIO)
    is_password_correct = compare_digest(credentials.password, SENHA)
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=401, detail="Unauthorized credentials", headers={"WWW-Authenticate": "Basic"})
    
    return credentials
