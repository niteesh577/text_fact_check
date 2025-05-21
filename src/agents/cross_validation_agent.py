from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
import torch
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification

class ValidationResult(BaseModel):
    biases: List[Dict[str, str]] = Field(description="List of identified biases")
    logical_fallacies: str = Field(description="List of logical fallacies")
    cross_references: List[str] = Field(description="Cross-referenced sources")
    confidence_score: float = Field(description="Overall confidence score")





class CrossValidationAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="mixtral-8x7b-32768"
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a critical analysis agent specialized in identifying:
                      1. Cognitive biases and prejudices in information
                      2. Logical fallacies in arguments
                      3. Cross-referencing different sources
                      4. Evaluating the strength of evidence
                      
                      Analyze the research and verification results thoroughly."""),
            ("user", """Analyze the following claim and research results:
                    Claim: {claim}
                    Research: {research_results}
                    Verification: {verification_results}""")
        ])
        
        self.output_parser = PydanticOutputParser(pydantic_object=ValidationResult)

    def identify_biases(self, content):
        common_biases = {
            "confirmation_bias": "Looking for information that confirms existing beliefs",
            "selection_bias": "Cherry-picking data that supports a particular view",
            "recency_bias": "Giving too much weight to recent events",
            "authority_bias": "Excessive trust in authority figures"
        }
        
        identified_biases = []
        claim_text = content["claim"].lower()
        research_data = content["research"]


        
        # Simplified implementation to avoid LLM calls during analysis
        if "search_results" in research_data and "organic_results" in research_data["search_results"]:
            results = research_data["search_results"]["organic_results"]
            if len(results) < 3:
                identified_biases.append({
                    "type": "confirmation_bias",
                    "description": "Limited number of sources may indicate confirmation bias"
                })
        
        # Check for authority bias in the claim
        authority_terms = ["expert", "official", "authority", "scientist", "professor", "doctor"]
        if any(term in claim_text for term in authority_terms):
            identified_biases.append({
                "type": "authority_bias",
                "description": "Claim relies on authority figures"
            })
        
        return identified_biases

    def check_logical_fallacies(self, content):
        fallacy_types = {
            "ad_hominem": "Attacking the person instead of the argument",
            "false_causality": "Assuming correlation implies causation",
            "straw_man": "Misrepresenting an argument to make it easier to attack",
            "appeal_to_emotion": "Using emotions instead of facts"
        }
        
        identified_fallacies = []
        claim_text = content["claim"].lower()
        research_data = content["research"]
        
        # Check for ad hominem attacks
        if "search_results" in research_data and "organic_results" in research_data["search_results"]:
            for result in research_data["search_results"]["organic_results"]:
                snippet = result.get("snippet", "").lower()
                if any(phrase in snippet for phrase in ["idiot", "stupid", "incompetent", "fool"]):
                    identified_fallacies.append({
                        "type": "ad_hominem",
                        "description": "Arguments contain personal attacks"
                    })
                    break
        
        # Simplified check for false causality
        causality_terms = ["causes", "because of", "due to", "leads to", "results in"]
        if any(term in claim_text for term in causality_terms):
            identified_fallacies.append({
                "type": "potential_false_causality",
                "description": "Claim may assume causation without sufficient evidence"
            })
        
        # Check for appeal to emotion
        emotional_words = ["shocking", "outrageous", "terrifying", "heartbreaking"]
        if any(word in claim_text for word in emotional_words):
            identified_fallacies.append({
                "type": "appeal_to_emotion",
                "description": "Claim uses emotional language instead of facts"
            })
        
        return identified_fallacies

    def run(self, state):
        claim = state["claim"]
        research_results = state["research_results"]
        verification_results = state["verification_results"]
        
        # Analyze for biases
        biases = self.identify_biases({
            "claim": claim,
            "research": research_results
        })
        
        # # Check for logical fallacies
        # fallacies = self.check_logical_fallacies({
        #     "claim": claim,
        #     "research": research_results
        # })

        model = AutoModelForSequenceClassification.from_pretrained("q3fer/distilbert-base-fallacy-classification")
        tokenizer = AutoTokenizer.from_pretrained("q3fer/distilbert-base-fallacy-classification")

        inputs = tokenizer(claim, return_tensors='pt')

        with torch.no_grad():
            logits = model(**inputs)
            scores = logits[0][0]
            scores = torch.nn.Softmax(dim=0)(scores)

            _, ranking = torch.topk(scores, k=scores.shape[0])
            ranking = ranking.tolist()
        
        results = [f"{i+1}) {model.config.id2label[ranking[i]]} {scores[ranking[i]]:.4f}" for i in range(scores.shape[0])]
        fallacies = '\n'.join(results)
        print(fallacies)

        
        # Simplified cross-reference implementation
        cross_refs = []
        sources = []
        
        if "search_results" in research_results and "organic_results" in research_results["search_results"]:
            for result in research_results["search_results"]["organic_results"]:
                if "link" in result:
                    sources.append(result["link"])
        
        if "source_content" in research_results and "url" in research_results["source_content"]:
            sources.append(research_results["source_content"]["url"])
        
        # Add basic cross-references
        if len(sources) >= 2:
            cross_refs.append(f"Multiple sources found: {len(sources)}")
        
        # Calculate confidence score based on multiple factors
        confidence_factors = {
            "bias_penalty": len(biases) * -0.1,
            "fallacy_penalty": len(fallacies) * -0.15,
            "source_count": min(len(sources) * 0.1, 0.3)
        }
        
        base_confidence = 0.7
        confidence_score = base_confidence + sum(confidence_factors.values())
        confidence_score = max(0.0, min(1.0, confidence_score))  # Clamp between 0 and 1
        
        validation_result = ValidationResult(
            biases=biases,
            logical_fallacies=fallacies,
            cross_references=cross_refs,
            confidence_score=confidence_score,
        )
        
        state["validation_results"] = validation_result.dict()
        state["messages"].append({
            "agent": "validation",
            "content": "Cross-validation and bias analysis completed"
        })
        
        return state
