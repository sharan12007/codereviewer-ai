# AI Code Reviewer

AI-powered code review using GitHub webhooks + LLM (Groq/Gemini/Anthropic) + VS Code extension.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- ngrok
- A GitHub App
- A Groq API key (free) from https://console.groq.com

---

## 1. Clone and Setup
```bash
git clone <your_repo_url>
cd ai-reviewer
```

---

## 2. Backend Setup
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r backend/requirements.txt
```

---

## 3. Configure Environment
```bash
cp .env.example .env
```

Fill in your `.env`:

| Variable | How to get it |
|---|---|
| `GITHUB_WEBHOOK_SECRET` | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GITHUB_APP_ID` | From GitHub App settings page |
| `GITHUB_PRIVATE_KEY_PATH` | Path to downloaded `.pem` file |
| `GITHUB_CLIENT_ID` | From GitHub OAuth App |
| `GITHUB_CLIENT_SECRET` | From GitHub OAuth App |
| `GROQ_API_KEY` | From https://console.groq.com |
| `JWT_SECRET` | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ENCRYPTION_KEY` | Run: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

---

## 4. Create GitHub App

1. Go to https://github.com/settings/apps/new
2. Fill in:
   - **Name**: `ai-code-reviewer-yourname`
   - **Homepage URL**: `http://localhost:8000`
   - **Webhook URL**: `https://YOUR_NGROK_URL/webhook`
   - **Webhook secret**: same as `GITHUB_WEBHOOK_SECRET` in `.env`
3. Permissions:
   - Contents: Read-only
   - Pull requests: Read & Write
4. Subscribe to events: Pull request
5. Click **Create GitHub App**
6. Download private key → save as `github_app.pem` in project root

---

## 5. Start ngrok
```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` URL.
Update your GitHub App's Webhook URL to: `https://xxxx.ngrok-free.app/webhook`

---

## 6. Run the Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
# {"status":"ok","db":"ok"}
```

---

## 7. Build and Run VS Code Extension
```bash
cd extension
npm install
npm run compile
```

Press **F5** in VS Code to launch Extension Development Host.

Commands available (Ctrl+Shift+P):
- `AI Reviewer: Review Current File`
- `AI Reviewer: Sign In with GitHub`
- `AI Reviewer: Sign Out`
- `AI Reviewer: Clear Comments`

---

## 8. Run with Docker
```bash
docker compose up --build
```

Verify:
```bash
curl http://localhost:8000/health
```

---

## 9. Full Flow Test

1. Install the GitHub App on a test repository
2. Open a PR on that repo
3. Watch the backend logs — review job should be picked up
4. AI review comments appear on the PR within 1-2 minutes

---

## Project Structure
```
ai-reviewer/
├── backend/          # FastAPI server
├── extension/        # VS Code extension
├── db/               # SQLite database (auto-created)
├── .env.example      # Environment template
├── Dockerfile
└── docker-compose.yml
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No LLM API key found` | Set `GROQ_API_KEY` in `.env` |
| `Invalid signature` on webhook | Check `GITHUB_WEBHOOK_SECRET` matches GitHub App setting |
| `models/gemini-1.5-flash not found` | Switch to Groq — set `GROQ_API_KEY` |
| Extension not compiling | Run `npm install` in `extension/` folder |
| DB not created | Check `db/` folder exists, run server once |