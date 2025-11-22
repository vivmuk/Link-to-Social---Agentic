"""LangGraph Coordinator - Orchestrates the multi-agent workflow."""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import logging

from agents.summarization_agent import SummarizationAgent
from agents.creative_agent import CreativeAgent

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State structure for the LangGraph workflow."""
    url: str
    posts_data: dict  # Now includes article metadata from Venice.ai scraping
    images_data: dict
    final_output: dict
    error: str


class Coordinator:
    """Coordinates the multi-agent workflow using LangGraph."""
    
    def __init__(self):
        self.summarizer = SummarizationAgent()
        self.creative = CreativeAgent()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes - scraper is now integrated into summarization via Venice.ai
        workflow.add_node("summarizer", self._summarizer_node)
        workflow.add_node("creative", self._creative_node)
        workflow.add_node("coordinator", self._coordinator_node)
        
        # Define edges - simplified workflow
        workflow.set_entry_point("summarizer")
        workflow.add_edge("summarizer", "creative")
        workflow.add_edge("creative", "coordinator")
        workflow.add_edge("coordinator", END)
        
        # Compile workflow
        return workflow.compile()
    
    async def _summarizer_node(self, state: WorkflowState) -> WorkflowState:
        """Execute summarization agent with Venice.ai web scraping."""
        logger.info(f"Processing URL with Venice.ai web scraping: {state['url']}")
        try:
            # Venice.ai will automatically scrape the URL and generate posts
            posts_data = await self.summarizer.generate_posts(state["url"])
            state["posts_data"] = posts_data
            
            if posts_data.get("status") != "success":
                state["error"] = f"Post generation failed: {posts_data.get('error', 'Unknown error')}"
                logger.error(state["error"])
            
        except Exception as e:
            logger.error(f"Summarizer node error: {str(e)}")
            state["error"] = f"Summarizer error: {str(e)}"
            state["posts_data"] = {"status": "error", "error": str(e)}
        
        return state
    
    async def _creative_node(self, state: WorkflowState) -> WorkflowState:
        """Execute creative agent."""
        logger.info("Generating images...")
        try:
            if state.get("error"):
                # Skip if previous step failed
                state["images_data"] = {"status": "error", "error": "Previous step failed"}
                return state
            
            # Prepare article data from posts_data (which includes metadata from Venice.ai)
            article_data = {
                "title": state["posts_data"].get("article_title", "Article"),
                "author": state["posts_data"].get("article_author"),
                "date": state["posts_data"].get("article_date"),
                "url": state["url"]
            }
            
            images_data = await self.creative.generate_images(
                article_data,
                state["posts_data"]
            )
            state["images_data"] = images_data
            
            if images_data.get("status") != "success":
                state["error"] = f"Image generation failed: {images_data.get('error', 'Unknown error')}"
                logger.error(state["error"])
            
        except Exception as e:
            logger.error(f"Creative node error: {str(e)}")
            state["error"] = f"Creative error: {str(e)}"
            state["images_data"] = {"status": "error", "error": str(e)}
        
        return state
    
    async def _coordinator_node(self, state: WorkflowState) -> WorkflowState:
        """Final coordination and output formatting."""
        logger.info("Coordinating final output...")
        
        # Check for errors
        if state.get("error"):
            state["final_output"] = {
                "status": "error",
                "error": state["error"],
                "url": state["url"]
            }
            return state
        
        # Compile final output
        posts = state.get("posts_data", {})
        images = state.get("images_data", {})
        
        state["final_output"] = {
            "status": "success",
            "url": state["url"],
            "article": {
                "title": posts.get("article_title", ""),
                "author": posts.get("article_author"),
                "date": posts.get("article_date"),
                "url": state["url"]
            },
            "posts": {
                "linkedin": posts.get("linkedin_post", ""),
                "twitter": posts.get("twitter_post", ""),
                "key_insights": posts.get("key_insights", [])
            },
            "images": {
                "infographic": images.get("infographic_image"),
                "social": images.get("social_image")
            }
        }
        
        return state
    
    async def process_url(self, url: str) -> dict:
        """
        Process a URL through the complete workflow.
        
        Args:
            url: URL to process
        
        Returns:
            Final output dictionary with posts and images
        """
        initial_state: WorkflowState = {
            "url": url,
            "posts_data": {},
            "images_data": {},
            "final_output": {},
            "error": ""
        }
        
        # Execute workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        return final_state.get("final_output", {
            "status": "error",
            "error": "Workflow execution failed",
            "url": url
        })

