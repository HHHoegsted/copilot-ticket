const app = document.getElementById("app");

let currentUser = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body && body.detail ? body.detail : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return body;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

function navigate(hash) {
  if (window.location.hash !== hash) {
    window.location.hash = hash;
  } else {
    render();
  }
}

function render() {
  const hash = window.location.hash || "#/login";
  if (hash === "#/login") return renderLogin();
  if (hash === "#/register") return renderRegister();
  // Everything else is a protected page.
  if (!currentUser) return navigate("#/login");
  if (hash === "#/tickets") return renderList();
  if (hash === "#/tickets/new") return renderCreate();
  const match = hash.match(/^#\/tickets\/(\d+)$/);
  if (match) return renderDetail(match[1]);
  return renderNotFound();
}

function renderLogin() {
  app.innerHTML = `
    <div class="card">
      <h1>Log in</h1>
      <form id="login-form">
        <label>Username
          <input name="username" required autocomplete="username">
        </label>
        <label>Password
          <input name="password" type="password" required autocomplete="current-password">
        </label>
        <p class="error" id="login-error"></p>
        <button type="submit">Log in</button>
      </form>
      <p class="muted">No account? <a href="#/register">Register</a></p>
    </div>`;
  document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target));
    try {
      currentUser = await api("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
      navigate("#/tickets");
    } catch (error) {
      document.getElementById("login-error").textContent = error.message;
    }
  });
}

function renderRegister() {
  app.innerHTML = `
    <div class="card">
      <h1>Register</h1>
      <form id="register-form">
        <label>Username
          <input name="username" required minlength="3" maxlength="64" autocomplete="username">
        </label>
        <label>Password
          <input name="password" type="password" required minlength="8" maxlength="128" autocomplete="new-password">
        </label>
        <p class="error" id="register-error"></p>
        <button type="submit">Register</button>
      </form>
      <p class="muted">Already have an account? <a href="#/login">Log in</a></p>
    </div>`;
  document.getElementById("register-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target));
    try {
      await api("/api/auth/register", { method: "POST", body: JSON.stringify(data) });
      currentUser = await api("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
      navigate("#/tickets");
    } catch (error) {
      document.getElementById("register-error").textContent = error.message;
    }
  });
}

function renderList() {
  app.innerHTML = `<div class="card wide"><h1>Tickets</h1><p class="muted">Loading&hellip;</p></div>`;
  api("/api/tickets")
    .then((tickets) => {
      const rows = tickets
        .map(
          (t) => `
        <tr class="clickable" data-id="${t.id}">
          <td>${t.id}</td>
          <td>${escapeHtml(t.title)}</td>
          <td><span class="badge status-${t.status}">${t.status}</span></td>
          <td>${t.assignee ? escapeHtml(t.assignee.username) : '<span class="muted">unassigned</span>'}</td>
          <td>${new Date(t.created_at).toLocaleString()}</td>
        </tr>`
        )
        .join("");
      app.innerHTML = `
      <div class="card wide">
        <div class="row">
          <h1>Tickets</h1>
          ${currentUser.role === "customer" ? '<a class="btn" href="#/tickets/new">New ticket</a>' : ""}
        </div>
        ${
          tickets.length
            ? `<table>
              <thead><tr><th>#</th><th>Title</th><th>Status</th><th>Assignee</th><th>Created</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>`
            : '<p class="muted">No tickets yet.</p>'
        }
        <p class="muted"><a href="#/login" id="logout-link">Log out</a></p>
      </div>`;
      document.querySelectorAll("tr.clickable").forEach((tr) => {
        tr.addEventListener("click", () => navigate(`#/tickets/${tr.dataset.id}`));
      });
      document.getElementById("logout-link").addEventListener("click", (event) => {
        event.preventDefault();
        logout();
      });
    })
    .catch((error) => {
      app.innerHTML = `<div class="card wide"><h1>Tickets</h1><p class="error">${escapeHtml(error.message)}</p></div>`;
    });
}

function renderCreate() {
  app.innerHTML = `
    <div class="card">
      <h1>New ticket</h1>
      <form id="create-form">
        <label>Title
          <input name="title" required maxlength="200">
        </label>
        <label>Description
          <textarea name="description" required rows="5"></textarea>
        </label>
        <p class="error" id="create-error"></p>
        <button type="submit">Create ticket</button>
      </form>
      <p class="muted"><a href="#/tickets">Back to tickets</a></p>
    </div>`;
  document.getElementById("create-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target));
    try {
      const ticket = await api("/api/tickets", { method: "POST", body: JSON.stringify(data) });
      navigate(`#/tickets/${ticket.id}`);
    } catch (error) {
      document.getElementById("create-error").textContent = error.message;
    }
  });
}

function renderDetail(id) {
  app.innerHTML = `<div class="card wide"><h1>Ticket ${id}</h1><p class="muted">Loading&hellip;</p></div>`;
  const agentsPromise =
    currentUser.role === "agent" ? api("/api/agents").catch(() => []) : Promise.resolve([]);
  Promise.all([api(`/api/tickets/${id}`), agentsPromise])
    .then(([ticket, agents]) => {
      const replies = ticket.replies
        .map(
          (r) => `
        <div class="reply">
          <div class="reply-meta">
            ${escapeHtml(r.author.username)} &middot; ${new Date(r.created_at).toLocaleString()}
          </div>
          <div class="reply-body">${escapeHtml(r.body)}</div>
        </div>`
        )
        .join("");
      app.innerHTML = `
      <div class="card wide">
        <h1>${ticket.id}: ${escapeHtml(ticket.title)}</h1>
        <p class="muted">
          Status: <span class="badge status-${ticket.status}">${ticket.status}</span>
          &middot; Created by ${escapeHtml(ticket.creator.username)}
          &middot; Assignee: ${ticket.assignee ? escapeHtml(ticket.assignee.username) : "unassigned"}
          &middot; Created ${new Date(ticket.created_at).toLocaleString()}
          &middot; Updated ${new Date(ticket.updated_at).toLocaleString()}
        </p>
        ${
          currentUser.role === "agent"
            ? `<div class="row">
              <button class="btn" id="claim-btn">Claim</button>
              <select id="assignee-select">
                ${agents
                  .map(
                    (a) =>
                      `<option value="${a.id}" ${ticket.assignee && ticket.assignee.id === a.id ? "selected" : ""}>${escapeHtml(a.username)}</option>`
                  )
                  .join("")}
              </select>
              <button class="btn" id="assign-btn">Assign</button>
            </div>
            <div class="row">
              ${ticket.status === "open" ? '<button class="btn" id="status-btn" data-status="in_progress">Start progress</button>' : ""}
              ${ticket.status === "in_progress" ? '<button class="btn" id="status-btn" data-status="resolved">Mark resolved</button>' : ""}
              ${ticket.status === "resolved" ? '<button class="btn" id="status-btn" data-status="open">Reopen</button>' : ""}
            </div>`
            : ticket.creator.id === currentUser.id && ticket.status === "resolved"
              ? `<div class="row">
                <button class="btn" id="status-btn" data-status="closed">Close</button>
                <button class="btn" id="status-btn-2" data-status="open">Reopen</button>
              </div>`
              : ""
        }
        <p>${escapeHtml(ticket.description)}</p>
        <h2>Conversation</h2>
        <div class="thread">${replies || '<p class="muted">No replies yet.</p>'}</div>
        <form id="reply-form">
          <label>Reply
            <textarea name="body" required rows="3"></textarea>
          </label>
          <p class="error" id="reply-error"></p>
          <button type="submit">Post reply</button>
        </form>
        <p class="muted"><a href="#/tickets">Back to tickets</a></p>
      </div>`;
      document.getElementById("reply-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(event.target));
        try {
          await api(`/api/tickets/${id}/replies`, { method: "POST", body: JSON.stringify(data) });
          renderDetail(id);
        } catch (error) {
          document.getElementById("reply-error").textContent = error.message;
        }
      });
      if (currentUser.role === "agent") {
        const assign = async (assigneeId) => {
          try {
            await api(`/api/tickets/${id}/assignee`, {
              method: "PUT",
              body: JSON.stringify({ assignee_id: assigneeId }),
            });
            renderDetail(id);
          } catch (error) {
            alert(error.message);
          }
        };
        document.getElementById("claim-btn").addEventListener("click", () => assign(currentUser.id));
        document.getElementById("assign-btn").addEventListener("click", () =>
          assign(Number(document.getElementById("assignee-select").value))
        );
      }
      document.querySelectorAll("[data-status]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            await api(`/api/tickets/${id}/status`, {
              method: "PUT",
              body: JSON.stringify({ status: btn.dataset.status }),
            });
            renderDetail(id);
          } catch (error) {
            alert(error.message);
          }
        });
      });
    })
    .catch(() => renderNotFound());
}

function renderNotFound() {
  app.innerHTML = `
    <div class="card">
      <h1>Not found</h1>
      <p class="muted"><a href="#/tickets">Back to tickets</a></p>
    </div>`;
}

async function logout() {
  await api("/api/auth/logout", { method: "POST" });
  currentUser = null;
  navigate("#/login");
}

window.addEventListener("hashchange", render);

async function init() {
  try {
    currentUser = await api("/api/auth/me");
  } catch {
    currentUser = null;
  }
  if (!currentUser && !window.location.hash) navigate("#/login");
  render();
}

init();