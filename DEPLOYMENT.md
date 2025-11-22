# Deployment Guide - Link-to-Social Agent

This guide covers deploying the Link-to-Social Agent to Railway.

## 🚂 Railway Deployment

### Option 1: Quick Deploy via Railway Dashboard

1. **Prepare Your Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Create Railway Project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**
   - Go to your service → Variables tab
   - Add `VENICE_API_KEY` with your Venice.ai API key
   - Value: `lnWNeSg0pA_rQUooNpbfpPDBaj2vJnWol5WqKWrIEF`

4. **Configure Service Settings**
   - Railway should auto-detect FastAPI
   - If not, set:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
     - **Health Check Path**: `/health`

5. **Deploy**
   - Railway will automatically deploy
   - Watch the build logs
   - Your app will be live at `https://<your-project>.railway.app`

### Option 2: Deploy via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Link to existing project (if needed)
railway link

# Set environment variables
railway variables set VENICE_API_KEY=lnWNeSg0pA_rQUooNpbfpPDBaj2vJnWol5WqKWrIEF

# Deploy
railway up
```

### Option 3: Docker Deployment

If you prefer Docker (recommended for production):

1. **Build and Test Locally**
   ```bash
   docker build -t link-to-social .
   docker run -p 8000:8000 -e VENICE_API_KEY=your_key link-to-social
   ```

2. **Deploy to Railway**
   - Railway automatically detects `Dockerfile`
   - Just push to GitHub and Railway will build from Dockerfile
   - Add environment variables in Railway dashboard

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VENICE_API_KEY` | Your Venice.ai API key | `lnWNeSg0pA_rQUooNpbfpPDBaj2vJnWol5WqKWrIEF` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODEL` | LLM model ID | `llama-3.2-3b` |
| `IMAGE_MODEL` | Image generation model | `venice-sd35` |
| `PORT` | Server port | `8000` (Railway sets this) |

## 📊 Monitoring

### View Logs

```bash
# Via CLI
railway logs

# Via Dashboard
# Go to your service → Deployments → View logs
```

### Health Check

Railway automatically checks `/health` endpoint:
- ✅ Healthy: Returns 200 OK
- ❌ Unhealthy: Service will restart

## 🐛 Troubleshooting

### Build Fails

**Issue**: Dependencies not installing
```bash
# Check requirements.txt
# Ensure all packages are listed
# Try building locally first:
pip install -r requirements.txt
```

**Issue**: Python version mismatch
- Railway uses Python 3.11 by default (from Dockerfile)
- If issues, specify in `runtime.txt`:
  ```
  python-3.11
  ```

### Deployment Fails

**Issue**: Application won't start
- Check Railway logs for errors
- Verify `VENICE_API_KEY` is set
- Ensure port uses `$PORT` environment variable
- Check health endpoint: `curl https://your-app.railway.app/health`

**Issue**: Timeout errors
- Increase health check timeout in `railway.json`
- Check if Venice.ai API is accessible
- Verify API key is valid

### Runtime Errors

**Issue**: Scraping fails
- Some websites block scrapers
- Check logs for specific error
- May need to adjust User-Agent or timeout

**Issue**: Image generation fails
- Verify Venice.ai API key is correct
- Check API quota/balance
- Ensure image model is available

## 💰 Cost Considerations

### Railway Pricing
- **Hobby Plan**: Free tier available (limited hours)
- **Pro Plan**: $20/month (unlimited usage)
- Check [Railway pricing](https://railway.app/pricing) for details

### Venice.ai API Costs
- Text generation: ~$0.15-0.60 per 1M tokens (input/output)
- Image generation: ~$0.01 per image
- Each request uses:
  - 1 LLM call (text generation)
  - 2 image generations
  - Estimated cost: ~$0.03 per article

### Optimizations
- Use faster/cheaper models in `config.py`
- Reduce image steps if speed is priority
- Cache results for duplicate URLs

## 🚀 Post-Deployment

### Test Your Deployment

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Test processing
curl -X POST https://your-app.railway.app/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

### Custom Domain (Optional)

1. Go to Railway dashboard
2. Service → Settings → Generate Domain
3. Or add custom domain in Domains tab

### Continuous Deployment

- Railway automatically deploys on `git push`
- Monitor deployments in Railway dashboard
- Set up branch deployments for staging

## 📝 Checklist

Before deploying:

- [ ] Code pushed to GitHub
- [ ] `VENICE_API_KEY` environment variable set
- [ ] Tested locally with `python app.py`
- [ ] Dockerfile builds successfully (if using)
- [ ] Health endpoint works (`/health`)
- [ ] Railway project created and linked

After deploying:

- [ ] Application accessible at Railway URL
- [ ] Health check returns 200
- [ ] Can process a test URL
- [ ] Logs show no errors
- [ ] Environment variables visible in dashboard

## 🔐 Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use Railway secrets** for sensitive data
3. **Rotate API keys** regularly
4. **Monitor API usage** in Venice.ai dashboard
5. **Set up rate limiting** (future enhancement)

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Venice.ai API Docs](https://docs.venice.ai)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---

**Need Help?**
- Check Railway logs
- Review Venice.ai API status
- Verify environment variables are set correctly

