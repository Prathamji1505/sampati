import { useEffect, useState } from "react";
import {
  ArrowDownToLine,
  Check,
  Copy,
  KeyRound,
  LockKeyhole,
  Plus,
  RefreshCw,
  ShieldCheck,
  Upload,
  Users,
} from "lucide-react";
import { api, downloadRegister } from "./api";
import type {
  Aircraft,
  Preview,
  SessionState,
  Workspace,
  WorkspaceScope,
} from "./types";
import "./workspace-tools.css";

type Overview = {
  total: number;
  statuses: Record<string, number>;
  freshness: Record<string, number>;
  sources: {
    name: string;
    count: number;
    needs_review: number;
    last_report: string;
  }[];
  attention: { aircraft_id: string; reason: string }[];
  summary: string[];
  summary_method: string;
  generated_at: string;
};
type Source = {
  id: string;
  name: string;
  enabled: boolean;
  created_at: string;
  last_received_at: string | null;
};
type Incoming = {
  id: string;
  source_name: string;
  filename: string;
  state: string;
  row_count: number;
  received_at: string;
  import_id: string | null;
};
type Sources = { sources: Source[]; incoming: Incoming[] };
type Team = {
  members: {
    user_id: string;
    username: string;
    display_name: string;
    role: string;
  }[];
  invitations: {
    id: string;
    username: string;
    role: string;
    expires_at: string;
    state: string;
  }[];
};
type Props = {
  view: "overview" | "sources" | "team" | "account";
  scope: WorkspaceScope;
  session: SessionState | null;
  workspace: Workspace | null;
  onSessionUpdated: (session: SessionState) => void;
  onSignIn: () => void;
  onRefresh: () => void;
  onPreview: (preview: Preview) => void;
  onInspect: (aircraft: Aircraft) => void;
};
const when = (value: string | null) =>
  value ? new Date(value).toLocaleString() : "Waiting for the first file";
const json = (body: unknown) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export default function WorkspaceTools(props: Props) {
  const {
    view,
    scope,
    session,
    workspace,
    onSessionUpdated,
    onSignIn,
    onPreview,
    onInspect,
  } = props;
  const [overview, setOverview] = useState<Overview | null>(null);
  const [sources, setSources] = useState<Sources | null>(null);
  const [team, setTeam] = useState<Team | null>(null);
  const [security, setSecurity] = useState<{
    recovery_codes_remaining: number;
    active_sessions: number;
  } | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [oneTimeKey, setOneTimeKey] = useState<{
    token: string;
    ingest_path: string;
  } | null>(null);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [codes, setCodes] = useState<string[]>([]);
  const isOwner = session?.workspace?.role === "owner";
  const canEdit = session?.workspace?.role !== "viewer";
  const privatePage = view === "sources" || view === "team";
  const unavailable =
    (privatePage && scope === "demo") || (view === "account" && !session?.user);

  async function load() {
    if (unavailable) {
      setLoading(false);
      return;
    }
    try {
      if (view === "overview") setOverview(await api<Overview>("/overview"));
      else if (view === "sources") setSources(await api<Sources>("/sources"));
      else if (view === "team") setTeam(await api<Team>("/team"));
      else setSecurity(await api("/auth/security"));
      setError("");
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, [view, scope, workspace?.server_time]);

  async function action(work: () => Promise<unknown>, message = "") {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
      await load();
      if (message) setNotice(message);
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function copy(value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setNotice("Copied. Keep this value somewhere private.");
    } catch {
      setError(
        "Copy is unavailable in this browser. Select and copy the value manually.",
      );
    }
  }
  async function review(id: string) {
    setBusy(true);
    setError("");
    try {
      onPreview(
        await api<Preview>(`/sources/inbox/${id}/preview`, {
          method: "POST",
          ...json({}),
        }),
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (unavailable)
    return (
      <section className="tools-panel tools-empty">
        <LockKeyhole size={30} strokeWidth={1.4} />
        <h2>
          {view === "account"
            ? "Keep your account in your hands."
            : "A private workspace for your organisation."}
        </h2>
        <p>
          Sign in and select your organisation to{" "}
          {view === "team"
            ? "invite teammates and manage access"
            : view === "sources"
              ? "connect datasets and review incoming files"
              : "manage your password and recovery codes"}
          .
        </p>
        <button className="button primary" onClick={onSignIn}>
          Sign in or create an account
        </button>
      </section>
    );

  return (
    <div className="workspace-tools">
      {error && (
        <div className="message error" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="message success" role="status">
          <Check size={16} />
          {notice}
        </div>
      )}
      <div className="tools-toolbar">
        <span>
          {loading
            ? "Loading workspace details…"
            : "Based on this workspace only"}
        </span>
        <button
          className="button secondary"
          onClick={() => void load()}
          disabled={busy}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>
      {view === "overview" && overview && (
        <>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>Reported status</h2>
              <span>
                {overview.total} accepted{" "}
                {overview.total === 1 ? "record" : "records"}
              </span>
            </div>
            <div className="status-report">
              {(
                [
                  ["available", "Reported available"],
                  ["unavailable", "Unavailable"],
                  ["unknown", "Unknown"],
                ] as const
              ).map(([key, label]) => (
                <div className="report-bar-row" key={key}>
                  <span>{label}</span>
                  <div className="report-bar-track">
                    <span
                      className={`report-bar-fill report-${key}`}
                      style={{
                        width: `${overview.total ? ((overview.statuses[key] || 0) / overview.total) * 100 : 0}%`,
                      }}
                    />
                  </div>
                  <strong>{overview.statuses[key] || 0}</strong>
                </div>
              ))}
            </div>
            <p className="tools-muted">
              Status is reported by the source. It does not establish
              airworthiness.
            </p>
          </section>
          <div className="tools-two-columns">
            <section className="tools-panel">
              <h2>What the records tell us</h2>
              <ul className="fact-list">
                {overview.summary.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <p className="tools-muted">{overview.summary_method}</p>
            </section>
            <section className="tools-panel">
              <h2>Needs attention</h2>
              {overview.attention.length ? (
                <ul className="attention-list">
                  {overview.attention.map((item) => (
                    <li key={item.aircraft_id}>
                      <button
                        className="text-button"
                        onClick={() => {
                          const found = workspace?.aircraft.find(
                            (row) => row.aircraft_id === item.aircraft_id,
                          );
                          if (found) onInspect(found);
                        }}
                      >
                        {item.aircraft_id}
                      </button>
                      <span>{item.reason}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="tools-muted">
                  No stale, future-dated or incomplete records in this view.
                </p>
              )}
            </section>
          </div>
          <section className="tools-panel">
            <h2>Source coverage</h2>
            <div className="table-scroll">
              <table className="tools-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Records</th>
                    <th>Need review</th>
                    <th>Latest source report</th>
                  </tr>
                </thead>
                <tbody>
                  {overview.sources.map((source) => (
                    <tr key={source.name}>
                      <td>{source.name}</td>
                      <td>{source.count}</td>
                      <td>{source.needs_review}</td>
                      <td>{when(source.last_report)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!overview.sources.length && (
              <p className="tools-muted">
                Sources appear after an import is confirmed.
              </p>
            )}
            <div className="tools-actions">
              <button
                className="button secondary"
                onClick={() => void action(() => downloadRegister("xlsx"))}
              >
                <ArrowDownToLine size={15} />
                Export Excel
              </button>
              <button
                className="button secondary"
                onClick={() => void action(() => downloadRegister("json"))}
              >
                Export JSON
              </button>
            </div>
          </section>
        </>
      )}

      {view === "sources" && (
        <>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>Connected sources</h2>
              <span>Files arrive in the review inbox</span>
            </div>
            {isOwner && (
              <form
                className="tools-inline-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  const form = event.currentTarget;
                  const name = String(new FormData(form).get("name") || "");
                  void action(async () => {
                    setOneTimeKey(
                      await api("/sources", {
                        method: "POST",
                        ...json({ name }),
                      }),
                    );
                    form.reset();
                  }, "Connection created. Save its key before leaving this page.");
                }}
              >
                <label>
                  Source name
                  <input
                    name="name"
                    required
                    minLength={2}
                    maxLength={100}
                    placeholder="For example, Civil fleet register"
                  />
                </label>
                <button className="button primary" disabled={busy}>
                  <Plus size={16} />
                  Create connection
                </button>
              </form>
            )}
            {oneTimeKey && (
              <div className="secret-result">
                <h3>Save this source key now</h3>
                <p>
                  Shown once. This key submits datasets only; it cannot read
                  records or approve imports.
                </p>
                <label className="sr-only" htmlFor="source-key">
                  Source key
                </label>
                <div className="secret-copy">
                  <input
                    id="source-key"
                    type="password"
                    value={oneTimeKey.token}
                    readOnly
                    autoComplete="off"
                  />
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => void copy(oneTimeKey.token)}
                  >
                    <Copy size={14} />
                    Copy key
                  </button>
                </div>
                <code>
                  {window.location.origin}
                  {oneTimeKey.ingest_path}
                </code>
                <button
                  className="text-button"
                  onClick={() => setOneTimeKey(null)}
                >
                  I have saved it
                </button>
              </div>
            )}
            <div className="source-list">
              {sources?.sources.map((source) => (
                <div className="source-row" key={source.id}>
                  <div>
                    <h3>{source.name}</h3>
                    <p>
                      {source.enabled ? "Enabled" : "Disabled"} ·{" "}
                      {when(source.last_received_at)}
                    </p>
                    <small>Source ID: {source.id}</small>
                  </div>
                  <div className="tools-actions">
                    {canEdit && (
                      <button
                        className="button secondary"
                        disabled={busy || !source.enabled}
                        onClick={() =>
                          void action(
                            () =>
                              api(`/sources/${source.id}/simulate`, {
                                method: "POST",
                                ...json({}),
                              }),
                            "A fictional update is waiting in the inbox.",
                          )
                        }
                      >
                        Generate fictional update
                      </button>
                    )}
                    {isOwner && (
                      <>
                        <button
                          className="text-button"
                          disabled={busy}
                          onClick={() =>
                            void action(async () => {
                              setOneTimeKey(
                                await api(`/sources/${source.id}/rotate`, {
                                  method: "POST",
                                  ...json({}),
                                }),
                              );
                            }, "The previous key has been revoked.")
                          }
                        >
                          Rotate key
                        </button>
                        <button
                          className="text-button"
                          disabled={busy}
                          onClick={() =>
                            void action(
                              () =>
                                api(`/sources/${source.id}`, {
                                  method: "PATCH",
                                  ...json({ enabled: !source.enabled }),
                                }),
                              source.enabled
                                ? "Connection disabled."
                                : "Connection enabled.",
                            )
                          }
                        >
                          {source.enabled ? "Disable" : "Enable"}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {sources && !sources.sources.length && (
              <p className="tools-muted">
                No connections yet. An organisation owner can create the first
                one.
              </p>
            )}
            <details className="connector-guide">
              <summary>Connect a changing file on your computer</summary>
              <p>
                The included watcher submits a file when its contents change.
                Set <code>SAMPATI_SOURCE_TOKEN</code> in your terminal, then run
                the script with your source ID and file path:
              </p>
              <pre>
                py scripts/watch_dataset.py --source-id YOUR_SOURCE_ID --file
                "C:\path\fleet.csv"
              </pre>
              <p>
                Keep that terminal running. CSV and .xlsx files use the same
                checks as manual uploads. Incoming files wait for review; they
                never replace accepted records automatically.
              </p>
            </details>
          </section>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>Incoming datasets</h2>
              <span>Review before acceptance</span>
            </div>
            <div className="table-scroll">
              <table className="tools-table">
                <thead>
                  <tr>
                    <th>Dataset</th>
                    <th>Source</th>
                    <th>Records</th>
                    <th>Received</th>
                    <th>State</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sources?.incoming.map((item) => (
                    <tr key={item.id}>
                      <td>{item.filename}</td>
                      <td>{item.source_name}</td>
                      <td>{item.row_count}</td>
                      <td>{when(item.received_at)}</td>
                      <td>
                        <span
                          className={`change-label ${item.state === "accepted" ? "change-new" : item.state === "rejected" ? "change-blocked" : ""}`}
                        >
                          {item.state}
                        </span>
                      </td>
                      <td>
                        {item.state === "pending" && canEdit && (
                          <div className="tools-actions">
                            <button
                              className="button secondary"
                              disabled={busy}
                              onClick={() => void review(item.id)}
                            >
                              Review
                            </button>
                            <button
                              className="text-button"
                              disabled={busy}
                              onClick={() =>
                                void action(
                                  () =>
                                    api(`/sources/inbox/${item.id}/reject`, {
                                      method: "POST",
                                      ...json({}),
                                    }),
                                  "Incoming dataset rejected. Accepted records were not changed.",
                                )
                              }
                            >
                              Reject
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!sources?.incoming.length && (
              <p className="tools-muted">
                No incoming files. Connect a file or generate a fictional update
                to try the workflow.
              </p>
            )}
          </section>
        </>
      )}

      {view === "team" && (
        <>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>Members</h2>
              <span>{session?.workspace?.name}</span>
            </div>
            <div className="table-scroll">
              <table className="tools-table">
                <thead>
                  <tr>
                    <th>Person</th>
                    <th>Username</th>
                    <th>Role</th>
                    <th>Access</th>
                  </tr>
                </thead>
                <tbody>
                  {team?.members.map((member) => (
                    <tr key={member.user_id}>
                      <td>
                        {member.display_name}
                        {member.user_id === session?.user?.id ? " (you)" : ""}
                      </td>
                      <td>@{member.username}</td>
                      <td>
                        {isOwner ? (
                          <select
                            aria-label={`Role for ${member.username}`}
                            value={member.role}
                            disabled={busy}
                            onChange={(event) =>
                              void action(async () => {
                                await api(`/team/members/${member.user_id}`, {
                                  method: "PATCH",
                                  ...json({ role: event.target.value }),
                                });
                                onSessionUpdated(await api("/auth/session"));
                              }, "Role updated.")
                            }
                          >
                            <option value="owner">Owner</option>
                            <option value="editor">Editor</option>
                            <option value="viewer">Viewer</option>
                          </select>
                        ) : (
                          member.role
                        )}
                      </td>
                      <td>
                        {isOwner && (
                          <button
                            className="text-button"
                            disabled={busy}
                            onClick={() =>
                              void action(async () => {
                                await api(`/team/members/${member.user_id}`, {
                                  method: "DELETE",
                                });
                                if (member.user_id === session?.user?.id)
                                  onSessionUpdated(await api("/auth/session"));
                              }, "Membership removed.")
                            }
                          >
                            Remove
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="tools-muted">
              Owners manage access and connections. Editors import and review
              data. Viewers read records and reports. At least one owner must
              remain.
            </p>
          </section>
          {isOwner && (
            <section className="tools-panel">
              <h2>Invite an existing account</h2>
              <p className="tools-muted">
                Ask your teammate to create a Sampati account, then enter their
                username. The code works only for that account and expires in
                three days.
              </p>
              <form
                className="tools-inline-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  const form = event.currentTarget;
                  const data = new FormData(form);
                  void action(async () => {
                    const result = await api<{ token: string }>(
                      "/team/invitations",
                      {
                        method: "POST",
                        ...json({
                          username: data.get("username"),
                          role: data.get("role"),
                        }),
                      },
                    );
                    setInviteCode(result.token);
                    form.reset();
                  }, "Invitation created. Share the code with the intended teammate.");
                }}
              >
                <label>
                  Teammate username
                  <input
                    name="username"
                    required
                    minLength={3}
                    maxLength={32}
                    autoCapitalize="none"
                    placeholder="Their Sampati username"
                  />
                </label>
                <label>
                  Role
                  <select name="role">
                    <option value="viewer">Viewer</option>
                    <option value="editor">Editor</option>
                  </select>
                </label>
                <button className="button primary" disabled={busy}>
                  <Users size={15} />
                  Create invitation
                </button>
              </form>
              {inviteCode && (
                <div className="secret-result">
                  <h3>Invitation code</h3>
                  <div className="secret-copy">
                    <input
                      aria-label="Created invitation code"
                      value={inviteCode}
                      readOnly
                    />
                    <button
                      className="button secondary"
                      onClick={() => void copy(inviteCode)}
                    >
                      <Copy size={14} />
                      Copy
                    </button>
                  </div>
                  <p>
                    The recipient can paste this in Organisation team → Accept
                    an invitation.
                  </p>
                </div>
              )}
              {team?.invitations.length ? (
                <ul className="invitation-list">
                  {team.invitations.map((invite) => (
                    <li key={invite.id}>
                      <span>
                        @{invite.username} · {invite.role} · {invite.state}
                      </span>
                      {invite.state === "pending" && (
                        <button
                          className="text-button"
                          onClick={() =>
                            void action(
                              () =>
                                api(`/team/invitations/${invite.id}`, {
                                  method: "DELETE",
                                }),
                              "Invitation revoked.",
                            )
                          }
                        >
                          Revoke
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              ) : null}
            </section>
          )}
          <section className="tools-panel">
            <h2>Accept an invitation</h2>
            <form
              className="tools-inline-form"
              onSubmit={(event) => {
                event.preventDefault();
                const token = String(
                  new FormData(event.currentTarget).get("token") || "",
                ).trim();
                void action(async () => {
                  onSessionUpdated(
                    await api<SessionState>("/team/invitations/accept", {
                      method: "POST",
                      ...json({ token }),
                    }),
                  );
                }, "You joined the organisation.");
              }}
            >
              <label>
                Invitation code
                <input
                  name="token"
                  required
                  minLength={20}
                  maxLength={200}
                  autoComplete="off"
                  placeholder="Paste the code shared with your account"
                />
              </label>
              <button className="button primary" disabled={busy}>
                Accept invitation
              </button>
            </form>
            <p className="tools-muted">
              Your existing organisation remains available in the workspace
              selector.
            </p>
          </section>
        </>
      )}

      {view === "account" && (
        <>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>{session?.user?.display_name}</h2>
              <span>@{session?.user?.username}</span>
            </div>
            <p className="tools-muted">
              {security?.active_sessions ?? "…"} active sessions ·{" "}
              {security?.recovery_codes_remaining ?? "…"} unused recovery codes
            </p>
            <h3>Change your password</h3>
            <form
              className="tools-form"
              onSubmit={(event) => {
                event.preventDefault();
                const form = event.currentTarget;
                const data = new FormData(form);
                void action(async () => {
                  const next = await api<SessionState>("/auth/password", {
                    method: "POST",
                    ...json({
                      current_password: data.get("current_password"),
                      new_password: data.get("new_password"),
                    }),
                  });
                  onSessionUpdated(next);
                  setCodes([]);
                  form.reset();
                }, "Password changed. Other sessions and old recovery codes were revoked. Generate a new recovery set below.");
              }}
            >
              <label>
                Current password
                <input
                  name="current_password"
                  type="password"
                  autoComplete="current-password"
                  required
                  maxLength={128}
                />
              </label>
              <label>
                New password
                <input
                  name="new_password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={12}
                  maxLength={128}
                />
              </label>
              <button className="button primary" disabled={busy}>
                Change password
              </button>
            </form>
          </section>
          <section className="tools-panel">
            <h2>One-time recovery codes</h2>
            <p className="tools-muted">
              Save these privately before you need them. A code can reset your
              password once, without email. A new set invalidates the previous
              set.
            </p>
            <form
              className="tools-inline-form"
              onSubmit={(event) => {
                event.preventDefault();
                const form = event.currentTarget;
                const current_password = String(
                  new FormData(form).get("current_password") || "",
                );
                void action(async () => {
                  const result = await api<{ codes: string[] }>(
                    "/auth/recovery-codes",
                    { method: "POST", ...json({ current_password }) },
                  );
                  setCodes(result.codes);
                  form.reset();
                }, "Recovery codes generated. Save them now; they cannot be shown again.");
              }}
            >
              <label>
                Confirm your password
                <input
                  name="current_password"
                  type="password"
                  required
                  autoComplete="current-password"
                  maxLength={128}
                />
              </label>
              <button className="button secondary" disabled={busy}>
                <KeyRound size={16} />
                Generate new codes
              </button>
            </form>
            {codes.length > 0 && (
              <div className="secret-result">
                <h3>Save all five codes somewhere private</h3>
                <ul className="recovery-code-list">
                  {codes.map((code) => (
                    <li key={code}>
                      <code>{code}</code>
                    </li>
                  ))}
                </ul>
                <div className="tools-actions">
                  <button
                    className="button secondary"
                    onClick={() => void copy(codes.join("\n"))}
                  >
                    <Copy size={14} />
                    Copy codes
                  </button>
                  <button className="text-button" onClick={() => setCodes([])}>
                    I have saved them
                  </button>
                </div>
              </div>
            )}
            <p className="tools-muted">
              If you lose your password and every recovery code, this local app
              cannot recover the account for you.
            </p>
          </section>
        </>
      )}
    </div>
  );
}
