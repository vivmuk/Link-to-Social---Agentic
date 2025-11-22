"""FastAPI application for Link-to-Social Agent."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional
import base64
import logging
from workflow.coordinator import Coordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Link-to-Social Agent",
    description="Transform articles into professional social media posts with AI-generated images",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize coordinator
coordinator = Coordinator()


class ProcessRequest(BaseModel):
    """Request model for processing articles (URL or direct text)."""
    url: Optional[HttpUrl] = None
    article_text: Optional[str] = None
    use_web_scraping: bool = False  # Whether to use web scraping when URL is provided


class ProcessingStatus(BaseModel):
    """Status model for async processing."""
    job_id: str
    status: str
    message: str


# In-memory storage for jobs (use Redis in production)
jobs = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Link-to-Social Agent | Enterprise Content Platform</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-navy: #1a2332;
                --primary-gold: #d4af37;
                --accent-blue: #2c5f8d;
                --text-dark: #1a2332;
                --text-medium: #4a5568;
                --text-light: #718096;
                --bg-light: #f7fafc;
                --bg-white: #ffffff;
                --border-color: #e2e8f0;
                --success-color: #38a169;
                --error-color: #e53e3e;
                --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
                --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
                --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
                --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.12);
            }
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg-light);
                color: var(--text-dark);
                line-height: 1.6;
                min-height: 100vh;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            .header {
                background: var(--bg-white);
                border-bottom: 1px solid var(--border-color);
                padding: 1.25rem 0;
                position: sticky;
                top: 0;
                z-index: 100;
                box-shadow: var(--shadow-sm);
            }
            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .logo {
                font-family: 'Playfair Display', serif;
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--primary-navy);
                letter-spacing: -0.02em;
            }
            .logo-accent {
                color: var(--primary-gold);
            }
            .header-tagline {
                font-size: 0.875rem;
                color: var(--text-light);
                font-weight: 400;
                margin-left: 1rem;
                display: none;
            }
            @media (min-width: 768px) {
                .header-tagline {
                    display: inline;
                }
            }
            .main-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 2rem;
            }
            .hero-section {
                text-align: center;
                margin-bottom: 4rem;
                padding: 2rem 0;
            }
            .hero-title {
                font-family: 'Playfair Display', serif;
                font-size: clamp(2rem, 5vw, 3.5rem);
                font-weight: 700;
                color: var(--primary-navy);
                margin-bottom: 1rem;
                line-height: 1.2;
                letter-spacing: -0.02em;
            }
            .hero-subtitle {
                font-size: clamp(1rem, 2vw, 1.25rem);
                color: var(--text-medium);
                max-width: 700px;
                margin: 0 auto 1.5rem;
                font-weight: 400;
            }
            .hero-description {
                font-size: 1rem;
                color: var(--text-light);
                max-width: 600px;
                margin: 0 auto;
            }
            .content-container {
                display: grid;
                grid-template-columns: 1fr;
                gap: 3rem;
                margin-bottom: 4rem;
            }
            @media (min-width: 1024px) {
                .content-container {
                    grid-template-columns: 1fr 1fr;
                }
            }
            .card {
                background: var(--bg-white);
                border-radius: 12px;
                box-shadow: var(--shadow-md);
                padding: 2.5rem;
                border: 1px solid var(--border-color);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .card:hover {
                box-shadow: var(--shadow-lg);
                transform: translateY(-2px);
            }
            .card-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--primary-navy);
                margin-bottom: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            .card-title::before {
                content: '';
                width: 4px;
                height: 24px;
                background: var(--primary-gold);
                border-radius: 2px;
            }
            .form-group {
                margin-bottom: 1.5rem;
            }
            label {
                display: block;
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--text-dark);
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            input[type="url"], textarea {
                width: 100%;
                padding: 1rem 1.25rem;
                border: 2px solid var(--border-color);
                border-radius: 8px;
                font-size: 1rem;
                font-family: inherit;
                color: var(--text-dark);
                transition: all 0.2s;
                background: var(--bg-white);
            }
            input[type="url"]:focus, textarea:focus {
                outline: none;
                border-color: var(--accent-blue);
                box-shadow: 0 0 0 3px rgba(44, 95, 141, 0.1);
            }
            input[type="url"]::placeholder, textarea::placeholder {
                color: var(--text-light);
            }
            textarea {
                resize: vertical;
                line-height: 1.6;
            }
            .btn-primary {
                width: 100%;
                padding: 1rem 2rem;
                background: var(--primary-navy);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                position: relative;
                overflow: hidden;
            }
            .btn-primary::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            .btn-primary:hover::before {
                left: 100%;
            }
            .btn-primary:hover {
                background: var(--accent-blue);
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }
            .btn-primary:active {
                transform: translateY(0);
            }
            .btn-primary:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 2rem;
                background: var(--bg-white);
                border-radius: 12px;
                margin-top: 2rem;
                box-shadow: var(--shadow-md);
            }
            .loading.active {
                display: block;
            }
            .spinner-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
            }
            .spinner {
                width: 48px;
                height: 48px;
                border: 4px solid var(--border-color);
                border-top-color: var(--primary-gold);
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .loading-text {
                font-size: 1rem;
                color: var(--text-medium);
                font-weight: 500;
            }
            .loading-subtext {
                font-size: 0.875rem;
                color: var(--text-light);
                margin-top: 0.5rem;
            }
            .results {
                display: none;
                margin-top: 3rem;
            }
            .results.active {
                display: block;
            }
            .result-section {
                background: var(--bg-white);
                border-radius: 12px;
                box-shadow: var(--shadow-md);
                padding: 2.5rem;
                margin-bottom: 2rem;
                border: 1px solid var(--border-color);
            }
            .result-section h2 {
                font-family: 'Playfair Display', serif;
                font-size: 2rem;
                font-weight: 700;
                color: var(--primary-navy);
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 2px solid var(--primary-gold);
            }
            .post-box {
                background: var(--bg-light);
                padding: 1.5rem;
                border-radius: 8px;
                margin-bottom: 1.5rem;
                border-left: 4px solid var(--primary-gold);
            }
            .post-label {
                font-size: 0.75rem;
                font-weight: 600;
                color: var(--primary-gold);
                margin-bottom: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }
            .post-box p {
                color: var(--text-dark);
                line-height: 1.8;
                white-space: pre-wrap;
                font-size: 1rem;
            }
            .insights {
                background: linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, rgba(212, 175, 55, 0.1) 100%);
                padding: 1.5rem;
                border-radius: 8px;
                margin-top: 1.5rem;
                border: 1px solid rgba(212, 175, 55, 0.2);
            }
            .insights h3 {
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--primary-navy);
                margin-bottom: 1rem;
            }
            .insights ul {
                list-style: none;
                padding: 0;
            }
            .insights li {
                padding: 0.5rem 0;
                color: var(--text-medium);
                line-height: 1.6;
                position: relative;
                padding-left: 1.5rem;
            }
            .insights li::before {
                content: '→';
                position: absolute;
                left: 0;
                color: var(--primary-gold);
                font-weight: 600;
            }
            .image-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2rem;
                margin-top: 2rem;
            }
            @media (min-width: 768px) {
                .image-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            .image-card {
                background: var(--bg-white);
                border-radius: 8px;
                overflow: hidden;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--border-color);
            }
            .image-card img {
                width: 100%;
                height: auto;
                display: block;
            }
            .image-card-content {
                padding: 1.5rem;
            }
            .image-card h3 {
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--primary-navy);
                margin-bottom: 1rem;
            }
            .btn-download {
                width: 100%;
                padding: 0.75rem 1.5rem;
                background: var(--primary-navy);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 0.875rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .btn-download:hover {
                background: var(--accent-blue);
                transform: translateY(-1px);
                box-shadow: var(--shadow-sm);
            }
            .btn-secondary {
                background: transparent;
                border: 2px solid var(--primary-navy);
                color: var(--primary-navy);
                padding: 0.75rem 2rem;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.875rem;
                font-weight: 600;
                transition: all 0.2s;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .btn-secondary:hover {
                background: var(--primary-navy);
                color: white;
            }
            .error {
                background: #fff5f5;
                border: 1px solid #fed7d7;
                color: #c53030;
                padding: 1.5rem;
                border-radius: 8px;
                margin-top: 2rem;
                border-left: 4px solid var(--error-color);
            }
            .error strong {
                display: block;
                margin-bottom: 0.5rem;
            }
            .workflow-tracker {
                margin-top: 2rem;
                margin-bottom: 3rem;
                background: var(--bg-white);
                border-radius: 12px;
                padding: 2rem;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--border-color);
                display: none;
            }
            .workflow-tracker.active {
                display: block;
            }
            .workflow-tracker h3 {
                font-family: 'Playfair Display', serif;
                font-size: 1.75rem;
                font-weight: 700;
                color: var(--primary-navy);
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 2px solid var(--primary-gold);
            }
            .audit-entry {
                background: var(--bg-light);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-left: 4px solid var(--primary-gold);
                transition: all 0.2s;
            }
            .audit-entry:hover {
                box-shadow: var(--shadow-sm);
                transform: translateX(4px);
            }
            .audit-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 1rem;
                flex-wrap: wrap;
                gap: 1rem;
            }
            .audit-agent {
                font-weight: 600;
                color: var(--primary-navy);
                font-size: 1.125rem;
            }
            .audit-status {
                padding: 0.25rem 0.75rem;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .audit-status.success {
                background: #c6f6d5;
                color: #22543d;
            }
            .audit-status.error {
                background: #fed7d7;
                color: #742a2a;
            }
            .audit-meta {
                font-size: 0.875rem;
                color: var(--text-light);
                margin-top: 0.5rem;
            }
            .audit-section {
                margin-top: 1rem;
            }
            .audit-section-title {
                font-weight: 600;
                color: var(--text-dark);
                margin-bottom: 0.5rem;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .audit-data {
                background: white;
                border: 1px solid var(--border-color);
                border-radius: 6px;
                padding: 1rem;
                font-family: 'Courier New', monospace;
                font-size: 0.875rem;
                color: var(--text-dark);
                max-height: 100px;
                overflow-y: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
                transition: max-height 0.3s;
            }
            .audit-data.expanded {
                max-height: 500px;
            }
            .audit-toggle {
                color: var(--accent-blue);
                cursor: pointer;
                font-size: 0.875rem;
                margin-top: 0.5rem;
                display: inline-block;
            }
            .audit-toggle:hover {
                text-decoration: underline;
            }
            .diagram-container {
                width: 100%;
                max-width: 100%;
                overflow-x: auto;
                padding: 1rem;
                background: var(--bg-light);
                border-radius: 8px;
            }
            .workflow-diagram {
                width: 100%;
                height: auto;
                max-width: 700px;
                margin: 0 auto;
                display: block;
            }
            .diagram-note {
                text-align: center;
                margin-top: 1.5rem;
                color: var(--text-light);
                font-size: 0.875rem;
                font-style: italic;
            }
            .toggle-details {
                text-align: center;
                margin-top: 1.5rem;
            }
            .workflow-details {
                margin-top: 2rem;
                padding: 2rem;
                background: var(--bg-light);
                border-radius: 8px;
                display: none;
            }
            .workflow-details.active {
                display: block;
            }
            .workflow-details h3 {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--primary-navy);
                margin-bottom: 1.5rem;
            }
            .workflow-step {
                background: var(--bg-white);
                padding: 1.5rem;
                border-radius: 8px;
                margin-bottom: 1.5rem;
                border-left: 4px solid var(--primary-gold);
                box-shadow: var(--shadow-sm);
            }
            .workflow-step h4 {
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--primary-navy);
                margin-bottom: 0.75rem;
            }
            .workflow-step p {
                color: var(--text-medium);
                line-height: 1.7;
                margin-bottom: 0.5rem;
            }
            .workflow-step code {
                background: var(--bg-light);
                padding: 0.125rem 0.375rem;
                border-radius: 4px;
                font-size: 0.875em;
                color: var(--accent-blue);
            }
            .tech-stack {
                font-size: 0.875rem;
                color: var(--text-light);
                font-style: italic;
                margin-top: 0.5rem;
            }
            .footer {
                background: var(--primary-navy);
                color: white;
                padding: 2rem 0;
                margin-top: 4rem;
                text-align: center;
            }
            .footer-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
            }
            .footer p {
                color: rgba(255, 255, 255, 0.7);
                font-size: 0.875rem;
            }
            @media (max-width: 768px) {
                .main-container {
                    padding: 2rem 1rem;
                }
                .diagram-container {
                    padding: 0.5rem;
                }
                .workflow-diagram {
                    transform: scale(0.9);
                    transform-origin: top center;
                }
                .result-section {
                    padding: 1.5rem;
                }
            }
        </style>
    </head>
    <body>
        <header class="header">
            <div class="header-content">
                <div>
                    <div class="logo">Link<span class="logo-accent">Social</span></div>
                    <span class="header-tagline">Enterprise Content Platform</span>
                </div>
            </div>
        </header>

        <main class="main-container">
            <div class="hero-section">
                <h1 class="hero-title">Transform Articles into Professional Social Content</h1>
                <p class="hero-subtitle">AI-powered platform for creating executive-grade social media posts and visual assets</p>
                <p class="hero-description">Leveraging multi-agent orchestration to deliver LinkedIn, X/Twitter content, and branded imagery with consulting firm precision</p>
            </div>

            <div class="content-container">
                <div class="card">
                    <h2 class="card-title">Article Processing</h2>
                    <form id="processForm">
                        <div class="form-group">
                            <label>Input Method</label>
                            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                                <label style="display: flex; align-items: center; cursor: pointer; font-weight: normal; text-transform: none;">
                                    <input type="radio" name="inputMethod" value="text" id="methodText" checked style="margin-right: 0.5rem;">
                                    Paste Article Text
                                </label>
                                <label style="display: flex; align-items: center; cursor: pointer; font-weight: normal; text-transform: none;">
                                    <input type="radio" name="inputMethod" value="url" id="methodUrl" style="margin-right: 0.5rem;">
                                    URL (with Web Scraping)
                                </label>
                            </div>
                        </div>
                        
                        <div class="form-group" id="textInputGroup">
                            <label for="articleText">Article Text</label>
                            <textarea id="articleText" name="articleText" rows="10" 
                                placeholder="Paste the full article text here..." 
                                style="width: 100%; padding: 1rem 1.25rem; border: 2px solid var(--border-color); border-radius: 8px; font-size: 1rem; font-family: inherit; color: var(--text-dark); resize: vertical; min-height: 200px;"></textarea>
                            <div style="font-size: 0.75rem; color: var(--text-light); margin-top: 0.5rem;">
                                <span id="textLength">0</span> characters
                            </div>
                        </div>
                        
                        <div class="form-group" id="urlInputGroup" style="display: none;">
                            <label for="url">Article URL</label>
                            <input type="url" id="url" name="url" placeholder="https://example.com/article">
                            <div style="margin-top: 0.75rem;">
                                <label style="display: flex; align-items: center; cursor: pointer; font-weight: normal; text-transform: none; font-size: 0.875rem;">
                                    <input type="checkbox" id="enableScraping" checked style="margin-right: 0.5rem;">
                                    Enable Venice.ai Web Scraping
                                </label>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn-primary" id="submitBtn">Process Article</button>
                    </form>

                    <div class="loading" id="loading">
                        <div class="spinner-container">
                            <div class="spinner"></div>
                            <div>
                                <div class="loading-text">Processing Article</div>
                                <div class="loading-subtext">This may take 20-30 seconds</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2 class="card-title">Workflow Architecture</h2>
                    <div class="diagram-container">
                <h2>🔄 Multi-Agent Orchestration Workflow</h2>
                <div class="diagram-container">
                    <svg class="workflow-diagram" viewBox="0 0 700 600" xmlns="http://www.w3.org/2000/svg">
                        <!-- Background -->
                        <defs>
                            <linearGradient id="inputGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                                <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                            </linearGradient>
                            <linearGradient id="agentGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
                                <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
                            </linearGradient>
                            <linearGradient id="coordGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" style="stop-color:#f093fb;stop-opacity:1" />
                                <stop offset="100%" style="stop-color:#f5576c;stop-opacity:1" />
                            </linearGradient>
                            <linearGradient id="outputGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
                                <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
                            </linearGradient>
                            <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                                <polygon points="0 0, 10 3, 0 6" fill="#667eea" />
                            </marker>
                        </defs>
                        
                        <!-- Input Box -->
                        <rect x="250" y="20" width="200" height="60" rx="10" fill="url(#inputGrad)" stroke="#333" stroke-width="2"/>
                        <text x="350" y="45" text-anchor="middle" fill="white" font-size="14" font-weight="bold">URL Input</text>
                        <text x="350" y="65" text-anchor="middle" fill="white" font-size="11">Article Link</text>
                        
                        <!-- Arrow 1 -->
                        <line x1="350" y1="80" x2="350" y2="120" stroke="#667eea" stroke-width="3" marker-end="url(#arrowhead)"/>
                        
                        <!-- Summarization Agent (with Venice.ai Web Scraping) -->
                        <rect x="200" y="120" width="300" height="100" rx="10" fill="url(#agentGrad)" stroke="#333" stroke-width="2"/>
                        <text x="350" y="145" text-anchor="middle" fill="white" font-size="16" font-weight="bold">✍️ Summarization Agent</text>
                        <text x="350" y="165" text-anchor="middle" fill="white" font-size="12">Venice.ai Web Scraping + LLM</text>
                        <text x="350" y="185" text-anchor="middle" fill="white" font-size="12">Extracts content &amp; Generates Posts</text>
                        <text x="350" y="205" text-anchor="middle" fill="white" font-size="12">LinkedIn &amp; X/Twitter + Metadata</text>
                        
                        <!-- Arrow 2 -->
                        <line x1="350" y1="220" x2="350" y2="260" stroke="#667eea" stroke-width="3" marker-end="url(#arrowhead)"/>
                        
                        <!-- Creative Agent -->
                        <rect x="200" y="260" width="300" height="80" rx="10" fill="url(#agentGrad)" stroke="#333" stroke-width="2"/>
                        <text x="350" y="285" text-anchor="middle" fill="white" font-size="16" font-weight="bold">🎨 Creative Agent</text>
                        <text x="350" y="305" text-anchor="middle" fill="white" font-size="12">Generates: Infographic + Social Media Images</text>
                        <text x="350" y="325" text-anchor="middle" fill="white" font-size="12">Venice.ai Image API (watercolor style)</text>
                        
                        <!-- Arrow 3 -->
                        <line x1="350" y1="340" x2="350" y2="380" stroke="#667eea" stroke-width="3" marker-end="url(#arrowhead)"/>
                        
                        <!-- Coordinator -->
                        <rect x="250" y="380" width="200" height="60" rx="10" fill="url(#coordGrad)" stroke="#333" stroke-width="2"/>
                        <text x="350" y="405" text-anchor="middle" fill="white" font-size="16" font-weight="bold">🎯 Coordinator</text>
                        <text x="350" y="425" text-anchor="middle" fill="white" font-size="12">LangGraph Workflow Orchestration</text>
                        
                        <!-- Arrow 4 -->
                        <line x1="350" y1="440" x2="350" y2="470" stroke="#667eea" stroke-width="3" marker-end="url(#arrowhead)"/>
                        
                        <!-- Output Box -->
                        <rect x="150" y="470" width="400" height="30" rx="10" fill="url(#outputGrad)" stroke="#333" stroke-width="2"/>
                        <text x="350" y="490" text-anchor="middle" fill="white" font-size="14" font-weight="bold">📦 Output: Posts + Images Package</text>
                        
                        <!-- LangGraph Badge -->
                        <rect x="20" y="380" width="120" height="40" rx="5" fill="#fff" stroke="#667eea" stroke-width="2"/>
                        <text x="80" y="400" text-anchor="middle" fill="#667eea" font-size="12" font-weight="bold">LangGraph</text>
                        <text x="80" y="415" text-anchor="middle" fill="#666" font-size="10">Orchestration</text>
                        
                        <!-- Venice.ai Web Scraping Badge -->
                        <rect x="560" y="120" width="120" height="50" rx="5" fill="#fff" stroke="#4facfe" stroke-width="2"/>
                        <text x="620" y="140" text-anchor="middle" fill="#4facfe" font-size="11" font-weight="bold">Venice.ai</text>
                        <text x="620" y="155" text-anchor="middle" fill="#666" font-size="9">Web Scraping</text>
                        <text x="620" y="168" text-anchor="middle" fill="#666" font-size="9">Built-in</text>
                        
                        <!-- State Management Indicator -->
                        <text x="80" y="360" text-anchor="middle" fill="#666" font-size="9" font-style="italic">State Management</text>
                        <text x="620" y="360" text-anchor="middle" fill="#666" font-size="9" font-style="italic">Error Handling</text>
                    </svg>
                </div>
                <p class="diagram-note">
                    Powered by LangGraph multi-agent orchestration • Venice.ai built-in web scraping • Sequential workflow with state management
                </p>
                <div class="toggle-details">
                    <button onclick="toggleWorkflowDetails()" class="btn-secondary" id="toggleBtn">View Technical Details</button>
                </div>
                <div class="workflow-details" id="workflowDetails">
                    <h3>Workflow Architecture</h3>
                    
                    <div class="workflow-step">
                        <h4>1️⃣ Input → Summarization Agent (with Venice.ai Web Scraping)</h4>
                        <p><strong>Purpose:</strong> Scrape article content and generate professional social media posts in one step</p>
                        <p><strong>Process:</strong> Uses Venice.ai's built-in web scraping feature (<code>enable_web_scraping: true</code>) to automatically fetch and parse the article URL. Then uses Venice.ai LLM (llama-3.2-3b) with a consulting-style prompt to create LinkedIn (3-5 sentences) and X/Twitter posts (<280 chars), plus extracts key insights and article metadata</p>
                        <p><strong>Output:</strong> LinkedIn post, Twitter post, 3-5 key insights, article title, author, and date</p>
                        <p class="tech-stack">Tech: Venice.ai API with web scraping enabled, JSON schema validation, prompt engineering</p>
                    </div>
                    
                    <div class="workflow-step">
                        <h4>2️⃣ Summarization → Creative Agent</h4>
                        <p><strong>Purpose:</strong> Generate professional watercolor-style images for social media</p>
                        <p><strong>Process:</strong> Creates two images using Venice.ai Image API: (1) Infographic with key insights and title, (2) Social media-optimized image. Both in 1080x1080 format with consulting firm aesthetic</p>
                        <p><strong>Output:</strong> Base64-encoded infographic and social media images</p>
                        <p class="tech-stack">Tech: Venice.ai Image API, style presets, negative prompts</p>
                    </div>
                    
                    <div class="workflow-step">
                        <h4>3️⃣ Creative → Coordinator</h4>
                        <p><strong>Purpose:</strong> Orchestrate workflow, manage state, and validate outputs</p>
                        <p><strong>Process:</strong> LangGraph coordinator validates all agent outputs, handles errors, and compiles final package. Manages workflow state across all steps</p>
                        <p><strong>Output:</strong> Final structured output with posts, images, and metadata</p>
                        <p class="tech-stack">Tech: LangGraph, state management, error handling</p>
                    </div>
                    
                    <div class="workflow-step">
                        <h4>4️⃣ Coordinator → Output</h4>
                        <p><strong>Purpose:</strong> Deliver ready-to-use social media package</p>
                        <p><strong>Process:</strong> Formats final output with article metadata, posts, key insights, and downloadable images</p>
                        <p><strong>Output:</strong> Complete package ready for LinkedIn/X/Twitter sharing</p>
                        <p class="tech-stack">Tech: FastAPI, JSON response, base64 image encoding</p>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #e7f3ff; border-radius: 8px; border-left: 4px solid #2196F3;">
                        <p style="color: #333; margin: 0;"><strong>💡 Key Features:</strong></p>
                        <ul style="color: #666; margin-top: 10px; margin-left: 20px;">
                            <li><strong>Simplified Architecture:</strong> Uses Venice.ai's built-in web scraping, eliminating need for separate scraper agent</li>
                            <li>Sequential workflow ensures data flows correctly between agents</li>
                            <li>Error handling at each stage prevents cascading failures</li>
                            <li>State management tracks progress through entire workflow</li>
                            <li>Each agent is independent and can be optimized separately</li>
                            <li>Venice.ai handles web scraping, content extraction, and LLM generation in one API call</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <div class="results" id="results">
            <div class="workflow-tracker" id="workflowTracker">
                <h3>📊 Agent Workflow & Audit Trail</h3>
                <div id="auditEntries"></div>
            </div>
            
            <div class="result-section">
                <h2>Social Media Posts</h2>
                <div class="post-box">
                    <span class="post-label">LinkedIn Post</span>
                    <p id="linkedinPost"></p>
                </div>
                <div class="post-box">
                    <span class="post-label">X/Twitter Post</span>
                    <p id="twitterPost"></p>
                </div>
                <div class="insights" id="insights"></div>
            </div>

            <div class="result-section">
                <h2>Generated Visual Assets</h2>
                <div class="image-grid">
                    <div class="image-card">
                        <img id="infographicImg" alt="Infographic">
                        <div class="image-card-content">
                            <h3>Infographic</h3>
                            <button class="btn-download" onclick="downloadImage('infographic', 'infographic.webp')">Download</button>
                        </div>
                    </div>
                    <div class="image-card">
                        <img id="socialImg" alt="Social Media Image">
                        <div class="image-card-content">
                            <h3>Social Media Image</h3>
                            <button class="btn-download" onclick="downloadImage('social', 'social-media.webp')">Download</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="footer">
        <div class="footer-content">
            <p>© 2024 LinkSocial Enterprise Platform. Built with LangGraph & Venice.ai</p>
        </div>
    </footer>
        
        <script>
            let currentResult = null;
            
            // Handle input method toggle
            document.querySelectorAll('input[name="inputMethod"]').forEach(radio => {
                radio.addEventListener('change', function() {
                    const textGroup = document.getElementById('textInputGroup');
                    const urlGroup = document.getElementById('urlInputGroup');
                    const textArea = document.getElementById('articleText');
                    const urlInput = document.getElementById('url');
                    
                    if (this.value === 'text') {
                        textGroup.style.display = 'block';
                        urlGroup.style.display = 'none';
                        if (urlInput) urlInput.removeAttribute('required');
                        if (textArea) textArea.setAttribute('required', 'required');
                    } else {
                        textGroup.style.display = 'none';
                        urlGroup.style.display = 'block';
                        if (textArea) textArea.removeAttribute('required');
                        if (urlInput) urlInput.setAttribute('required', 'required');
                    }
                });
            });
            
            // Update character count
            const articleTextEl = document.getElementById('articleText');
            if (articleTextEl) {
                articleTextEl.addEventListener('input', function() {
                    const lengthDisplay = document.getElementById('textLength');
                    if (lengthDisplay) {
                        lengthDisplay.textContent = this.value.length.toLocaleString();
                    }
                });
            }
            
            // Form submission
            const form = document.getElementById('processForm') || document.getElementById('urlForm');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const submitBtn = document.getElementById('submitBtn');
                    const loading = document.getElementById('loading');
                    const results = document.getElementById('results');
                    
                    submitBtn.disabled = true;
                    loading.classList.add('active');
                    results.classList.remove('active');
                    
                    try {
                        const inputMethod = document.querySelector('input[name="inputMethod"]:checked');
                        let requestBody = {};
                        
                        if (!inputMethod || inputMethod.value === 'text') {
                            const articleText = document.getElementById('articleText')?.value.trim();
                            if (!articleText) {
                                throw new Error('Please paste article text');
                            }
                            requestBody = {
                                article_text: articleText,
                                use_web_scraping: false
                            };
                        } else {
                            const url = document.getElementById('url')?.value.trim();
                            if (!url) {
                                throw new Error('Please enter a URL');
                            }
                            requestBody = {
                                url: url,
                                use_web_scraping: document.getElementById('enableScraping')?.checked || false
                            };
                        }
                        
                        const response = await fetch('/process', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(requestBody)
                        });
                        
                        if (!response.ok) {
                            const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
                            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        const data = await response.json();
                        
                        if (data.status === 'success') {
                            currentResult = data;
                            displayResults(data);
                            if (data.audit_trail && data.audit_trail.length > 0) {
                                displayWorkflowTracker(data.audit_trail);
                            }
                            window.scrollTo({ top: document.getElementById('results').offsetTop - 100, behavior: 'smooth' });
                        } else {
                            showError(data.error || data.detail || 'An error occurred');
                        }
                    } catch (error) {
                        console.error('Error processing request:', error);
                        showError('Failed to process: ' + (error.message || error));
                    } finally {
                        submitBtn.disabled = false;
                        loading.classList.remove('active');
                    }
                });
            }
            
            function displayResults(data) {
                const results = document.getElementById('results');
                
                // Display posts
                document.getElementById('linkedinPost').textContent = data.posts.linkedin || 'No post generated';
                document.getElementById('twitterPost').textContent = data.posts.twitter || 'No post generated';
                
                // Display insights
                const insightsDiv = document.getElementById('insights');
                if (data.posts.key_insights && data.posts.key_insights.length > 0) {
                    insightsDiv.innerHTML = '<h3>Key Insights</h3><ul>' + 
                        data.posts.key_insights.map(insight => '<li>' + insight + '</li>').join('') + 
                        '</ul>';
                } else {
                    insightsDiv.innerHTML = '';
                }
                
                // Display images
                if (data.images.infographic) {
                    document.getElementById('infographicImg').src = 'data:image/webp;base64,' + data.images.infographic;
                }
                if (data.images.social) {
                    document.getElementById('socialImg').src = 'data:image/webp;base64,' + data.images.social;
                }
                
                results.classList.add('active');
            }
            
            function displayWorkflowTracker(auditTrail) {
                const trackerContainer = document.getElementById('workflowTracker');
                if (!trackerContainer) {
                    // Create tracker container if it doesn't exist
                    const results = document.getElementById('results');
                    const tracker = document.createElement('div');
                    tracker.id = 'workflowTracker';
                    tracker.className = 'workflow-tracker active';
                    tracker.innerHTML = '<h3>📊 Agent Workflow & Audit Trail</h3><div id="auditEntries"></div>';
                    results.insertBefore(tracker, results.firstChild);
                }
                
                const entriesContainer = document.getElementById('auditEntries');
                if (!entriesContainer) return;
                
                entriesContainer.innerHTML = '';
                
                auditTrail.forEach((entry, index) => {
                    const entryDiv = document.createElement('div');
                    entryDiv.className = 'audit-entry';
                    
                    const statusClass = entry.status === 'success' ? 'success' : 'error';
                    const inputPreview = JSON.stringify(entry.input, null, 2);
                    const outputPreview = JSON.stringify(entry.output, null, 2);
                    
                    entryDiv.innerHTML = `
                        <div class="audit-header">
                            <div>
                                <span class="audit-agent">${entry.agent} - ${entry.step}</span>
                                <div class="audit-meta">
                                    ${entry.timestamp} • Duration: ${entry.duration_ms?.toFixed(2) || 0}ms
                                </div>
                            </div>
                            <span class="audit-status ${statusClass}">${entry.status}</span>
                        </div>
                        
                        <div class="audit-section">
                            <div class="audit-section-title">📥 Input Data</div>
                            <div class="audit-data collapsed" id="input-${index}">${escapeHtml(inputPreview)}</div>
                            <span class="audit-toggle" onclick="toggleAuditData('input-${index}', this)">Show Full Input</span>
                        </div>
                        
                        <div class="audit-section">
                            <div class="audit-section-title">📤 Output Data</div>
                            <div class="audit-data collapsed" id="output-${index}">${escapeHtml(outputPreview)}</div>
                            <span class="audit-toggle" onclick="toggleAuditData('output-${index}', this)">Show Full Output</span>
                        </div>
                    `;
                    
                    entriesContainer.appendChild(entryDiv);
                });
                
                trackerContainer.classList.add('active');
            }
            
            function toggleAuditData(id, toggleEl) {
                const dataEl = document.getElementById(id);
                if (dataEl) {
                    dataEl.classList.toggle('expanded');
                    toggleEl.textContent = dataEl.classList.contains('expanded') 
                        ? 'Collapse'
                        : 'Show Full ' + (id.startsWith('input') ? 'Input' : 'Output');
                }
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            function showError(message) {
                const results = document.getElementById('results');
                results.innerHTML = '<div class="error"><strong>Error:</strong> ' + message + '</div>';
                results.classList.add('active');
            }
            
            function downloadImage(type, filename) {
                if (!currentResult || !currentResult.images) return;
                
                const imageData = currentResult.images[type];
                if (!imageData) return;
                
                const link = document.createElement('a');
                link.href = 'data:image/webp;base64,' + imageData;
                link.download = filename;
                link.click();
            }
            
            function toggleWorkflowDetails() {
                const details = document.getElementById('workflowDetails');
                const btn = document.getElementById('toggleBtn');
                details.classList.toggle('active');
                btn.textContent = details.classList.contains('active') 
                    ? 'Hide Technical Details' 
                    : 'View Technical Details';
            }
        </script>
    </body>
    </html>
    """


@app.post("/process")
async def process_url(request: ProcessRequest):
    """Process a URL or article text and return social media content with audit trail."""
    try:
        # Validate input
        if not request.url and not request.article_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'url' (with use_web_scraping=True) or 'article_text' must be provided"
            )
        
        if request.use_web_scraping and not request.url:
            raise HTTPException(
                status_code=400,
                detail="URL is required when use_web_scraping is True"
            )
        
        url_str = str(request.url) if request.url else ""
        article_text = request.article_text or ""
        
        if request.url:
            logger.info(f"Processing URL: {url_str} (scraping: {request.use_web_scraping})")
        else:
            logger.info(f"Processing direct text (length: {len(article_text)} chars)")
        
        # Execute workflow
        result = await coordinator.process_url(
            url=url_str,
            article_text=article_text,
            use_web_scraping=request.use_web_scraping
        )
        
        if result.get("status") == "error":
            error_message = result.get("error", "Processing failed")
            logger.error(f"Workflow error: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=error_message
            )
        
        return JSONResponse(content=result)
        
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors."""
    return Response(content="", media_type="image/x-icon")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "link-to-social-agent"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

