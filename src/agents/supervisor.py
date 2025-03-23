from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import Dict, TypedDict
from src.agents.research_agent import ResearchAgent
from src.agents.verification_agent import VerificationAgent
from src.agents.cross_validation_agent import CrossValidationAgent
from src.agents.summary_agent import SummaryAgent


class AgentState(TypedDict):
    claim: str
    source: str
    research_results: dict
    verification_results: dict
    validation_results: dict
    final_summary: dict
    messages: list
    next_agent: str


class SupervisorAgent:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.verification_agent = VerificationAgent()
        self.validation_agent = CrossValidationAgent()
        self.summary_agent = SummaryAgent()
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        workflow = StateGraph(AgentState)

        # Define the nodes
        workflow.add_node("research", self.research_agent.run)
        workflow.add_node("verification", self.verification_agent.run)
        workflow.add_node("validation", self.validation_agent.run)
        workflow.add_node("summary", self.summary_agent.run)

        # Define the edges
        workflow.add_edge("research", "verification")
        workflow.add_edge("verification", "validation")
        workflow.add_edge("validation", "summary")
        workflow.add_edge("summary", END)

        workflow.set_entry_point("research")
        return workflow.compile()

    def run_fact_check(self, claim: str, source: str = None) -> dict:
        initial_state = {
            "claim": claim,
            "source": source,
            "research_results": {},
            "verification_results": {},
            "validation_results": {},
            "final_summary": {},
            "messages": [],
            "next_agent": "research"
        }

        result = self.workflow.invoke(initial_state)
        return result