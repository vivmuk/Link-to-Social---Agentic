# Quick Start Guide - Link-to-Social Agent

Get up and running in 5 minutes!

## 🚀 Local Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable

Create a `.env` file in the project root:

```bash
VENICE_API_KEY=lnWNeSg0pA_rQUooNpbfpPDBaj2vJnWol5WqKWrIEF
```

### 3. Run the Application

```bash
python app.py
```

Visit `http://localhost:8000` in your browser.

## 🌐 Test It Out

### Via Browser
1. Open `http://localhost:8000`
2. Paste any article URL
3. Click "Generate Content"
4. Wait 20-30 seconds
5. Download your posts and images!

### Via API

```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/article"}'
```

## 🚂 Deploy to Railway

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

### Step 2: Connect to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 3: Set Environment Variable

1. Go to your service → Variables tab
2. Add: `VENICE_API_KEY` = `lnWNeSg0pA_rQUooNpbfpPDBaj2vJnWol5WqKWrIEF`

### Step 4: Deploy!

Railway will automatically:
- Detect FastAPI
- Install dependencies
- Start the server
- Provide a URL like `https://your-app.railway.app`

## ✅ Verify Deployment

```bash
# Check health
curl https://your-app.railway.app/health

# Should return: {"status":"healthy","service":"link-to-social-agent"}
```

## 📝 What You Get

For each article URL, you'll receive:

1. **LinkedIn Post** (3-5 sentences)
2. **X/Twitter Post** (< 280 characters)
3. **Key Insights** (3-5 bullet points)
4. **Infographic Image** (1080x1080, watercolor style)
5. **Social Media Image** (1080x1080, optimized for posts)

## 🎨 Example Output

### LinkedIn Post
```
🎯 Strategic insights from the latest industry analysis reveal three key trends 
shaping the consulting landscape in 2024. Data-driven decision making, 
AI integration, and sustainable business practices are emerging as critical 
differentiators. How is your organization adapting to these shifts?
```

### X/Twitter Post
```
🚀 Key insights: Strategic transformation requires three pillars—data, AI, and 
sustainability. How's your organization adapting? #Consulting #Strategy
```

## 🐛 Troubleshooting

### "VENICE_API_KEY not found"
- Ensure `.env` file exists in project root
- Check variable name is exactly `VENICE_API_KEY`
- Restart your application after adding `.env`

### "Module not found"
- Run `pip install -r requirements.txt`
- Ensure you're in the project directory
- Check Python version (3.9+ required)

### Scraping fails
- Try a different article URL
- Some sites block scrapers
- Check logs for specific error message

### Image generation fails
- Verify Venice.ai API key is correct
- Check API balance/quota
- Ensure internet connection

## 📚 Next Steps

- Read [README.md](README.md) for full documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide
- Customize prompts in `agents/` directory
- Adjust image styles in `agents/creative_agent.py`

## 🎯 Tips

- **Faster Processing**: Use `llama-3.2-3b` model (default)
- **Better Quality**: Switch to `llama-3.3-70b` in `config.py`
- **Custom Styles**: Edit prompts in `agents/creative_agent.py`
- **Different Images**: Adjust `image_model` in `config.py`

---

**Ready to transform articles into social media gold! 🎉**

