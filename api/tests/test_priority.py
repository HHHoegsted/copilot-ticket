import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _register_and_login(client, username: str) -> None:
    client.post("/api/auth/register", json={"username": username, "password": "secret-123"})
    client.post("/api/auth/login", json={"username": username, "password": "secret-123"})


def _create_ticket(client, **extra) -> dict:
    payload = {"title": "A problem", "description": "details", **extra}
    response = client.post("/api/tickets", json=payload)
    assert response.status_code == 201
    return response.json()


def _login_agent(client, agent: dict) -> None:
    client.post("/api/auth/login", json={"username": agent["username"], "password": agent["password"]})


def _set_priority(client, ticket_id: int, priority: str):
    return client.put(f"/api/tickets/{ticket_id}/priority", json={"priority": priority})


def test_customer_sets_priority_at_creation(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client, priority="high")
    assert ticket["priority"] == "high"


def test_priority_defaults_to_normal(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    assert ticket["priority"] == "normal"


def test_unknown_priority_at_creation_is_422(client):
    _register_and_login(client, _unique("alice"))
    response = client.post(
        "/api/tickets", json={"title": "t", "description": "d", "priority": "bogus"}
    )
    assert response.status_code == 422


def test_agent_can_change_priority_in_any_state(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    assert _set_priority(agent_client, ticket["id"], "urgent").status_code == 200
    for status in ("in_progress", "resolved"):
        assert agent_client.put(
            f"/api/tickets/{ticket['id']}/status", json={"status": status}
        ).status_code == 200
    assert _set_priority(agent_client, ticket["id"], "low").status_code == 200
    detail = agent_client.get(f"/api/tickets/{ticket['id']}")
    assert detail.json()["priority"] == "low"


def test_customer_cannot_change_priority(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    assert _set_priority(client, ticket["id"], "urgent").status_code == 403


def test_unknown_priority_change_is_422(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    assert _set_priority(agent_client, ticket["id"], "bogus").status_code == 422