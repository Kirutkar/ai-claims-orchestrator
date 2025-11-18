# Render Deployment Guide

This guide will help you deploy the AI Claims Orchestrator backend to Render.

## Prerequisites

1. GitHub account
2. Render account (free, no credit card required)
3. Google Gemini API key
4. Qdrant instance (cloud or external)

## Step 1: Prepare Your Repository

The repository is already configured with:
- ✅ `render.yaml` - Render configuration
- ✅ `backend/Dockerfile` - Production-ready Dockerfile
- ✅ `.renderignore` - Files to exclude from deployment

## Step 2: Push to GitHub

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

## Step 3: Deploy on Render

### 3.1 Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended) or email
4. **No credit card required!**

### 3.2 Create New Web Service

1. Click "New +" button
2. Select "Web Service"
3. Connect your GitHub repository
4. Select the repository: `ai-claims-orchestrator`

### 3.3 Configure Service

Render will automatically detect `render.yaml` and configure:
- **Name**: `ai-claims-backend` (or customize)
- **Region**: Oregon (or choose closest)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (uses root)
- **Runtime**: Docker (auto-detected)

### 3.4 Set Environment Variables

Click "Environment" tab and add:

**Required:**
```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Qdrant Configuration (choose one):**

**Option A: Qdrant Cloud**
```
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

**Option B: External Qdrant Server**
```
QDRANT_HOST=your-qdrant-server.com
QDRANT_PORT=6333
QDRANT_API_KEY=your_api_key_if_needed
```

**Optional (already set in render.yaml):**
```
GEMINI_MODEL=gemini-1.5-flash
QDRANT_COLLECTION=insurance_claims
DEBUG_MODE=false
```

### 3.5 Deploy

1. Click "Create Web Service"
2. Render will:
   - Build Docker image
   - Install dependencies
   - Start the service
3. Wait for deployment (5-10 minutes first time)

## Step 4: Verify Deployment

### Check Logs

In Render dashboard, click "Logs" tab. You should see:

```
✅ Connected to Qdrant at ...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test Endpoints

Your backend will be available at:
```
https://ai-claims-backend.onrender.com
```

Test endpoints:
```bash
# Root endpoint
curl https://ai-claims-backend.onrender.com/

# Health check
curl https://ai-claims-backend.onrender.com/health

# API docs
# Open in browser: https://ai-claims-backend.onrender.com/docs
```

## Step 5: Update Frontend (if needed)

If you have a frontend, update the API URL:

```javascript
// In frontend/src/services/api.js
const API_BASE_URL = 'https://ai-claims-backend.onrender.com';
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key | `AIza...` |
| `QDRANT_URL` | ⚠️ One of | Qdrant cloud URL | `https://xxx.qdrant.io` |
| `QDRANT_HOST` | ⚠️ One of | Qdrant host (if not URL) | `host.docker.internal` |
| `QDRANT_PORT` | No | Qdrant port | `6333` |
| `QDRANT_API_KEY` | No | Qdrant API key | `xxx` |
| `QDRANT_COLLECTION` | No | Collection name | `insurance_claims` |
| `GEMINI_MODEL` | No | Gemini model | `gemini-1.5-flash` |
| `DEBUG_MODE` | No | Debug mode | `false` |

## Free Tier Limitations

Render free tier includes:
- ✅ 750 hours/month (enough for 24/7 for ~25 days)
- ✅ 512 MB RAM
- ✅ Auto SSL certificates
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ First request after spin-down takes 30-60 seconds

### Keep Service Awake (Optional)

To prevent spin-down, you can use a service like:
- UptimeRobot (free)
- cron-job.org (free)
- Set up a simple ping every 10 minutes

## Troubleshooting

### Build Fails

**Issue**: Docker build fails
**Solution**: 
- Check logs in Render dashboard
- Verify `backend/Dockerfile` is correct
- Ensure `requirements.txt` is valid

### Service Won't Start

**Issue**: Service crashes on start
**Solution**:
- Check logs for errors
- Verify environment variables are set
- Check Qdrant connection

### Can't Connect to Qdrant

**Issue**: Qdrant connection errors
**Solution**:
- Verify `QDRANT_URL` or `QDRANT_HOST` is correct
- Check Qdrant is accessible from Render's network
- For local Qdrant, use `host.docker.internal` won't work - use external URL

### Slow First Request

**Issue**: First request is slow
**Solution**: 
- This is normal - service spins down after inactivity
- Use a keep-alive service to prevent spin-down
- Or upgrade to paid plan for always-on

## Updating Deployment

### Automatic Updates

With `autoDeploy: true` in `render.yaml`, Render automatically deploys when you push to the connected branch.

### Manual Update

1. Go to Render dashboard
2. Click "Manual Deploy"
3. Select branch/commit
4. Deploy

## Monitoring

### View Logs

- Real-time logs in Render dashboard
- Click "Logs" tab in your service

### Metrics

- View metrics in Render dashboard
- CPU, Memory, Request count

## Security Best Practices

1. ✅ Never commit `.env` files
2. ✅ Use Render's environment variables (encrypted)
3. ✅ Keep API keys secret
4. ✅ Use HTTPS (auto-enabled by Render)
5. ✅ Set `DEBUG_MODE=false` in production

## Cost

**Free Tier**: $0/month
- 750 hours/month
- 512 MB RAM
- 100 GB bandwidth

**Paid Plans**: Start at $7/month
- Always-on (no spin-down)
- More resources
- Better performance

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Render Status: https://status.render.com

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Test all endpoints
3. ✅ Update frontend API URL
4. ✅ Set up monitoring (optional)
5. ✅ Configure keep-alive (optional)

Your backend is now live! 🚀

