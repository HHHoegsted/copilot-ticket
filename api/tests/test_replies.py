import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _register_and_login(client, username: str) -> None:
    client.post("/api/auth/register", json={"username": username, "password": "secret-123"})
    client.post("/api/auth/login", json={"username": username, "password": "secret-123"})


def _create_ticket(client, title: str = "A problem") -> dict:
    response = client.post("/api/tickets", json={"title": title, "description": "details"})
    assert response.status_code == 201
    return response.json()


def test_detail_includes_replies_in_order_with_author_and_timestamp(client):
    username = _unique("alice")
    _register_and_login(client, username)
    ticket = _create_ticket(client)
    client.post(f"/api/tickets/{ticket['id']}/replies", json={"body": "first reply"})
    client.post(f"/api/tickets/{ticket['id']}/replies", json={"body": "second reply"})
    response = client.get(f"/api/tickets/{ticket['id']}")
    assert response.status_code == 200
    body = response.json()
    assert [r["body"] for r in body["replies"]] == ["first reply", "second reply"]
    for reply in body["replies"]:
        assert reply["author"]["username"] == username
        assert reply["created_at"] is not None


def test_ticket_creator_can_post_reply(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    response = client.post(f"/api/tickets/{ticket['id']}/replies", json={"body": "hello"})
    assert response.status_code == 201
    assert response.json()["body"] == "hello"


def test_agent_can_post_reply_to_any_ticket(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    agent_client.post(
        "/api/auth/login", json={"username": agent["username"], "password": agent["password"]}
    )
    response = agent_client.post(f"/api/tickets/{ticket['id']}/replies", json={"body": "on it"})
    assert response.status_code == 201
    assert response.json()["author"]["username"] == agent["username"]


def test_other_customer_cannot_view_or_reply_to_ticket(client, make_client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    other = make_client()
    _register_and_login(other, _unique("bob"))
    assert other.get(f"/api/tickets/{ticket['id']}").status_code == 404
    assert other.post(f"/api/tickets/{ticket['id']}/replies", json={"body": "hi"}).status_code == 404


def test_reply_requires_body(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    response = client.post(f"/api/tickets/{ticket['id']}/replies", json={"body": ""})
    assert response.status_code == 422