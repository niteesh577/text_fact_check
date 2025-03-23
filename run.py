import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the app
from src.app import app

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs("./data/chroma", exist_ok=True)
    app.run(debug=True, port=5000)