import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import Brand from "./Brand";
import { api } from "./api";
import type { SessionState } from "./types";
import "./accounts.css";

export default function AuthScreen({
  mode,
  loading = false,
  message = "",
  onModeChange,
  onAuthenticated,
  onDemo,
  onHome,
}: {
  mode: "login" | "register" | "recover";
  loading?: boolean;
  message?: string;
  onModeChange: (mode: "login" | "register" | "recover") => void;
  onAuthenticated: (session: SessionState) => void;
  onDemo: () => void;
  onHome: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const register = mode === "register";
  const recovering = mode === "recover";
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const fields = new FormData(event.currentTarget);
    const body = {
      username: String(fields.get("username") || ""),
      password: String(fields.get("password") || ""),
    };
    try {
      const session = await api<SessionState>(
        register
          ? "/auth/signup"
          : recovering
            ? "/auth/recover"
            : "/auth/login",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(
            recovering
              ? {
                  username: body.username,
                  recovery_code: fields.get("recovery_code"),
                  new_password: body.password,
                }
              : register
                ? {
                    ...body,
                    display_name: fields.get("display_name"),
                    organisation_name: fields.get("organisation_name"),
                  }
                : body,
          ),
        },
      );
      onAuthenticated(session);
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <header className="auth-header">
        <Brand onNavigate={onHome} />
        <button className="text-button" onClick={onDemo}>
          <ArrowLeft size={15} />
          Explore the demo
        </button>
      </header>
      <main className="auth-layout">
        <section className="auth-story">
          <span className="auth-story-icon">
            <ShieldCheck size={27} strokeWidth={1.4} />
          </span>
          <h1 id="auth-title" tabIndex={-1}>
            {register
              ? "A workspace of your own."
              : recovering
                ? "Find your way back."
                : "Your records. Your workspace."}
          </h1>
          <p>
            {register
              ? "Create your account and a separate space for your organisation’s fictional aircraft reports."
              : recovering
                ? "Use one of your saved recovery codes to choose a new password and return to your organisation."
                : "Pick up where you left off. Your confirmed records and import history stay with your organisation."}
          </p>
          <div className="auth-promise">
            <LockKeyhole size={18} />
            <div>
              <strong>Separate by organisation.</strong>
              <p>
                Account workspaces are kept apart from each other and from the
                public demo.
              </p>
            </div>
          </div>
          <div className="auth-story-art" aria-hidden="true" />
        </section>
        <section className="auth-panel" aria-labelledby="auth-form-title">
          <h2 id="auth-form-title">
            {loading
              ? "Checking your session…"
              : register
                ? "Create an account"
                : recovering
                  ? "Recover your account"
                  : "Welcome back"}
          </h2>
          <p className="auth-intro">
            {register
              ? "Your organisation starts with an empty register."
              : recovering
                ? "You need a recovery code saved from Account settings."
                : "Sign in with your Sampati username."}
          </p>
          {(error || message) && (
            <div className="message error" role="alert">
              {error || message}
            </div>
          )}
          <form key={mode} onSubmit={submit}>
            {register && (
              <>
                <label>
                  Your name
                  <input
                    name="display_name"
                    autoComplete="name"
                    required
                    minLength={2}
                    maxLength={80}
                    placeholder="How should we address you?"
                    disabled={busy || loading}
                  />
                </label>
                <label>
                  Organisation name
                  <input
                    name="organisation_name"
                    autoComplete="organization"
                    required
                    minLength={2}
                    maxLength={100}
                    placeholder="For example, Cedar Civil Transport"
                    disabled={busy || loading}
                  />
                </label>
              </>
            )}
            <div className="auth-input-group">
              <label htmlFor="account-username">Username</label>
              <input
                id="account-username"
                aria-describedby={register ? "username-help" : undefined}
                name="username"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                required
                minLength={3}
                maxLength={32}
                pattern={"[A-Za-z0-9][A-Za-z0-9._\\-]{2,31}"}
                title="3–32 letters, numbers, dots, underscores or hyphens."
                placeholder="Your username"
                disabled={busy || loading}
              />
              {register && (
                <small id="username-help">
                  3–32 letters, numbers, dots, underscores or hyphens.
                </small>
              )}
            </div>
            {recovering && (
              <label>
                Recovery code
                <input
                  name="recovery_code"
                  required
                  minLength={12}
                  maxLength={100}
                  autoComplete="off"
                  placeholder="Paste an unused recovery code"
                  disabled={busy || loading}
                />
              </label>
            )}
            <div className="auth-input-group">
              <label htmlFor="account-password">
                {recovering ? "New password" : "Password"}
              </label>
              <span className="password-field">
                <input
                  id="account-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete={
                    register || recovering ? "new-password" : "current-password"
                  }
                  required
                  minLength={register || recovering ? 12 : 1}
                  maxLength={128}
                  placeholder={
                    register || recovering
                      ? "Choose at least 12 characters"
                      : "Your password"
                  }
                  disabled={busy || loading}
                />
                <button
                  type="button"
                  className="icon-button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </div>
            <button
              className="button primary auth-submit"
              disabled={busy || loading}
              type="submit"
            >
              {busy
                ? register
                  ? "Creating your workspace…"
                  : recovering
                    ? "Recovering account…"
                    : "Signing in…"
                : register
                  ? "Create account & workspace"
                  : recovering
                    ? "Reset password & sign in"
                    : "Sign in"}
              {!busy && <ArrowRight size={17} />}
            </button>
          </form>
          <p className="auth-alternative">
            {register ? "Already have an account?" : "New to Sampati?"}
            <button
              className="text-button"
              disabled={busy}
              onClick={() => {
                setError("");
                onModeChange(register ? "login" : "register");
              }}
            >
              {register ? "Sign in" : "Create an account"}
            </button>
          </p>
          {!register && !recovering && (
            <button
              className="text-button"
              disabled={busy}
              onClick={() => onModeChange("recover")}
            >
              Use a recovery code
            </button>
          )}
          <p className="auth-local-note">
            Local learning prototype · Use fictional aircraft records.
          </p>
        </section>
      </main>
      <footer className="auth-footer">
        SAMPATI · सम्पाति<span>Source first. Every change, traceable.</span>
      </footer>
    </div>
  );
}
