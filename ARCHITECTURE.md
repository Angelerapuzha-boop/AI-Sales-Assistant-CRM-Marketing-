# Architecture Documentation

## System Overview

The AI Sales Assistant CRM is a full-stack application designed for B2B sales teams. It combines traditional CRM functionality with AI-powered automation across email, calling, and lead intelligence.

## Component Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   React UI  │────▶│   FastAPI    │────▶│  Supabase PG    │
│  (Vite)     │     │   Backend    │     │  PostgreSQL     │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    ┌─────────┐     ┌──────────┐     ┌───────────┐
    │  Groq   │     │  Gmail   │     │  Calendar │
    │  OpenAI │     │  API     │     │  API      │
    └─────────┘     └──────────┘     └───────────┘
         │                 │                 │
    ┌─────────┐     ┌──────────┐
    │ Bland   │     │ Telegram │
    │ AI      │     │ Bot      │
    └─────────┘     └──────────┘
```

## Reliability Pattern

All external integrations use:
1. **Retry logic** (tenacity, 3 attempts with exponential backoff)
2. **Fallback providers** (Groq → OpenAI → Template)
3. **Graceful degradation** (local email send if Gmail fails)
4. **Structured logging** (structlog)
5. **Connection pooling** (SQLAlchemy QueuePool)

## Database Schema

11 tables: users, companies, contacts, lead_scores, buying_signals, emails, email_events, meetings, call_logs, notifications, audit_logs

See `database/schema.sql` and Alembic migration `001_initial_schema.py`.

## Lead Scoring Algorithm

Score (0-100) = revenue + employees + industry + buying signals + email activity + seniority

Categories:
- Hot: 70-100
- Warm: 40-69
- Cold: 0-39

## Authentication Flow

1. Login → JWT access token (30 min) + refresh token (7 days)
2. API requests include Bearer token
3. 401 triggers automatic refresh
4. RBAC enforced per endpoint

## Scheduler Jobs

- Meeting reminders: every 5 minutes
- Daily Telegram report: configurable hour (default 8 AM UTC)
