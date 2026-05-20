from fastapi.testclient import TestClient

from main import app
from auth import verify_keycloak_token
client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Container API läuft"
    }
def test_containers_requires_auth():
    response = client.get("/containers")

    assert response.status_code in [401, 403]

def fake_verify_keycloak_token():
    return {
        "resource_access": {
            "container-api-client": {
                "roles": [
                    "container:view",
                    "container:restart",
                    "container:notify",
                    "container:admin",
                ]
            }
        }
    }

def test_list_containers_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeImage:
        tags = ["nginx:latest"]

    class FakeContainer:
        name = "nginx"
        short_id = "abc123"
        status = "running"
        image = FakeImage()

    class FakeContainers:
        def list(self, all=True):
            return [FakeContainer()]

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    response = client.get("/containers")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "nginx",
            "id": "abc123",
            "status": "running",
            "image": ["nginx:latest"],
        }
    ]
    
def test_container_health_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeContainer:
        name = "nginx"
        status = "running"
        attrs = {
            "RestartCount": 0
        }

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    response = client.get("/containers/nginx/health")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "name": "nginx",
        "status": "running",
        "running": True,
        "restart_count": 0,
    }
    
def test_container_stats_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    fake_stats = {
        "memory_stats": {
            "usage": 104857600,
            "limit": 209715200,
        },
        "cpu_stats": {
            "cpu_usage": {
                "total_usage": 200000000,
                "percpu_usage": [1, 2],
            },
            "system_cpu_usage": 1000000000,
        },
        "precpu_stats": {
            "cpu_usage": {
                "total_usage": 100000000,
            },
            "system_cpu_usage": 500000000,
        },
    }

    class FakeContainer:
        name = "nginx"
        status = "running"

        def stats(self, stream=False):
            return fake_stats

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    response = client.get("/containers/nginx/stats")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "name": "nginx",
        "status": "running",
        "cpu_percent": 40.0,
        "memory_usage_mb": 100.0,
        "memory_limit_mb": 200.0,
    }
    
def test_container_alert_with_high_memory(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    fake_stats = {
        "memory_stats": {
            "usage": 900,
            "limit": 1000,
        }
    }

    class FakeContainer:
        name = "nginx"
        status = "running"

        def stats(self, stream=False):
            return fake_stats

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    monkeypatch.setattr(
        containers_router,
        "save_history",
        lambda db, container_name, status, memory_percent, alerts: None
    )

    response = client.get("/containers/nginx/alert")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "name": "nginx",
        "status": "warning",
        "memory_percent": 90.0,
        "alerts": ["memory usage is high"],
    }
    
def test_restart_container(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    restart_called = {
        "called": False
    }

    class FakeContainer:
        def restart(self):
            restart_called["called"] = True

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    response = client.post("/containers/nginx/restart")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "message": "nginx restarted successfully"
    }

    assert restart_called["called"] is True
    
def test_restart_blocked_container():
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    response = client.post("/containers/container-api/restart")

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "container-api darf nicht über diese API neu gestartet werden"
    }

def test_notify_alert_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    fake_stats = {
        "memory_stats": {
            "usage": 900,
            "limit": 1000,
        }
    }

    slack_called = {
        "called": False
    }

    class FakeContainer:
        name = "nginx"
        status = "running"

        def stats(self, stream=False):
            return fake_stats

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    class FakeSlackResponse:
        status_code = 200

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, json):
            slack_called["called"] = True
            return FakeSlackResponse()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    monkeypatch.setattr(
        containers_router,
        "SLACK_WEBHOOK_URL",
        "https://example.com/slack"
    )

    monkeypatch.setattr(
        containers_router.httpx,
        "AsyncClient",
        lambda: FakeAsyncClient()
    )

    response = client.post("/containers/nginx/notify")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "warning"
    assert response.json()["message"] == "notification sent"
    assert slack_called["called"] is True
    
def test_notify_alert_no_alerts(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    fake_stats = {
        "memory_stats": {
            "usage": 100,
            "limit": 1000,
        }
    }

    class FakeContainer:
        name = "nginx"
        status = "running"

        def stats(self, stream=False):
            return fake_stats

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    monkeypatch.setattr(
        containers_router,
        "SLACK_WEBHOOK_URL",
        "https://example.com/slack"
    )

    response = client.post("/containers/nginx/notify")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "no alerts"
    }

def test_container_logs_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeContainer:
        name = "nginx"

        def logs(self, tail=50):
            return b"line1\nline2\nline3"

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    response = client.get("/containers/nginx/logs?lines=3")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "name": "nginx",
        "lines": 3,
        "logs": "line1\nline2\nline3",
    }
    
def test_get_container_detail_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeImage:
        tags = ["nginx:latest"]

    class FakeContainer:
        name = "nginx"
        short_id = "abc123"
        status = "running"
        image = FakeImage()
        attrs = {
            "NetworkSettings": {
                "Ports": {
                    "80/tcp": [
                        {
                            "HostIp": "0.0.0.0",
                            "HostPort": "8080"
                        }
                    ]
                }
            },
            "Created": "2026-05-20T12:00:00Z"
        }

    class FakeContainers:
        def get(self, container_name):
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    response = client.get("/containers/nginx")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "name": "nginx",
        "id": "abc123",
        "status": "running",
        "image": ["nginx:latest"],
        "ports": {
            "80/tcp": [
                {
                    "HostIp": "0.0.0.0",
                    "HostPort": "8080"
                }
            ]
        },
        "created": "2026-05-20T12:00:00Z"
    }
    
def test_get_container_not_found(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    import docker

    class FakeContainers:
        def get(self, container_name):
            raise docker.errors.NotFound("not found")

    class FakeDockerClient:
        containers = FakeContainers()

    import routers.containers as containers_router

    monkeypatch.setattr(
        containers_router,
        "client",
        FakeDockerClient()
    )

    response = client.get("/containers/unknown")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Container not found"
    }
    
def test_get_history_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeHistory:
        container_name = "nginx"
        status = "warning"
        memory_percent = 90.0
        alerts = "memory usage is high"
        created_at = "2026-05-20T12:00:00"

    class FakeQuery:
        def filter(self, *args):
            return self

        def order_by(self, *args):
            return self

        def limit(self, value):
            return self

        def all(self):
            return [FakeHistory()]

    class FakeDB:
        def query(self, model):
            return FakeQuery()

    from database import get_db

    def fake_get_db():
        yield FakeDB()

    app.dependency_overrides[get_db] = fake_get_db

    response = client.get("/history/nginx")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "container_name": "nginx",
            "status": "warning",
            "memory_percent": 90.0,
            "alerts": ["memory usage is high"],
            "created_at": "2026-05-20T12:00:00",
        }
    ]
    
def test_export_history_with_mock():
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeHistory:
        container_name = "nginx"
        status = "warning"
        memory_percent = 90.0
        alerts = "memory usage is high"
        created_at = "2026-05-20T12:00:00"

    class FakeQuery:
        def filter(self, *args):
            return self

        def order_by(self, *args):
            return self

        def all(self):
            return [FakeHistory()]

    class FakeDB:
        def query(self, model):
            return FakeQuery()

    from database import get_db

    def fake_get_db():
        yield FakeDB()

    app.dependency_overrides[get_db] = fake_get_db

    response = client.get("/history/nginx/export")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "nginx" in response.text
    assert "warning" in response.text
    assert "memory usage is high" in response.text
    
def test_monitor_snapshot(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    fake_stats = {
        "memory_stats": {
            "usage": 500,
            "limit": 1000,
        }
    }

    class FakeContainer:
        def __init__(self, name):
            self.name = name
            self.status = "running"

        def stats(self, stream=False):
            return fake_stats

    class FakeContainers:
        def list(self, all=True):
            return [
                FakeContainer("nginx"),
                FakeContainer("redis"),
            ]

    class FakeDockerClient:
        containers = FakeContainers()

    save_called = {
        "count": 0
    }

    def fake_save_history(
        db,
        container_name,
        status,
        memory_percent,
        alerts
    ):
        save_called["count"] += 1

    import routers.monitor as monitor_router

    monkeypatch.setattr(
        monitor_router,
        "client",
        FakeDockerClient()
    )

    monkeypatch.setattr(
        monitor_router,
        "save_history",
        fake_save_history
    )

    response = client.post("/monitor/snapshot")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "snapshot saved"
    assert data["containers_checked"] == 2

    assert save_called["count"] == 2
    
def test_list_keycloak_users_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeResponse:
        status_code = 200

        def json(self):
            return [
                {
                    "id": "user-1",
                    "username": "testuser",
                    "email": "test@example.com",
                    "enabled": True,
                }
            ]

    import routers.keycloak_users as keycloak_router

    monkeypatch.setattr(
        keycloak_router,
        "keycloak_admin_headers",
        lambda: {
            "Authorization": "Bearer fake-token",
            "Content-Type": "application/json",
        }
    )

    monkeypatch.setattr(
        keycloak_router.requests,
        "get",
        lambda url, headers, verify=False: FakeResponse()
    )

    response = client.get("/keycloak/users")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "user-1",
            "username": "testuser",
            "email": "test@example.com",
            "enabled": True,
        }
    ]
    
def test_create_keycloak_user_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeResponse:
        status_code = 201
        text = ""

    import routers.keycloak_users as keycloak_router

    monkeypatch.setattr(
        keycloak_router,
        "keycloak_admin_headers",
        lambda: {
            "Authorization": "Bearer fake-token",
            "Content-Type": "application/json",
        }
    )

    monkeypatch.setattr(
        keycloak_router.requests,
        "post",
        lambda url, headers, json, verify=False: FakeResponse()
    )

    response = client.post(
        "/keycloak/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "password123"
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "message": "User testuser created successfully"
    }
    
def test_update_keycloak_user_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeResponse:
        status_code = 204
        text = ""

    import routers.keycloak_users as keycloak_router

    monkeypatch.setattr(
        keycloak_router,
        "keycloak_admin_headers",
        lambda: {
            "Authorization": "Bearer fake-token",
            "Content-Type": "application/json",
        }
    )

    monkeypatch.setattr(
        keycloak_router.requests,
        "put",
        lambda url, headers, json, verify=False: FakeResponse()
    )

    response = client.put(
        "/keycloak/users/user-1",
        json={
            "email": "new@example.com",
            "enabled": True
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "message": "User user-1 updated successfully",
        "updated_fields": {
            "email": "new@example.com",
            "enabled": True
        }
    }
    
def test_delete_keycloak_user_with_mock(monkeypatch):
    app.dependency_overrides[verify_keycloak_token] = fake_verify_keycloak_token

    class FakeResponse:
        status_code = 204
        text = ""

    import routers.keycloak_users as keycloak_router

    monkeypatch.setattr(
        keycloak_router,
        "keycloak_admin_headers",
        lambda: {
            "Authorization": "Bearer fake-token",
            "Content-Type": "application/json",
        }
    )

    monkeypatch.setattr(
        keycloak_router.requests,
        "delete",
        lambda url, headers, verify=False: FakeResponse()
    )

    response = client.delete("/keycloak/users/user-1")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "message": "User user-1 deleted successfully"
    }