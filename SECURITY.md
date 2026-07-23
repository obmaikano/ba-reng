# Security Policy

This project processes only publicly available parliamentary data from Botswana government sources. It does not collect, store, or transmit personal or sensitive user data.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |

## Reporting a Vulnerability

This is an open government weekend project with no production deployment. If you find a security issue:

1. Open a [GitHub Issue](https://github.com/obmaikano/ba-reng/issues) with the label `security`.
2. Include the affected version, a description of the issue, and steps to reproduce (if applicable).

Do not disclose the issue publicly until it is resolved.

## Expectations

- The project runs on SQLite with no network-facing authentication for internal APIs.
- API keys, JWT secrets, and database paths are configured via environment variables (see `.env.example`).
- The `.env` file must never be committed. It is in `.gitignore`.
- CORS is restricted to the frontend origin in development.
