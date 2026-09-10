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
  if (hash.startsWith("#/login")) return renderLogin();
  if (hash.startsWith("#/register")) return renderRegister();
  // Everything else is a protected page.
  if (!currentUser) return navigate("#/login");
  return renderHome();
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

function renderHome() {
  app.innerHTML = `
    <div class="card">
      <h1>Ticketing</h1>
      <p>Logged in as <strong>${escapeHtml(currentUser.username)}</strong> (${escapeHtml(currentUser.role)})</p>
      <button id="logout">Log out</button>
    </div>`;
  document.getElementById("logout").addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST" });
    currentUser = null;
    navigate("#/login");
  });
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