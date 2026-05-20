import requests
from fastapi import HTTPException

from config import (
    KEYCLOAK_URL,
    KEYCLOAK_REALM,
    KEYCLOAK_ADMIN_CLIENT_ID,
    KEYCLOAK_ADMIN_CLIENT_SECRET,
)


def get_keycloak_admin_token():
    token_url = (
        f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
        "/protocol/openid-connect/token"
    )

    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": KEYCLOAK_ADMIN_CLIENT_ID,
            "client_secret": KEYCLOAK_ADMIN_CLIENT_SECRET,
        },
        verify=False,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Could not get Keycloak admin token: {response.text}",
        )

    return response.json()["access_token"]


def keycloak_admin_headers():
    token = get_keycloak_admin_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }