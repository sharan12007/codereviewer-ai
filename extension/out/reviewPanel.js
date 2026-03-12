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
exports.CommentsTreeProvider = exports.SummaryItem = exports.FileItem = exports.CommentItem = void 0;
const vscode = __importStar(require("vscode"));
const SEVERITY_ICONS = {
    critical: "$(error)",
    warning: "$(warning)",
    suggestion: "$(info)",
    info: "$(info)",
};
class CommentItem extends vscode.TreeItem {
    constructor(comment, filePath) {
        const icon = SEVERITY_ICONS[comment.severity] || "$(info)";
        const label = `${icon} [${comment.severity.toUpperCase()}] Line ${comment.line}`;
        super(label, vscode.TreeItemCollapsibleState.None);
        this.comment = comment;
        this.filePath = filePath;
        this.description = comment.category;
        this.tooltip = new vscode.MarkdownString(`**${comment.severity.toUpperCase()}** — ${comment.category}\n\n${comment.body}\n\n*Confidence: ${Math.round(comment.confidence * 100)}%*`);
        // Click to jump to line
        this.command = {
            command: "ai-reviewer.goToLine",
            title: "Go to line",
            arguments: [filePath, comment.line],
        };
        // Icon based on severity
        if (comment.severity === "critical") {
            this.iconPath = new vscode.ThemeIcon("error", new vscode.ThemeColor("errorForeground"));
        }
        else if (comment.severity === "warning") {
            this.iconPath = new vscode.ThemeIcon("warning", new vscode.ThemeColor("editorWarning.foreground"));
        }
        else {
            this.iconPath = new vscode.ThemeIcon("info");
        }
    }
}
exports.CommentItem = CommentItem;
class FileItem extends vscode.TreeItem {
    constructor(filePath, commentCount) {
        super(filePath, vscode.TreeItemCollapsibleState.Expanded);
        this.filePath = filePath;
        this.children = [];
        this.description = `${commentCount} issue${commentCount !== 1 ? "s" : ""}`;
        this.iconPath = new vscode.ThemeIcon("file-code");
    }
}
exports.FileItem = FileItem;
class SummaryItem extends vscode.TreeItem {
    constructor(summary, modelUsed) {
        super("Summary", vscode.TreeItemCollapsibleState.None);
        this.description = modelUsed;
        this.tooltip = summary;
        this.iconPath = new vscode.ThemeIcon("book");
    }
}
exports.SummaryItem = SummaryItem;
class CommentsTreeProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.fileItems = [];
        this.summaryItem = null;
        this.emptyMessage = "No reviews yet. Run 'AI Reviewer: Review Current File'";
    }
    setComments(filePath, comments, summary, modelUsed) {
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
    clear() {
        this.fileItems = [];
        this.summaryItem = null;
        this.emptyMessage = "No reviews yet. Run 'AI Reviewer: Review Current File'";
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            // Root level
            const roots = [];
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
exports.CommentsTreeProvider = CommentsTreeProvider;
//# sourceMappingURL=reviewPanel.js.map