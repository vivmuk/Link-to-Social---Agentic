# Link-to-Social Agent

A multi-agent LangGraph system that transforms articles into professional social media content with AI-generated images. Built for management consulting firms with a sophisticated, watercolor-inspired aesthetic.

## 🎯 Features

- **Multi-Agent Workflow**: Scraper → Summarizer → Creative → Coordinator
- **Professional Content**: Management consulting-style social media posts
- **AI-Generated Images**: Two professional images per article:
  - Infographic (watercolor style)
  - Social media post image
- **Dual Platform Support**: LinkedIn and X/Twitter formatted posts
- **Venice.ai Integration**: Powered by Venice.ai for both text and image generation

## 🛠️ Tech Stack

- **LangGraph**: Multi-agent orchestration
- **FastAPI**: Web framework
- **Venice.ai API**: LLM and image generation
- **BeautifulSoup4**: Web scraping
- **aiohttp**: Async HTTP client

## 📋 Prerequisites

- Python 3.9+
- Venice.ai API Key ([Get one here](https://venice.ai))
- Playwright (for advanced scraping, optional)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright (optional, for advanced scraping)
playwright install
```

### 2. Configure Environment

Create a `.env` file:

```bash
VENICE_API_KEY=your_venice_api_key_here
```

### 3. Run Locally

```bash
python app.py
```

Visit `http://localhost:8000` in your browser.

### 4. Test the API

```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

## 📁 Project Structure

```
.
├── agents/
│   ├── scraper_agent.py      # Web scraping agent
│   ├── summarization_agent.py # LLM-powered post generation
│   └── creative_agent.py      # Image generation agent
├── workflow/
│   └── coordinator.py         # LangGraph workflow coordinator
├── app.py                     # FastAPI application
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Configuration

Edit `config.py` to customize:

- **LLM Model**: Default is `llama-3.2-3b` (fast and affordable)
- **Image Model**: Default is `venice-sd35`
- **Image Dimensions**: Default is 1080x1080 (square format)
- **Temperature**: Control creativity of text generation

## 🚂 Deployment to Railway

### Option 1: Deploy via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Set environment variables
railway variables set VENICE_API_KEY=your_api_key_here

# Deploy
railway up
```

### Option 2: Deploy via GitHub

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Connect to Railway**:
   - Go to [Railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**:
   - Go to Variables tab
   - Add `VENICE_API_KEY` with your API key

4. **Deploy**:
   - Railway will automatically detect FastAPI
   - Add a service with the following settings:
     - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
     - **Health Check Path**: `/health`

### Option 3: Using Railway's Dockerfile (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create a `.dockerignore`:

```
__pycache__
*.pyc
.env
.venv
venv/
*.log
.git
```

Then deploy via Railway:

```bash
railway up
```

## 🌐 Railway Configuration

### Port Configuration

Railway automatically provides a `PORT` environment variable. Update `app.py` if needed:

```python
import os

port = int(os.environ.get("PORT", 8000))
uvicorn.run(app, host="0.0.0.0", port=port)
```

### Health Checks

Railway will automatically check `/health` endpoint. Make sure it returns 200.

### Environment Variables

Set these in Railway dashboard:

- `VENICE_API_KEY`: Your Venice.ai API key (required)
- `LLM_MODEL`: Override default LLM model (optional)
- `IMAGE_MODEL`: Override default image model (optional)

## 📊 API Endpoints

### `POST /process`

Process a URL and generate social media content.

**Request**:
```json
{
  "url": "https://example.com/article"
}
```

**Response**:
```json
{
  "status": "success",
  "url": "https://example.com/article",
  "article": {
    "title": "Article Title",
    "author": "Author Name",
    "date": "2024-01-01",
    "url": "https://example.com/article"
  },
  "posts": {
    "linkedin": "LinkedIn post text...",
    "twitter": "Twitter post text...",
    "key_insights": ["Insight 1", "Insight 2"]
  },
  "images": {
    "infographic": "base64-encoded-image",
    "social": "base64-encoded-image"
  }
}
```

### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "link-to-social-agent"
}
```

## 🎨 Customization

### Change Image Style

Edit `agents/creative_agent.py` to modify prompts:

```python
prompt = f"""Your custom style description here..."""
```

### Change Post Style

Edit `agents/summarization_agent.py` to modify the prompt template:

```python
def _create_consulting_prompt(self, title, content, author, url):
    # Customize your prompt here
    return f"""Your custom prompt..."""
```

## 🔍 Troubleshooting

### Scraping Fails

- Check if the URL is publicly accessible
- Some sites block scrapers - try a different article
- Check timeout settings in `config.py`

### Image Generation Fails

- Verify Venice.ai API key is correct
- Check API quota/balance
- Ensure image model is available

### Slow Processing

- Image generation takes 10-20 seconds per image
- Use faster LLM model: `llama-3.2-3b`
- Reduce image steps in `config.py`

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

This is a learning project! Feel free to:
- Add new agents
- Improve prompts
- Add more image styles
- Enhance the UI

## 📧 Support

For issues or questions:
- Check Venice.ai documentation: https://docs.venice.ai
- Review Railway logs in dashboard
- Check application logs for detailed errors

---

Built with ❤️ for management consulting firms

