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


def _login_agent(client, agent: dict) -> None:
    client.post("/api/auth/login", json={"username": agent["username"], "password": agent["password"]})


def test_tickets_start_unassigned(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    assert ticket["assignee"] is None


def test_agent_can_self_claim(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    response = agent_client.put(
        f"/api/tickets/{ticket['id']}/assignee", json={"assignee_id": agent["id"]}
    )
    assert response.status_code == 200
    assert response.json()["assignee"]["username"] == agent["username"]


def test_agent_can_assign_to_another_agent_and_reassign(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent_one = make_agent()
    agent_two = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent_one)
    response = agent_client.put(
        f"/api/tickets/{ticket['id']}/assignee", json={"assignee_id": agent_two["id"]}
    )
    assert response.status_code == 200
    assert response.json()["assignee"]["username"] == agent_two["username"]
    response = agent_client.put(
        f"/api/tickets/{ticket['id']}/assignee", json={"assignee_id": agent_one["id"]}
    )
    assert response.status_code == 200
    assert response.json()["assignee"]["username"] == agent_one["username"]


def test_customer_cannot_assign(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    response = client.put(f"/api/tickets/{ticket['id']}/assignee", json={"assignee_id": 1})
    assert response.status_code == 403


def test_assign_to_unknown_user_is_404(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    response = agent_client.put(
        f"/api/tickets/{ticket['id']}/assignee", json={"assignee_id": 999999}
    )
    assert response.status_code == 404


def test_assign_to_customer_is_422(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    response = agent_client.put(
        f"/api/tickets/{ticket['id']}/assignee", json={"assignee_id": ticket["creator"]["id"]}
    )
    assert response.status_code == 422


def test_agents_list_is_agents_only(client, make_client, make_agent):
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    response = agent_client.get("/api/agents")
    assert response.status_code == 200
    usernames = [a["username"] for a in response.json()]
    assert "agent" in usernames
    assert agent["username"] in usernames
    customer = make_client()
    _register_and_login(customer, _unique("alice"))
    assert customer.get("/api/agents").status_code == 403