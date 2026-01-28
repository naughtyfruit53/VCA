# VCA

# Voice AI Agent Platform (Multi-Tenant)

A multi-tenant, India-first Voice AI platform that answers and makes phone calls for small and medium businesses using SIP-based telephony and AI-driven conversations.

## Core Objectives
- AI-powered call answering (Inbound)
- Cost-optimized telephony using SIP + Asterisk
- Multi-tenant SaaS architecture
- Designed for Indian SMBs (₹5k–₹10k/month pricing tier)
- Modular design to support future outbound, sales, and dispatcher agents

---

## High-Level Architecture

Telephony:
- SIP Trunk (India provider)
- Asterisk (PBX)

Backend:
- FastAPI (Python)
- Redis (call session state)
- PostgreSQL (Supabase) for persistence

AI Layer:
- STT: Whisper (self-hosted)
- LLM: OpenAI / Grok / Gemini (pluggable)
- TTS: OpenAI TTS / Coqui (pluggable)

Frontend:
- Next.js (Admin dashboard)
- Tenant onboarding & configuration
- Call logs & summaries

---

## Repository Structure (Planned)

```text
voice-ai-platform/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── tenants.py
│   │   │   ├── calls.py
│   │   │   ├── ai_profiles.py
│   │   ├── services/
│   │   │   ├── stt/
│   │   │   ├── tts/
│   │   │   ├── llm/
│   │   │   ├── call_router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── redis.py
│   │   │   ├── database.py
│   │   ├── models/
│   │   └── schemas/
│   └── requirements.txt
│
├── telephony/
│   ├── asterisk/
│   │   ├── pjsip.conf
│   │   ├── extensions.conf
│   ├── agi/
│   │   └── ai_bridge.py
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── docs/
│   ├── architecture.md
│   ├── call-flow.md
│
└── README.md

Multi-Tenancy Model

Every resource is scoped by tenant_id

Telephony DID → tenant_id mapping

Isolated AI profiles per tenant

Redis used only for live call sessions

PostgreSQL is the source of truth

MVP Scope (Phase 1)

Inbound call answering only

Single AI receptionist agent

English language only

Call summary via SMS / dashboard

Manual tenant onboarding

Non-Goals (Explicitly Out of Scope for MVP)

Cold calling

CRM integrations

Multi-language

Advanced analytics

White-label UI

Guiding Principles

Cost efficiency > feature richness

Deterministic logic > AI magic

Fast response time (<1s) is critical

Everything must be replaceable (STT, LLM, TTS)

Status

🚧 Under active development
This README will evolve as modules are implemented.
