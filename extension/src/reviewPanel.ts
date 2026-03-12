import * as vscode from "vscode";
import { ReviewComment } from "./diagnostics";

const SEVERITY_ICONS: Record<string, string> = {
  critical: "$(error)",
  warning: "$(warning)",
  suggestion: "$(info)",
  info: "$(info)",
};

export class CommentItem extends vscode.TreeItem {
  constructor(
    public readonly comment: ReviewComment,
    public readonly filePath: string
  ) {
    const icon = SEVERITY_ICONS[comment.severity] || "$(info)";
    const label = `${icon} [${comment.severity.toUpperCase()}] Line ${comment.line}`;
    super(label, vscode.TreeItemCollapsibleState.None);

    this.description = comment.category;
    this.tooltip = new vscode.MarkdownString(
      `**${comment.severity.toUpperCase()}** — ${comment.category}\n\n${comment.body}\n\n*Confidence: ${Math.round(comment.confidence * 100)}%*`
    );

    // Click to jump to line
    this.command = {
      command: "ai-reviewer.goToLine",
      title: "Go to line",
      arguments: [filePath, comment.line],
    };

    // Icon based on severity
    if (comment.severity === "critical") {
      this.iconPath = new vscode.ThemeIcon(
        "error",
        new vscode.ThemeColor("errorForeground")
      );
    } else if (comment.severity === "warning") {
      this.iconPath = new vscode.ThemeIcon(
        "warning",
        new vscode.ThemeColor("editorWarning.foreground")
      );
    } else {
      this.iconPath = new vscode.ThemeIcon("info");
    }
  }
}

export class FileItem extends vscode.TreeItem {
  public children: CommentItem[] = [];

  constructor(public readonly filePath: string, commentCount: number) {
    super(filePath, vscode.TreeItemCollapsibleState.Expanded);
    this.description = `${commentCount} issue${commentCount !== 1 ? "s" : ""}`;
    this.iconPath = new vscode.ThemeIcon("file-code");
  }
}

export class SummaryItem extends vscode.TreeItem {
  constructor(summary: string, modelUsed: string) {
    super("Summary", vscode.TreeItemCollapsibleState.None);
    this.description = modelUsed;
    this.tooltip = summary;
    this.iconPath = new vscode.ThemeIcon("book");
  }
}

export class CommentsTreeProvider
  implements vscode.TreeDataProvider<vscode.TreeItem>
{
  private _onDidChangeTreeData = new vscode.EventEmitter<
    vscode.TreeItem | undefined | null | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private fileItems: FileItem[] = [];
  private summaryItem: SummaryItem | null = null;
  private emptyMessage = "No reviews yet. Run 'AI Reviewer: Review Current File'";

  setComments(
    filePath: string,
    comments: ReviewComment[],
    summary: string,
    modelUsed: string
  ): void {
    this.fileItems = [];
    this.summaryItem = null;

    if (comments.length === 0) {
      this.emptyMessage = "✓ No issues found!";
      this._onDidChangeTreeData.fire();
      return;
    }

    // Summary item
    this.summaryItem = new SummaryItem(summary, modelUsed);

    // Group by file
    const fileItem = new FileItem(filePath, comments.length);
    fileItem.children = comments.map((c) => new CommentItem(c, filePath));
    this.fileItems = [fileItem];

    this._onDidChangeTreeData.fire();
  }

  clear(): void {
    this.fileItems = [];
    this.summaryItem = null;
    this.emptyMessage = "No reviews yet. Run 'AI Reviewer: Review Current File'";
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): vscode.TreeItem[] {
    if (!element) {
      // Root level
      const roots: vscode.TreeItem[] = [];
      if (this.summaryItem) {
        roots.push(this.summaryItem);
      }
      if (this.fileItems.length > 0) {
        roots.push(...this.fileItems);
      }
      if (roots.length === 0) {
        const empty = new vscode.TreeItem(this.emptyMessage);
        empty.iconPath = new vscode.ThemeIcon("info");
        return [empty];
      }
      return roots;
    }

    // File item children
    if (element instanceof FileItem) {
      return element.children;
    }

    return [];
  }
}
