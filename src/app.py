from flask import Flask, request, jsonify
from src.agents.supervisor import SupervisorAgent
from dotenv import load_dotenv
import os
import logging
import json
from flask_cors import CORS

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fact_check.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required API keys
if not os.getenv("GROQ_API_KEY"):
    logger.warning("GROQ_API_KEY not found in environment variables")

if not os.getenv("SERPAPI_API_KEY"):
    logger.warning("SERPAPI_API_KEY not found in environment variables")

app = Flask(__name__)

CORS(app)  # Enable CORS for all routes


@app.route('/fact-check', methods=['POST'])
def fact_check():
    try:
        data = request.json
        claim = data.get('claim')
        source = data.get('source', None)

        if not claim:
            return jsonify({"error": "Claim is required"}), 400

        logger.info(f"Processing fact check for claim: {claim}")
        if source:
            logger.info(f"Using provided source: {source}")
        
        # Create supervisor agent and run fact check
        supervisor = SupervisorAgent()
        logger.info("Starting fact-checking workflow")
        result = supervisor.run_fact_check(claim, source)
        
        # Log the completion of each agent's work
        for message in result.get("messages", []):
            agent = message.get("agent", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            if message.get("error", False):
                logger.error(f"[{agent.upper()}] {content} at {timestamp}")
            else:
                logger.info(f"[{agent.upper()}] {content} at {timestamp}")
        
        # Log the final verdict
        final_summary = result.get("final_summary", {})
        verdict = final_summary.get("verdict", "Unknown")
        confidence = final_summary.get("confidence_level", 0.0)
        logger.info(f"Final verdict: {verdict} (confidence: {confidence:.2f})")
        
        # Format the response for better readability
        formatted_response = {
            "verdict": final_summary.get("verdict"),
            "confidence": final_summary.get("confidence_level"),
            "summary": final_summary.get("evidence_summary"),
            "key_findings": [
                {
                    "finding": finding.get("finding"),
                    "source": finding.get("source"),
                    "relevance": "High" if i < 2 else "Medium"
                } for i, finding in enumerate(final_summary.get("key_findings", []))
            ],
            "sources": [
                {
                    "url": citation.get("source"),
                    "trust_score": float(citation.get("trust_score", "0")) if citation.get("trust_score", "N/A").replace(".", "", 1).isdigit() else 0.0,
                    "reliability": "High" if float(citation.get("trust_score", "0")) > 0.7 else "Medium" if float(citation.get("trust_score", "0")) > 0.4 else "Low"
                } for citation in final_summary.get("citations", []) if not citation.get("source").endswith("_error") and citation.get("source") != "timestamp"
            ]
        }
        
        # Log the formatted response
        logger.info(f"Returning formatted response with {len(formatted_response['key_findings'])} key findings and {len(formatted_response['sources'])} sources")
        
        return jsonify(formatted_response)

    except Exception as e:
        logger.error(f"Error processing fact check: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs("./data/chroma", exist_ok=True)
    app.run(debug=True, port=5000)