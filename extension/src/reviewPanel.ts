import * as vscode from "vscode";
import { ReviewComment } from "./diagnostics";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

class GroupItem extends vscode.TreeItem {
  constructor(
    label: string,
    public readonly children: CommentItem[]
  ) {
    super(label, vscode.TreeItemCollapsibleState.Expanded);
  }
}

class CommentItem extends vscode.TreeItem {
  constructor(
    public readonly comment: ReviewComment,
    public readonly filePath: string
  ) {
    super(
      `Line ${comment.line}: ${comment.body.slice(0, 55)}${comment.body.length > 55 ? "…" : ""}`,
      vscode.TreeItemCollapsibleState.None
    );
    this.tooltip = comment.body;
    this.description = `${comment.category} · ${Math.round(comment.confidence * 100)}%`;
    this.command = {
      command: "ai-reviewer.goToLine",
      title: "Go to line",
      arguments: [filePath, comment.line],
    };
    const iconMap: Record<string, string> = {
      critical: "error",
      warning: "warning",
      suggestion: "info",
      info: "lightbulb",
    };
    this.iconPath = new vscode.ThemeIcon(iconMap[comment.severity] ?? "circle-outline");
  }
}

type AnyItem = GroupItem | CommentItem;

export class CommentsTreeProvider implements vscode.TreeDataProvider<AnyItem> {
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<AnyItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private panel: vscode.WebviewPanel | undefined;
  private comments: ReviewComment[] = [];
  private summary = "";
  private modelUsed = "";
  private filePath = "";

  setContext(_context: vscode.ExtensionContext): void {}

  setComments(
    filePath: string,
    comments: ReviewComment[],
    summary: string,
    modelUsed: string
  ): void {
    this.comments = comments;
    this.summary = summary;
    this.modelUsed = modelUsed;
    this.filePath = filePath;
    this._onDidChangeTreeData.fire();
    this.updateWebview();
  }

  clear(): void {
    this.comments = [];
    this.summary = "";
    this.modelUsed = "";
    this.filePath = "";
    this._onDidChangeTreeData.fire();
    this.updateWebview();
  }

  // ── Tree (left sidebar) ──────────────────────────────────────────────────

  getTreeItem(element: AnyItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: AnyItem): AnyItem[] {
    if (!element) {
      // Root — show group headers or placeholder
      if (this.comments.length === 0) {
        const item = new vscode.TreeItem(
          "Run: AI Reviewer: Review Current File",
          vscode.TreeItemCollapsibleState.None
        );
        item.iconPath = new vscode.ThemeIcon("shield");
        return [item as AnyItem];
      }

      const groups: GroupItem[] = [];

      const addGroup = (label: string, severity: string, icon: string) => {
        const items = this.comments
          .filter((c) => c.severity === severity)
          .map((c) => new CommentItem(c, this.filePath));
        if (items.length === 0) { return; }
        const g = new GroupItem(`${label}  (${items.length})`, items);
        g.iconPath = new vscode.ThemeIcon(icon);
        groups.push(g);
      };

      addGroup("Critical", "critical", "error");
      addGroup("Warnings", "warning", "warning");
      addGroup("Suggestions", "suggestion", "info");
      addGroup("Info", "info", "lightbulb");

      return groups;
    }

    // Child level — return comments inside a group
    if (element instanceof GroupItem) {
      return element.children;
    }

    return [];
  }

  // ── Webview panel (right side) ───────────────────────────────────────────

  showPanel(): void {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Beside);
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      "aiReviewerPanel",
      "AI Reviewer",
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true }
    );

    this.panel.onDidDispose(() => { this.panel = undefined; });

    this.panel.webview.onDidReceiveMessage((msg: unknown) => {
      if (
        typeof msg === "object" && msg !== null &&
        "command" in msg && (msg as Record<string, unknown>).command === "goToLine" &&
        "filePath" in msg && "line" in msg
      ) {
        const m = msg as { command: string; filePath: string; line: number };
        void this.goToLine(m.filePath, m.line);
      }
    });

    this.updateWebview();
  }

  private updateWebview(): void {
    if (!this.panel) { return; }
    this.panel.webview.html = this.getWebviewContent();
  }

  private async goToLine(filePath: string, line: number): Promise<void> {
    try {
      const uri = vscode.Uri.file(filePath);
      const doc = await vscode.workspace.openTextDocument(uri);
      const editor = await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
      const lineIndex = Math.max(0, line - 1);
      const range = editor.document.lineAt(lineIndex).range;
      editor.selection = new vscode.Selection(range.start, range.end);
      editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
    } catch {}
  }

  private getWebviewContent(): string {
    const critical = this.comments.filter((c) => c.severity === "critical");
    const warning = this.comments.filter((c) => c.severity === "warning");
    const suggestion = this.comments.filter((c) => c.severity === "suggestion");
    const info = this.comments.filter((c) => c.severity === "info");
    const hasComments = this.comments.length > 0;
    const fileName = this.filePath.split(/[\\/]/).pop() ?? this.filePath;

    const renderGroup = (list: ReviewComment[], color: string, label: string): string => {
      if (list.length === 0) { return ""; }
      const cards = list.map((c) => `
        <div class="card" onclick="goTo(${JSON.stringify(this.filePath)}, ${c.line})">
          <div class="card-top">
            <span class="badge" style="background:${color}20;color:${color};border:1px solid ${color}40">
              ${escapeHtml(c.severity.toUpperCase())}
            </span>
            <span class="cat">${escapeHtml(c.category)}</span>
            <span class="linenum">Line ${c.line}</span>
            <span class="pct">${Math.round(c.confidence * 100)}%</span>
          </div>
          <div class="body">${escapeHtml(c.body)}</div>
          <div class="bar"><div class="bar-fill" style="width:${Math.round(c.confidence * 100)}%;background:${color}"></div></div>
        </div>`).join("");

      return `
        <div class="section">
          <div class="section-title" style="color:${color}">${label}  <span class="count">${list.length}</span></div>
          ${cards}
        </div>`;
    };

    const emptyHtml = `
      <div class="empty">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">${this.summary ? "No issues found!" : "No review yet"}</div>
        <div class="empty-sub">${this.summary ? escapeHtml(this.summary) : "Open a file and run<br><strong>AI Reviewer: Review Current File</strong>"}</div>
      </div>`;

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    padding: 16px;
    background: var(--vscode-editor-background);
    color: var(--vscode-editor-foreground);
    font-family: var(--vscode-font-family);
    font-size: 13px;
  }
  .header { margin-bottom: 14px; }
  .title { font-size: 16px; font-weight: 700; margin-bottom: 5px; }
  .filename {
    display: inline-block; font-family: monospace; font-size: 12px;
    color: var(--vscode-descriptionForeground);
    background: var(--vscode-textBlockQuote-background);
    padding: 2px 8px; border-radius: 4px;
  }
  .chips { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
  .chip { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 999px; }
  .chip.r { background: rgba(248,81,73,.15); color: #f85149; }
  .chip.y { background: rgba(210,153,34,.15); color: #d29922; }
  .chip.b { background: rgba(88,166,255,.15); color: #58a6ff; }
  .chip.p { background: rgba(188,140,255,.15); color: #bc8cff; }
  .model {
    display: inline-block; font-size: 11px; font-family: monospace;
    background: var(--vscode-textBlockQuote-background);
    color: var(--vscode-descriptionForeground);
    padding: 3px 8px; border-radius: 4px; margin-bottom: 12px;
  }
  .summary-label {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .5px; color: var(--vscode-descriptionForeground); margin-bottom: 5px;
  }
  .summary-box {
    padding: 10px 12px; border-left: 3px solid #58a6ff; border-radius: 4px;
    background: var(--vscode-textBlockQuote-background);
    line-height: 1.6; margin-bottom: 16px; font-size: 12px;
  }
  .section { margin-bottom: 16px; }
  .section-title {
    font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .5px; padding-bottom: 6px; margin-bottom: 8px;
    border-bottom: 1px solid var(--vscode-panel-border);
    display: flex; align-items: center; gap: 6px;
  }
  .count {
    font-size: 11px; background: var(--vscode-textBlockQuote-background);
    padding: 1px 7px; border-radius: 999px;
    color: var(--vscode-descriptionForeground);
  }
  .card {
    padding: 10px; margin-bottom: 8px;
    border: 1px solid var(--vscode-panel-border); border-radius: 6px;
    background: var(--vscode-textBlockQuote-background);
    cursor: pointer; transition: border-color .15s;
  }
  .card:hover { border-color: #58a6ff; }
  .card-top {
    display: flex; align-items: center; gap: 6px;
    flex-wrap: wrap; margin-bottom: 6px;
  }
  .badge { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 999px; }
  .cat {
    font-size: 10px; background: var(--vscode-editor-background);
    color: var(--vscode-descriptionForeground);
    padding: 2px 6px; border-radius: 4px;
  }
  .linenum {
    font-size: 10px; font-family: monospace; color: #58a6ff;
    background: rgba(88,166,255,.1); padding: 2px 6px; border-radius: 4px;
  }
  .pct { font-size: 10px; color: var(--vscode-descriptionForeground); margin-left: auto; }
  .body { font-size: 12px; line-height: 1.5; margin-bottom: 6px; }
  .bar { height: 2px; background: var(--vscode-panel-border); border-radius: 1px; }
  .bar-fill { height: 100%; border-radius: 1px; }
  .empty { text-align: center; padding: 48px 16px; color: var(--vscode-descriptionForeground); }
  .empty-icon { font-size: 36px; margin-bottom: 12px; }
  .empty-title { font-size: 14px; font-weight: 600; color: var(--vscode-editor-foreground); margin-bottom: 8px; }
  .empty-sub { line-height: 1.7; }
</style>
</head>
<body>
  <div class="header">
    <div class="title">🛡️ AI Code Review</div>
    ${this.filePath ? `<span class="filename">${escapeHtml(fileName)}</span>` : ""}
  </div>

  ${hasComments ? `
    <div class="chips">
      ${critical.length > 0 ? `<span class="chip r">🔴 ${critical.length} Critical</span>` : ""}
      ${warning.length > 0 ? `<span class="chip y">🟡 ${warning.length} Warning</span>` : ""}
      ${suggestion.length > 0 ? `<span class="chip b">🔵 ${suggestion.length} Suggestion</span>` : ""}
      ${info.length > 0 ? `<span class="chip p">⚪ ${info.length} Info</span>` : ""}
    </div>
    ${this.modelUsed ? `<span class="model">🤖 ${escapeHtml(this.modelUsed)}</span>` : ""}
    ${this.summary ? `<div class="summary-label">Summary</div><div class="summary-box">${escapeHtml(this.summary)}</div>` : ""}
    ${renderGroup(critical, "#f85149", "Critical Issues")}
    ${renderGroup(warning, "#d29922", "Warnings")}
    ${renderGroup(suggestion, "#58a6ff", "Suggestions")}
    ${renderGroup(info, "#bc8cff", "Info")}
  ` : emptyHtml}

  <script>
    const vscode = acquireVsCodeApi();
    function goTo(filePath, line) {
      vscode.postMessage({ command: "goToLine", filePath, line });
    }
  </script>
</body>
</html>`;
  }
}