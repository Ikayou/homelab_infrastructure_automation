from fastapi import HTTPException, Depends, Security, Header
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt
import requests

from config import (
    API_KEY,
    KEYCLOAK_ISSUER,
    KEYCLOAK_JWKS_URL,
    KEYCLOAK_CLIENT_ID,
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{KEYCLOAK_ISSUER}/protocol/openid-connect/auth",
    tokenUrl=f"{KEYCLOAK_ISSUER}/protocol/openid-connect/token",
)


def verify_keycloak_token(token: str = Security(oauth2_scheme)):
    try:
        jwks = requests.get(KEYCLOAK_JWKS_URL, verify=False).json()
        unverified_header = jwt.get_unverified_header(token)

        key = None
        for jwk in jwks["keys"]:
            if jwk["kid"] == unverified_header["kid"]:
                key = jwk
                break

        if key is None:
            raise HTTPException(status_code=401, detail="Public key not found")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            options={"verify_aud": False},
        )

        return payload

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def require_client_role(required_role: str):
    def role_checker(payload=Depends(verify_keycloak_token)):
        client_roles = (
            payload
            .get("resource_access", {})
            .get(KEYCLOAK_CLIENT_ID, {})
            .get("roles", [])
        )

        if required_role not in client_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Client role '{required_role}' required"
            )

        return payload

    return role_checker


def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY is not set")

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")