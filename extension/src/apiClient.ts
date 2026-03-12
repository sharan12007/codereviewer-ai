import * as vscode from "vscode";
import axios from "axios";
import { ReviewComment } from "./diagnostics";

export interface FileReviewResponse {
  review_id: number | null;
  comments: ReviewComment[];
  summary: string;
  model_used: string;
  tokens_used: number;
}

export class ApiClient {
  private readonly TOKEN_KEY = "ai-reviewer.jwt";

  constructor(private context: vscode.ExtensionContext) {}

  private getServerUrl(): string {
    const config = vscode.workspace.getConfiguration("aiReviewer");
    return config.get<string>("serverUrl", "http://localhost:8000");
  }

  async getToken(): Promise<string | undefined> {
    return this.context.secrets.get(this.TOKEN_KEY);
  }

  async setToken(token: string): Promise<void> {
    await this.context.secrets.store(this.TOKEN_KEY, token);
  }

  async deleteToken(): Promise<void> {
    await this.context.secrets.delete(this.TOKEN_KEY);
  }

  async signIn(): Promise<void> {
    try {
      const serverUrl = this.getServerUrl();
      const redirectUri = "vscode://ai-reviewer/callback";
      const resp = await axios.post(
        `${serverUrl}/auth/github?redirect_uri=${encodeURIComponent(redirectUri)}`
      );
      const url: string = resp.data.url;
      await vscode.env.openExternal(vscode.Uri.parse(url));
    } catch (err) {
      vscode.window.showErrorMessage(`Sign in failed: ${err}`);
    }
  }

  async signOut(): Promise<void> {
    await this.deleteToken();
    vscode.window.showInformationMessage("Signed out of AI Reviewer");
  }

  async reviewFile(
    filePath: string,
    content: string,
    language?: string
  ): Promise<FileReviewResponse> {
    const serverUrl = this.getServerUrl();
    const token = await this.getToken();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const resp = await axios.post(
      `${serverUrl}/review/file`,
      {
        file_path: filePath,
        content: content,
        language: language,
        context: "code review",
      },
      { headers }
    );

    return resp.data;
  }

  async getReviews(): Promise<unknown[]> {
    const serverUrl = this.getServerUrl();
    const token = await this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const resp = await axios.get(`${serverUrl}/reviews`, { headers });
    return resp.data;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const serverUrl = this.getServerUrl();
      const resp = await axios.get(`${serverUrl}/health`);
      return resp.data.status === "ok";
    } catch {
      return false;
    }
  }
}