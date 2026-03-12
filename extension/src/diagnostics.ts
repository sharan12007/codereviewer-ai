import * as vscode from "vscode";

export interface ReviewComment {
  line: number;
  end_line?: number;
  severity: string;
  category: string;
  confidence: number;
  body: string;
  position?: number;
  file_path?: string;
}

export function applyDiagnostics(
  collection: vscode.DiagnosticCollection,
  uri: vscode.Uri,
  comments: ReviewComment[]
): void {
  const diagnostics: vscode.Diagnostic[] = comments.map((c) => {
    // VS Code lines are 0-indexed. LLM returns 1-indexed.
    const line = Math.max(0, c.line - 1);
    const endLine = c.end_line ? Math.max(0, c.end_line - 1) : line;
    const range = new vscode.Range(line, 0, endLine, 999);

    const severity =
      c.severity === "critical" || c.severity === "warning"
        ? vscode.DiagnosticSeverity.Warning
        : vscode.DiagnosticSeverity.Information;

    const d = new vscode.Diagnostic(range, c.body, severity);
    d.source = "AI Reviewer";
    d.code = c.category;
    return d;
  });

  collection.set(uri, diagnostics);
}

export function clearDiagnostics(collection: vscode.DiagnosticCollection): void {
  collection.clear();
}