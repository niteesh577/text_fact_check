import chromadb
from chromadb.config import Settings
import json
from typing import Dict, Any, Optional, List
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

class ChromaStore:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory="./data/chroma",
            is_persistent=True
        ))
        
        # Create collections for different types of data
        self.research_collection = self.client.get_or_create_collection(
            name="research_results",
            metadata={"description": "Stores research findings and source content"}
        )
        
        self.verification_collection = self.client.get_or_create_collection(
            name="verification_results",
            metadata={"description": "Stores source verification results"}
        )

    def validate_claim(self, claim: str) -> Optional[str]:
        if not claim:
            return "Claim cannot be empty"
        if not isinstance(claim, str):
            return "Claim must be a string"
        if len(claim.strip()) == 0:
            return "Claim cannot be whitespace only"
        return None

    def store_research_results(self, claim: str, research_data: Dict[str, Any]) -> bool:
        try:
            error = self.validate_claim(claim)
            if error:
                logging.error(f"Invalid claim: {error}")
                return False

            if not isinstance(research_data, dict):
                logging.error("Research data must be a dictionary")
                return False

            # Convert research data to string for storage
            research_str = json.dumps(research_data)
            
            self.research_collection.add(
                documents=[research_str],
                metadatas=[{"claim": claim, "timestamp": str(datetime.now())}],
                ids=[f"research_{hash(claim)}"]
            )
            return True
        except Exception as e:
            logging.error(f"Error storing research results: {str(e)}")
            return False

    def store_verification_results(self, claim: str, verification_data: Dict[str, Any]) -> bool:
        try:
            error = self.validate_claim(claim)
            if error:
                logging.error(f"Invalid claim: {error}")
                return False

            if not isinstance(verification_data, dict):
                logging.error("Verification data must be a dictionary")
                return False

            verification_str = json.dumps(verification_data)
            
            self.verification_collection.add(
                documents=[verification_str],
                metadatas=[{"claim": claim, "timestamp": str(datetime.now())}],
                ids=[f"verification_{hash(claim)}"]
            )
            return True
        except Exception as e:
            logging.error(f"Error storing verification results: {str(e)}")
            return False

    def get_research_results(self, claim: str) -> Optional[Dict[str, Any]]:
        try:
            error = self.validate_claim(claim)
            if error:
                logging.error(f"Invalid claim: {error}")
                return None

            results = self.research_collection.query(
                query_texts=[claim],
                n_results=1
            )
            
            if results and results['documents'] and len(results['documents'][0]) > 0:
                try:
                    return json.loads(results['documents'][0][0])
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding research results: {str(e)}")
                    return None
            return None
        except Exception as e:
            logging.error(f"Error retrieving research results: {str(e)}")
            return None

    def get_verification_results(self, claim: str) -> Optional[Dict[str, Any]]:
        try:
            error = self.validate_claim(claim)
            if error:
                logging.error(f"Invalid claim: {error}")
                return None

            results = self.verification_collection.query(
                query_texts=[claim],
                n_results=1
            )
            
            if results and results['documents'] and len(results['documents'][0]) > 0:
                try:
                    return json.loads(results['documents'][0][0])
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding verification results: {str(e)}")
                    return None
            return None
        except Exception as e:
            logging.error(f"Error retrieving verification results: {str(e)}")
            return None

    def search_similar_claims(self, claim: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            error = self.validate_claim(claim)
            if error:
                logging.error(f"Invalid claim: {error}")
                return []

            if not isinstance(limit, int) or limit < 1:
                logging.error("Limit must be a positive integer")
                return []

            results = self.research_collection.query(
                query_texts=[claim],
                n_results=limit
            )
            
            similar_claims = []
            if results and results['documents'] and results['metadatas']:
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    try:
                        similar_claims.append({
                            "claim": metadata.get("claim", ""),
                            "research": json.loads(doc)
                        })
                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding similar claim: {str(e)}")
                        continue
            
            return similar_claims
        except Exception as e:
            logging.error(f"Error searching similar claims: {str(e)}")
            return []