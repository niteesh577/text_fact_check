import requests
from urllib.parse import urlparse
import whois
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from bs4 import BeautifulSoup
import re

logging.basicConfig(level=logging.INFO)

class SourceChecker:
    def __init__(self):
        self.known_reliable_domains = {
            "reuters.com": 0.9,
            "apnews.com": 0.9,
            "bbc.com": 0.85,
            "nature.com": 0.95,
            "sciencemag.org": 0.95
        }

    def validate_url(self, url: str) -> Optional[str]:
        if not url:
            return "URL cannot be empty"
        if not isinstance(url, str):
            return "URL must be a string"
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return "Invalid URL format"
            return None
        except Exception as e:
            return f"URL validation error: {str(e)}"

    def check_domain_authority(self, url: str) -> Dict[str, Any]:
        error = self.validate_url(url)
        if error:
            logging.error(f"URL validation failed: {error}")
            return {"error": error, "status": "failed"}

        domain = urlparse(url).netloc
        try:
            # Get domain information
            domain_info = whois.whois(domain)
            
            # Calculate domain age
            creation_date = domain_info.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            domain_age = (datetime.now() - creation_date).days if creation_date else 0
            
            # Check for HTTPS
            uses_https = url.startswith("https://")
            
            # Additional domain checks
            domain_parts = domain.split(".")
            is_subdomain = len(domain_parts) > 2
            
            return {
                "domain": domain,
                "age_days": domain_age,
                "registrar": domain_info.registrar,
                "is_trusted": domain in self.known_reliable_domains,
                "base_trust_score": self.known_reliable_domains.get(domain, 0.5),
                "uses_https": uses_https,
                "is_subdomain": is_subdomain,
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"Domain authority check failed for {domain}: {str(e)}")
            return {
                "domain": domain,
                "error": str(e),
                "status": "failed"
            }

    def analyze_content_quality(self, content: str) -> Dict[str, Any]:
        try:
            # Parse content with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Count citations and references
            citation_count = len(soup.find_all(["cite", "blockquote"]))
            reference_count = len(re.findall(r'\[\d+\]|\(\d{4}\)', text_content))
            
            # Check for structured content
            has_headings = bool(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]))
            has_lists = bool(soup.find_all(["ul", "ol"]))
            has_tables = bool(soup.find_all("table"))
            
            # Check for dates
            date_patterns = r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
            dates_found = re.findall(date_patterns, text_content, re.IGNORECASE)
            
            return {
                "citations": {
                    "count": citation_count + reference_count,
                    "has_citations": citation_count + reference_count > 0
                },
                "structure": {
                    "has_headings": has_headings,
                    "has_lists": has_lists,
                    "has_tables": has_tables
                },
                "content_stats": {
                    "length": len(text_content),
                    "word_count": len(text_content.split()),
                    "has_dates": bool(dates_found),
                    "date_count": len(dates_found)
                }
            }
        except Exception as e:
            logging.error(f"Content analysis failed: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }

    def analyze_source(self, url: str, content: str) -> Dict[str, Any]:
        try:
            if not content or not isinstance(content, str):
                raise ValueError("Content must be a non-empty string")

            domain_info = self.check_domain_authority(url)
            if domain_info.get("status") == "failed":
                return {
                    "error": domain_info.get("error"),
                    "status": "failed"
                }
            
            # Analyze content characteristics
            content_analysis = self.analyze_content_quality(content)
            if content_analysis.get("status") == "failed":
                return {
                    "error": content_analysis.get("error"),
                    "status": "failed"
                }
            
            analysis_result = {
                "domain_info": domain_info,
                "content_analysis": content_analysis,
                "overall_score": self.calculate_overall_score(domain_info, content_analysis),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"Source analysis failed: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }

    def calculate_overall_score(self, domain_info: Dict[str, Any], content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if domain_info.get("status") == "failed" or "error" in domain_info:
                raise ValueError(f"Invalid domain info: {domain_info.get('error')}")

            base_score = domain_info.get("base_trust_score", 0.5)
            
            # Domain-based modifiers
            domain_modifiers = {
                "uses_https": 0.1 if domain_info.get("uses_https") else 0,
                "domain_age": min(0.1, domain_info.get("age_days", 0) / 3650),  # Max bonus for 10 years
                "trusted_domain": 0.2 if domain_info.get("is_trusted") else 0
            }
            
            # Content-based modifiers
            content_modifiers = {
                "citations": min(0.15, content_analysis["citations"]["count"] * 0.02),
                "content_length": min(0.1, content_analysis["content_stats"]["word_count"] / 2000),
                "structure": 0.1 if all(content_analysis["structure"].values()) else 0,
                "dates_present": 0.05 if content_analysis["content_stats"]["has_dates"] else 0
            }
            
            # Calculate final score
            domain_score = sum(domain_modifiers.values())
            content_score = sum(content_modifiers.values())
            final_score = min(max(base_score + domain_score + content_score, 0.0), 1.0)
            
            return {
                "score": final_score,
                "components": {
                    "base_score": base_score,
                    "domain_modifiers": domain_modifiers,
                    "content_modifiers": content_modifiers
                },
                "explanation": self.generate_score_explanation(final_score, domain_modifiers, content_modifiers)
            }
            
        except Exception as e:
            logging.error(f"Score calculation failed: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def generate_score_explanation(self, final_score: float, domain_modifiers: Dict[str, float], 
                                 content_modifiers: Dict[str, float]) -> str:
        score_ranges = {
            (0.8, 1.0): "Highly reliable",
            (0.6, 0.8): "Generally reliable",
            (0.4, 0.6): "Moderately reliable",
            (0.2, 0.4): "Somewhat unreliable",
            (0.0, 0.2): "Unreliable"
        }
        
        # Determine reliability level
        reliability = next((desc for (min_score, max_score), desc in score_ranges.items() 
                          if min_score <= final_score <= max_score), "Unknown reliability")
        
        # Generate explanation
        positive_factors = []
        negative_factors = []
        
        # Check domain factors
        if domain_modifiers["uses_https"] > 0:
            positive_factors.append("uses secure HTTPS connection")
        if domain_modifiers["trusted_domain"] > 0:
            positive_factors.append("comes from a trusted domain")
        if domain_modifiers["domain_age"] > 0.05:
            positive_factors.append("has established domain history")
            
        # Check content factors
        if content_modifiers["citations"] > 0:
            positive_factors.append("includes citations and references")
        if content_modifiers["content_length"] > 0.05:
            positive_factors.append("provides comprehensive content")
        if content_modifiers["structure"] > 0:
            positive_factors.append("well-structured with headings and lists")
            
        explanation = f"Source is {reliability} ({final_score:.2f}/1.0). "
        if positive_factors:
            explanation += "Positive factors: " + ", ".join(positive_factors) + ". "
        if negative_factors:
            explanation += "Areas for improvement: " + ", ".join(negative_factors) + "."
            
        return explanation