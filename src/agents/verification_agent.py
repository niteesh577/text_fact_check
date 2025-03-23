from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from typing import Dict, Any, Optional
from ..tools.source_checker import SourceChecker
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

class VerificationAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="mixtral-8x7b-32768"
        )
        self.source_checker = SourceChecker()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a verification agent. Analyze sources for credibility "
                      "and assign trust scores based on authority, recency, and reliability."),
            ("user", "Analyze the following research results and provide verification:\n{input}")
        ])

    def calculate_trust_score(self, source_data):
        score = 0
        factors = {
            "domain_authority": 0.3,
            "content_quality": 0.3,
            "source_age": 0.2,
            "citation_count": 0.2
        }
        
        # Implementation of trust score calculation
        return {
            "score": score,
            "factors": factors,
            "explanation": "Detailed explanation of the score"
        }

    def validate_input(self, state: Dict[str, Any]) -> Optional[str]:
        if not state:
            return "State cannot be empty"
        if "research_results" not in state:
            return "Research results are required in state"
        if not isinstance(state["research_results"], dict):
            return "Research results must be a dictionary"
        return None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate input
            error = self.validate_input(state)
            if error:
                raise ValueError(error)

            research_results = state["research_results"]
            verification_data = {
                "trust_scores": {},
                "source_analysis": {},
                "overall_credibility": 0,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                # Analyze each source
                total_score = 0
                valid_sources = 0
                
                for source, content in research_results.items():
                    if source.endswith("_error"):
                        continue
                        
                    try:
                        trust_score = self.calculate_trust_score(content)
                        verification_data["trust_scores"][source] = trust_score
                        
                        if trust_score["score"] is not None:
                            total_score += trust_score["score"]
                            valid_sources += 1
                            
                    except Exception as e:
                        logging.error(f"Error calculating trust score for {source}: {str(e)}")
                        verification_data["trust_scores"][source] = {
                            "error": str(e),
                            "score": None
                        }
                
                # Calculate overall credibility
                verification_data["overall_credibility"] = (
                    total_score / valid_sources if valid_sources > 0 else 0
                )
                
            except Exception as e:
                logging.error(f"Error in source analysis: {str(e)}")
                verification_data["analysis_error"] = str(e)
            
            state["verification_results"] = verification_data
            state["messages"].append({
                "agent": "verification",
                "content": "Source verification completed" + (
                    " with some errors" if "analysis_error" in verification_data else ""
                ),
                "timestamp": datetime.now().isoformat()
            })
            
            return state
            
        except Exception as e:
            logging.error(f"Critical error in verification agent: {str(e)}")
            state["messages"].append({
                "agent": "verification",
                "content": f"Verification failed: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            })
            return state