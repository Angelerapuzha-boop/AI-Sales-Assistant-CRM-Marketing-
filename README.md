# AI Sales Assistant CRM

Production-ready AI-powered Sales CRM with lead scoring, email automation, calendar integration, AI calling, and Telegram notifications.

## Architecture

```
ai-sales-crm/
├── frontend/          # React 18 + TypeScript + Vite + Tailwind + Shadcn UI
├── backend/           # FastAPI + SQLAlchemy + Alembic
├── database/          # Schema reference
├── migrations/        # Migration docs
├── scripts/           # Seed & migration scripts
├── docs/              # Documentation
├── docker-compose.yml
├── Dockerfile
├── render.yaml
└── .env.example
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind, Shadcn UI, React Query, Recharts |
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler |
| Database | PostgreSQL (Supabase) |
| AI | Groq (primary), OpenAI (fallback), Templates (final fallback) |
| Auth | JWT + Refresh Tokens, bcrypt, RBAC |
| Integrations | Gmail, Google Calendar, Bland AI, Telegram |

## Quick Start (Docker)

```bash
# 1. Clone/copy project and configure environment
cp .env.example .env
# Edit .env with your Supabase DATABASE_URL and API keys

# 2. Start all services
docker-compose up --build

# 3. Access the app
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Default Admin:** `admin@aisales.com` / `Admin@123456`

## Local Development

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed admin user
python ../scripts/seed_admin.py

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Settings → Database** and copy the connection string
3. Set `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
4. Run migrations: `cd backend && alembic upgrade head`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/auth/*` | Login, register, refresh, profile |
| `/api/companies/*` | CRUD + AI summary + buying signals |
| `/api/contacts/*` | CRUD + search |
| `/api/leads/*` | Scoring, top leads, insights |
| `/api/emails/*` | Generate, send, analytics |
| `/api/meetings/*` | Schedule, calendar sync, prep notes |
| `/api/analytics/*` | Dashboard, analytics, notifications |
| `/api/calls/*` | Bland AI outbound calls |
| `/api/telegram/*` | Bot webhook + commands |
| `/api/health` | Health check |
| `/api/status` | App status |
| `/api/info` | App info |

## Deployment

### Render

```bash
# Connect repo to Render, it reads render.yaml automatically
# Set environment variables in Render dashboard
```

### Railway

```bash
railway init
railway add --service backend
railway variables set DATABASE_URL=your-supabase-url
railway up
```

### Docker (VPS/AWS/Azure/GCP)

```bash
docker build -t ai-sales-crm -f Dockerfile.full .
docker run -p 80:80 --env-file .env ai-sales-crm
```

### AWS/GCP/Azure

Use the Docker image with your cloud container service (ECS, Cloud Run, AKS, etc.) and connect to Supabase PostgreSQL.

## Environment Variables

See `.env.example` for all required variables. Key integrations:

- `GROQ_API_KEY` - Groq AI for content generation
- `GMAIL_API_KEY` / `GMAIL_CLIENT_ID` - Gmail sending
- `GOOGLE_CALENDAR_API_KEY` / `GOOGLE_CLIENT_ID` - Calendar sync
- `BLAND_AI_API_KEY` - AI outbound calls
- `TELEGRAM_BOT_TOKEN` - Telegram bot notifications
- `DATABASE_URL` - Supabase PostgreSQL connection

## Security

- JWT authentication with refresh tokens
- Password hashing (bcrypt)
- Rate limiting (SlowAPI)
- Role-based access (Admin, Manager, Sales Rep)
- Input validation (Pydantic)
- Audit logging
- No hardcoded credentials in source code

## Telegram Bot Commands

`/start` `/help` `/dashboard` `/leads` `/topleads` `/companies` `/meetings` `/analytics` `/report` `/generateemail` `/health`

## License

MIT
