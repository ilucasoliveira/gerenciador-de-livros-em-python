import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from secrets import compare_digest

load_dotenv()

USUARIO = os.getenv("MEU_USUARIO")
SENHA = os.getenv("MINHA_SENHA")

if not USUARIO or not SENHA:
    raise RuntimeError(
        "Variáveis de ambiente MEU_USUARIO e MINHA_SENHA são obrigatórias. "
        "Defina-as no arquivo .env antes de subir a aplicação."
    )

security = HTTPBasic()

def user_authenticate(credentials: HTTPBasicCredentials=Depends(security)):
    is_username_correct = compare_digest(credentials.username, USUARIO)
    is_password_correct = compare_digest(credentials.password, SENHA)
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=401, detail="Unauthorized credentials", headers={"WWW-Authenticate": "Basic"})
    
    return credentials
