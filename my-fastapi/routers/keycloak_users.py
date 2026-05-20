from fastapi import APIRouter, Depends, HTTPException
import requests

from auth import require_client_role
from schemas import KeycloakUserCreate, KeycloakUserUpdate
from config import KEYCLOAK_URL, KEYCLOAK_REALM
from services.keycloak_service import keycloak_admin_headers

router = APIRouter(prefix="/keycloak/users", tags=["Keycloak Users"])


@router.get("")
def list_keycloak_users(
    payload=Depends(require_client_role("container:admin"))
):
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users"

    response = requests.get(
        url,
        headers=keycloak_admin_headers(),
        verify=False,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()


@router.post("")
def create_keycloak_user(
    user: KeycloakUserCreate,
    payload=Depends(require_client_role("container:admin"))
):
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users"

    payload_data = {
        "username": user.username,
        "email": user.email,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "enabled": True,
        "emailVerified": True,
        "credentials": [
            {
                "type": "password",
                "value": user.password,
                "temporary": False,
            }
        ],
    }

    response = requests.post(
        url,
        headers=keycloak_admin_headers(),
        json=payload_data,
        verify=False,
    )

    if response.status_code not in [201, 204]:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {
        "message": f"User {user.username} created successfully"
    }


@router.put("/{user_id}")
def update_keycloak_user(
    user_id: str,
    user: KeycloakUserUpdate,
    payload=Depends(require_client_role("container:admin"))
):
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}"

    update_data = {}

    if user.email is not None:
        update_data["email"] = user.email

    if user.first_name is not None:
        update_data["firstName"] = user.first_name

    if user.last_name is not None:
        update_data["lastName"] = user.last_name

    if user.enabled is not None:
        update_data["enabled"] = user.enabled

    response = requests.put(
        url,
        headers=keycloak_admin_headers(),
        json=update_data,
        verify=False,
    )

    if response.status_code != 204:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {
        "message": f"User {user_id} updated successfully",
        "updated_fields": update_data,
    }


@router.delete("/{user_id}")
def delete_keycloak_user(
    user_id: str,
    payload=Depends(require_client_role("container:admin"))
):
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}"

    response = requests.delete(
        url,
        headers=keycloak_admin_headers(),
        verify=False,
    )

    if response.status_code != 204:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {
        "message": f"User {user_id} deleted successfully"
    }