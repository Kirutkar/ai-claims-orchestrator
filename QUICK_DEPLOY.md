# Quick Deploy Guide - Frontend + Backend Together

## 🚀 Single Deployment for Both Services

Your repository is now configured to deploy **both frontend and backend together** on Render!

## ✅ What's Configured

- ✅ `render.yaml` - Contains both services
- ✅ Backend Dockerfile - Production-ready
- ✅ Frontend Dockerfile - Builds React and serves static files
- ✅ Automatic backend URL injection - Frontend knows backend URL automatically

## 📋 Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Configure frontend + backend deployment"
git push origin main
```

### 2. Deploy on Render

1. Go to **https://render.com**
2. Sign up (free, no credit card)
3. Click **"New +"** → **"Blueprint"**
4. Connect your GitHub repository
5. Select `ai-claims-orchestrator`
6. Render will **automatically detect** `render.yaml` and create **both services**!

### 3. Set Environment Variables

**Backend Service:**
- `GEMINI_API_KEY` (required)
- `QDRANT_URL` or `QDRANT_HOST` (required)
- `QDRANT_API_KEY` (if needed)

**Frontend Service:**
- ✅ `VITE_API_URL` - **Automatically set** from backend URL!
- No manual configuration needed!

### 4. Deploy!

Click "Apply" and Render will:
1. ✅ Build backend Docker image
2. ✅ Build frontend Docker image (with backend URL baked in)
3. ✅ Deploy both services
4. ✅ Link them together

## 🌐 Your URLs

After deployment:

- **Frontend**: `https://ai-claims-frontend.onrender.com`
- **Backend API**: `https://ai-claims-backend.onrender.com`
- **API Docs**: `https://ai-claims-backend.onrender.com/docs`

## ✨ Key Features

### Automatic Backend URL Injection

Render automatically sets `VITE_API_URL` in frontend using backend service URL:

```yaml
envVars:
  - key: VITE_API_URL
    fromService:
      type: web
      name: ai-claims-backend
      property: url
```

This means:
- ✅ Frontend automatically knows backend URL
- ✅ No manual configuration needed
- ✅ Works even if backend URL changes
- ✅ Both services deploy together

### How It Works

1. **Backend deploys first** → Gets URL: `https://ai-claims-backend.onrender.com`
2. **Frontend builds** → Render injects backend URL as `VITE_API_URL`
3. **Frontend builds React** → Vite bakes backend URL into the build
4. **Frontend deploys** → Serves static files with correct API URL

## ✅ Verification

### Test Backend
```bash
curl https://ai-claims-backend.onrender.com/
```

### Test Frontend
```bash
curl https://ai-claims-frontend.onrender.com/
```

### Test Integration
1. Open: `https://ai-claims-frontend.onrender.com`
2. Submit a claim
3. Check browser console - API calls should work
4. Verify claim appears

## 🆓 Free Tier

Both services use free tier:
- ✅ 750 hours/month each (enough for ~25 days 24/7)
- ✅ 512 MB RAM each
- ✅ Free SSL for both
- ⚠️ Both spin down after 15 min inactivity
- ⚠️ First request after spin-down takes 30-60 seconds

## 🔧 Troubleshooting

### Frontend Can't Connect to Backend

**Check:**
1. Backend is running: `curl https://ai-claims-backend.onrender.com/`
2. `VITE_API_URL` is set in frontend service (check Render dashboard)
3. CORS is configured (should allow frontend origin)

### Build Fails

**Check:**
1. Logs in Render dashboard
2. `VITE_API_URL` is available at build time
3. Frontend Dockerfile is correct

## 📚 Full Documentation

See [DEPLOY_BOTH.md](DEPLOY_BOTH.md) for complete guide.

## 🎉 Success!

Your full-stack application is now live:
- ✅ Frontend: React app
- ✅ Backend: FastAPI API  
- ✅ Both deployed together
- ✅ Automatically linked
- ✅ Free tier (no credit card)

Enjoy! 🚀

