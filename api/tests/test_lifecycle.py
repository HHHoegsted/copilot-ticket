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


def _set_status(client, ticket_id: int, status: str):
    return client.put(f"/api/tickets/{ticket_id}/status", json={"status": status})


def _resolve(client, ticket_id: int, agent_client, agent: dict) -> None:
    assert _set_status(agent_client, ticket_id, "in_progress").status_code == 200
    assert _set_status(agent_client, ticket_id, "resolved").status_code == 200


def test_agent_moves_open_to_in_progress_to_resolved(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    response = _set_status(agent_client, ticket["id"], "in_progress")
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    response = _set_status(agent_client, ticket["id"], "resolved")
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_agent_can_reopen_resolved(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    _resolve(client, ticket["id"], agent_client, agent)
    response = _set_status(agent_client, ticket["id"], "open")
    assert response.status_code == 200
    assert response.json()["status"] == "open"


def test_customer_can_close_own_resolved(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    _resolve(client, ticket["id"], agent_client, agent)
    response = _set_status(client, ticket["id"], "closed")
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_customer_can_reopen_own_resolved(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    _resolve(client, ticket["id"], agent_client, agent)
    response = _set_status(client, ticket["id"], "open")
    assert response.status_code == 200
    assert response.json()["status"] == "open"


def test_customer_cannot_move_to_in_progress_or_resolved(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    assert _set_status(client, ticket["id"], "in_progress").status_code == 403
    assert _set_status(client, ticket["id"], "resolved").status_code == 409


def test_customer_cannot_close_or_reopen_another_customers_ticket(
    client, make_client, make_agent
):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    _resolve(client, ticket["id"], agent_client, agent)
    bob = make_client()
    _register_and_login(bob, _unique("bob"))
    assert _set_status(bob, ticket["id"], "closed").status_code == 404
    assert _set_status(bob, ticket["id"], "open").status_code == 404


def test_agent_cannot_close(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    _resolve(client, ticket["id"], agent_client, agent)
    assert _set_status(agent_client, ticket["id"], "closed").status_code == 403


def test_invalid_transitions_are_rejected_with_409(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    # open: only in_progress is valid
    assert _set_status(agent_client, ticket["id"], "resolved").status_code == 409
    assert _set_status(agent_client, ticket["id"], "closed").status_code == 409
    # in_progress: only resolved is valid
    assert _set_status(agent_client, ticket["id"], "in_progress").status_code == 200
    assert _set_status(agent_client, ticket["id"], "open").status_code == 409
    assert _set_status(agent_client, ticket["id"], "closed").status_code == 409


def test_closed_is_terminal(client, make_client, make_agent):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    agent = make_agent()
    agent_client = make_client()
    _login_agent(agent_client, agent)
    _resolve(client, ticket["id"], agent_client, agent)
    assert _set_status(client, ticket["id"], "closed").status_code == 200
    assert _set_status(agent_client, ticket["id"], "in_progress").status_code == 409
    assert _set_status(agent_client, ticket["id"], "open").status_code == 409
    assert _set_status(client, ticket["id"], "open").status_code == 409


def test_unknown_status_is_422(client):
    _register_and_login(client, _unique("alice"))
    ticket = _create_ticket(client)
    assert _set_status(client, ticket["id"], "bogus").status_code == 422