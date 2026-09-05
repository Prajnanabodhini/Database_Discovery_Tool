# Prompt — Local Web UI Architecture and Security

Implement local Flask UI.

Default:
WEB_HOST=127.0.0.1
WEB_PORT=8765
WEB_AUTO_OPEN_BROWSER=true

Security:
- bind loopback only
- CSRF/session token for POSTs
- same-origin checks
- no shell endpoint
- no arbitrary SQL endpoint
- no arbitrary Python eval
- strict database-name allowlist from config
- strict mode enum
- path containment checks
- safe file types
- sanitize errors
- no secrets in HTML

Provide dashboard, output browser, file viewer, run detail and compare pages.

Core operation must work offline without CDN.
