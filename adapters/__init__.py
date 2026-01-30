"""
Adapters package for external service integrations.

This package contains adapters for integrating with external services
such as telephony providers, notification services, etc.

All adapters MUST:
- Enforce strict tenant_id scoping
- Handle errors gracefully
- Log all interactions
- Never store raw provider payloads
"""
