"""LangGraph Coordinator - Orchestrates the multi-agent workflow."""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import logging
import time
from datetime import datetime

from agents.summarization_agent import SummarizationAgent
from agents.creative_agent import CreativeAgent

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State structure for the LangGraph workflow."""
    url: str  # URL or empty if using direct text
    article_text: str  # Direct article text (alternative to URL)
    use_web_scraping: bool  # Whether to use web scraping or direct text
    posts_data: dict  # Now includes article metadata from Venice.ai scraping
    images_data: dict
    final_output: dict
    error: str
    audit_trail: List[Dict[str, Any]]  # Complete audit log of agent activities


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
    
    def _add_audit_entry(self, state: WorkflowState, agent_name: str, step: str, 
                        input_data: Dict[str, Any], output_data: Dict[str, Any], 
                        status: str = "success", duration_ms: float = 0) -> None:
        """Add an entry to the audit trail."""
        if "audit_trail" not in state:
            state["audit_trail"] = []
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "step": step,
            "status": status,
            "duration_ms": duration_ms,
            "input": input_data,
            "output": output_data
        }
        state["audit_trail"].append(entry)
        logger.info(f"Audit: {agent_name} - {step} - {status} ({duration_ms:.2f}ms)")
    
    async def _summarizer_node(self, state: WorkflowState) -> WorkflowState:
        """Execute summarization agent with Venice.ai web scraping or direct text."""
        start_time = time.time()
        agent_name = "SummarizationAgent"
        
        try:
            # Determine input method
            use_scraping = state.get("use_web_scraping", False) and state.get("url", "")
            article_text = state.get("article_text", "")
            
            if use_scraping and state.get("url"):
                logger.info(f"Processing URL with Venice.ai web scraping: {state['url']}")
                input_data = {
                    "type": "url",
                    "url": state["url"],
                    "method": "venice_web_scraping"
                }
                posts_data = await self.summarizer.generate_posts(state["url"], use_web_scraping=True)
            elif article_text:
                logger.info(f"Processing direct article text (length: {len(article_text)} chars)")
                input_data = {
                    "type": "text",
                    "text_length": len(article_text),
                    "text_preview": article_text[:200] + "..." if len(article_text) > 200 else article_text,
                    "method": "direct_text"
                }
                posts_data = await self.summarizer.generate_posts_from_text(article_text)
            else:
                raise ValueError("Either URL with web scraping enabled or article_text must be provided")
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Prepare output data for audit (truncate for readability)
            output_data = {
                "status": posts_data.get("status"),
                "linkedin_post_length": len(posts_data.get("linkedin_post", "")),
                "twitter_post_length": len(posts_data.get("twitter_post", "")),
                "key_insights_count": len(posts_data.get("key_insights", [])),
                "article_title": posts_data.get("article_title", ""),
                "article_author": posts_data.get("article_author"),
                "article_date": posts_data.get("article_date")
            }
            
            state["posts_data"] = posts_data
            
            if posts_data.get("status") != "success":
                state["error"] = f"Post generation failed: {posts_data.get('error', 'Unknown error')}"
                logger.error(state["error"])
                self._add_audit_entry(state, agent_name, "generate_posts", input_data, 
                                    {"error": state["error"]}, "error", duration_ms)
            else:
                self._add_audit_entry(state, agent_name, "generate_posts", input_data, output_data, "success", duration_ms)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Summarizer node error: {str(e)}")
            state["error"] = f"Summarizer error: {str(e)}"
            state["posts_data"] = {"status": "error", "error": str(e)}
            
            input_data = {
                "type": "url" if state.get("url") else "text",
                "url": state.get("url", ""),
                "text_length": len(state.get("article_text", ""))
            }
            self._add_audit_entry(state, agent_name, "generate_posts", input_data, 
                                {"error": str(e)}, "error", duration_ms)
        
        return state
    
    async def _creative_node(self, state: WorkflowState) -> WorkflowState:
        """Execute creative agent."""
        start_time = time.time()
        agent_name = "CreativeAgent"
        
        try:
            if state.get("error"):
                # Skip if previous step failed
                state["images_data"] = {"status": "error", "error": "Previous step failed"}
                self._add_audit_entry(state, agent_name, "generate_images", 
                                    {"reason": "skipped_due_to_error"}, 
                                    {"error": "Previous step failed"}, "error", 0)
                return state
            
            # Prepare article data from posts_data
            article_data = {
                "title": state["posts_data"].get("article_title", "Article"),
                "author": state["posts_data"].get("article_author"),
                "date": state["posts_data"].get("article_date"),
                "url": state.get("url", "")
            }
            
            input_data = {
                "article_title": article_data["title"],
                "key_insights_count": len(state["posts_data"].get("key_insights", [])),
                "images_to_generate": ["infographic", "social_media"]
            }
            
            logger.info("Generating images...")
            images_data = await self.creative.generate_images(
                article_data,
                state["posts_data"]
            )
            
            duration_ms = (time.time() - start_time) * 1000
            state["images_data"] = images_data
            
            if images_data.get("status") != "success":
                state["error"] = f"Image generation failed: {images_data.get('error', 'Unknown error')}"
                logger.error(state["error"])
                output_data = {"error": state["error"]}
                self._add_audit_entry(state, agent_name, "generate_images", input_data, 
                                    output_data, "error", duration_ms)
            else:
                output_data = {
                    "status": "success",
                    "infographic_generated": bool(images_data.get("infographic_image")),
                    "social_image_generated": bool(images_data.get("social_image")),
                    "infographic_size_chars": len(images_data.get("infographic_image", "")),
                    "social_image_size_chars": len(images_data.get("social_image", ""))
                }
                self._add_audit_entry(state, agent_name, "generate_images", input_data, 
                                    output_data, "success", duration_ms)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Creative node error: {str(e)}")
            state["error"] = f"Creative error: {str(e)}"
            state["images_data"] = {"status": "error", "error": str(e)}
            
            self._add_audit_entry(state, agent_name, "generate_images", 
                                {"error": "exception"}, {"error": str(e)}, "error", duration_ms)
        
        return state
    
    async def _coordinator_node(self, state: WorkflowState) -> WorkflowState:
        """Final coordination and output formatting."""
        start_time = time.time()
        agent_name = "Coordinator"
        
        logger.info("Coordinating final output...")
        
        # Check for errors
        if state.get("error"):
            state["final_output"] = {
                "status": "error",
                "error": state["error"],
                "url": state.get("url", ""),
                "audit_trail": state.get("audit_trail", [])
            }
            self._add_audit_entry(state, agent_name, "compile_output", 
                                {"has_error": True}, {"error": state["error"]}, "error", 0)
            return state
        
        # Compile final output
        posts = state.get("posts_data", {})
        images = state.get("images_data", {})
        
        input_data = {
            "posts_data_available": bool(posts),
            "images_data_available": bool(images),
            "posts_status": posts.get("status"),
            "images_status": images.get("status")
        }
        
        state["final_output"] = {
            "status": "success",
            "url": state.get("url", ""),
            "article": {
                "title": posts.get("article_title", ""),
                "author": posts.get("article_author"),
                "date": posts.get("article_date"),
                "url": state.get("url", "")
            },
            "posts": {
                "linkedin": posts.get("linkedin_post", ""),
                "twitter": posts.get("twitter_post", ""),
                "key_insights": posts.get("key_insights", [])
            },
            "images": {
                "infographic": images.get("infographic_image"),
                "social": images.get("social_image")
            },
            "audit_trail": state.get("audit_trail", [])  # Include full audit trail
        }
        
        duration_ms = (time.time() - start_time) * 1000
        output_data = {
            "status": "success",
            "output_keys": list(state["final_output"].keys()),
            "audit_trail_entries": len(state.get("audit_trail", []))
        }
        self._add_audit_entry(state, agent_name, "compile_output", input_data, output_data, "success", duration_ms)
        
        return state
    
    async def process_url(self, url: str = "", article_text: str = "", use_web_scraping: bool = False) -> dict:
        """
        Process a URL or article text through the complete workflow.
        
        Args:
            url: URL to process (if use_web_scraping is True)
            article_text: Direct article text content (alternative to URL)
            use_web_scraping: Whether to use web scraping (requires URL) or direct text
        
        Returns:
            Final output dictionary with posts, images, and audit trail
        """
        if not url and not article_text:
            return {
                "status": "error",
                "error": "Either URL (with use_web_scraping=True) or article_text must be provided",
                "audit_trail": []
            }
        
        if use_web_scraping and not url:
            return {
                "status": "error",
                "error": "URL is required when use_web_scraping is True",
                "audit_trail": []
            }
        
        initial_state: WorkflowState = {
            "url": url or "",
            "article_text": article_text or "",
            "use_web_scraping": use_web_scraping,
            "posts_data": {},
            "images_data": {},
            "final_output": {},
            "error": "",
            "audit_trail": []
        }
        
        # Add initial audit entry
        input_method = "url_with_scraping" if (use_web_scraping and url) else "direct_text"
        initial_input = {
            "method": input_method,
            "url": url if url else None,
            "text_length": len(article_text) if article_text else None
        }
        self._add_audit_entry(initial_state, "System", "workflow_start", initial_input, 
                            {"workflow_initialized": True}, "success", 0)
        
        # Execute workflow
        workflow_start = time.time()
        final_state = await self.workflow.ainvoke(initial_state)
        workflow_duration = (time.time() - workflow_start) * 1000
        
        # Add final audit entry
        final_output = final_state.get("final_output", {})
        self._add_audit_entry(final_state, "System", "workflow_complete", 
                            {"total_duration_ms": workflow_duration}, 
                            {"status": final_output.get("status", "unknown"),
                             "total_audit_entries": len(final_state.get("audit_trail", []))}, 
                            final_output.get("status", "error"), workflow_duration)
        
        return final_state.get("final_output", {
            "status": "error",
            "error": "Workflow execution failed",
            "url": url or "",
            "audit_trail": final_state.get("audit_trail", [])
        })

