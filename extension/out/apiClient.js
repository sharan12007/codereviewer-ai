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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApiClient = void 0;
const vscode = __importStar(require("vscode"));
const axios_1 = __importDefault(require("axios"));
class ApiClient {
    constructor(context) {
        this.context = context;
        this.TOKEN_KEY = "ai-reviewer.jwt";
    }
    getServerUrl() {
        const config = vscode.workspace.getConfiguration("aiReviewer");
        return config.get("serverUrl", "http://localhost:8000");
    }
    async getToken() {
        return this.context.secrets.get(this.TOKEN_KEY);
    }
    async setToken(token) {
        await this.context.secrets.store(this.TOKEN_KEY, token);
    }
    async deleteToken() {
        await this.context.secrets.delete(this.TOKEN_KEY);
    }
    async signIn() {
        try {
            const serverUrl = this.getServerUrl();
            const redirectUri = "vscode://ai-reviewer/callback";
            const resp = await axios_1.default.post(`${serverUrl}/auth/github?redirect_uri=${encodeURIComponent(redirectUri)}`);
            const url = resp.data.url;
            await vscode.env.openExternal(vscode.Uri.parse(url));
        }
        catch (err) {
            vscode.window.showErrorMessage(`Sign in failed: ${err}`);
        }
    }
    async signOut() {
        await this.deleteToken();
        vscode.window.showInformationMessage("Signed out of AI Reviewer");
    }
    async reviewFile(filePath, content, language) {
        const serverUrl = this.getServerUrl();
        const token = await this.getToken();
        const headers = {
            "Content-Type": "application/json",
        };
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        const resp = await axios_1.default.post(`${serverUrl}/review/file`, {
            file_path: filePath,
            content: content,
            language: language,
            context: "code review",
        }, { headers });
        return resp.data;
    }
    async getAutofix(code, issue, category, language, filePath) {
        const serverUrl = this.getServerUrl();
        const resp = await axios_1.default.post(`${serverUrl}/autofix`, {
            code,
            issue,
            category,
            language,
            file_path: filePath,
        });
        return resp.data;
    }
    async getReviews() {
        const serverUrl = this.getServerUrl();
        const token = await this.getToken();
        const headers = {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        const resp = await axios_1.default.get(`${serverUrl}/reviews`, { headers });
        return resp.data;
    }
    async checkHealth() {
        try {
            const serverUrl = this.getServerUrl();
            const resp = await axios_1.default.get(`${serverUrl}/health`);
            return resp.data.status === "ok";
        }
        catch {
            return false;
        }
    }
}
exports.ApiClient = ApiClient;
//# sourceMappingURL=apiClient.js.map