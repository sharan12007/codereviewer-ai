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
exports.applyDiagnostics = applyDiagnostics;
exports.clearDiagnostics = clearDiagnostics;
const vscode = __importStar(require("vscode"));
function applyDiagnostics(collection, uri, comments) {
    const diagnostics = comments.map((c) => {
        // VS Code lines are 0-indexed. LLM returns 1-indexed.
        const line = Math.max(0, c.line - 1);
        const endLine = c.end_line ? Math.max(0, c.end_line - 1) : line;
        const range = new vscode.Range(line, 0, endLine, 999);
        const severity = c.severity === "critical" || c.severity === "warning"
            ? vscode.DiagnosticSeverity.Warning
            : vscode.DiagnosticSeverity.Information;
        const d = new vscode.Diagnostic(range, c.body, severity);
        d.source = "AI Reviewer";
        d.code = c.category;
        return d;
    });
    collection.set(uri, diagnostics);
}
function clearDiagnostics(collection) {
    collection.clear();
}
//# sourceMappingURL=diagnostics.js.map