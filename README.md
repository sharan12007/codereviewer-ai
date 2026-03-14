<div align="center">

# 🤖 AI Code Reviewer

### Automated Pull Request Analysis powered by Groq LLM

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> **AI Code Reviewer** automatically reviews every Pull Request on your GitHub repository using a Large Language Model, posts structured inline comments with severity ratings and confidence scores, and provides a one-click AI-powered fix directly inside VS Code.

<br/>

![Dashboard Preview](https://img.shields.io/badge/Dashboard-Live%20Preview-blueviolet?style=flat-square)
![VS Code Extension](https://img.shields.io/badge/VS%20Code-Extension%20Ready-blue?style=flat-square)
![GitHub Integration](https://img.shields.io/badge/GitHub-Webhook%20Integration-black?style=flat-square)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Environment Configuration](#2-environment-configuration)
  - [3. GitHub App Setup](#3-github-app-setup)
  - [4. Backend Setup](#4-backend-setup)
  - [5. VS Code Extension Setup](#5-vs-code-extension-setup)
- [Running the Application](#-running-the-application)
  - [Option A: Docker (Recommended)](#option-a-docker-recommended)
  - [Option B: Local Development](#option-b-local-development)
- [How It Works](#-how-it-works)
  - [GitHub PR Review Flow](#github-pr-review-flow)
  - [VS Code File Review Flow](#vs-code-file-review-flow)
  - [AI Autofix Flow](#ai-autofix-flow)
- [API Reference](#-api-reference)
- [VS Code Extension Usage](#-vs-code-extension-usage)
- [Dashboard](#-dashboard)
- [Database Schema](#-database-schema)
- [Configuration Reference](#-configuration-reference)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Development Guide](#-development-guide)
- [Academic Context](#-academic-context)
- [License](#-license)

---

## 🌟 Overview

AI Code Reviewer is a full-stack developer tool that brings automated, AI-powered code review into your existing GitHub workflow. When a developer opens or updates a Pull Request, a GitHub webhook triggers the review pipeline — the diff is fetched, chunked, analysed by a Groq LLM, filtered for noise, and the comments are posted directly back to the PR within seconds.

The system also ships a VS Code extension that lets developers review any open file on-demand and — crucially — fix any identified issue with a single click using the **AI Autofix** feature. The original and fixed files are shown side-by-side in a VS Code diff view before any changes are applied.

This project was built as an MVP in a single sprint following a strict pre-production specification. Every decision — framework, library version, database, queue mechanism — was made deliberately and documented.

---

## ✨ Features

### Core Review Features
- 🔄 **Automatic PR Reviews** — triggered instantly via GitHub webhooks on `opened`, `synchronize`, `reopened` events
- 📝 **Structured Comments** — every comment includes severity, category, confidence score, and line position
- 🎯 **Inline GitHub Comments** — comments attach directly to the relevant diff lines on the PR
- 🔊 **Noise Filtering** — removes low-confidence (<0.6) comments and deduplicates by position + category
- 📊 **Comment Capping** — maximum 20 comments per review, prioritised by severity

### AI Autofix
- ⚡ **One-Click Fix** — click "Fix with AI" on any comment in VS Code to generate a complete fix
- 🔍 **Diff View** — see exactly what changed before applying, using VS Code's native diff editor
- ✅ **Apply & Save** — one click applies the fix and saves the file
- 🧠 **Context-Aware** — the LLM receives the full file + issue description + line number for precise fixes

### VS Code Extension
- 🛡 **Activity Bar Icon** — dedicated AI Reviewer panel in the VS Code sidebar
- 🌲 **TreeView Comments** — comments grouped by severity (Critical / Warnings / Suggestions / Info)
- 🔴 **Problems Panel** — all issues appear in VS Code's built-in Problems panel with proper severity
- 📌 **Click to Navigate** — click any comment to jump to the exact line in the file
- 🔐 **Secure Auth** — GitHub OAuth PKCE flow, JWT stored in OS keychain via VS Code SecretStorage
- 💻 **Right-Click Fix** — right-click any file in the editor → "AI Reviewer: Fix Issue at Cursor"

### Dashboard & Analytics
- 📈 **Live Dashboard** at `/dashboard` — dark-themed, GitHub-inspired UI
- 📡 **Real-time SSE Feed** — live activity stream of review events
- 📊 **Severity Breakdown** — visual breakdown of comment categories
- 🗂 **Review History** — all past reviews with model, duration, and comment count
- 🔁 **Auto-refresh** — PR list and stats update automatically

### Developer Experience
- 🐳 **Docker Ready** — single `docker compose up --build` starts everything
- 🔒 **HMAC-SHA256 Webhook Validation** — every webhook is cryptographically verified
- ♻️ **Async Job Queue** — `asyncio.Queue` handles concurrent PRs without Redis
- 📡 **SSE Notifications** — VS Code extension receives real-time status updates
- 🔑 **Multi-LLM Support** — Groq (primary), Anthropic Claude, Google Gemini as fallbacks

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                               │
│  ┌──────────────────┐              ┌──────────────────────────────┐  │
│  │  VS Code Extension│              │     Web Dashboard /dashboard  │  │
│  │  (TypeScript)     │              │     (FastAPI HTML + SSE)     │  │
│  └────────┬─────────┘              └──────────────┬───────────────┘  │
└───────────│────────────────────────────────────────│─────────────────┘
            │ REST + SSE                             │ HTTP
┌───────────▼────────────────────────────────────────▼─────────────────┐
│                        FASTAPI BACKEND                                │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐ ┌─────────────┐  │
│  │/webhook │ │/review   │ │/autofix   │ │/auth   │ │/events (SSE)│  │
│  │         │ │/file     │ │           │ │        │ │             │  │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └────────┘ └─────────────┘  │
│       │           │             │                                     │
│  ┌────▼───────────▼─────────────▼──────────────────────────────────┐ │
│  │              asyncio.Queue (in-memory job queue)                  │ │
│  └──────────────────────────────┬───────────────────────────────────┘ │
│                                 │                                     │
│  ┌──────────────────────────────▼───────────────────────────────────┐ │
│  │                    REVIEW PIPELINE                                │ │
│  │  Diff Parser → Prompt Engine → LLM Client → Noise Filter         │ │
│  └──────────────────────────────┬───────────────────────────────────┘ │
└─────────────────────────────────│────────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼───────┐    ┌───────────▼──────────┐  ┌────────▼────────┐
│   SQLite DB    │    │     Groq LLM API     │  │   GitHub API    │
│  (SQLModel)    │    │  llama-3.1-8b-instant│  │   (PyGithub)    │
└────────────────┘    └──────────────────────┘  └─────────────────┘
```

### Data Flow — GitHub Webhook Path

| Step | Actor | Action |
|------|-------|--------|
| 1 | GitHub | `POST /webhook` — `pull_request` event fired |
| 2 | FastAPI | Validates HMAC-SHA256 signature. Rejects if mismatch → 401 |
| 3 | FastAPI | Enqueues job into `asyncio.Queue`. Returns HTTP 200 immediately |
| 4 | Worker | Dequeues job. Calls `run_pr_review()` |
| 5 | Diff Parser | Fetches changed files via PyGithub. Skips binaries, lock files, removed files |
| 6 | Chunker | Splits patches into ≤3000 token chunks using tiktoken `cl100k_base` |
| 7 | Prompt Engine | Builds structured prompt with `SYSTEM_PROMPT` instructing JSON-only output |
| 8 | LLM Client | Calls Groq API. Parses JSON. Retries once on 429 or parse failure |
| 9 | Noise Filter | Drops confidence <0.6. Deduplicates. Caps at 20. Sorts by severity |
| 10 | GitHub Poster | Posts review via PyGithub. Falls back to body-only if inline positions invalid |
| 11 | DB Writer | Persists `Review` + `ReviewComment` rows to SQLite |
| 12 | SSE Broadcaster | Pushes completion event to all connected VS Code clients |

---

## 🛠 Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Backend Framework | FastAPI | 0.111.0 | REST API, webhooks, SSE |
| ASGI Server | Uvicorn | 0.29.0 | Production-grade async server |
| ORM | SQLModel | 0.0.18 | SQLite database access |
| Database | SQLite | built-in | Persistent storage |
| Primary LLM | Groq | latest | `llama-3.1-8b-instant` — free tier |
| Fallback LLM | Anthropic | 0.28.0 | `claude-sonnet-4-20250514` |
| Fallback LLM | Google Gemini | 0.7.2 | `gemini-1.5-flash` |
| GitHub Integration | PyGithub | 2.3.0 | PR files, posting reviews |
| Token Counter | tiktoken | 0.7.0 | Accurate chunk sizing |
| HTTP Client | httpx | 0.27.0 | Async HTTP calls |
| Data Validation | Pydantic | 2.7.1 | Request/response models |
| Auth | python-jose | 3.3.0 | JWT creation & validation |
| Encryption | passlib / Fernet | 1.7.4 | Access token encryption |
| Frontend | TypeScript + VS Code API | 5.4.5 | Extension development |
| HTTP Client (ext) | axios | 1.7.2 | Extension API calls |
| Containerisation | Docker + Compose | latest | Single-command deployment |
| Tunnel | ngrok | latest | Expose webhook to GitHub |

---

## 📁 Project Structure

```
ai-reviewer/
├── backend/
│   ├── main.py                 # FastAPI app entrypoint + lifespan
│   ├── config.py               # Settings from .env via pydantic-settings
│   ├── database.py             # SQLite engine + session factory
│   ├── models.py               # SQLModel ORM table definitions
│   ├── worker.py               # asyncio.Queue consumer loop
│   ├── sse.py                  # Server-Sent Events broadcaster
│   ├── requirements.txt        # Pinned Python dependencies
│   ├── routers/
│   │   ├── webhook.py          # POST /webhook — GitHub event receiver
│   │   ├── reviews.py          # GET /reviews, GET /reviews/{id}, POST /feedback
│   │   ├── file_review.py      # POST /review/file — on-demand file review
│   │   ├── auth.py             # GitHub OAuth PKCE + JWT issuance
│   │   ├── dashboard.py        # GET /dashboard — web UI
│   │   └── autofix.py          # POST /autofix — AI fix generation
│   └── services/
│       ├── github_client.py    # PyGithub wrapper — fetch diffs, post reviews
│       ├── diff_parser.py      # Diff fetching, filtering, chunking
│       ├── prompt_engine.py    # SYSTEM_PROMPT + build_prompt()
│       ├── llm_client.py       # Groq / Anthropic / Gemini unified interface
│       ├── noise_filter.py     # Confidence filter + deduplication + cap
│       ├── review_pipeline.py  # Full PR review orchestration
│       └── autofix_engine.py   # AI fix generation engine
├── extension/
│   ├── src/
│   │   ├── extension.ts        # Activate + register all commands
│   │   ├── apiClient.ts        # HTTP calls to FastAPI backend
│   │   ├── reviewPanel.ts      # TreeView provider + webview panel
│   │   └── diagnostics.ts      # VS Code Problems panel integration
│   ├── package.json            # Extension manifest + contributes
│   └── tsconfig.json           # TypeScript compiler config
├── db/                         # Auto-created. SQLite file lives here.
├── .env.example                # Template — copy to .env and fill in
├── .gitignore
├── Dockerfile                  # python:3.11-slim based image
├── docker-compose.yml          # Single-service compose with volume mounts
└── README.md
```

---

## 📦 Prerequisites

Before you begin, make sure you have:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Docker Desktop | latest | [docker.com](https://docker.com) |
| VS Code | 1.89+ | [code.visualstudio.com](https://code.visualstudio.com) |
| ngrok | latest | [ngrok.com](https://ngrok.com) |
| Git | any | [git-scm.com](https://git-scm.com) |

You also need accounts on:
- **GitHub** — for GitHub App creation and OAuth
- **Groq** — free API key at [console.groq.com](https://console.groq.com) (no billing required)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/ai-reviewer.git
cd ai-reviewer
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Open `.env` and fill in every value:

```env
# ── GitHub App ────────────────────────────────────────────────
GITHUB_WEBHOOK_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(32))">
GITHUB_APP_ID=<numeric App ID from GitHub App settings page>
GITHUB_PRIVATE_KEY_PATH=./github_app.pem
GITHUB_CLIENT_ID=<OAuth App Client ID>
GITHUB_CLIENT_SECRET=<OAuth App Client Secret>

# ── LLM Keys (at least one required) ─────────────────────────
GROQ_API_KEY=<from console.groq.com — free>
ANTHROPIC_API_KEY=<optional>
GOOGLE_API_KEY=<optional>

# ── Security ──────────────────────────────────────────────────
JWT_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(32))">
ENCRYPTION_KEY=<generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# ── Server ────────────────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
```

> ⚠️ **Never commit `.env` to git.** It is already in `.gitignore`.

### 3. GitHub App Setup

#### Step 1 — Create the GitHub App

Go to [https://github.com/settings/apps/new](https://github.com/settings/apps/new) and fill in:

| Field | Value |
|-------|-------|
| GitHub App name | `ai-code-reviewer-yourname` (must be globally unique) |
| Homepage URL | `http://localhost:8000` |
| Webhook URL | `https://<your-ngrok-url>/webhook` ← update after ngrok starts |
| Webhook secret | Same value as `GITHUB_WEBHOOK_SECRET` in `.env` |
| Repository permissions → Contents | Read-only |
| Repository permissions → Pull requests | Read & Write |
| Repository permissions → Metadata | Read-only (auto) |
| Subscribe to events → Pull request | ✅ Checked |
| Where can this app be installed? | Only on this account |

#### Step 2 — Download credentials

1. After creating the app, note the **App ID** shown at the top → set `GITHUB_APP_ID`
2. Scroll to **Private keys** → click **Generate a private key** → download the `.pem` file
3. Move/rename it to `./github_app.pem` in the project root
4. In the left sidebar, go to **OAuth App** section → note **Client ID** and generate a **Client Secret**
5. Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `.env`

#### Step 3 — Install the app on your repo

Go to your GitHub App → **Install App** → select the repository you want to review PRs on.

### 4. Backend Setup

#### Using Docker (recommended)

```bash
# Build and start
docker compose up --build

# To rebuild after code changes
docker compose down
docker compose up --build
```

#### Using local Python

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Start ngrok (required for GitHub webhooks)

Open a **new terminal** and run:

```bash
ngrok http 8000
```

Copy the `https://xxx.ngrok-free.app` URL and update your GitHub App's **Webhook URL** to:
```
https://xxx.ngrok-free.app/webhook
```

Go to GitHub App Settings → paste the new URL → Save.

### 5. VS Code Extension Setup

Open a **new VS Code window** with the extension folder as root:

```bash
code ai-reviewer/extension
```

Then in the VS Code terminal:

```bash
npm install
npm run compile
```

Press **F5** → this launches the **Extension Development Host** — a new VS Code window with the AI Reviewer extension loaded.

---

## 🏃 Running the Application

### Option A: Docker (Recommended)

```bash
# From project root
docker compose up --build
```

Services started:
- Backend API at `http://localhost:8000`
- Dashboard at `http://localhost:8000/dashboard`
- Health check at `http://localhost:8000/health`

```bash
# Stop
docker compose down

# Rebuild after changes
docker compose down && docker compose up --build
```

### Option B: Local Development

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — ngrok:**
```bash
ngrok http 8000
```

**Terminal 3 — Extension (in extension/ folder):**
```bash
npm run watch   # auto-recompile on save
```
Then press F5 in VS Code.

---

## 🔄 How It Works

### GitHub PR Review Flow

```
Developer opens PR
       │
       ▼
GitHub fires POST /webhook
       │
       ▼
FastAPI validates HMAC-SHA256 signature
       │
       ├── Invalid → 401 Unauthorized
       │
       └── Valid → enqueue job → return 200 immediately
                        │
                        ▼
               Background worker picks up job
                        │
                        ▼
               Fetch PR file diffs (PyGithub)
               Skip: removed files, lock files,
                     binary files, zero additions
                        │
                        ▼
               Split patches into chunks (tiktoken)
               Max 3000 tokens per chunk
               Split at @@ hunk boundaries
                        │
                        ▼
               For each chunk → build prompt → call Groq LLM
               Model: llama-3.1-8b-instant
               Response: JSON with position, body, severity,
                         category, confidence
                        │
                        ▼
               Noise filter:
               1. Drop confidence < 0.6
               2. Deduplicate (same position + category)
               3. Sort: critical > warning > suggestion > info
               4. Cap at 20 comments
                        │
                        ▼
               Post review to GitHub PR (PyGithub)
               → Try inline comments first
               → Fall back to body-only if 422 error
                        │
                        ▼
               Save Review + ReviewComment rows to SQLite
                        │
                        ▼
               Broadcast SSE event to VS Code extension
```

### VS Code File Review Flow

```
Developer: AI Reviewer: Review Current File (Ctrl+Shift+P)
       │
       ▼
Extension reads active editor content + language
       │
       ▼
POST /review/file with {file_path, content, language}
       │
       ▼
FastAPI runs same pipeline (chunk → prompt → LLM → filter)
No GitHub posting for file reviews
       │
       ▼
Returns JSON array of comments with line numbers
       │
       ▼
Extension applies:
  ├── VS Code Diagnostics (Problems panel)
  └── TreeView sidebar (grouped by severity)
```

### AI Autofix Flow

```
Developer clicks "Fix with AI" on a comment
       │
       ▼
POST /autofix with {file_content, issue, language, line}
       │
       ▼
Groq LLM receives full file + issue description
Generates complete fixed file
Returns: {fixed_code, explanation, changes[]}
       │
       ▼
VS Code opens diff view:
  Left:  original file
  Right: AI-fixed version
       │
       ▼
Developer reviews the diff
       │
       ├── "Apply Fix" → WorkspaceEdit replaces content → file saved
       └── "Dismiss"  → no changes made
```

---

## 📡 API Reference

### Public Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | None | Health check. Returns `{status: ok, db: ok}` |
| `GET` | `/dashboard` | None | Live web dashboard (HTML) |
| `GET` | `/events` | None | SSE stream for real-time updates |
| `POST` | `/webhook` | HMAC signature | Receive GitHub PR events |
| `POST` | `/auth/github` | None | Start GitHub OAuth PKCE flow |
| `GET` | `/auth/callback` | None | OAuth callback — issues JWT |

### Authenticated Endpoints (Bearer JWT)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/me` | Current user info |
| `POST` | `/review/file` | Review a single file, returns comments |
| `POST` | `/autofix` | Generate AI fix for a specific issue |
| `GET` | `/reviews` | List all reviews (query: `repo_id`, `pr_number`, `limit`, `offset`) |
| `GET` | `/reviews/{id}` | Single review with all comments |
| `POST` | `/feedback/{comment_id}` | Submit thumbs up (1) or down (-1) |
| `GET` | `/repos` | List registered repositories |
| `POST` | `/repos/register` | Register a repo + install webhook |

### POST /review/file — Request Body

```json
{
  "file_path": "src/auth/login.py",
  "content": "<full file content>",
  "language": "python",
  "context": "code review"
}
```

### POST /review/file — Response

```json
{
  "review_id": null,
  "comments": [
    {
      "line": 42,
      "end_line": 45,
      "severity": "warning",
      "category": "security",
      "confidence": 0.91,
      "body": "SQL query constructed via string formatting..."
    }
  ],
  "summary": "Found 2 issues: 1 security, 1 style.",
  "model_used": "llama-3.1-8b-instant",
  "tokens_used": 1247
}
```

### POST /autofix — Request Body

```json
{
  "file_content": "<full file content>",
  "issue": "SQL query constructed via string formatting — use parameterised queries",
  "language": "python",
  "category": "security",
  "file_path": "login.py",
  "line": 42
}
```

### POST /autofix — Response

```json
{
  "fixed_code": "<complete fixed file content>",
  "explanation": "Replaced string-formatted SQL with parameterised query to prevent SQL injection.",
  "changes": [
    {"line": 42, "description": "Changed to cursor.execute() with parameters tuple"}
  ],
  "model_used": "llama-3.1-8b-instant"
}
```

---

## 🖥 VS Code Extension Usage

### Commands (Ctrl+Shift+P)

| Command | Description |
|---------|-------------|
| `AI Reviewer: Review Current File` | Reviews the active file and shows comments |
| `AI Reviewer: Fix Issue at Cursor` | Generates AI fix for the comment nearest to cursor |
| `AI Reviewer: Show Review Panel` | Opens the full review webview panel |
| `AI Reviewer: Clear Comments` | Removes all diagnostics and sidebar comments |
| `AI Reviewer: Sign In with GitHub` | Opens GitHub OAuth flow in browser |
| `AI Reviewer: Sign Out` | Clears stored JWT |

### Right-Click Menus

- **Editor context menu**: `AI Reviewer: Fix Issue at Cursor`
- **Sidebar comment context menu**: `AI Reviewer: Fix This Issue`

### Status Bar

A `$(shield) AI Review` button appears in the bottom status bar. Click it to review the current file instantly.

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `aiReviewer.serverUrl` | `http://localhost:8000` | Backend server URL |

---

## 📊 Dashboard

Open `http://localhost:8000/dashboard` in any browser.

Features:
- **Stats cards** — total repos, PRs, reviews, comments
- **Severity breakdown** — visual count of critical / warning / suggestion / info
- **Live activity feed** — real-time SSE stream showing review events as they happen
- **Review history table** — all past reviews with model, duration, comment count
- **PR detail view** — click any PR to expand and see all comments
- **Auto-refresh** — stats and PR list update every 30 seconds

---

## 🗄 Database Schema

```
User
├── id (PK)
├── github_id (unique)
├── github_login
├── email
├── access_token_enc (Fernet encrypted)
└── created_at

Repository
├── id (PK)
├── github_repo_id (unique)
├── full_name (owner/repo)
├── default_branch
├── webhook_active
└── created_at

PullRequest
├── id (PK)
├── repo_id (FK → Repository)
├── pr_number
├── title, author, head_sha
├── status (pending|reviewing|completed|failed)
├── created_at, updated_at

Review
├── id (PK)
├── pr_id (FK → PullRequest)
├── model_used
├── tokens_used, duration_ms
├── summary
├── github_review_id
└── created_at

ReviewComment
├── id (PK)
├── review_id (FK → Review)
├── file_path
├── line, body
├── severity (critical|warning|suggestion|info)
├── confidence (0.0–1.0)
├── category (bug|security|style|performance|logic|documentation)
└── created_at

Feedback
├── id (PK)
├── comment_id (FK → ReviewComment)
├── github_login
├── rating (1=helpful, -1=not helpful)
└── created_at
```

---

## ⚙ Configuration Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_WEBHOOK_SECRET` | ✅ | HMAC secret for webhook validation |
| `GITHUB_APP_ID` | ✅ | GitHub App numeric ID |
| `GITHUB_PRIVATE_KEY_PATH` | ✅ | Path to `.pem` private key file |
| `GITHUB_CLIENT_ID` | ✅ | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | ✅ | GitHub OAuth App client secret |
| `GROQ_API_KEY` | ✅ | Groq API key (free tier available) |
| `ANTHROPIC_API_KEY` | ⬜ | Anthropic API key (fallback LLM) |
| `GOOGLE_API_KEY` | ⬜ | Google Gemini API key (fallback LLM) |
| `JWT_SECRET` | ✅ | Min 32 random characters for JWT signing |
| `ENCRYPTION_KEY` | ✅ | Fernet key for encrypting GitHub access tokens |
| `HOST` | ⬜ | Bind host (default: `0.0.0.0`) |
| `PORT` | ⬜ | Bind port (default: `8000`) |
| `ENVIRONMENT` | ⬜ | `development` or `production` |

---

## 🔒 Security

### Webhook Security
- Every incoming webhook is validated with **HMAC-SHA256** using `hmac.compare_digest()` (timing-attack resistant)
- Webhooks older than 5 minutes are rejected
- GitHub App installation tokens are cached in memory with TTL — never logged or persisted

### Authentication
- GitHub OAuth **PKCE flow** — no passwords stored
- JWT tokens signed with HS256, 7-day expiry
- JWTs stored in VS Code **SecretStorage** → OS keychain (Keychain on macOS, Credential Manager on Windows, libsecret on Linux)
- GitHub access tokens encrypted at rest using **Fernet symmetric encryption**

### Secrets Management
- All secrets loaded from `.env` at startup via `pydantic-settings`
- `.env` is in `.gitignore` — never committed
- Docker passes secrets via `env_file` directive — not baked into the image

---

## 🔧 Troubleshooting

### Server won't start

```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000      # Windows
lsof -i :8000                     # macOS/Linux

# Kill the process using port 8000
taskkill /PID <pid> /F            # Windows
kill -9 <pid>                     # macOS/Linux
```

### ngrok ERR_NGROK_108 (too many sessions)

```bash
# Kill all existing ngrok processes
taskkill /IM ngrok.exe /F         # Windows
pkill ngrok                       # macOS/Linux

# Then start fresh
ngrok http 8000
```

### Webhook returns 401

- Check `GITHUB_WEBHOOK_SECRET` in `.env` matches the secret in GitHub App settings exactly
- Make sure you're sending the request with the correct `X-Hub-Signature-256` header

### No comments posted to PR

1. Check backend logs: `docker compose logs -f` or uvicorn terminal
2. Check if the ngrok URL in GitHub App settings is up to date
3. Verify the GitHub App is installed on the repo
4. Check the `GROQ_API_KEY` is valid: visit [console.groq.com](https://console.groq.com)

### VS Code extension "Cannot connect to server"

1. Make sure the backend is running: `GET http://localhost:8000/health` should return `{"status":"ok"}`
2. Check `aiReviewer.serverUrl` in VS Code settings matches your server URL
3. If using Docker, ensure the container is healthy: `docker compose ps`

### "uvicorn is not recognized" on Windows

```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1

# Then use python -m
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### PowerShell script execution disabled

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 👨‍💻 Development Guide

### Running Tests

```bash
cd backend
python test_phase3.py   # Tests diff parser, LLM client, noise filter
```

### Adding a New LLM Provider

1. Add the API key to `.env.example` and `config.py`
2. In `services/llm_client.py`, add a new branch in `__init__` and `review()`
3. Add the model name constant at the top of the file

### Modifying the Review Prompt

Edit `SYSTEM_PROMPT` in `services/prompt_engine.py`. The prompt **must** instruct the LLM to return only JSON with no markdown fences — otherwise JSON parsing fails.

### Adding a New API Endpoint

1. Create or edit a router in `backend/routers/`
2. Import and include it in `backend/main.py` with `app.include_router()`
3. Add a corresponding method to `extension/src/apiClient.ts`

### Rebuilding the Extension

```bash
cd extension
npm run compile        # One-time build
npm run watch          # Auto-rebuild on save (use during development)
```

---

## 🎓 Academic Context

This project was developed as a final year B.Tech project at:

**Coimbatore Institute of Technology**  
Department of Information Technology  
Academic Year 2024–2025

### Team

| Name | Roll Number |
|------|-------------|
| G Sharan Eshwar | 2403717620521051 |
| S Praanesh | 2403717620521031 |
| Prathap M | 2403717620521035 |
| R Prasanna Adithyaa | 2403717620521034 |
| G P Harish | 2403717620521015 |

### MVP Checklist (All 10 items passing ✅)

| # | Test | Result |
|---|------|--------|
| 1 | `GET /health` returns `{status: ok, db: ok}` | ✅ |
| 2 | `POST /webhook` with wrong HMAC → 401 | ✅ |
| 3 | `POST /webhook` with correct HMAC → 200 + job enqueued | ✅ |
| 4 | Real PR on GitHub → AI review comments posted within 3 min | ✅ |
| 5 | `POST /review/file` with Python snippet → JSON with comments | ✅ |
| 6 | `GET /events` → SSE stream with 30s ping | ✅ |
| 7 | VS Code Sign In → GitHub OAuth → "Signed in" confirmation | ✅ |
| 8 | VS Code Review File → comments in Problems panel <30s | ✅ |
| 9 | VS Code Activity Bar → AI Reviewer icon + sidebar tree | ✅ |
| 10 | `docker compose up` → server starts, `/health` returns ok | ✅ |

---

## 📄 License

```
MIT License

Copyright (c) 2025 G Sharan Eshwar, S Praanesh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<div align="center">

**Built with ❤️ at Coimbatore Institute of Technology**

[🌐 Dashboard](http://localhost:8000/dashboard) · [📡 Health Check](http://localhost:8000/health) · [📖 API Docs](http://localhost:8000/docs)

</div>
