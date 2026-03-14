import * as vscode from "vscode";
import { ApiClient } from "./apiClient";
import { applyDiagnostics, ReviewComment } from "./diagnostics";
import { CommentsTreeProvider } from "./reviewPanel";

async function reviewCurrentFile(
  apiClient: ApiClient,
  diagnostics: vscode.DiagnosticCollection,
  commentsProvider: CommentsTreeProvider
): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active file open.");
    return;
  }

  const document = editor.document;
  const filePath = document.fileName;
  const content = document.getText();
  const languageId = document.languageId;

  const healthy = await apiClient.checkHealth();
  if (!healthy) {
    vscode.window.showErrorMessage(
      "AI Reviewer backend is not running.\nStart it with: uvicorn main:app --reload"
    );
    return;
  }

  commentsProvider.showPanel();

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "AI Reviewer: Analyzing code...",
      cancellable: false,
    },
    async () => {
      try {
        const result = await apiClient.reviewFile(filePath, content, languageId);

        const comments: ReviewComment[] = (result.comments || []).map((c) => ({
          ...c,
          line: c.line || c.position || 1,
        }));

        applyDiagnostics(diagnostics, document.uri, comments);
        commentsProvider.setComments(
          filePath,
          comments,
          result.summary || "",
          result.model_used || "unknown"
        );

        if (comments.length === 0) {
          vscode.window.showInformationMessage("AI Reviewer: ✅ LGTM — No issues found.");
        } else {
          vscode.window.showInformationMessage(
            `AI Reviewer: Found ${comments.length} issue${comments.length !== 1 ? "s" : ""}. Check the review panel.`
          );
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`AI Reviewer failed: ${message}`);
      }
    }
  );
}

export function activate(context: vscode.ExtensionContext): void {
  const apiClient = new ApiClient(context);
  const diagnostics = vscode.languages.createDiagnosticCollection("ai-reviewer");
  const commentsProvider = new CommentsTreeProvider();

  commentsProvider.setContext(context);

  context.subscriptions.push(
    diagnostics,

    vscode.window.registerTreeDataProvider("ai-reviewer.commentsView", commentsProvider),

    vscode.window.registerUriHandler({
      handleUri(uri: vscode.Uri) {
        const token = new URLSearchParams(uri.query).get("token");
        if (token) {
          void apiClient.setToken(token).then(() => {
            vscode.window.showInformationMessage("AI Reviewer: Signed in successfully.");
          });
        }
      },
    }),

    vscode.commands.registerCommand(
      "ai-reviewer.goToLine",
      async (filePath: string, line: number) => {
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
    ),

    vscode.commands.registerCommand("ai-reviewer.reviewFile", () =>
      reviewCurrentFile(apiClient, diagnostics, commentsProvider)
    ),
    vscode.commands.registerCommand("ai-reviewer.signIn", () => apiClient.signIn()),
    vscode.commands.registerCommand("ai-reviewer.signOut", () => apiClient.signOut()),
    vscode.commands.registerCommand("ai-reviewer.clearComments", () => {
      diagnostics.clear();
      commentsProvider.clear();
      vscode.window.showInformationMessage("AI Reviewer: Comments cleared.");
    }),
    vscode.commands.registerCommand("ai-reviewer.showPanel", () =>
      commentsProvider.showPanel()
    )
  );

  vscode.window.showInformationMessage(
    "AI Reviewer is active. Open a file and run 'AI Reviewer: Review Current File'."
  );
}

export function deactivate(): void {}