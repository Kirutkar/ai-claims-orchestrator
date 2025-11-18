# Deploy Frontend + Backend Together on Render

This guide shows how to deploy both React frontend and FastAPI backend together on Render in a single deployment.

## 🎯 Architecture

```
┌─────────────────────┐
│  Frontend (React)   │ → https://ai-claims-frontend.onrender.com
│  Port: 3000         │
└──────────┬──────────┘
           │
           │ API Calls (/api/*)
           │
┌──────────▼──────────┐
│  Backend (FastAPI)  │ → https://ai-claims-backend.onrender.com
│  Port: 8000         │
└─────────────────────┘
```

## ✅ What's Configured

The `render.yaml` file includes **both services**:

1. **Backend Service** (`ai-claims-backend`)
   - FastAPI application
   - Docker-based
   - Port 8000

2. **Frontend Service** (`ai-claims-frontend`)
   - React application
   - Docker-based (builds React, serves static files)
   - Port 3000
   - Automatically configured to use backend URL

## 🚀 Deployment Steps

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Configure frontend + backend deployment"
git push origin main
```

### Step 2: Deploy on Render

1. **Go to Render**: https://render.com
2. **Sign up** (free, no credit card)
3. **New → Blueprint** (or "New Static Site" + "New Web Service")
4. **Connect GitHub** and select your repo
5. **Render will detect `render.yaml`** and create both services automatically!

### Step 3: Set Environment Variables

#### Backend Environment Variables:
- `GEMINI_API_KEY` (required)
- `QDRANT_URL` or `QDRANT_HOST` (required)
- `QDRANT_API_KEY` (if needed)

#### Frontend Environment Variables:
- `VITE_API_URL` - **Automatically set** from backend service URL! ✨
- No manual configuration needed!

### Step 4: Deploy!

Click "Apply" and Render will:
1. Build backend Docker image
2. Build frontend Docker image (with backend URL)
3. Deploy both services
4. Link them together

## 🌐 Access Your Application

After deployment:

- **Frontend**: `https://ai-claims-frontend.onrender.com`
- **Backend API**: `https://ai-claims-backend.onrender.com`
- **API Docs**: `https://ai-claims-backend.onrender.com/docs`

## 🔗 How It Works

### Automatic Backend URL Injection

Render automatically sets `VITE_API_URL` in the frontend service using the backend service URL:

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

### Frontend API Configuration

The frontend uses `VITE_API_URL` environment variable:

```javascript
// frontend/src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

When deployed:
- `VITE_API_URL` = `https://ai-claims-backend.onrender.com`
- All API calls go to the backend automatically

## 📋 Environment Variables

### Backend (`ai-claims-backend`)

**Required:**
- `GEMINI_API_KEY` - Google Gemini API key

**Qdrant (choose one):**
- `QDRANT_URL` - Qdrant cloud URL
- `QDRANT_HOST` - Qdrant host
- `QDRANT_API_KEY` - Qdrant API key (if needed)

**Optional:**
- `GEMINI_MODEL` - Default: `gemini-1.5-flash`
- `DEBUG_MODE` - Default: `false`
- `QDRANT_COLLECTION` - Default: `insurance_claims`

### Frontend (`ai-claims-frontend`)

**Automatically Set:**
- `VITE_API_URL` - Backend service URL (from Render)

**Optional:**
- `NODE_ENV` - Default: `production`

## ✅ Verification

### Test Backend
```bash
curl https://ai-claims-backend.onrender.com/
curl https://ai-claims-backend.onrender.com/health
```

### Test Frontend
```bash
curl https://ai-claims-frontend.onrender.com/
```

### Test Integration
1. Open frontend: `https://ai-claims-frontend.onrender.com`
2. Submit a claim
3. Check browser console - API calls should go to backend
4. Verify claim appears in backend

## 🔧 Troubleshooting

### Frontend Can't Connect to Backend

**Issue**: Frontend shows API errors

**Solution**:
1. Check `VITE_API_URL` is set in frontend service
2. Verify backend is running: `curl https://ai-claims-backend.onrender.com/`
3. Check CORS settings in backend (should allow frontend origin)
4. Check browser console for errors

### Backend CORS Issues

**Issue**: CORS errors in browser

**Solution**:
1. In backend environment variables, set:
   ```
   CORS_ORIGINS=https://ai-claims-frontend.onrender.com
   ```
2. Or use `*` for testing (already set in render.yaml)

### Build Fails

**Issue**: Frontend build fails

**Solution**:
1. Check logs in Render dashboard
2. Verify `VITE_API_URL` is available at build time
3. Check `frontend/Dockerfile` is correct
4. Ensure `package.json` has build script

## 💡 Tips

1. **Free Tier**: Both services use free tier (750 hours/month each)
2. **Spin-down**: Both services spin down after 15 min inactivity
3. **First Request**: May take 30-60 seconds after spin-down
4. **Keep-Alive**: Use UptimeRobot to ping both services

## 📊 Service Status

Check both services in Render dashboard:
- Backend: Shows health status, logs, metrics
- Frontend: Shows build status, logs, metrics

## 🔄 Updates

When you push to GitHub:
- ✅ Both services auto-deploy (if `autoDeploy: true`)
- ✅ Frontend rebuilds with latest backend URL
- ✅ Backend redeploys with latest code

## 🎉 Success!

Your full-stack application is now live:
- ✅ Frontend: React app
- ✅ Backend: FastAPI API
- ✅ Both deployed together
- ✅ Automatically linked
- ✅ Free tier (no credit card)

## 📚 Next Steps

1. ✅ Test all features
2. ✅ Set up monitoring (optional)
3. ✅ Configure custom domains (optional)
4. ✅ Set up keep-alive service (optional)

Enjoy your deployed application! 🚀

