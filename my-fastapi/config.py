import os

API_KEY = os.getenv("API_KEY")

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://keycloak.local")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "container-api")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "container-api-client")

KEYCLOAK_ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
KEYCLOAK_JWKS_URL = f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs"

KEYCLOAK_ADMIN_CLIENT_ID = os.getenv("KEYCLOAK_ADMIN_CLIENT_ID")
KEYCLOAK_ADMIN_CLIENT_SECRET = os.getenv("KEYCLOAK_ADMIN_CLIENT_SECRET")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
DATABASE_URL = os.getenv("DATABASE_URL")