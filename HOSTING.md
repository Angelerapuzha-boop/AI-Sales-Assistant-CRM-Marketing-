# Hosting Instructions

## Option 1: Docker Compose (Recommended for VPS)

```bash
git clone <your-repo>
cd ai-sales-crm
cp .env.example .env
# Edit .env with Supabase DATABASE_URL and API keys
docker-compose up -d --build
```

Access: http://your-server-ip:5173

## Option 2: Render

1. Push code to GitHub
2. Connect repo in Render dashboard
3. Render auto-detects `render.yaml`
4. Set environment variables:
   - DATABASE_URL (Supabase connection string)
   - GROQ_API_KEY, GMAIL_API_KEY, etc.
   - CORS_ORIGINS (your frontend URL)
5. Deploy

## Option 3: Railway

```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

Set variables in Railway dashboard.

## Option 4: AWS (ECS/Fargate)

1. Build and push Docker image to ECR
2. Create ECS task definition with env vars from `.env.example`
3. Connect to Supabase PostgreSQL (external)
4. Use ALB for HTTPS

## Option 5: Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/PROJECT/ai-sales-crm
gcloud run deploy ai-sales-crm --image gcr.io/PROJECT/ai-sales-crm --set-env-vars-from-file .env
```

## Option 6: Azure Container Apps

Deploy `Dockerfile.full` with environment variables from Azure Key Vault.

## Supabase Configuration

1. Create Supabase project
2. Copy **Connection string** (Transaction pooler recommended)
3. Set as `DATABASE_URL`
4. Run: `cd backend && alembic upgrade head`
5. Run: `python scripts/seed_admin.py`

## Telegram Bot Setup

1. Message @BotFather on Telegram → `/newbot`
2. Copy token → `TELEGRAM_BOT_TOKEN`
3. Get your chat ID → `TELEGRAM_ADMIN_CHAT_ID`
4. Set webhook: `POST /api/telegram/setup-webhook`

## Google OAuth Setup

1. Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add redirect URI: `https://your-domain.com/api/auth/google/callback`
4. Enable Gmail API and Google Calendar API
5. Set client ID/secret in `.env`

## Post-Deployment Checklist

- [ ] Run database migrations
- [ ] Seed admin user
- [ ] Verify `/api/health` returns healthy
- [ ] Test login at frontend
- [ ] Configure Telegram webhook
- [ ] Test AI email generation
- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY
