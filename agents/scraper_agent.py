"""Scraper Agent - Extracts content from web URLs."""
import asyncio
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import aiohttp
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class ScraperAgent:
    """Agent responsible for extracting article content from URLs."""
    
    def __init__(self, max_content_length: int = 50000, timeout: int = 30):
        self.max_content_length = max_content_length
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Returns:
            Dictionary with extracted content:
            - title: Article title
            - content: Main text content
            - author: Author name (if found)
            - date: Publication date (if found)
            - metadata: Additional metadata
            - url: Original URL
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=self.headers, allow_redirects=True) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: Failed to fetch URL")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # Extract title
                    title = self._extract_title(soup)
                    
                    # Extract main content
                    content = self._extract_content(soup)
                    
                    # Extract author
                    author = self._extract_author(soup)
                    
                    # Extract date
                    date = self._extract_date(soup)
                    
                    # Extract metadata
                    metadata = self._extract_metadata(soup, url)
                    
                    # Truncate content if too long
                    if len(content) > self.max_content_length:
                        content = content[:self.max_content_length] + "..."
                    
                    return {
                        "title": title,
                        "content": content,
                        "author": author,
                        "date": date,
                        "metadata": metadata,
                        "url": url,
                        "status": "success"
                    }
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout scraping {url}")
            return {"status": "error", "error": "Request timeout", "url": url}
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {"status": "error", "error": str(e), "url": url}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        # Try multiple selectors
        selectors = [
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'twitter:title'}),
            ('h1', {}),
            ('title', {})
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    title = element.get('content', '')
                else:
                    title = element.get_text(strip=True)
                if title:
                    return title
        
        return "Untitled Article"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        # Try article-specific selectors first
        article_selectors = [
            'article',
            '[role="article"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main',
            '.content'
        ]
        
        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                # Get all paragraphs
                paragraphs = article.find_all(['p', 'h2', 'h3', 'h4'])
                text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                if len(text) > 200:  # Meaningful content
                    return text
        
        # Fallback: get all paragraphs
        paragraphs = soup.find_all('p')
        text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        return text if text else "No content extracted"
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author name."""
        selectors = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('.author', {}),
            ('[rel="author"]', {})
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    author = element.get('content', '')
                else:
                    author = element.get_text(strip=True)
                if author:
                    return author
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date."""
        selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'pubdate'}),
            ('time', {}),
            ('.date', {}),
            ('.published', {})
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    date = element.get('content', '')
                elif tag == 'time':
                    date = element.get('datetime') or element.get_text(strip=True)
                else:
                    date = element.get_text(strip=True)
                if date:
                    return date
        
        return None
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract additional metadata."""
        metadata = {}
        
        # Description
        desc_selectors = [
            ('meta', {'property': 'og:description'}),
            ('meta', {'name': 'description'}),
            ('meta', {'name': 'twitter:description'})
        ]
        
        for tag, attrs in desc_selectors:
            element = soup.find(tag, attrs)
            if element and element.get('content'):
                metadata['description'] = element.get('content')
                break
        
        # Image
        img_selectors = [
            ('meta', {'property': 'og:image'}),
            ('meta', {'name': 'twitter:image'}),
        ]
        
        for tag, attrs in img_selectors:
            element = soup.find(tag, attrs)
            if element and element.get('content'):
                img_url = element.get('content')
                # Make absolute URL
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    parsed = urlparse(url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                metadata['image'] = img_url
                break
        
        return metadata

