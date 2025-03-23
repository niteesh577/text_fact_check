from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any, Optional
from src.tools.search import SearchTool
from src.tools.web_scraper import WebScraperTool
from src.database.chroma_store import ChromaStore
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)


class ResearchAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="mixtral-8x7b-32768"
        )
        self.search_tool = SearchTool()
        self.scraper_tool = WebScraperTool()
        self.db = ChromaStore()

        self.tools = [
            Tool(
                name="web_search",
                func=self.search_tool.search,
                description="Search the web for information about a claim"
            ),
            Tool(
                name="web_scraper",
                func=self.scraper_tool.scrape,
                description="Scrape and extract content from a webpage URL"
            )
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a research agent tasked with gathering information about claims. "
                       "Use the search tool to find relevant information and the scraper to extract "
                       "detailed content from reliable sources."),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])

        self.agent = create_openai_functions_agent(
            llm=self.llm,
            prompt=self.prompt,
            tools=self.tools
        )
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools)

    def validate_input(self, state: Dict[str, Any]) -> Optional[str]:
        if not state:
            return "State cannot be empty"
        if "claim" not in state:
            return "Claim is required in state"
        if not isinstance(state["claim"], str) or not state["claim"].strip():
            return "Claim must be a non-empty string"
        return None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate input
            error = self.validate_input(state)
            if error:
                raise ValueError(error)

            claim = state["claim"]
            source = state.get("source")
            research_data = {}

            # If source is provided, scrape it first
            if source:
                try:
                    source_content = self.scraper_tool.scrape(source)
                    if source_content.get("status") == "failed":
                        logging.error(f"Failed to scrape source: {source_content.get('error')}")
                        research_data["source_error"] = source_content.get("error")
                    else:
                        research_data["source_content"] = source_content
                except Exception as e:
                    logging.error(f"Error scraping source {source}: {str(e)}")
                    research_data["source_error"] = str(e)

            # Search for additional information
            try:
                search_query = f"fact check: {claim}"
                search_results = self.search_tool.search(search_query)
                if search_results.get("status") == "failed":
                    logging.error(f"Search failed: {search_results.get('error')}")
                    research_data["search_error"] = search_results.get("error")
                else:
                    research_data["search_results"] = search_results
            except Exception as e:
                logging.error(f"Error performing search: {str(e)}")
                research_data["search_error"] = str(e)

            # Store in ChromaDB for future reference
            try:
                research_data["timestamp"] = datetime.now().isoformat()
                self.db.store_research_results(claim, research_data)
            except Exception as e:
                logging.error(f"Error storing research results: {str(e)}")
                research_data["storage_error"] = str(e)

            state["research_results"] = research_data
            state["messages"].append({
                "agent": "research",
                "content": "Research completed" + (
                    " with some errors" if any(k.endswith("_error") for k in research_data.keys()) else ""
                ),
                "timestamp": datetime.now().isoformat()
            })

            return state

        except Exception as e:
            logging.error(f"Critical error in research agent: {str(e)}")
            state["messages"].append({
                "agent": "research",
                "content": f"Research failed: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            })
            return state