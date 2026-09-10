import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _register_and_login(client, username: str) -> None:
    client.post("/api/auth/register", json={"username": username, "password": "secret-123"})
    client.post("/api/auth/login", json={"username": username, "password": "secret-123"})


def test_customer_can_create_ticket(client):
    username = _unique("alice")
    _register_and_login(client, username)
    response = client.post(
        "/api/tickets", json={"title": "Cannot log in", "description": "I keep getting an error"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Cannot log in"
    assert body["description"] == "I keep getting an error"
    assert body["status"] == "open"
    assert body["creator"]["username"] == username
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_ticket_creation_requires_title(client):
    _register_and_login(client, _unique("alice"))
    response = client.post("/api/tickets", json={"title": "", "description": "something"})
    assert response.status_code == 422


def test_agent_cannot_create_ticket(client, make_agent):
    agent = make_agent()
    client.post("/api/auth/login", json={"username": agent["username"], "password": agent["password"]})
    response = client.post("/api/tickets", json={"title": "t", "description": "d"})
    assert response.status_code == 403


def test_customer_list_shows_only_own_tickets_newest_first(client, make_client):
    _register_and_login(client, _unique("alice"))
    other = make_client()
    _register_and_login(other, _unique("bob"))
    client.post("/api/tickets", json={"title": "first", "description": "d"})
    client.post("/api/tickets", json={"title": "second", "description": "d"})
    other.post("/api/tickets", json={"title": "bob ticket", "description": "d"})
    response = client.get("/api/tickets")
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["second", "first"]


def test_agent_list_shows_all_tickets_newest_first(client, make_client, make_agent):
    agent = make_agent()
    _register_and_login(client, _unique("alice"))
    other = make_client()
    _register_and_login(other, _unique("bob"))
    client.post("/api/tickets", json={"title": "alice ticket", "description": "d"})
    other.post("/api/tickets", json={"title": "bob ticket", "description": "d"})
    agent_client = make_client()
    agent_client.post(
        "/api/auth/login", json={"username": agent["username"], "password": agent["password"]}
    )
    response = agent_client.get("/api/tickets")
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["bob ticket", "alice ticket"]


def test_customer_cannot_fetch_another_customers_ticket(client, make_client):
    _register_and_login(client, _unique("alice"))
    other = make_client()
    _register_and_login(other, _unique("bob"))
    ticket_id = other.post("/api/tickets", json={"title": "bob secret", "description": "d"}).json()["id"]
    assert client.get(f"/api/tickets/{ticket_id}").status_code == 404


def test_agent_can_fetch_any_ticket(client, make_client, make_agent):
    agent = make_agent()
    _register_and_login(client, _unique("alice"))
    ticket_id = client.post("/api/tickets", json={"title": "alice ticket", "description": "d"}).json()["id"]
    agent_client = make_client()
    agent_client.post(
        "/api/auth/login", json={"username": agent["username"], "password": agent["password"]}
    )
    response = agent_client.get(f"/api/tickets/{ticket_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ticket_id


def test_unauthenticated_ticket_requests_are_refused(client):
    assert client.get("/api/tickets").status_code == 401
    assert client.post("/api/tickets", json={"title": "t", "description": "d"}).status_code == 401