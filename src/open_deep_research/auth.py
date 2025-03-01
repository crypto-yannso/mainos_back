from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Définir l'en-tête d'authentification
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Clé API (idéalement stockée dans une variable d'environnement)
API_KEY = os.getenv("MAINOS_API_KEY", "votre-cle-api-secrete-par-defaut")

# Fonction de dépendance pour vérifier la clé API
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide"
        )
    return api_key 