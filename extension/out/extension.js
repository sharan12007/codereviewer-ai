"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const apiClient_1 = require("./apiClient");
const diagnostics_1 = require("./diagnostics");
const reviewPanel_1 = require("./reviewPanel");
async function reviewCurrentFile(apiClient, diagnostics, commentsProvider) {
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
        vscode.window.showErrorMessage("AI Reviewer backend is not running.\nStart it with: uvicorn main:app --reload");
        return;
    }
    commentsProvider.showPanel();
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "AI Reviewer: Analyzing code...",
        cancellable: false,
    }, async () => {
        try {
            const result = await apiClient.reviewFile(filePath, content, languageId);
            const comments = (result.comments || []).map((c) => ({
                ...c,
                line: c.line || c.position || 1,
            }));
            (0, diagnostics_1.applyDiagnostics)(diagnostics, document.uri, comments);
            commentsProvider.setComments(filePath, comments, result.summary || "", result.model_used || "unknown");
            if (comments.length === 0) {
                vscode.window.showInformationMessage("AI Reviewer: ✅ LGTM — No issues found.");
            }
            else {
                vscode.window.showInformationMessage(`AI Reviewer: Found ${comments.length} issue${comments.length !== 1 ? "s" : ""}. Check the review panel.`);
            }
        }
        catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            vscode.window.showErrorMessage(`AI Reviewer failed: ${message}`);
        }
    });
}
function activate(context) {
    const apiClient = new apiClient_1.ApiClient(context);
    const diagnostics = vscode.languages.createDiagnosticCollection("ai-reviewer");
    const commentsProvider = new reviewPanel_1.CommentsTreeProvider();
    commentsProvider.setContext(context);
    context.subscriptions.push(diagnostics, vscode.window.registerTreeDataProvider("ai-reviewer.commentsView", commentsProvider), vscode.window.registerUriHandler({
        handleUri(uri) {
            const token = new URLSearchParams(uri.query).get("token");
            if (token) {
                void apiClient.setToken(token).then(() => {
                    vscode.window.showInformationMessage("AI Reviewer: Signed in successfully.");
                });
            }
        },
    }), vscode.commands.registerCommand("ai-reviewer.goToLine", async (filePath, line) => {
        try {
            const uri = vscode.Uri.file(filePath);
            const doc = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
            const lineIndex = Math.max(0, line - 1);
            const range = editor.document.lineAt(lineIndex).range;
            editor.selection = new vscode.Selection(range.start, range.end);
            editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
        }
        catch { }
    }), vscode.commands.registerCommand("ai-reviewer.reviewFile", () => reviewCurrentFile(apiClient, diagnostics, commentsProvider)), vscode.commands.registerCommand("ai-reviewer.signIn", () => apiClient.signIn()), vscode.commands.registerCommand("ai-reviewer.signOut", () => apiClient.signOut()), vscode.commands.registerCommand("ai-reviewer.clearComments", () => {
        diagnostics.clear();
        commentsProvider.clear();
        vscode.window.showInformationMessage("AI Reviewer: Comments cleared.");
    }), vscode.commands.registerCommand("ai-reviewer.showPanel", () => commentsProvider.showPanel()));
    vscode.window.showInformationMessage("AI Reviewer is active. Open a file and run 'AI Reviewer: Review Current File'.");
}
function deactivate() { }
//# sourceMappingURL=extension.js.map