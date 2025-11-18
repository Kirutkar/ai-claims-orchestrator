# Quick Start - Render Deployment

## 🚀 Deploy to Render in 5 Minutes

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Deploy on Render

1. **Sign up**: https://render.com (free, no credit card)
2. **New Web Service** → Connect GitHub → Select repo
3. **Render auto-detects** `render.yaml` configuration
4. **Add Environment Variables**:
   - `GEMINI_API_KEY` (required)
   - `QDRANT_URL` or `QDRANT_HOST` (required)
   - `QDRANT_API_KEY` (if needed)

### Step 3: Deploy!

Click "Create Web Service" and wait ~5 minutes.

Your backend will be live at: `https://ai-claims-backend.onrender.com`

## 📝 Environment Variables

**Required:**
- `GEMINI_API_KEY` - Your Google Gemini API key

**Qdrant (choose one):**
- `QDRANT_URL` - Qdrant cloud URL (e.g., `https://xxx.qdrant.io`)
- `QDRANT_HOST` - Qdrant host (e.g., `your-server.com`)
- `QDRANT_PORT` - Qdrant port (default: `6333`)
- `QDRANT_API_KEY` - Qdrant API key (if needed)

**Optional:**
- `GEMINI_MODEL` - Default: `gemini-1.5-flash`
- `DEBUG_MODE` - Default: `false`
- `QDRANT_COLLECTION` - Default: `insurance_claims`

## ✅ Verify Deployment

```bash
# Test root endpoint
curl https://your-app.onrender.com/

# Test health check
curl https://your-app.onrender.com/health

# View API docs
# Open: https://your-app.onrender.com/docs
```

## 📚 Full Documentation

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed guide.

## 🆓 Free Tier

- ✅ 750 hours/month (enough for ~25 days 24/7)
- ✅ 512 MB RAM
- ✅ Free SSL
- ⚠️ Spins down after 15 min inactivity
- ⚠️ First request after spin-down takes 30-60 seconds

## 🔧 Troubleshooting

**Build fails?** Check logs in Render dashboard
**Service won't start?** Verify environment variables
**Can't connect to Qdrant?** Check QDRANT_URL/HOST is correct

## 🎉 Done!

Your backend is now live on Render! 🚀

