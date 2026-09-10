# Server-side sessions instead of JWT

For authentication we chose server-side sessions stored in Postgres (httpOnly cookie carrying the session ID) over stateless JWTs. Sessions are revocable — logout invalidates immediately — there is no token-expiry logic in the client, and the database is already a dependency, so statelessness buys nothing at this scale.