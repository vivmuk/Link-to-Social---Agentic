"""Summarization Agent - Generates social media posts from article content."""
import json
from typing import Dict, Any
import aiohttp
import logging
from config import settings

logger = logging.getLogger(__name__)


class SummarizationAgent:
    """Agent responsible for generating social media posts."""
    
    def __init__(self):
        self.api_key = settings.venice_api_key
        self.base_url = settings.venice_base_url
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
    
    async def generate_posts(self, url: str) -> Dict[str, Any]:
        """
        Generate LinkedIn and X/Twitter posts directly from a URL using Venice.ai's web scraping.
        
        Args:
            url: Article URL to scrape and process
        
        Returns:
            Dictionary with linkedin_post, twitter_post, article metadata, and key_insights
        """
        # Create prompt for management consulting style
        # Venice.ai will automatically scrape the URL with enable_web_scraping
        prompt = self._create_consulting_prompt(url)
        
        try:
            # Call Venice.ai API with web scraping enabled
            response = await self._call_venice_api(prompt, url)
            
            if response:
                # Parse the JSON response
                posts = self._parse_response(response)
                return {
                    "status": "success",
                    "linkedin_post": posts.get("linkedin_post", ""),
                    "twitter_post": posts.get("twitter_post", ""),
                    "key_insights": posts.get("key_insights", []),
                    "article_title": posts.get("article_title", ""),
                    "article_author": posts.get("article_author"),
                    "article_date": posts.get("article_date")
                }
            else:
                raise Exception("Empty response from API")
                
        except Exception as e:
            logger.error(f"Error generating posts: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "linkedin_post": None,
                "twitter_post": None
            }
    
    def _create_consulting_prompt(self, url: str) -> str:
        """Create a professional consulting-style prompt that includes the URL for Venice.ai web scraping."""
        return f"""You are a senior management consultant creating social media content for a prestigious consulting firm. Your writing style is:
- Professional yet approachable
- Data-driven and insight-focused
- Clear and concise
- Thought-provoking
- Uses business terminology appropriately

Please analyze the article at this URL: {url}

Generate TWO social media posts based on this article:

1. LinkedIn Post (3-5 sentences):
   - Start with a hook that captures attention
   - Include 2-3 key insights or takeaways
   - End with a thought-provoking question or call to action
   - Format: Professional, engaging, suitable for B2B audience
   - Length: 150-300 characters

2. X/Twitter Post (under 280 characters):
   - Punchy and engaging
   - Include 1-2 key insights
   - Use strategic line breaks for readability
   - May include emojis sparingly (max 2)
   - Include a call to action or question

3. Extract 3-5 key insights as a JSON array

4. Extract article metadata:
   - title: Article title
   - author: Author name (if available)
   - date: Publication date (if available)

Return your response as a JSON object with this exact structure:
{{
  "linkedin_post": "Your LinkedIn post text here",
  "twitter_post": "Your X/Twitter post text here",
  "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
  "article_title": "Article Title",
  "article_author": "Author Name or null",
  "article_date": "Publication Date or null"
}}"""
    
    async def _call_venice_api(self, prompt: str, article_url: str) -> str:
        """Call Venice.ai API for text generation with web scraping enabled."""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert social media content creator for management consulting firms. You create professional, insight-driven content that engages business executives and thought leaders."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_completion_tokens": 1500,
            "venice_parameters": {
                "enable_web_scraping": True,  # Enable Venice.ai's built-in web scraping
                "enable_web_citations": False,
                "include_venice_system_prompt": True
            },
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "linkedin_post": {
                            "type": "string",
                            "description": "LinkedIn post text (3-5 sentences)"
                        },
                        "twitter_post": {
                            "type": "string",
                            "description": "X/Twitter post text (under 280 characters)"
                        },
                        "key_insights": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of 3-5 key insights"
                        },
                        "article_title": {
                            "type": "string",
                            "description": "Article title extracted from the webpage"
                        },
                        "article_author": {
                            "type": "string",
                            "nullable": True,
                            "description": "Article author if available, otherwise null"
                        },
                        "article_date": {
                            "type": "string",
                            "nullable": True,
                            "description": "Publication date if available, otherwise null"
                        }
                    },
                    "required": ["linkedin_post", "twitter_post", "key_insights", "article_title"]
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the API response and format posts."""
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            
            # Extract posts
            linkedin_post = data.get("linkedin_post", "")
            twitter_post = data.get("twitter_post", "")
            
            # Ensure Twitter post is under 280 chars
            if len(twitter_post) > 280:
                twitter_post = twitter_post[:277] + "..."
            
            return {
                "linkedin_post": linkedin_post,
                "twitter_post": twitter_post,
                "key_insights": data.get("key_insights", []),
                "article_title": data.get("article_title", "Untitled Article"),
                "article_author": data.get("article_author"),
                "article_date": data.get("article_date")
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Fallback: return raw response
            return {
                "linkedin_post": response_text[:500],
                "twitter_post": response_text[:280],
                "key_insights": [],
                "article_title": "Untitled Article",
                "article_author": None,
                "article_date": None
            }

