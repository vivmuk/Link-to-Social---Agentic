"""Summarization Agent - Generates social media posts from article content."""
import json
import asyncio
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
        
        # Validate API key
        if not self.api_key or self.api_key.strip() == "":
            logger.warning("Venice API key is not set. Please set VENICE_API_KEY environment variable.")
    
    async def generate_posts_from_text(self, article_text: str) -> Dict[str, Any]:
        """
        Generate LinkedIn and X/Twitter posts directly from article text.
        
        Args:
            article_text: Full article text content
        
        Returns:
            Dictionary with linkedin_post, twitter_post, article metadata, and key_insights
        """
        # Create prompt for management consulting style using direct text
        prompt = self._create_consulting_prompt_from_text(article_text)
        
        try:
            # Call Venice.ai API without web scraping (using direct text)
            response = await self._call_venice_api_direct(prompt)
            
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
            logger.error(f"Error generating posts from text: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "linkedin_post": None,
                "twitter_post": None
            }
    
    async def generate_posts(self, url: str, use_web_scraping: bool = True) -> Dict[str, Any]:
        """
        Generate LinkedIn and X/Twitter posts directly from a URL using Venice.ai's web scraping.
        
        Args:
            url: Article URL to scrape and process
            use_web_scraping: Whether to enable web scraping (default: True)
        
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
    
    def _create_consulting_prompt_from_text(self, article_text: str) -> str:
        """Create a professional consulting-style prompt using direct article text."""
        return f"""You are a senior management consultant creating social media content for a prestigious consulting firm. Your writing style is:
- Professional yet approachable
- Data-driven and insight-focused
- Clear and concise
- Thought-provoking
- Uses business terminology appropriately

Please analyze the following article text:

{article_text[:5000]}

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
   - title: Article title (extract from text or infer)
   - author: Author name (if available, otherwise null)
   - date: Publication date (if available, otherwise null)

Return your response as a JSON object with this exact structure:
{{
  "linkedin_post": "Your LinkedIn post text here",
  "twitter_post": "Your X/Twitter post text here",
  "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
  "article_title": "Article Title",
  "article_author": "Author Name or null",
  "article_date": "Publication Date or null"
}}"""
    
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
        # Validate API key
        if not self.api_key or self.api_key.strip() == "":
            raise Exception("Venice API key is not configured. Please set VENICE_API_KEY environment variable.")
        
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
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "choices" in data and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                        else:
                            raise Exception("Invalid response format from Venice API")
                    else:
                        response_text = await response.text()
                        logger.error(f"Venice API error {response.status} for URL {article_url}: {response_text}")
                        
                        # Try to parse error message
                        error_msg = response_text
                        try:
                            error_json = json.loads(response_text)
                            if isinstance(error_json, dict) and "error" in error_json:
                                error_obj = error_json["error"]
                                if isinstance(error_obj, dict):
                                    error_msg = error_obj.get("message", str(error_obj))
                                else:
                                    error_msg = str(error_obj)
                        except:
                            pass
                        
                        # Provide more helpful error messages
                        if response.status == 401:
                            raise Exception("Venice API authentication failed. Please check your API key is set correctly in Railway environment variables.")
                        elif response.status == 402:
                            raise Exception("Venice API payment required. Please check your account balance at venice.ai")
                        elif response.status == 429:
                            raise Exception("Venice API rate limit exceeded. Please try again in a few moments.")
                        elif response.status == 500:
                            # Web scraping failed - provide helpful error message
                            logger.error(f"Venice API web scraping failed (HTTP 500) for URL: {article_url}")
                            logger.info("This typically means the URL cannot be accessed by Venice.ai's scraping service.")
                            raise Exception(
                                f"❌ Web scraping failed: Venice.ai could not access this URL.\n\n"
                                f"**Why this happens:**\n"
                                f"- URL requires authentication/login\n"
                                f"- URL is behind a paywall or subscription\n"
                                f"- URL blocks automated access (anti-bot protection)\n"
                                f"- URL is temporarily unavailable\n\n"
                                f"💡 **Solution:** Use the 'Paste Article Text' option instead of URL scraping:\n"
                                f"1. Copy the full article text from the webpage\n"
                                f"2. Select 'Paste Article Text' in the form\n"
                                f"3. Paste the article content directly\n"
                                f"4. This bypasses scraping and works with any content"
                            )
                        else:
                            raise Exception(f"Venice API error {response.status}: {error_msg}")
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Venice API: {str(e)}")
            raise Exception(f"Network error: Unable to connect to Venice API. {str(e)}")
        except asyncio.TimeoutError:
            logger.error("Venice API request timed out")
            raise Exception("Request timed out. The URL might be too complex or Venice API is experiencing delays.")
    
    async def _call_venice_api_direct(self, prompt: str) -> str:
        """Call Venice.ai API for text generation without web scraping (using direct text)."""
        if not self.api_key or self.api_key.strip() == "":
            raise Exception("Venice API key is not configured. Please set VENICE_API_KEY environment variable.")
        
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
                "enable_web_scraping": False,  # No web scraping for direct text
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
                            "description": "Article title extracted from the text"
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
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            if "choices" in data and len(data["choices"]) > 0:
                                return data["choices"][0]["message"]["content"]
                            else:
                                raise Exception("Invalid response format from Venice API")
                        except json.JSONDecodeError:
                            raise Exception(f"Invalid JSON response from Venice API: {response_text[:200]}")
                    else:
                        logger.error(f"Venice API error {response.status}: {response_text}")
                        error_msg = response_text
                        try:
                            error_json = json.loads(response_text)
                            if isinstance(error_json, dict) and "error" in error_json:
                                error_obj = error_json["error"]
                                if isinstance(error_obj, dict):
                                    error_msg = error_obj.get("message", str(error_obj))
                                else:
                                    error_msg = str(error_obj)
                        except:
                            pass
                        
                        if response.status == 401:
                            raise Exception("Venice API authentication failed. Please check your API key.")
                        elif response.status == 402:
                            raise Exception("Venice API payment required. Please check your account balance.")
                        elif response.status == 429:
                            raise Exception("Venice API rate limit exceeded. Please try again later.")
                        else:
                            raise Exception(f"Venice API error {response.status}: {error_msg}")
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Venice API: {str(e)}")
            raise Exception(f"Network error: Unable to connect to Venice API. {str(e)}")
        except asyncio.TimeoutError:
            logger.error("Venice API request timed out")
            raise Exception("Request timed out. Please try again later.")
    
    async def _call_venice_api_fallback(self, prompt: str, article_url: str) -> str:
        """Fallback: Call Venice API without web scraping, just analyze the URL."""
        logger.info("Using fallback method without web scraping")
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Simplified prompt without web scraping
        fallback_prompt = f"""Based on the article URL: {article_url}

Please create social media posts. Since I cannot directly access the article, please generate:

1. LinkedIn Post (3-5 sentences, professional consulting style)
2. X/Twitter Post (under 280 characters)
3. 3-5 key insights as a JSON array
4. Article title: Extract from URL or use "Article"
5. Article author: null
6. Article date: null

Return as JSON with this structure:
{{
  "linkedin_post": "...",
  "twitter_post": "...",
  "key_insights": ["..."],
  "article_title": "...",
  "article_author": null,
  "article_date": null
}}"""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert social media content creator for management consulting firms."
                },
                {
                    "role": "user",
                    "content": fallback_prompt
                }
            ],
            "temperature": self.temperature,
            "max_completion_tokens": 1500,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "linkedin_post": {"type": "string"},
                        "twitter_post": {"type": "string"},
                        "key_insights": {"type": "array", "items": {"type": "string"}},
                        "article_title": {"type": "string"},
                        "article_author": {"type": "string", "nullable": True},
                        "article_date": {"type": "string", "nullable": True}
                    },
                    "required": ["linkedin_post", "twitter_post", "key_insights", "article_title"]
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        if "choices" in data and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                        else:
                            raise Exception("Invalid response format from Venice API")
                    except json.JSONDecodeError:
                        raise Exception(f"Invalid JSON response from fallback: {response_text[:200]}")
                else:
                    raise Exception(f"Fallback API error {response.status}: {response_text}")
    
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

