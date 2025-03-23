import requests
from typing import Optional
import os
import logging
from langchain_community.tools.tavily_search import TavilySearchResults

logger = logging.getLogger(__name__)

class SearchTool:
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not self.tavily_api_key or len(self.tavily_api_key.strip()) == 0:
            raise ValueError("TAVILY_API_KEY environment variable is not set or empty")
        self.tavily_tool = TavilySearchResults(max_results=5)

    def search(self, query: str) -> dict:
        if not query or len(query.strip()) == 0:
            logger.error("Search query cannot be empty")
            return {
                "error": "Search query cannot be empty",
                "status": "failed"
            }
        
        logger.info(f"Performing search with query: {query}")

        try:
            # Use Tavily API for search via LangChain's TavilySearchResults tool
            logger.info("Sending request to Tavily API")
            search_response = self.tavily_tool.invoke(query)
            logger.info("Received response from Tavily API")
            
            # Handle different response formats from Tavily API
            # TavilySearchResults might return a list directly or a dict with results key
            organic_results = []
            
            if isinstance(search_response, list):
                # If response is a list, process it directly
                results_list = search_response
                logger.info(f"Received list response with {len(results_list)} results")
            elif isinstance(search_response, dict) and "results" in search_response:
                # If response is a dict with results key, extract the list
                results_list = search_response.get("results", [])
                logger.info(f"Received dict response with {len(results_list)} results")
            else:
                logger.error(f"Invalid response format from Tavily API: {type(search_response)}")
                return {
                    "error": "Invalid response format from Tavily API",
                    "status": "failed"
                }
            
            # Transform Tavily response to match expected format for compatibility
            logger.info("Processing search results")
            for i, result in enumerate(results_list):
                # Handle both dict and object-like result formats
                if isinstance(result, dict):
                    organic_result = {
                        "position": result.get("index", i),
                        "title": result.get("title", ""),
                        "link": result.get("url", ""),
                        "snippet": result.get("content", ""),
                        "source": result.get("source", "")
                    }
                else:
                    # Try to access attributes if result is an object
                    try:
                        organic_result = {
                            "position": getattr(result, "index", i),
                            "title": getattr(result, "title", ""),
                            "link": getattr(result, "url", ""),
                            "snippet": getattr(result, "content", ""),
                            "source": getattr(result, "source", "")
                        }
                    except AttributeError:
                        logger.warning(f"Skipping result {i} due to missing attributes")
                        continue
                
                # Log the source and title for debugging
                logger.info(f"Result {i+1}: {organic_result['title'][:50]}... from {organic_result['link']}")
                organic_results.append(organic_result)
            
            # Create a response format compatible with the existing code
            processed_results = {
                "organic_results": organic_results,
                "knowledge_graph": {},  # Tavily doesn't provide knowledge graph
                "related_questions": [],  # Tavily doesn't provide related questions
                "search_metadata": {
                    "query": query,
                    "result_count": len(organic_results),
                    "timestamp": "timestamp"
                }
            }
            
            logger.info(f"Search completed successfully with {len(organic_results)} results")
            return processed_results
            
        except requests.exceptions.Timeout:
            error_msg = "Request to Tavily API timed out. Please try again later."
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "failed"
            }
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if "401" in error_message:
                error_message = "Tavily API authentication failed. Please check your API key and ensure it is valid."
            elif "429" in error_message:
                error_message = "Tavily API rate limit exceeded. Please wait a moment before trying again."
            elif "403" in error_message:
                error_message = "Access to Tavily API is forbidden. Please verify your API key permissions."
            elif "503" in error_message:
                error_message = "Tavily API service is temporarily unavailable. Please try again later."
            
            logger.error(f"Request exception: {error_message}")
            return {
                "error": error_message,
                "status": "failed",
                "original_error": str(e)
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "status": "failed",
                "exception_type": type(e).__name__
            }