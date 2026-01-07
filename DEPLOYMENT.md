# Deployment Guide

This guide covers deploying EmailCraft AI to production using Docker and Render.

## 📋 Prerequisites

- GitHub account
- [Render](https://render.com) account (free tier available)
- GROQ API key from [console.groq.com](https://console.groq.com)

## 🐳 Docker Deployment

### Build Locally

```bash
# Build the Docker image
docker build -t emailcraft-ai .

# Run locally
docker run -p 8000:10000 \
  -e GROQ_API_KEY=your_api_key_here \
  -e GROQ_MODEL=llama-3.1-8b-instant \
  emailcraft-ai
```

Access at: `http://localhost:8000`

### Docker Configuration

The `Dockerfile` includes:

- Python 3.11 slim base image
- All dependencies from `requirements.txt`
- Frontend static files served by FastAPI
- Health check endpoint
- Runs on port 10000 (Render default)

## 🚀 Render Deployment

> **Auto-Deploy Enabled**: Once set up, pushing to `main` branch automatically triggers deployment - no manual clicking needed!

### Step 1: Prepare Your Repository

1. **Create GitHub Repository**

   ```bash
   # Initialize git (if not already done)
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create repo on GitHub** named `emailcraft-ai`

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/emailcraft-ai.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Connect Render to GitHub

1. **Go to Render Dashboard**: [https://dashboard.render.com](https://dashboard.render.com)

2. **First-time GitHub Setup** (if not connected):
   - Click your profile (top right) → **Account Settings**
   - Scroll to **GitHub** section
   - Click **Connect GitHub Account**
   - Authorize Render to access your repositories
   - Select **All repositories** or specific repos

### Step 3: Deploy with Blueprint (Recommended)

1. **Create New Service**

   - Dashboard → Click **New +** → **Blueprint**

2. **Select Repository**

   - Choose `emailcraft-ai` from the list
   - Click **Connect**

3. **Review Blueprint**

   - Render reads `render.yaml` automatically
   - Service name: `emailcraft-ai`
   - Region: Oregon (or closest to you)
   - Plan: Free
   - Click **Apply**

4. **Configure Environment Variables** (IMPORTANT!)

   - In the blueprint setup, you'll see environment variables
   - Click **Edit** next to `GROQ_API_KEY`
   - Enter your actual API key from [console.groq.com](https://console.groq.com)
   - `GROQ_MODEL` is already set to `llama-3.1-8b-instant`

5. **Deploy Service**

   - Click **Create Services**
   - Wait for initial build (~5-10 minutes)
   - Monitor build logs in real-time

6. **Verify Deployment**
   - Once status shows **Live** (green)
   - Your URL: `https://emailcraft-ai.onrender.com`
   - Click the URL to test the app

### Step 4: Enable Auto-Deploy (Already Set!)

✅ **Auto-deploy is enabled by default** via `render.yaml`:

```yaml
autoDeploy: true
```

**How it works:**

- Push to `main` → Render automatically detects → Builds → Deploys
- No manual clicking needed after initial setup
- Check **Events** tab to see auto-deploy history

### Step 5: Verify Settings

Go to your service → **Settings** tab and verify:

**Service Details:**

- ✅ Name: `emailcraft-ai`
- ✅ Runtime: Docker
- ✅ Branch: `main`
- ✅ Auto-Deploy: Enabled

**Build & Deploy:**

- ✅ Dockerfile Path: `./Dockerfile`
- ✅ Docker Command: Auto-detected from Dockerfile

**Health Checks:**

- ✅ Health Check Path: `/health`
- ✅ Health check should pass after deployment

**Environment Variables:**

- ✅ `GROQ_API_KEY`: [your key]
- ✅ `GROQ_MODEL`: `llama-3.1-8b-instant`
- ✅ `ANONYMIZED_TELEMETRY`: `False`

### Common First Deploy Issues

**Issue: Build fails with "requirements.txt not found"**

- Ensure all files are committed: `git status`
- Push all files: `git add . && git commit -m "Add all files" && git push`

**Issue: Service starts but crashes**

- Check **Logs** tab for Python errors
- Verify `GROQ_API_KEY` is set correctly
- Test locally first: `docker build -t emailcraft-ai . && docker run -p 8000:10000 emailcraft-ai`

**Issue: Service shows "Deploying" forever**

- Check build logs for stuck steps
- Free tier may be slower during peak times
- Cancel and retry deployment

**Issue: Can't connect to GitHub**

- Revoke and reconnect GitHub in Account Settings
- Ensure repository is public or Render has access to private repos

### Option 2: Manual Docker Service

1. **Go to Render Dashboard**
2. **New** → **Web Service**
3. **Connect Repository**
4. **Configure**:

   - Name: `emailcraft-ai`
   - Runtime: `Docker`
   - Region: Oregon (or closest)
   - Branch: `main`
   - Plan: Free

5. **Environment Variables**:

   ```
   GROQ_API_KEY=your_api_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   ANONYMIZED_TELEMETRY=False
   ```

6. **Deploy**

## 🔄 GitHub Actions CI/CD

The repository includes automated CI/CD via GitHub Actions.

### Pipeline Overview

```
Push to main → Lint → Build Docker → Deploy to Render
```

### Setup Auto-Deploy

1. **Get Render Deploy Hook**

   - Go to Render Dashboard → Your Service → Settings
   - Scroll to **Deploy Hook**
   - Copy the URL

2. **Add GitHub Secret**

   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Click **New repository secret**
   - Name: `RENDER_DEPLOY_HOOK_URL`
   - Value: (paste the Deploy Hook URL)

3. **Trigger Deployment**
   - Push to `main` branch
   - GitHub Actions will:
     1. Lint code
     2. Build Docker image
     3. Trigger Render deployment

### Manual Workflow Trigger

You can also trigger deployment manually:

1. Go to Actions tab in GitHub
2. Select "CI/CD Pipeline"
3. Click "Run workflow"

## 📁 Configuration Files

### render.yaml

```yaml
services:
  - type: web
    name: emailcraft-ai
    runtime: docker
    region: oregon
    plan: free
    dockerfilePath: ./Dockerfile
    envVars:
      - key: GROQ_API_KEY
        sync: false # Set manually
      - key: GROQ_MODEL
        value: llama-3.1-8b-instant
    healthCheckPath: /health
    autoDeploy: true
```

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
```

## 🔍 Health Check

The app includes a health check endpoint:

```bash
curl https://your-app.onrender.com/health
```

Response:

```json
{
  "status": "healthy",
  "message": "Cold Outreach AI Agent is running"
}
```

## ⚠️ Important Notes

### Free Tier Limitations

Render free tier:

- Spins down after 15 minutes of inactivity
- Cold start takes ~30-60 seconds
- 750 hours/month limit

### Production Recommendations

1. **Upgrade Plan**: For production use, upgrade to paid tier for always-on service
2. **Custom Domain**: Add your own domain in Render settings
3. **CORS**: Update `main.py` to restrict origins
4. **Rate Limiting**: Consider adding rate limiting for API endpoints

### Environment Variables

| Variable               | Required | Default                | Description        |
| ---------------------- | -------- | ---------------------- | ------------------ |
| `GROQ_API_KEY`         | Yes      | -                      | Your Groq API key  |
| `GROQ_MODEL`           | No       | `llama-3.1-8b-instant` | Groq model to use  |
| `ANONYMIZED_TELEMETRY` | No       | `False`                | ChromaDB telemetry |

## 🐛 Troubleshooting

### Build Failures

- Check Render logs for specific errors
- Ensure all files are committed to Git
- Verify `requirements.txt` is up to date

### App Not Loading

- Check if service is deployed (green status)
- Wait for cold start if using free tier
- Check health endpoint: `/health`

### API Errors

- Verify `GROQ_API_KEY` is set correctly
- Check Groq API quota at [console.groq.com](https://console.groq.com)

### ChromaDB Issues

- The vector store is created fresh on each deploy
- Data persists within the container but resets on redeploy
- For persistent storage, consider upgrading to use Render disks

## 📊 Monitoring

### Render Dashboard

- View logs in real-time
- Monitor CPU/memory usage
- Check request metrics

### Logs

Access logs via:

```bash
# In Render dashboard
Logs tab → Select your service
```

## 🔐 Security Checklist

- [ ] `GROQ_API_KEY` set as environment variable (not in code)
- [ ] CORS configured for production domain
- [ ] `.env` file not committed to Git
- [ ] Health check endpoint accessible

---

**Need help?** Open an issue on GitHub.
