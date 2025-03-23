# Fact Buddy

Fact Buddy is an innovative fact-checking platform that leverages a multi-agent system to verify claims using evidence-based analysis. It is designed to help users discern truth from misinformation by performing rigorous research, detecting biases and logical fallacies, and providing clear, evidence-based summaries with proper references.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

In an age where misinformation is rampant, Fact Buddy stands out as a tool to empower critical thinking and fact-checking. Using a multi-agent workflow, Fact Buddy breaks down claims, retrieves evidence from reputable sources, assesses source reliability, detects biases and logical fallacies, and synthesizes detailed summaries.

Our system integrates advanced AI models, web search, and web scraping tools along with a robust database for storing research results. Whether you're a researcher, journalist, or simply a curious individual, Fact Buddy aims to provide clear, reliable insights to help you make informed decisions.

---

## Features

- **Multi-Agent System**:  
  - **Claim Analysis Agent**: Breaks down and analyzes user claims.
  - **Research Agent**: Gathers information via web search and scraping.
  - **Verification Agent**: Evaluates the credibility of sources.
  - **Cross-Validation Agent**: Cross-checks findings from multiple sources.
  - **Summary Agent**: Synthesizes evidence into a clear, concise summary.
  - **Supervisor Agent**: Orchestrates the workflow among all agents.

- **Evidence-Based Analysis**:  
  - Collects and aggregates data from high-quality sources.
  - Detects bias, logical fallacies, and assesses overall reliability.

- **Database Integration**:  
  - Uses ChromaDB (or your chosen database) to store research results for future reference.

- **User-Friendly Interface**:  
  - A beautiful, dark-themed dashboard built with React, Tailwind CSS, and Framer Motion.
  - Responsive design ensures a seamless experience across devices.

---

## Architecture

Fact Buddy’s architecture is designed around a modular, multi-agent workflow. The core components include:

- **Agents**:  
  - **Research Agent**: Handles searching and scraping.
  - **Verification Agent**: Assesses the credibility of gathered information.
  - **Cross-Validation Agent**: Ensures consistency across multiple data sources.
  - **Summary Agent**: Creates detailed, evidence-based summaries.
  - **Supervisor Agent**: Routes and coordinates tasks among agents.

- **Tools**:  
  - **Search Tool**: Queries external APIs (e.g., Tavily API) for research papers and articles.
  - **Web Scraper Tool**: Uses requests, BeautifulSoup, and trafilatura to extract main content and metadata from web pages.
  - **Source Checker Tool**: Validates URLs, checks domain authority, and analyzes content quality.

- **Database**:  
  - Stores research results for tracking and further analysis (e.g., using ChromaDB).

- **Frontend**:  
  - A React-based dashboard that allows users to submit claims and view fact-check results.
  - Built with Tailwind CSS and Framer Motion for a sleek, modern look.

---

## Project Structure

```
fact-buddy/
├── src/
│   ├── agents/
│   │   ├── researchagent/
│   │   ├── verificationagent/
│   │   ├── crossvalidationagent/
│   │   ├── summaryagent/
│   │   └── supervisor/
│   ├── database/
│   │   └── chromadb/
│   └── tools/
│       ├── search.py
│       ├── sourcechecker.py
│       └── webscraper.py
├── frontend/
│   └── (React app for dashboard)
├── README.md
└── requirements.txt
```

- **src/agents/**: Contains code for different agents in the multi-agent workflow.
- **src/database/**: Contains database modules for storing research results.
- **src/tools/**: Contains helper modules for searching, scraping, and checking sources.
- **frontend/**: The React-based frontend dashboard.
- **requirements.txt**: Lists all Python dependencies.

---

## Installation

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/niteesh577/fact-buddy.git
   cd fact-buddy
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   - Create a `.env` file (or set environment variables in your shell) for keys like `TAVILY_API_KEY` and other configurations.
   ```bash
   echo "TAVILY_API_KEY=your_api_key_here" > .env
   ```

5. **Run the backend server (Flask or your chosen framework):**
   ```bash
   flask run --host=127.0.0.1 --port=5000
   ```

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```

---

## Usage

1. **Submit a Claim:**
   - On the dashboard, enter a claim in the input field (e.g., "Intermittent fasting causes bloating") and click "Submit".
  
2. **Backend Processing:**
   - Your claim is sent to the backend at `http://127.0.0.1:5000/fact-check`.
   - The multi-agent system processes the claim: searching for evidence, scraping web pages, checking source reliability, and synthesizing a summary.
  
3. **Viewing Results:**
   - The dashboard displays a structured response that includes:
     - **Confidence Level**
     - **Key Findings** with relevance and source links
     - **List of Sources** with trust scores and reliability
     - **Summary** and overall verdict

---

## Configuration

- **Environment Variables:**
  - `TAVILY_API_KEY`: API key for the Tavily Search API.
  - Other API keys and configuration details can be added to the `.env` file.

- **Database Configuration:**
  - Configure your ChromaDB settings in the `src/database/chroma_store` module.

---

## Contributing

Contributions are welcome! If you'd like to contribute to Fact Buddy, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push to your fork.
4. Open a pull request with a detailed description of your changes.

For major changes, please open an issue first to discuss what you would like to change.

---


## Acknowledgements

- **LangChain & LangGraph:**  
  The project leverages powerful frameworks like LangChain and LangGraph for building multi-agent systems.
- **Community Tools:**  
  Special thanks to contributors of `trafilatura`, `BeautifulSoup`, and other open-source projects that made this project possible.

---
