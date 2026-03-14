import logging
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select, func
from database import engine
from models import PullRequest, Review, ReviewComment, Repository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard/stats")
async def get_stats():
    with Session(engine) as session:
        total_prs = session.exec(select(func.count(PullRequest.id))).one()
        total_reviews = session.exec(select(func.count(Review.id))).one()
        total_comments = session.exec(select(func.count(ReviewComment.id))).one()

        critical = session.exec(
            select(func.count(ReviewComment.id)).where(ReviewComment.severity == "critical")
        ).one()
        warning = session.exec(
            select(func.count(ReviewComment.id)).where(ReviewComment.severity == "warning")
        ).one()
        suggestion = session.exec(
            select(func.count(ReviewComment.id)).where(ReviewComment.severity == "suggestion")
        ).one()
        info = session.exec(
            select(func.count(ReviewComment.id)).where(ReviewComment.severity == "info")
        ).one()

        avg_duration = session.exec(select(func.avg(Review.duration_ms))).one() or 0

        return {
            "total_prs": total_prs,
            "total_reviews": total_reviews,
            "total_comments": total_comments,
            "critical": critical,
            "warning": warning,
            "suggestion": suggestion,
            "info": info,
            "avg_duration_ms": round(avg_duration),
        }


@router.get("/dashboard/recent")
async def get_recent():
    with Session(engine) as session:
        prs = session.exec(
            select(PullRequest).order_by(PullRequest.created_at.desc()).limit(20)
        ).all()

        result = []
        for pr in prs:
            repo = session.get(Repository, pr.repo_id)
            review = session.exec(
                select(Review).where(Review.pr_id == pr.id)
            ).first()

            comment_counts = {"critical": 0, "warning": 0, "suggestion": 0, "info": 0}
            comments = []
            if review:
                comments = session.exec(
                    select(ReviewComment).where(ReviewComment.review_id == review.id)
                ).all()
                for c in comments:
                    if c.severity in comment_counts:
                        comment_counts[c.severity] += 1

            result.append({
                "pr_id": pr.id,
                "pr_number": pr.pr_number,
                "title": pr.title,
                "author": pr.author,
                "status": pr.status,
                "repo": repo.full_name if repo else "unknown",
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "review_id": review.id if review else None,
                "model_used": review.model_used if review else None,
                "duration_ms": review.duration_ms if review else 0,
                "total_comments": len(comments),
                "comment_counts": comment_counts,
                "summary": review.summary if review else "",
            })

        return result


@router.get("/dashboard/review/{review_id}/comments")
async def get_review_comments(review_id: int):
    with Session(engine) as session:
        comments = session.exec(
            select(ReviewComment).where(ReviewComment.review_id == review_id)
        ).all()
        return comments


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Code Reviewer — Dashboard</title>
<style>
  :root {
    --bg: #0d1117;
    --bg2: #161b22;
    --bg3: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --text2: #8b949e;
    --blue: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --yellow: #d29922;
    --purple: #bc8cff;
    --orange: #ffa657;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; min-height: 100vh; }

  /* NAV */
  nav { background: var(--bg2); border-bottom: 1px solid var(--border); padding: 0 24px; height: 60px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; }
  .nav-brand { display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 600; color: var(--text); }
  .nav-brand .shield { font-size: 22px; }
  .nav-status { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text2); }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* MAIN */
  main { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }
  h1 { font-size: 24px; font-weight: 600; margin-bottom: 8px; }
  .subtitle { color: var(--text2); font-size: 14px; margin-bottom: 32px; }

  /* STATS */
  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .stat-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 20px; transition: border-color 0.2s; }
  .stat-card:hover { border-color: var(--blue); }
  .stat-label { font-size: 12px; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .stat-value { font-size: 32px; font-weight: 700; }
  .stat-sub { font-size: 12px; color: var(--text2); margin-top: 4px; }
  .stat-card.blue .stat-value { color: var(--blue); }
  .stat-card.red .stat-value { color: var(--red); }
  .stat-card.green .stat-value { color: var(--green); }
  .stat-card.yellow .stat-value { color: var(--yellow); }
  .stat-card.purple .stat-value { color: var(--purple); }

  /* SECTION */
  .section { margin-bottom: 32px; }
  .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .section-title { font-size: 16px; font-weight: 600; }
  .badge { font-size: 12px; background: var(--bg3); border: 1px solid var(--border); border-radius: 12px; padding: 2px 10px; color: var(--text2); }

  /* SEVERITY BAR */
  .severity-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 32px; }
  .sev-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
  .sev-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .sev-label { font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
  .sev-count { font-size: 20px; font-weight: 700; }
  .sev-bar { height: 4px; border-radius: 2px; background: var(--bg3); overflow: hidden; }
  .sev-fill { height: 100%; border-radius: 2px; transition: width 0.8s ease; }
  .sev-card.critical .sev-fill { background: var(--red); }
  .sev-card.critical .sev-count { color: var(--red); }
  .sev-card.warning .sev-fill { background: var(--yellow); }
  .sev-card.warning .sev-count { color: var(--yellow); }
  .sev-card.suggestion .sev-fill { background: var(--blue); }
  .sev-card.suggestion .sev-count { color: var(--blue); }
  .sev-card.info .sev-fill { background: var(--purple); }
  .sev-card.info .sev-count { color: var(--purple); }

  /* PR TABLE */
  .pr-list { display: flex; flex-direction: column; gap: 12px; }
  .pr-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 16px 20px; cursor: pointer; transition: border-color 0.2s, background 0.2s; }
  .pr-card:hover { border-color: var(--blue); background: var(--bg3); }
  .pr-card.active { border-color: var(--blue); }
  .pr-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
  .pr-title { font-size: 15px; font-weight: 600; color: var(--blue); margin-bottom: 4px; }
  .pr-meta { font-size: 12px; color: var(--text2); display: flex; gap: 12px; flex-wrap: wrap; }
  .pr-meta span { display: flex; align-items: center; gap: 4px; }
  .pr-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
  .status-badge { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
  .status-completed { background: rgba(63,185,80,0.15); color: var(--green); border: 1px solid rgba(63,185,80,0.3); }
  .status-reviewing { background: rgba(210,153,34,0.15); color: var(--yellow); border: 1px solid rgba(210,153,34,0.3); }
  .status-pending { background: rgba(139,148,158,0.15); color: var(--text2); border: 1px solid var(--border); }
  .status-failed { background: rgba(248,81,73,0.15); color: var(--red); border: 1px solid rgba(248,81,73,0.3); }
  .comment-pills { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
  .pill { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }
  .pill.critical { background: rgba(248,81,73,0.15); color: var(--red); }
  .pill.warning { background: rgba(210,153,34,0.15); color: var(--yellow); }
  .pill.suggestion { background: rgba(88,166,255,0.15); color: var(--blue); }
  .pill.info { background: rgba(188,140,255,0.15); color: var(--purple); }

  /* DETAIL PANEL */
  .detail-panel { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-top: 16px; display: none; }
  .detail-panel.open { display: block; }
  .detail-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: var(--text2); }
  .summary-box { background: var(--bg3); border-left: 3px solid var(--blue); border-radius: 4px; padding: 12px 16px; font-size: 13px; line-height: 1.6; margin-bottom: 16px; color: var(--text); }
  .comment-item { border: 1px solid var(--border); border-radius: 6px; padding: 12px; margin-bottom: 8px; background: var(--bg); }
  .comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
  .comment-file { font-size: 12px; color: var(--text2); font-family: monospace; }
  .comment-line { font-size: 11px; background: var(--bg3); padding: 1px 6px; border-radius: 4px; color: var(--text2); }
  .comment-body { font-size: 13px; line-height: 1.5; color: var(--text); }
  .confidence-bar { height: 2px; background: var(--bg3); border-radius: 1px; margin-top: 8px; }
  .confidence-fill { height: 100%; border-radius: 1px; background: var(--green); }
  .model-tag { font-size: 11px; background: var(--bg3); border: 1px solid var(--border); padding: 2px 8px; border-radius: 4px; color: var(--text2); font-family: monospace; }

  /* ACTIVITY FEED */
  .activity-feed { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 16px; max-height: 200px; overflow-y: auto; }
  .activity-item { font-size: 12px; color: var(--text2); padding: 4px 0; border-bottom: 1px solid var(--border); display: flex; gap: 8px; }
  .activity-item:last-child { border: none; }
  .activity-time { color: var(--text2); white-space: nowrap; font-family: monospace; }
  .activity-msg { color: var(--text); }

  /* LOADING */
  .loading { color: var(--text2); text-align: center; padding: 40px; font-size: 14px; }
  .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid var(--border); border-top-color: var(--blue); border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* EMPTY STATE */
  .empty { text-align: center; padding: 60px 20px; color: var(--text2); }
  .empty-icon { font-size: 48px; margin-bottom: 16px; }
  .empty-title { font-size: 16px; font-weight: 600; color: var(--text); margin-bottom: 8px; }

  /* SCROLLBAR */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg2); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text2); }
</style>
</head>
<body>

<nav>
  <div class="nav-brand">
    <span class="shield">🛡️</span>
    <span>AI Code Reviewer</span>
  </div>
  <div class="nav-status">
    <div class="status-dot" id="statusDot"></div>
    <span id="statusText">Connecting...</span>
    <span style="margin-left:12px; color: var(--border)">|</span>
    <span style="margin-left:12px" id="lastUpdate"></span>
  </div>
</nav>

<main>
  <h1>Dashboard</h1>
  <p class="subtitle">Real-time AI code review monitoring</p>

  <!-- STATS -->
  <div class="stats-grid" id="statsGrid">
    <div class="stat-card blue">
      <div class="stat-label">Pull Requests</div>
      <div class="stat-value" id="statPRs">—</div>
      <div class="stat-sub">Total reviewed</div>
    </div>
    <div class="stat-card red">
      <div class="stat-label">Total Issues</div>
      <div class="stat-value" id="statIssues">—</div>
      <div class="stat-sub">Across all PRs</div>
    </div>
    <div class="stat-card green">
      <div class="stat-label">Reviews Done</div>
      <div class="stat-value" id="statReviews">—</div>
      <div class="stat-sub">Completed</div>
    </div>
    <div class="stat-card yellow">
      <div class="stat-label">Avg Duration</div>
      <div class="stat-value" id="statAvg">—</div>
      <div class="stat-sub">Per review</div>
    </div>
    <div class="stat-card purple">
      <div class="stat-label">Critical Issues</div>
      <div class="stat-value" id="statCritical">—</div>
      <div class="stat-sub">Need immediate attention</div>
    </div>
  </div>

  <!-- SEVERITY BREAKDOWN -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">Issues Breakdown</div>
    </div>
    <div class="severity-grid">
      <div class="sev-card critical">
        <div class="sev-header">
          <div class="sev-label">🔴 Critical</div>
          <div class="sev-count" id="sevCritical">0</div>
        </div>
        <div class="sev-bar"><div class="sev-fill" id="barCritical" style="width:0%"></div></div>
      </div>
      <div class="sev-card warning">
        <div class="sev-header">
          <div class="sev-label">🟡 Warning</div>
          <div class="sev-count" id="sevWarning">0</div>
        </div>
        <div class="sev-bar"><div class="sev-fill" id="barWarning" style="width:0%"></div></div>
      </div>
      <div class="sev-card suggestion">
        <div class="sev-header">
          <div class="sev-label">🔵 Suggestion</div>
          <div class="sev-count" id="sevSuggestion">0</div>
        </div>
        <div class="sev-bar"><div class="sev-fill" id="barSuggestion" style="width:0%"></div></div>
      </div>
      <div class="sev-card info">
        <div class="sev-header">
          <div class="sev-label">⚪ Info</div>
          <div class="sev-count" id="sevInfo">0</div>
        </div>
        <div class="sev-bar"><div class="sev-fill" id="barInfo" style="width:0%"></div></div>
      </div>
    </div>
  </div>

  <!-- LIVE ACTIVITY -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">Live Activity</div>
      <span class="badge" id="activityBadge">Listening...</span>
    </div>
    <div class="activity-feed" id="activityFeed">
      <div class="activity-item">
        <span class="activity-time">--:--:--</span>
        <span class="activity-msg">Waiting for events...</span>
      </div>
    </div>
  </div>

  <!-- PR LIST -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">Recent Pull Requests</div>
      <span class="badge" id="prBadge">Loading...</span>
    </div>
    <div id="prList" class="pr-list">
      <div class="loading"><span class="spinner"></span>Loading reviews...</div>
    </div>
  </div>
</main>

<script>
let allPRs = [];
let activePRId = null;

// ── TIME HELPERS ─────────────────────────────
function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff/60)}m ago`;
  if (diff < 86400) return `${Math.round(diff/3600)}h ago`;
  return `${Math.round(diff/86400)}d ago`;
}

function nowStr() {
  return new Date().toLocaleTimeString();
}

// ── ACTIVITY FEED ────────────────────────────
function addActivity(msg, type='info') {
  const feed = document.getElementById('activityFeed');
  const colors = { info: '#8b949e', success: '#3fb950', warning: '#d29922', error: '#f85149' };
  const item = document.createElement('div');
  item.className = 'activity-item';
  item.innerHTML = `<span class="activity-time">${nowStr()}</span><span class="activity-msg" style="color:${colors[type]}">${msg}</span>`;
  feed.insertBefore(item, feed.firstChild);
  if (feed.children.length > 20) feed.removeChild(feed.lastChild);
}

// ── LOAD STATS ───────────────────────────────
async function loadStats() {
  try {
    const res = await fetch('/dashboard/stats');
    const s = await res.json();
    document.getElementById('statPRs').textContent = s.total_prs;
    document.getElementById('statIssues').textContent = s.total_comments;
    document.getElementById('statReviews').textContent = s.total_reviews;
    document.getElementById('statAvg').textContent = s.avg_duration_ms > 0 ? `${(s.avg_duration_ms/1000).toFixed(1)}s` : '—';
    document.getElementById('statCritical').textContent = s.critical;

    const total = s.total_comments || 1;
    document.getElementById('sevCritical').textContent = s.critical;
    document.getElementById('sevWarning').textContent = s.warning;
    document.getElementById('sevSuggestion').textContent = s.suggestion;
    document.getElementById('sevInfo').textContent = s.info;
    document.getElementById('barCritical').style.width = `${Math.round(s.critical/total*100)}%`;
    document.getElementById('barWarning').style.width = `${Math.round(s.warning/total*100)}%`;
    document.getElementById('barSuggestion').style.width = `${Math.round(s.suggestion/total*100)}%`;
    document.getElementById('barInfo').style.width = `${Math.round(s.info/total*100)}%`;

    document.getElementById('lastUpdate').textContent = `Updated ${nowStr()}`;
  } catch(e) {
    console.error('Stats error:', e);
  }
}

// ── LOAD PR LIST ─────────────────────────────
async function loadPRs() {
  try {
    const res = await fetch('/dashboard/recent');
    allPRs = await res.json();
    document.getElementById('prBadge').textContent = `${allPRs.length} total`;
    renderPRs();
  } catch(e) {
    document.getElementById('prList').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-title">Failed to load PRs</div></div>';
  }
}

// ── RENDER PR LIST ───────────────────────────
function renderPRs() {
  const container = document.getElementById('prList');
  if (allPRs.length === 0) {
    container.innerHTML = `
      <div class="empty">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">No PRs reviewed yet</div>
        <div>Open a Pull Request on GitHub to trigger a review</div>
      </div>`;
    return;
  }

  container.innerHTML = allPRs.map(pr => {
    const pills = Object.entries(pr.comment_counts)
      .filter(([,v]) => v > 0)
      .map(([k,v]) => `<span class="pill ${k}">${k === 'critical' ? '🔴' : k === 'warning' ? '🟡' : k === 'suggestion' ? '🔵' : '⚪'} ${v} ${k}</span>`)
      .join('');

    const isActive = activePRId === pr.pr_id;

    return `
      <div class="pr-card ${isActive ? 'active' : ''}" onclick="toggleDetail(${pr.pr_id})" id="pr-card-${pr.pr_id}">
        <div class="pr-top">
          <div>
            <div class="pr-title">#${pr.pr_number} ${pr.title}</div>
            <div class="pr-meta">
              <span>📁 ${pr.repo}</span>
              <span>👤 ${pr.author}</span>
              <span>🕐 ${timeAgo(pr.created_at)}</span>
              ${pr.model_used ? `<span class="model-tag">${pr.model_used}</span>` : ''}
              ${pr.duration_ms ? `<span>⚡ ${(pr.duration_ms/1000).toFixed(1)}s</span>` : ''}
            </div>
            <div class="comment-pills">${pills || '<span style="color:var(--text2);font-size:12px">✅ No issues found</span>'}</div>
          </div>
          <div class="pr-right">
            <span class="status-badge status-${pr.status}">${pr.status}</span>
            <span style="font-size:20px;font-weight:700;color:var(--text)">${pr.total_comments}</span>
            <span style="font-size:11px;color:var(--text2)">issues</span>
          </div>
        </div>
        ${isActive ? renderDetail(pr) : ''}
      </div>`;
  }).join('');
}

// ── RENDER DETAIL ────────────────────────────
function renderDetail(pr) {
  if (!pr.review_id) return '';

  return `
    <div class="detail-panel open" id="detail-${pr.pr_id}">
      <div class="detail-title">Review Summary</div>
      ${pr.summary ? `<div class="summary-box">${pr.summary}</div>` : ''}
      <div id="comments-${pr.review_id}">
        <div class="loading"><span class="spinner"></span>Loading comments...</div>
      </div>
    </div>`;
}

// ── TOGGLE DETAIL ────────────────────────────
async function toggleDetail(prId) {
  if (activePRId === prId) {
    activePRId = null;
    renderPRs();
    return;
  }
  activePRId = prId;
  renderPRs();

  const pr = allPRs.find(p => p.pr_id === prId);
  if (!pr || !pr.review_id) return;

  try {
    const res = await fetch(`/dashboard/review/${pr.review_id}/comments`);
    const comments = await res.json();

    const container = document.getElementById(`comments-${pr.review_id}`);
    if (!container) return;

    if (comments.length === 0) {
      container.innerHTML = '<div style="color:var(--text2);font-size:13px;padding:8px 0">No inline comments</div>';
      return;
    }

    const sevEmoji = { critical: '🔴', warning: '🟡', suggestion: '🔵', info: '⚪' };

    container.innerHTML = comments.map(c => `
      <div class="comment-item">
        <div class="comment-header">
          <span class="pill ${c.severity}">${sevEmoji[c.severity] || '⚪'} ${c.severity}</span>
          <span class="pill ${c.category}" style="background:var(--bg3);color:var(--text2)">${c.category}</span>
          <span class="comment-file">${c.file_path}</span>
          <span class="comment-line">L${c.line}</span>
        </div>
        <div class="comment-body">${c.body}</div>
        <div class="confidence-bar">
          <div class="confidence-fill" style="width:${Math.round(c.confidence*100)}%;background:${c.confidence>0.8?'var(--green)':c.confidence>0.6?'var(--yellow)':'var(--red)'}"></div>
        </div>
        <div style="font-size:11px;color:var(--text2);margin-top:4px">Confidence: ${Math.round(c.confidence*100)}%</div>
      </div>`).join('');
  } catch(e) {
    console.error('Comments error:', e);
  }
}

// ── SSE REAL-TIME ────────────────────────────
function connectSSE() {
  const dot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  const es = new EventSource('/events');

  es.onopen = () => {
    dot.style.background = 'var(--green)';
    statusText.textContent = 'Live';
    addActivity('Connected to live event stream', 'success');
    document.getElementById('activityBadge').textContent = 'Live';
  };

  es.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data);
      if (event.type === 'ping') return;

      if (event.type === 'status') {
        addActivity(`PR #${event.pr_id} is being reviewed...`, 'warning');
        loadPRs();
        loadStats();
      } else if (event.type === 'completed') {
        addActivity(`✅ PR #${event.pr_id} review complete — ${event.comment_count} issues found`, 'success');
        loadPRs();
        loadStats();
      } else if (event.type === 'error') {
        addActivity(`❌ PR #${event.pr_id} review failed: ${event.message}`, 'error');
        loadPRs();
      }
    } catch(err) {}
  };

  es.onerror = () => {
    dot.style.background = 'var(--red)';
    statusText.textContent = 'Reconnecting...';
    addActivity('Connection lost, reconnecting...', 'error');
    setTimeout(connectSSE, 3000);
    es.close();
  };
}

// ── INIT ─────────────────────────────────────
loadStats();
loadPRs();
connectSSE();
setInterval(() => { loadStats(); loadPRs(); }, 30000);
</script>
</body>
</html>
'''