"""Creative Agent - Generates professional images using Venice.ai."""
import base64
import json
from typing import Dict, Any, List
import aiohttp
import logging
from config import settings

logger = logging.getLogger(__name__)


class CreativeAgent:
    """Agent responsible for generating professional consulting-style images."""
    
    def __init__(self):
        self.api_key = settings.venice_api_key
        self.base_url = settings.venice_base_url
        self.model = settings.image_model
        self.width = settings.image_width
        self.height = settings.image_height
        self.steps = settings.image_steps
        self.cfg_scale = settings.image_cfg_scale
    
    async def generate_images(
        self, 
        article_data: Dict[str, Any], 
        posts_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate two professional images:
        1. Infographic style image
        2. Social media post image
        
        Args:
            article_data: Scraped article information
            posts_data: Generated social media posts
        
        Returns:
            Dictionary with infographic_image and social_image (base64 encoded)
        """
        title = article_data.get("title", "Article")
        key_insights = posts_data.get("key_insights", [])
        
        try:
            # Generate infographic image
            infographic_image = await self._generate_infographic(
                title, 
                key_insights
            )
            
            # Generate social media image
            social_image = await self._generate_social_image(
                title,
                key_insights
            )
            
            return {
                "status": "success",
                "infographic_image": infographic_image,
                "social_image": social_image
            }
            
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "infographic_image": None,
                "social_image": None
            }
    
    async def _generate_infographic(
        self, 
        title: str, 
        key_insights: List[str]
    ) -> str:
        """Generate an infographic-style image."""
        insights_text = "\n".join([f"• {insight}" for insight in key_insights[:5]])
        
        # Professional consulting infographic prompt
        prompt = f"""Professional management consulting infographic design, watercolor style, 
elegant business aesthetics, minimalist layout, 
soft professional colors (navy blue, gold accents, white space),
title: "{title}",
key insights illustrated with icons and text,
clean typography, executive presentation style,
consulting firm quality, sophisticated and modern"""

        negative_prompt = """low quality, blurry, cartoonish, unprofessional, 
cluttered, bright neon colors, childish design, 
text overlay errors, distorted text, amateur design"""
        
        return await self._generate_image(prompt, negative_prompt)
    
    async def _generate_social_image(
        self, 
        title: str, 
        key_insights: List[str]
    ) -> str:
        """Generate a social media post image."""
        # Social media optimized image
        prompt = f"""Professional social media post image for management consulting, 
watercolor style, elegant business design,
title text: "{title[:60]}",
soft professional watercolor background in navy blue and gold tones,
minimalist composition with strategic white space,
sophisticated consulting firm branding,
clean modern aesthetics, suitable for LinkedIn and X/Twitter,
1080x1080 square format, centered composition,
executive presentation quality"""

        negative_prompt = """low quality, blurry, unreadable text, 
cluttered design, amateur graphics, 
bright garish colors, cartoonish elements,
distorted or overlapping text"""
        
        return await self._generate_image(prompt, negative_prompt)
    
    async def _generate_image(
        self, 
        prompt: str, 
        negative_prompt: str
    ) -> str:
        """Generate a single image using Venice.ai API."""
        url = f"{self.base_url}/image/generate"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": self.width,
            "height": self.height,
            "steps": self.steps,
            "cfg_scale": self.cfg_scale,
            "format": "webp",
            "return_binary": False,  # Return base64
            "safe_mode": False,
            "embed_exif_metadata": False,
            "hide_watermark": True,
            "style_preset": "Digital Art"  # Use style preset for consistent quality
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    # Venice returns base64 in images array
                    if data.get("images") and len(data["images"]) > 0:
                        return data["images"][0]
                    else:
                        raise Exception("No image in response")
                else:
                    error_text = await response.text()
                    raise Exception(f"Image API error {response.status}: {error_text}")

