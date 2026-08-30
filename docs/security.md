# Security

- Passwords: PBKDF2-SHA256 (120k iterations)
- JWT access tokens (24h)
- Secrets via environment only
- Upload: MIME allowlist, 10MB max, no executables
- Security headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- SQLAlchemy parameterized queries
- CORS restricted to local frontend origins
- Notification providers fail soft when credentials missing
- Never commit .env
