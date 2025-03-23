from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
import datetime

class SummaryOutput(BaseModel):
    verdict: str = Field(description="Final verdict on the claim")
    confidence_level: float = Field(description="Overall confidence in the conclusion")
    key_findings: List[Dict[str, str]] = Field(description="Main findings with citations")
    evidence_summary: str = Field(description="Detailed summary of supporting evidence")
    citations: List[Dict[str, str]] = Field(description="List of citations and sources, with trust_score as string")

class SummaryAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="mixtral-8x7b-32768"
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert summary agent that:
                      1. Synthesizes research findings and verification results
                      2. Provides evidence-based conclusions
                      3. Includes proper citations for all claims
                      4. Maintains objectivity in reporting
                      
                      Generate a comprehensive summary with citations."""),
            ("user", """Generate a summary for:
                    Claim: {claim}
                    Research Results: {research_results}
                    Verification Results: {verification_results}
                    Validation Results: {validation_results}""")
        ])
        
        self.output_parser = PydanticOutputParser(pydantic_object=SummaryOutput)

    def generate_citations(self, research_results, verification_results):
        citations = []
        for source, content in research_results.items():
            if source in verification_results["trust_scores"]:
                trust_score = verification_results["trust_scores"][source]["score"]
                citations.append({
                    "source": source,
                    "trust_score": str(trust_score) if trust_score is not None else "N/A",
                    "citation_text": f"Source: {source}, Trust Score: {trust_score}"
                })
        return citations

    def determine_verdict(self, all_results):
        # Implement improved verdict determination logic based on all available data
        confidence_threshold = 0.7
        supporting_evidence = 0
        contradicting_evidence = 0
        mixed_evidence = 0
        
        research = all_results["research"]
        verification = all_results["verification"]
        validation = all_results["validation"]
        
        # Count supporting and contradicting evidence with weighted scoring
        if "search_results" in research and "organic_results" in research["search_results"]:
            for result in research["search_results"]["organic_results"]:
                snippet = result.get("snippet", "").lower()
                source_url = result.get("link", "")
                
                # Check for trusted domains for higher weighting
                trusted_domains = ["reuters.com", "apnews.com", "bbc.com", "nature.com", 
                                  "sciencemag.org", "nih.gov", "who.int", "edu"]
                source_weight = 1.0
                for domain in trusted_domains:
                    if domain in source_url:
                        source_weight = 1.5
                        break
                
                # Check for supporting evidence
                support_terms = ["true", "confirmed", "verified", "proven", "accurate", "correct"]
                if any(term in snippet for term in support_terms):
                    supporting_evidence += 1 * source_weight
                
                # Check for contradicting evidence
                contradict_terms = ["false", "incorrect", "misleading", "wrong", "inaccurate", "debunked"]
                if any(term in snippet for term in contradict_terms):
                    contradicting_evidence += 1 * source_weight
                
                # Check for mixed/nuanced evidence
                mixed_terms = ["partially", "somewhat", "depends", "context", "nuanced", "mixed"]
                if any(term in snippet for term in mixed_terms):
                    mixed_evidence += 1 * source_weight
        
        # Consider validation confidence and source credibility
        confidence = validation.get("confidence_score", 0.5)
        overall_credibility = verification.get("overall_credibility", 0.5)
        
        # Adjust confidence based on source credibility
        adjusted_confidence = (confidence * 0.7) + (overall_credibility * 0.3)
        
        # Determine verdict with more nuanced logic
        total_evidence = supporting_evidence + contradicting_evidence + mixed_evidence
        if total_evidence == 0:
            verdict = "Insufficient Evidence"
            confidence = 0.3  # Low confidence when no evidence is found
        elif supporting_evidence > (contradicting_evidence + mixed_evidence) and adjusted_confidence >= confidence_threshold:
            verdict = "True"
        elif contradicting_evidence > (supporting_evidence + mixed_evidence) and adjusted_confidence >= confidence_threshold:
            verdict = "False"
        elif mixed_evidence > (supporting_evidence + contradicting_evidence):
            verdict = "Partially True"
        elif abs(supporting_evidence - contradicting_evidence) <= 1.0:
            verdict = "Partially True"  # When evidence is balanced
        else:
            # Default case when confidence is not high enough
            verdict = "Partially True"
            adjusted_confidence = max(0.5, adjusted_confidence)  # Ensure minimum confidence
        
        return {
            "verdict": verdict,
            "confidence": adjusted_confidence
        }

    def run(self, state):
        import logging
        logger = logging.getLogger(__name__)
        
        claim = state["claim"]
        research_results = state["research_results"]
        verification_results = state["verification_results"]
        validation_results = state["validation_results"]
        
        logger.info(f"Generating summary for claim: {claim}")
        
        # Generate citations with improved filtering
        citations = []
        if "search_results" in research_results and "organic_results" in research_results["search_results"]:
            for result in research_results["search_results"]["organic_results"]:
                if "link" in result:
                    source_url = result["link"]
                    # Calculate trust score based on domain
                    trust_score = 0.5  # Default score
                    
                    # Check for trusted domains
                    trusted_domains = {"reuters.com": 0.9, "apnews.com": 0.9, "bbc.com": 0.85, 
                                      "nature.com": 0.95, "sciencemag.org": 0.95, "nih.gov": 0.9, 
                                      "who.int": 0.9, "edu": 0.8}
                    
                    for domain, score in trusted_domains.items():
                        if domain in source_url:
                            trust_score = score
                            break
                    
                    citations.append({
                        "source": source_url,
                        "trust_score": str(trust_score),
                        "citation_text": f"Source: {source_url}, Trust Score: {trust_score}"
                    })
        
        logger.info(f"Generated {len(citations)} citations")
        
        # Determine final verdict with improved logic
        verdict_result = self.determine_verdict({
            "research": research_results,
            "verification": verification_results,
            "validation": validation_results
        })
        
        logger.info(f"Determined verdict: {verdict_result['verdict']} with confidence {verdict_result['confidence']:.2f}")
        
        # Generate key findings with improved context
        key_findings = []
        
        if "search_results" in research_results and "organic_results" in research_results["search_results"]:
            results = research_results["search_results"]["organic_results"]
            
            # Sort results by relevance (prioritize trusted sources)
            def get_source_weight(result):
                source_url = result.get("link", "")
                for domain in ["reuters", "apnews", "bbc", "nature", "science", "nih.gov", "who.int", ".edu"]:
                    if domain in source_url:
                        return 2.0
                return 1.0
            
            sorted_results = sorted(results, key=get_source_weight, reverse=True)
            
            for i, result in enumerate(sorted_results[:5]):  # Get top 5 results
                if "snippet" in result and "link" in result:
                    # Clean and format the finding
                    snippet = result["snippet"]
                    if len(snippet) > 300:  # Truncate long snippets
                        snippet = snippet[:297] + "..."
                    
                    key_findings.append({
                        "finding": snippet,
                        "source": result["link"],
                        "relevance": "High" if i < 2 else "Medium"
                    })
        
        logger.info(f"Generated {len(key_findings)} key findings")
        
        # Generate evidence summary with more detail
        evidence_summary = f"Based on our analysis, the claim '{claim}' appears to be {verdict_result['verdict']} "
        evidence_summary += f"with a confidence level of {verdict_result['confidence']:.2f}. "
        
        # Add information about supporting and contradicting evidence
        if verdict_result['verdict'] == "True":
            evidence_summary += "Multiple reliable sources support this claim. "
        elif verdict_result['verdict'] == "False":
            evidence_summary += "Multiple reliable sources contradict this claim. "
        elif verdict_result['verdict'] == "Partially True":
            evidence_summary += "The evidence shows this claim contains some truth but also some inaccuracies. "
        elif verdict_result['verdict'] == "Insufficient Evidence":
            evidence_summary += "We couldn't find sufficient reliable information to verify this claim. "
        
        if validation_results.get("biases") and len(validation_results.get("biases", [])) > 0:
            evidence_summary += f"We identified {len(validation_results['biases'])} potential biases in the sources. "
        
        if validation_results.get("logical_fallacies") and len(validation_results.get("logical_fallacies", [])) > 0:
            evidence_summary += f"We found {len(validation_results['logical_fallacies'])} logical fallacies in the arguments. "
        
        # Add information about source quality
        high_trust_sources = sum(1 for c in citations if float(c.get("trust_score", 0)) > 0.7)
        evidence_summary += f"Our analysis is based on {len(citations)} sources, of which {high_trust_sources} are highly reliable."
        
        logger.info("Generated evidence summary")
        
        # Generate comprehensive summary
        summary = SummaryOutput(
            verdict=verdict_result["verdict"],
            confidence_level=verdict_result["confidence"],
            key_findings=key_findings,
            evidence_summary=evidence_summary,
            citations=citations
        )
        
        state["final_summary"] = summary.dict()
        state["messages"].append({
            "agent": "summary",
            "content": "Final summary and conclusions generated",
            "timestamp": str(datetime.datetime.now().isoformat())
        })
        
        logger.info("Summary generation completed")
        return state