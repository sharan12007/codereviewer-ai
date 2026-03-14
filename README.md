# AI Code Reviewer

An AI-powered code review system that automatically analyzes pull requests, detects issues, and suggests improvements using Large Language Models.

## Overview

AI Code Reviewer is designed to assist developers by performing automated code reviews similar to tools like CodeRabbit.  
The system analyzes pull requests, understands code context, and generates intelligent feedback on:

- Code quality
- Logic errors
- Security vulnerabilities
- Performance issues
- Best practices

The goal is to integrate AI into the development workflow to improve code quality and reduce manual review effort.

---

## Features

- Automated Pull Request Analysis
- AI-Powered Code Suggestions
- Static Code Quality Checks
- Context-Aware Code Understanding
- GitHub Integration
- Real-Time Review Feedback

---

## Architecture

The system consists of the following components:

1. **Code Analyzer**
   - Parses repository structure
   - Extracts changed files from PR

2. **AI Review Engine**
   - Uses LLMs to analyze code
   - Generates human-readable feedback

3. **Review Orchestrator**
   - Coordinates analysis pipeline
   - Manages review workflow

4. **Integration Layer**
   - Connects with GitHub APIs
   - Posts comments on pull requests

---

## Tech Stack

- Python
- FastAPI
- LangChain / LangGraph
- GitHub API
- Docker
- Redis (optional for task queue)

---

## Project Structure

```
codereviewer-ai
│
├── src/
│   ├── analyzer/
│   ├── reviewer/
│   ├── agents/
│   └── api/
│
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```
git clone https://github.com/sharan12007/codereviewer-ai.git
cd codereviewer-ai
```

Create virtual environment:

```
python -m venv venv
```

Activate environment:

Windows
```
venv\Scripts\activate
```

Linux / Mac
```
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

## Running the Project

Start the API server:

```
uvicorn main:app --reload
```

---

## Example Workflow

1. Developer opens Pull Request
2. Code Reviewer detects changes
3. AI analyzes modified code
4. Suggestions are generated
5. Feedback is posted to PR

---

## Future Improvements

- Multi-agent review pipeline
- Security vulnerability detection
- Performance optimization analysis
- CI/CD integration
- VSCode extension

---

## Author

**G Sharan Eshwar**

GitHub: https://github.com/sharan12007  
LinkedIn: https://linkedin.com/in/sharan-eshwar-437094326
