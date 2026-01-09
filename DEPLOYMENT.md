# Deployment Guide 🚀

Complete guide for deploying EmailCraft AI to production.

---

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [Production Architecture](#-production-architecture)
- [Render Deployment](#-render-deployment)
- [Environment Variables](#-environment-variables)
- [Database Setup](#-database-setup)
- [Vector Store Setup](#-vector-store-setup)
- [Docker Deployment](#-docker-deployment)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Troubleshooting](#-troubleshooting)

---

## 📋 Prerequisites

| Service                          | Purpose    | Free Tier     |
| -------------------------------- | ---------- | ------------- |
| [Groq](https://console.groq.com) | LLM API    | ✅ 30 req/min |
| [Render](https://render.com)     | Hosting    | ✅ 750 hrs/mo |
| [Supabase](https://supabase.com) | PostgreSQL | ✅ 500 MB     |
| [Pinecone](https://pinecone.io)  | Vector DB  | ✅ 1 index    |

---

## 🏗️ Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         RENDER                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              EmailCraft AI (Docker)                  │    │
│  │  ┌──────────────┐  ┌──────────────┐                 │    │
│  │  │   FastAPI    │  │   Frontend   │                 │    │
│  │  │   Backend    │  │  (Static)    │                 │    │
│  │  └──────────────┘  └──────────────┘                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │  Groq    │        │ Supabase │        │ Pinecone │
    │   LLM    │        │ Postgres │        │ Vectors  │
    └──────────┘        └──────────┘        └──────────┘
```

### Local vs Production

| Component       | Local                      | Production             |
| --------------- | -------------------------- | ---------------------- |
| Database        | SQLite                     | PostgreSQL (Supabase)  |
| Vector Store    | ChromaDB                   | Pinecone               |
| Embeddings      | sentence-transformers      | Pinecone Inference API |
| Embedding Model | all-MiniLM-L6-v2           | multilingual-e5-large  |
| Batch Delay     | 2 seconds                  | 30 seconds             |
| Auto-Detection  | `PINECONE_API_KEY` not set | `PINECONE_API_KEY` set |

---

## 🖥️ Local Development Setup

Running locally requires **minimal setup** - just a Groq API key!

### What's Used Locally

| Component        | Technology            | Description                                |
| ---------------- | --------------------- | ------------------------------------------ |
| **Database**     | SQLite                | Auto-created `emails.db` file              |
| **Vector Store** | ChromaDB              | Local persistent storage in `vectorstore/` |
| **Embeddings**   | sentence-transformers | Uses `all-MiniLM-L6-v2` model              |
| **LLM**          | Groq                  | `llama-3.1-8b-instant` (free tier)         |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/07fahim/EmailCraft-AI.git
cd EmailCraft-AI

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
# Required - Get from https://console.groq.com
GROQ_API_KEY=gsk_your_api_key_here

# Optional - Default is llama-3.1-8b-instant
GROQ_MODEL=llama-3.1-8b-instant
```

### Run the App

```bash
python main.py
```

Open your browser: `http://localhost:8000`

### Local Features

- ✅ Single email generation
- ✅ Batch processing (2-second delay)
- ✅ Analytics dashboard
- ✅ Email history
- ✅ Excel export
- ✅ Portfolio matching (ChromaDB)

### Local File Structure

```
EmailCraft-AI/
├── emails.db           # SQLite database (auto-created)
├── vectorstore/
│   └── chroma_db/      # ChromaDB storage (auto-created)
└── .env                # Your API key
```

---

## 🚀 Render Deployment (Production)

Deploying to Render requires setting up **3 external services**:

### What's Used in Production

| Component        | Technology             | Free Tier                    |
| ---------------- | ---------------------- | ---------------------------- |
| **Hosting**      | Render (Docker)        | 750 hrs/month                |
| **Database**     | PostgreSQL (Supabase)  | 500 MB                       |
| **Vector Store** | Pinecone               | 1 index, 100k vectors        |
| **Embeddings**   | Pinecone Inference API | Uses `multilingual-e5-large` |
| **LLM**          | Groq                   | 30 requests/min              |

### Step 1: Prepare Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:

| Setting | Value               |
| ------- | ------------------- |
| Name    | `emailcraft-ai`     |
| Runtime | Docker              |
| Region  | Oregon (or closest) |
| Branch  | `main`              |
| Plan    | Free                |

### Step 3: Set Environment Variables

In Render Dashboard → Your Service → **Environment**:

| Variable               | Value                  | Notes                      |
| ---------------------- | ---------------------- | -------------------------- |
| `GROQ_API_KEY`         | `gsk_xxxxx`            | Required                   |
| `GROQ_MODEL`           | `llama-3.1-8b-instant` | Optional                   |
| `PINECONE_API_KEY`     | `pcsk_xxxxx`           | For production             |
| `PINECONE_ENVIRONMENT` | `us-east-1`            | Your Pinecone region       |
| `DATABASE_URL`         | `postgresql://...`     | Supabase URL               |
| `ANONYMIZED_TELEMETRY` | `False`                | Disable ChromaDB telemetry |

### Step 4: Deploy

1. Click **Deploy Service**
2. Wait for build (~5-10 minutes)
3. Access at: `https://emailcraft-ai.onrender.com`

### Auto-Deploy

Once connected, pushing to `main` automatically triggers deployment:

```bash
git push origin main  # Triggers auto-deploy
```

---

## 🔐 Environment Variables

### Required

```env
# LLM (Required)
GROQ_API_KEY=gsk_your_api_key_here
```

### Production (Optional)

```env
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# Vector Store (Pinecone)
PINECONE_API_KEY=pcsk_your_api_key_here
PINECONE_ENVIRONMENT=us-east-1

# Model Configuration
GROQ_MODEL=llama-3.1-8b-instant

# Telemetry
ANONYMIZED_TELEMETRY=False
```

---

## 🗄️ Database Setup

### Option 1: Supabase (Recommended)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to **Settings** → **Database**
4. Copy **Connection string** (URI format)
5. Add to Render as `DATABASE_URL`

### Option 2: Render PostgreSQL

1. In Render, create **PostgreSQL** service
2. Copy **Internal Database URL**
3. Add to your web service as `DATABASE_URL`

### Auto-Migration

Tables are created automatically on first run. The app detects:

- `DATABASE_URL` set → PostgreSQL mode
- `DATABASE_URL` not set → SQLite mode (local file)

---

## 🔍 Vector Store Setup

### Local: ChromaDB (Automatic)

No setup required! ChromaDB runs automatically in local mode:

- **Location**: `vectorstore/chroma_db/`
- **Embedding Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimensions**: 384

### Production: Pinecone Setup

1. Create account at [pinecone.io](https://pinecone.io)
2. Create new index:
   - **Name**: `email-templates` (auto-created by app)
   - **Dimensions**: `1024`
   - **Metric**: `cosine`
   - **Cloud**: AWS
   - **Region**: `us-east-1`
3. Copy API key from dashboard
4. Add to Render environment:
   - `PINECONE_API_KEY`: Your API key
   - `PINECONE_ENVIRONMENT`: `us-east-1`

### Embedding Models Comparison

| Environment    | Model                   | Dimensions | Provider                      |
| -------------- | ----------------------- | ---------- | ----------------------------- |
| **Local**      | `all-MiniLM-L6-v2`      | 384        | sentence-transformers (local) |
| **Production** | `multilingual-e5-large` | 1024       | Pinecone Inference API        |

### Auto-Detection

The app automatically selects:

- `PINECONE_API_KEY` set → Pinecone (production)
- `PINECONE_API_KEY` not set → ChromaDB (local)

---

## 🐳 Docker Deployment

### Build & Run Locally

```bash
# Build
docker build -t emailcraft-ai .

# Run
docker run -p 8000:10000 \
  -e GROQ_API_KEY=your_key \
  emailcraft-ai
```

### Dockerfile Overview

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

The repository includes `.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Trigger Render Deploy
        run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
```

### Setup

1. In Render → Service → **Settings** → Copy **Deploy Hook URL**
2. In GitHub → Repo → **Settings** → **Secrets** → Add:
   - Name: `RENDER_DEPLOY_HOOK_URL`
   - Value: (paste hook URL)

---

## ⚠️ Rate Limiting

### Groq Free Tier

- **Limit**: 30 requests/minute
- **Per email**: 4-5 LLM calls
- **Solution**: 30-second delay between batch emails

### Batch Processing

| Environment | Delay      | Detection              |
| ----------- | ---------- | ---------------------- |
| Local       | 2 seconds  | No `PINECONE_API_KEY`  |
| Production  | 30 seconds | `PINECONE_API_KEY` set |

### Expected Times

| Emails | Production Time |
| ------ | --------------- |
| 10     | ~8-10 minutes   |
| 20     | ~15-18 minutes  |
| 50     | ~35-45 minutes  |

---

## 🐛 Troubleshooting

### Build Failures

| Error                        | Solution                                   |
| ---------------------------- | ------------------------------------------ |
| `requirements.txt not found` | Ensure file is committed                   |
| `ModuleNotFoundError`        | Check all dependencies in requirements.txt |
| `Memory exceeded`            | Upgrade Render plan                        |

### Runtime Errors

| Error                    | Solution                                    |
| ------------------------ | ------------------------------------------- |
| `GROQ_API_KEY not found` | Set in Render environment                   |
| `429 Too Many Requests`  | Wait for rate limit reset (1 min)           |
| `502 Bad Gateway`        | Batch delay is working, wait for completion |
| `Connection refused`     | Check DATABASE_URL format                   |

### Health Check

Test your deployment:

```bash
curl https://emailcraft-ai.onrender.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "message": "Cold Outreach AI Agent is running"
}
```

---

## 📊 Monitoring

### Render Dashboard

- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, requests
- **Events**: Deploy history

### Log Messages

```
✅ Using PostgreSQL database (Supabase)
✅ Pinecone index 'email-templates' initialized
✅ System ready - first request will be fast!
⏳ Waiting 30s before next email...
```

---

## 🔐 Security Checklist

- [ ] `GROQ_API_KEY` in Render environment (not in code)
- [ ] `DATABASE_URL` in Render environment
- [ ] `PINECONE_API_KEY` in Render environment
- [ ] `.env` in `.gitignore`
- [ ] CORS configured for production domain
- [ ] Health check endpoint accessible

---

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Render Docs**: [docs.render.com](https://docs.render.com)
- **Groq Docs**: [console.groq.com/docs](https://console.groq.com/docs)
- **Pinecone Docs**: [docs.pinecone.io](https://docs.pinecone.io)

---

<div align="center">

**Ready to deploy? Let's go! 🚀**

</div>
