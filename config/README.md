# Configuration boundary

Runtime configuration is environment-backed. Do not place credentials in this
directory. Use the ignored root `.env` file or process environment and keep
`.env.example` as the non-secret schema. Explicit process-environment values take
precedence over values loaded from `.env`.

## Local sensitivity overrides

`sensitivity_overrides.toml.example` is a non-secret template. To enable local rules:

```powershell
Copy-Item config\sensitivity_overrides.toml.example config\sensitivity_overrides.toml
```

Keep the copied file local when database, schema, table, or column identifiers are
environment-sensitive. Set `SENSITIVITY_OVERRIDES_FILE` in `.env` only when using a
different path. If the configured file does not exist, no override rules are loaded.

Rules are evaluated before built-in column-name, extended-property, and sampled-value
signals. Exact rules take priority over pattern rules; file order resolves ties. Each
rule must use a supported category/action pair and should include a reviewable reason.
Invalid TOML or invalid rule values fail instead of being silently ignored. A
non-sensitive override is a security decision: review it carefully because it can
permit values to be preserved.
