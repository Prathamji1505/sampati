import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Download,
  Eye,
  EyeOff,
  RefreshCw,
  Search,
  Upload,
} from "lucide-react";
import { api } from "./api";
import type { SessionState, WorkspaceScope } from "./types";
import "./workspace-tools.css";
import "./relief-requests.css";
import "./automation.css";

type Source = {
  id: string;
  name: string;
  enabled: boolean;
  automation_mode: "review" | "new_drafts";
  policy_version: number;
  ingest_path: string;
  last_received_at: string | null;
  token?: string;
};
type Event = {
  id: string;
  version: number;
  action: string;
  actor: string;
  created_at: string;
  reason: string;
  after: Record<string, unknown>;
};
type Sources = { items: Source[]; can_manage: boolean; can_upload: boolean };
type Proposal = {
  row: number;
  reference: string;
  action: "new_draft" | "duplicate" | "conflict";
  values: Record<string, string>;
  request_id: string | null;
  request_status: string | null;
  differences: { field: string; accepted: string; incoming: string }[];
};
type Receipt = {
  id: string;
  filename: string;
  report_reference: string | null;
  source_id: string;
  source_name: string;
  state: string;
  version: number;
  automatic: boolean;
  received_at: string;
  received_actor: string;
  observed_at: string | null;
  observed_at_raw: string | null;
  source_policy_version: number;
  source_policy_mode: string;
  rule_version: string;
  row_count: number;
  error_count: number;
  reviewed_at: string | null;
  results: { reference: string; request_id: string; action: string }[];
};
type Detail = {
  receipt: Receipt & {
    raw_text: string;
    errors: { row: number | null; field: string; message: string }[];
    plan: {
      proposals: Proposal[];
      counts: Record<string, number>;
      warnings: { code: string; message: string }[];
      plan_hash: string;
      can_apply: boolean;
    };
    stock_hints: {
      position_id: string;
      item_name: string;
      store_name: string;
      category: string;
      unit: string;
      available: string;
    }[];
  };
  events: Event[];
};
type Inbox = {
  items: Receipt[];
  total: number;
  page: number;
  total_pages: number;
  counts: Record<string, number>;
  can_edit: boolean;
  freshness_hours: number;
};
const states: Record<string, string> = {
  all: "All files",
  pending: "Needs review",
  blocked: "Invalid file",
  applied: "Applied",
  dismissed: "Dismissed",
};
const actions = {
  new_draft: "New draft",
  duplicate: "Unchanged duplicate",
  conflict: "Conflict · paused",
};
const when = (value: string | null) =>
  value ? new Date(value).toLocaleString() : "Not supplied";
const json = (value: unknown) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(value),
});
const fieldName = (value: string) => value.replaceAll("_", " ");

export default function Automation({
  scope,
  session,
  onSignIn,
  initialId,
  onInitialUsed,
  onRequest,
}: {
  scope: WorkspaceScope;
  session: SessionState | null;
  onSignIn: () => void;
  initialId?: string | null;
  onInitialUsed: () => void;
  onRequest: (id: string) => void;
}) {
  const [mode, setMode] = useState<"list" | "detail" | "sources">("list");
  const [list, setList] = useState<Inbox | null>(null);
  const [sources, setSources] = useState<Sources | null>(null);
  const [selected, setSelected] = useState("");
  const [sourceDetail, setSourceDetail] = useState<{
    source: Source;
    events: Event[];
    next_before_version: number | null;
  } | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [state, setState] = useState("all");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [filterSource, setFilterSource] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [name, setName] = useState("");
  const [reason, setReason] = useState("");
  const [ack, setAck] = useState(false);
  const [enabled, setEnabled] = useState(true);
  const [rule, setRule] = useState("review");
  const [policyReason, setPolicyReason] = useState("");
  const [secret, setSecret] = useState<{
    token: string;
    sourceId: string;
  } | null>(null);
  const [reveal, setReveal] = useState(false);
  const epoch = useRef(0);
  const detailEpoch = useRef(0);
  const uploadInput = useRef<HTMLInputElement>(null);
  const canEdit = scope === "private" && list?.can_edit === true;
  const owner = scope === "private" && sources?.can_manage === true;
  const item = detail?.receipt;

  async function loadSources() {
    const data = await api<Sources>("/automation/sources");
    setSources(data);
    setSelected((value) =>
      data.items.some((source) => source.id === value)
        ? value
        : data.items[0]?.id || "",
    );
  }
  async function loadList() {
    const current = ++epoch.current;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        state,
        q: search,
        page: String(page),
      });
      if (filterSource) params.set("source_id", filterSource);
      const data = await api<Inbox>(`/automation/inbox?${params}`);
      if (current === epoch.current) {
        setList(data);
        if (data.page !== page) setPage(data.page);
      }
    } catch (problem) {
      if (current === epoch.current) setError((problem as Error).message);
    } finally {
      if (current === epoch.current) setLoading(false);
    }
  }
  useEffect(() => {
    void loadSources().catch((problem) => setError(problem.message));
  }, [scope]);
  useEffect(() => {
    const timer = setTimeout(() => setSearch(query), 250);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    void loadList();
    return () => {
      epoch.current++;
    };
  }, [scope, state, search, filterSource, page]);
  useEffect(() => {
    const current = ++detailEpoch.current;
    setSourceDetail(null);
    setPolicyReason("");
    if (!selected) return;
    void api<{
      source: Source;
      events: Event[];
      next_before_version: number | null;
    }>(`/automation/sources/${selected}`)
      .then((data) => {
        if (current !== detailEpoch.current) return;
        setSourceDetail(data);
        setEnabled(data.source.enabled);
        setRule(data.source.automation_mode);
      })
      .catch((problem) => {
        if (current === detailEpoch.current) setError(problem.message);
      });
    return () => {
      detailEpoch.current++;
    };
  }, [selected]);
  useEffect(() => {
    if (initialId) {
      void openReceipt(initialId);
      onInitialUsed();
    }
  }, [initialId]);
  useEffect(() => {
    if (mode !== "sources") {
      setSecret(null);
      setReveal(false);
    }
  }, [mode]);

  async function perform(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function refreshSource(id: string) {
    const next = await api<{
      source: Source;
      events: Event[];
      next_before_version: number | null;
    }>(`/automation/sources/${id}`);
    setSourceDetail(next);
    setEnabled(next.source.enabled);
    setRule(next.source.automation_mode);
    setPolicyReason("");
    await loadSources();
  }
  async function openReceipt(id: string) {
    await perform(async () => {
      const next = await api<Detail>(`/automation/inbox/${id}`);
      setDetail(next);
      setReason("");
      setAck(false);
      setMode("detail");
    });
  }
  function back() {
    setMode("list");
    setError("");
    setNotice("");
    void loadList();
    void loadSources().catch((problem) => setError(problem.message));
  }
  async function downloadFormat() {
    await perform(async () => {
      const format = await api<unknown>("/automation/contract");
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(format, null, 2)], {
          type: "application/json",
        }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = "sampati-relief-intake-guide.json";
      link.click();
      URL.revokeObjectURL(url);
      setNotice(
        "Format guide downloaded. Its example is fictional; replace its details before use.",
      );
    });
  }
  async function createSource() {
    await perform(async () => {
      const created = await api<Source>("/automation/sources", {
        method: "POST",
        ...json({ name }),
      });
      await loadSources();
      setSelected(created.id);
      setSecret({ token: created.token!, sourceId: created.id });
      setReveal(false);
      setName("");
      setNotice(
        "Source created with manual review. Save its private key if you will connect a file watcher.",
      );
    });
  }
  async function savePolicy(rotate = false) {
    if (!sourceDetail) return;
    await perform(async () => {
      const current = sourceDetail.source;
      const result = await api<Source>(
        `/automation/sources/${current.id}${rotate ? "/rotate" : ""}`,
        {
          method: rotate ? "POST" : "PATCH",
          ...json({
            expected_version: current.policy_version,
            reason: policyReason,
            ...(!rotate ? { enabled, automation_mode: rule } : {}),
          }),
        },
      );
      await refreshSource(current.id);
      if (rotate) {
        setSecret({ token: result.token!, sourceId: current.id });
        setReveal(false);
      }
      setNotice(
        rotate
          ? "New key created. The previous key is inactive."
          : "Source policy saved. Pending files still need a separate decision.",
      );
    });
  }
  async function receive(file?: File) {
    await perform(async () => {
      let options: RequestInit = { method: "POST" };
      if (file) {
        const body = new FormData();
        body.append("file", file);
        options = { ...options, body };
      }
      const result = await api<{
        receipt: Detail["receipt"];
        duplicate: boolean;
      }>(
        `/automation/sources/${selected}/${file ? "upload" : "example"}`,
        options,
      );
      const next = await api<Detail>(`/automation/inbox/${result.receipt.id}`);
      setDetail(next);
      setMode("detail");
      setReason("");
      setAck(false);
      setNotice(
        result.duplicate
          ? "This file was already received. Its original decision and evidence are shown."
          : result.receipt.automatic
            ? "The trusted-source rule created new drafts. Each request still needs human review."
            : "File saved. Inspect the proposals and source evidence below.",
      );
      await loadList();
    });
  }
  async function decide(action: "apply" | "dismiss") {
    if (!item) return;
    await perform(async () => {
      await api(`/automation/inbox/${item.id}/${action}`, {
        method: "POST",
        ...json({
          expected_version: item.version,
          reason,
          ...(action === "apply"
            ? { plan_hash: item.plan.plan_hash, acknowledge_warnings: ack }
            : {}),
        }),
      });
      setDetail(await api<Detail>(`/automation/inbox/${item.id}`));
      setReason("");
      setAck(false);
      setNotice(
        action === "apply"
          ? "File applied. New requests are drafts; duplicate requests were left unchanged."
          : "File dismissed. Its evidence and decision remain in history.",
      );
      await loadList();
    });
  }

  return (
    <div className="workspace-tools automation-workspace">
      {error && (
        <div className="message error" role="alert">
          {error} <span>Refresh the current view before retrying.</span>
        </div>
      )}
      {notice && (
        <div className="message success" role="status">
          {notice}
        </div>
      )}
      {scope === "demo" && (
        <div className="relief-demo-note">
          <p>
            Fictional examples · Read only. Rules check structured files and
            propose drafts. No AI model or live source is connected.
          </p>
          {!session?.user && (
            <button className="button secondary" onClick={onSignIn}>
              Sign in to connect a source
            </button>
          )}
        </div>
      )}

      {mode === "list" && (
        <>
          <div className="automation-intro">
            <h2>From a changing file to a reviewable draft</h2>
            <p>
              Send dated relief needs from a connected CSV or JSON file. New
              references become draft proposals; matching records stay unchanged
              and conflicting details pause the file.
            </p>
          </div>
          <div className="tools-toolbar">
            <span>
              {loading
                ? "Loading incoming files…"
                : `${list?.counts.all ?? 0} files recorded`}
            </span>
            <div className="tools-actions">
              <button
                className="button secondary"
                disabled={busy || loading}
                onClick={() =>
                  void perform(async () => {
                    await loadList();
                    await loadSources();
                  })
                }
              >
                <RefreshCw size={15} />
                Refresh inbox
              </button>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => void downloadFormat()}
              >
                <Download size={15} />
                Format guide
              </button>
              <button
                className="button primary"
                disabled={busy}
                onClick={() => {
                  setMode("sources");
                  setError("");
                  setNotice("");
                }}
              >
                Connected sources
              </button>
            </div>
          </div>
          <section
            className="register-panel"
            aria-label="Incoming relief files"
          >
            <div className="automation-filters">
              <label>
                Decision
                <select
                  value={state}
                  onChange={(event) => {
                    setState(event.target.value);
                    setPage(1);
                  }}
                >
                  {Object.entries(states).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label} ({list?.counts[key] ?? 0})
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Source
                <select
                  value={filterSource}
                  onChange={(event) => {
                    setFilterSource(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All sources</option>
                  {sources?.items.map((source) => (
                    <option key={source.id} value={source.id}>
                      {source.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="automation-search">
                <span>Find a file</span>
                <span>
                  <Search size={16} />
                  <input
                    aria-label="Find a file"
                    placeholder="Report, filename or source"
                    value={query}
                    onChange={(event) => {
                      setQuery(event.target.value);
                      setPage(1);
                    }}
                  />
                </span>
              </label>
            </div>
            <div className="table-scroll">
              <table className="tools-table automation-table">
                <thead>
                  <tr>
                    <th scope="col">Report &amp; source</th>
                    <th scope="col">Decision</th>
                    <th scope="col">Contents</th>
                    <th scope="col">Received</th>
                    <th scope="col">Review</th>
                  </tr>
                </thead>
                <tbody>
                  {list?.items.map((receipt) => (
                    <tr key={receipt.id}>
                      <td>
                        <strong>
                          {receipt.report_reference || receipt.filename}
                        </strong>
                        <span className="relief-secondary">
                          {receipt.source_name}
                        </span>
                        <small>{receipt.filename}</small>
                      </td>
                      <td>
                        <span
                          className={`automation-state automation-state-${receipt.state}`}
                        >
                          {states[receipt.state]}
                        </span>
                        {receipt.automatic && (
                          <span className="relief-secondary">
                            Trusted-source rule
                          </span>
                        )}
                      </td>
                      <td>
                        {receipt.row_count} valid rows
                        {receipt.error_count > 0 && (
                          <span className="relief-secondary">
                            {receipt.error_count} validation issues
                          </span>
                        )}
                      </td>
                      <td>{when(receipt.received_at)}</td>
                      <td>
                        <button
                          className="button secondary"
                          disabled={busy}
                          onClick={() => void openReceipt(receipt.id)}
                        >
                          Inspect file
                          <span className="sr-only">
                            {" "}
                            {receipt.report_reference || receipt.filename}
                          </span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!loading && !list?.items.length && (
              <div className="relief-empty">
                <h2>
                  {(list?.counts.all ?? 0) === 0
                    ? "Your inbox is ready for its first file"
                    : "No files match these filters"}
                </h2>
                <p>
                  {(list?.counts.all ?? 0) === 0
                    ? "Open Connected sources to add a relief desk, upload a file or try a fictional example."
                    : "Change the decision, source or search to see other files."}
                </p>
              </div>
            )}
            <div className="table-footer relief-pagination">
              <span>
                {list?.total ?? 0} matching files · Page {list?.page ?? 1} of{" "}
                {list?.total_pages ?? 1}
              </span>
              <div className="tools-actions">
                <button
                  className="button secondary"
                  disabled={busy || loading || (list?.page ?? 1) <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </button>
                <button
                  className="button secondary"
                  disabled={
                    busy ||
                    loading ||
                    (list?.page ?? 1) >= (list?.total_pages ?? 1)
                  }
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        </>
      )}

      {mode === "sources" && (
        <>
          <div className="tools-toolbar">
            <button className="button secondary" disabled={busy} onClick={back}>
              <ArrowLeft size={15} />
              Back to inbox
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() =>
                void perform(async () => {
                  await loadSources();
                  if (selected) await refreshSource(selected);
                })
              }
            >
              <RefreshCw size={15} />
              Refresh sources
            </button>
          </div>
          <section className="tools-panel">
            <h2>Connected relief sources</h2>
            <p className="tools-muted">
              Each source has a private upload key and its own rule. New sources
              start with manual review. A file watcher can send changed files
              while it is running on your PC.
            </p>
            {owner && (
              <form
                className="tools-inline-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  void createSource();
                }}
              >
                <label>
                  New source name
                  <input
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    minLength={2}
                    maxLength={100}
                    required
                    disabled={busy}
                    placeholder="For example, community relief desk"
                  />
                </label>
                <button className="button primary" disabled={busy}>
                  Add source
                </button>
              </form>
            )}
            {!owner && (
              <p className="tools-muted">
                An organisation owner manages source keys and trusted-source
                rules.
              </p>
            )}
            <label className="automation-source-select">
              Select source
              <select
                value={selected}
                disabled={busy || !sources?.items.length}
                onChange={(event) => {
                  setSelected(event.target.value);
                  setSecret(null);
                }}
              >
                <option value="" disabled>
                  No source selected
                </option>
                {sources?.items.map((source) => (
                  <option value={source.id} key={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </label>
          </section>
          {sourceDetail && (
            <>
              <section className="tools-panel">
                <div className="tools-panel-heading">
                  <h2>{sourceDetail.source.name}</h2>
                  <span>
                    Policy v{sourceDetail.source.policy_version} ·{" "}
                    {sourceDetail.source.enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <dl className="relief-details">
                  <div>
                    <dt>Current rule</dt>
                    <dd>
                      {sourceDetail.source.automation_mode === "review"
                        ? "Review every file"
                        : "Create new drafts automatically"}
                    </dd>
                  </div>
                  <div>
                    <dt>Last new file received</dt>
                    <dd>{when(sourceDetail.source.last_received_at)}</dd>
                  </div>
                  <div className="relief-full-field">
                    <dt>Source ID · use with the file watcher</dt>
                    <dd>{sourceDetail.source.id}</dd>
                  </div>
                </dl>
                {canEdit && (
                  <>
                    <p className="tools-muted">
                      CSV or JSON · UTF-8 · Up to 200 requests and 256 KiB. An
                      example also follows this source’s current rule and may
                      create fictional drafts.
                    </p>
                    <div className="tools-actions">
                      <input
                        ref={uploadInput}
                        type="file"
                        accept=".csv,.json"
                        hidden
                        onChange={(event) => {
                          const file = event.target.files?.[0];
                          event.target.value = "";
                          if (file) void receive(file);
                        }}
                      />
                      <button
                        className="button primary"
                        disabled={busy || !sourceDetail.source.enabled}
                        onClick={() => uploadInput.current?.click()}
                      >
                        <Upload size={15} />
                        Upload relief file
                      </button>
                      <button
                        className="button secondary"
                        disabled={busy || !sourceDetail.source.enabled}
                        onClick={() => void receive()}
                      >
                        Try fictional example
                      </button>
                      <button
                        className="button secondary"
                        disabled={busy}
                        onClick={() => void downloadFormat()}
                      >
                        <Download size={15} />
                        Format guide
                      </button>
                    </div>
                  </>
                )}
                {secret?.sourceId === selected && (
                  <div className="automation-key">
                    <h3>Save this private source key</h3>
                    <p>
                      This key is shown only now. Keep it in your watcher
                      terminal, outside your dataset and project files.
                    </p>
                    <label>
                      Source key
                      <input
                        aria-label="Source key"
                        readOnly
                        type={reveal ? "text" : "password"}
                        value={secret.token}
                      />
                    </label>
                    <div className="tools-actions">
                      <button
                        className="button secondary"
                        onClick={() => setReveal(!reveal)}
                      >
                        {reveal ? <EyeOff size={15} /> : <Eye size={15} />}{" "}
                        {reveal ? "Hide key" : "Reveal key"}
                      </button>
                      <button
                        className="button secondary"
                        onClick={() =>
                          void perform(async () => {
                            await navigator.clipboard.writeText(secret.token);
                            setNotice("Source key copied. Save it privately.");
                          })
                        }
                      >
                        Copy key
                      </button>
                      <button
                        className="button secondary"
                        onClick={() => setSecret(null)}
                      >
                        I saved the key
                      </button>
                    </div>
                  </div>
                )}
              </section>
              {owner && (
                <section className="tools-panel">
                  <h2>Trusted-source rule</h2>
                  <p className="tools-muted">
                    Automatic mode creates new drafts only when the whole file
                    is valid, current and conflict-free. It never approves
                    needs, reserves supplies or confirms a delivery. Changing
                    the rule does not process files already waiting in the
                    inbox.
                  </p>
                  <form
                    className="relief-form"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void savePolicy();
                    }}
                  >
                    <label>
                      Incoming files
                      <select
                        aria-label="Incoming files"
                        value={rule}
                        onChange={(event) => setRule(event.target.value)}
                        disabled={busy}
                      >
                        <option value="review">Review every file</option>
                        <option value="new_drafts">
                          Create new drafts automatically
                        </option>
                      </select>
                    </label>
                    <label>
                      Connection
                      <select
                        aria-label="Connection"
                        value={String(enabled)}
                        onChange={(event) =>
                          setEnabled(event.target.value === "true")
                        }
                        disabled={busy}
                      >
                        <option value="true">Enabled</option>
                        <option value="false">
                          Disabled · stop new uploads
                        </option>
                      </select>
                    </label>
                    <label className="relief-full-field">
                      Reason for policy or key change
                      <textarea
                        value={policyReason}
                        onChange={(event) =>
                          setPolicyReason(event.target.value)
                        }
                        maxLength={500}
                        rows={2}
                        required
                        disabled={busy}
                      />
                    </label>
                    <div className="relief-form-actions">
                      <button
                        className="button primary"
                        disabled={busy || !policyReason.trim()}
                      >
                        Save source policy
                      </button>
                      <button
                        type="button"
                        className="button secondary"
                        disabled={busy || !policyReason.trim()}
                        onClick={() => void savePolicy(true)}
                      >
                        Replace private key
                      </button>
                    </div>
                  </form>
                </section>
              )}
              <section className="tools-panel">
                <h2>Source history</h2>
                <Audit events={sourceDetail.events} />
                {sourceDetail.next_before_version && (
                  <button
                    className="button secondary"
                    disabled={busy}
                    onClick={() =>
                      void perform(async () => {
                        const older = await api<typeof sourceDetail>(
                          `/automation/sources/${selected}?before_version=${sourceDetail.next_before_version}`,
                        );
                        setSourceDetail({
                          ...older,
                          events: [...sourceDetail.events, ...older.events],
                        });
                      })
                    }
                  >
                    Load earlier source history
                  </button>
                )}
              </section>
            </>
          )}
        </>
      )}

      {mode === "detail" && item && (
        <>
          <div className="tools-toolbar">
            <button className="button secondary" disabled={busy} onClick={back}>
              <ArrowLeft size={15} />
              Back to inbox
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => void openReceipt(item.id)}
            >
              <RefreshCw size={15} />
              Refresh preview
            </button>
          </div>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>{item.report_reference || item.filename}</h2>
              <span
                className={`automation-state automation-state-${item.state}`}
              >
                {states[item.state]}
                {item.automatic ? " · Trusted-source rule" : ""}
              </span>
            </div>
            <dl className="relief-details">
              <div>
                <dt>Source</dt>
                <dd>
                  {item.source_name}
                  <small>{item.filename}</small>
                </dd>
              </div>
              <div>
                <dt>Source observation</dt>
                <dd>
                  {when(item.observed_at)}
                  <small>{item.observed_at_raw}</small>
                </dd>
              </div>
              <div>
                <dt>Received</dt>
                <dd>
                  {when(item.received_at)}
                  <small>{item.received_actor}</small>
                </dd>
              </div>
              <div>
                <dt>Rule at receipt</dt>
                <dd>
                  {item.source_policy_mode === "review"
                    ? "Review every file"
                    : "Create new drafts automatically"}
                  <small>
                    Policy v{item.source_policy_version} · {item.rule_version}
                  </small>
                </dd>
              </div>
            </dl>
            <p className="tools-muted">
              Structured-file rules check fields and references. A draft is a
              recorded proposal; people must verify the need before submitting
              and reviewing it.
            </p>
          </section>
          {!!item.plan.warnings.length && (
            <section
              className="automation-warning"
              aria-label="Source warnings"
            >
              <h2>Check the source context</h2>
              {item.plan.warnings.map((warning) => (
                <p key={warning.code}>{warning.message}</p>
              ))}
            </section>
          )}
          {!!item.errors.length && (
            <section className="tools-panel">
              <h2>Fix the file before it can create drafts</h2>
              <p className="tools-muted">
                No rows from an invalid file are applied. Correct the source
                file and upload it again; this original stays in the inbox until
                dismissed.
              </p>
              <ul className="automation-errors">
                {item.errors.map((problem, index) => (
                  <li key={index}>
                    <strong>
                      {problem.row ? `Row ${problem.row} · ` : ""}
                      {fieldName(problem.field)}
                    </strong>
                    <span>{problem.message}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {item.state !== "applied" && !!item.plan.proposals.length && (
            <section className="tools-panel">
              <h2>Draft proposals</h2>
              <p className="tools-muted">
                {item.plan.counts.new_draft} new · {item.plan.counts.duplicate}{" "}
                unchanged · {item.plan.counts.conflict} conflicting. A conflict
                pauses the whole file. Reconcile the source details and upload a
                corrected report.
              </p>
              <div className="automation-proposals">
                {item.plan.proposals.map((proposal, index) => (
                  <article key={index}>
                    <div className="tools-panel-heading">
                      <h3>{proposal.reference}</h3>
                      <span
                        className={`automation-state automation-action-${proposal.action}`}
                      >
                        {actions[proposal.action]}
                      </span>
                    </div>
                    <p>
                      {proposal.values.quantity} {proposal.values.unit} ·{" "}
                      {proposal.values.item_name}
                    </p>
                    <p className="tools-muted">
                      {proposal.values.requesting_organisation} ·{" "}
                      {proposal.values.locality}
                      <br />
                      Needed {when(proposal.values.needed_by)} ·{" "}
                      {proposal.values.source_name}
                    </p>
                    {proposal.values.note && (
                      <p className="tools-muted">{proposal.values.note}</p>
                    )}
                    {!!proposal.differences.length && (
                      <dl className="automation-differences">
                        {proposal.differences.map((difference) => (
                          <div key={difference.field}>
                            <dt>{fieldName(difference.field)}</dt>
                            <dd>
                              <span>
                                Accepted: {difference.accepted || "Empty"}
                              </span>
                              <span>
                                Incoming: {difference.incoming || "Empty"}
                              </span>
                            </dd>
                          </div>
                        ))}
                      </dl>
                    )}
                    {proposal.request_id && (
                      <button
                        className="button secondary"
                        disabled={busy}
                        onClick={() => onRequest(proposal.request_id!)}
                      >
                        View accepted request
                      </button>
                    )}
                  </article>
                ))}
              </div>
            </section>
          )}
          {item.state === "applied" && (
            <section className="tools-panel">
              <h2>
                {item.automatic
                  ? "Drafts created by the source rule"
                  : "File applied"}
              </h2>
              <p className="tools-muted">
                Accepted {when(item.reviewed_at)}. Created requests remain
                drafts until a person submits and reviews them. Duplicate
                records retain their original details and status.
              </p>
              <ul className="automation-results">
                {item.results.map((result) => (
                  <li key={result.reference}>
                    <div>
                      <strong>{result.reference}</strong>
                      <span>
                        {result.action === "created_draft"
                          ? "Created as a draft"
                          : "Matching request left unchanged"}
                      </span>
                    </div>
                    <button
                      className="button secondary"
                      disabled={busy}
                      onClick={() => onRequest(result.request_id)}
                    >
                      View request
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {!!item.stock_hints.length && (
            <section className="tools-panel">
              <h2>Inventory to investigate</h2>
              <p className="tools-muted">
                These records share a category and unit with the file. Check the
                actual item, condition, location and current count. No supplies
                are reserved by intake.
              </p>
              <ul className="automation-hints">
                {item.stock_hints.map((hint) => (
                  <li key={hint.position_id}>
                    <strong>{hint.item_name}</strong>
                    <span>
                      {hint.store_name} · {hint.available} {hint.unit} recorded
                      available
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {canEdit && ["pending", "blocked"].includes(item.state) && (
            <section className="tools-panel">
              <h2>Record your decision</h2>
              <form
                className="automation-decision"
                onSubmit={(event) => {
                  event.preventDefault();
                  void decide("apply");
                }}
              >
                <label>
                  Reason for accepting or dismissing this file
                  <textarea
                    aria-label="Reason for accepting or dismissing this file"
                    value={reason}
                    onChange={(event) => setReason(event.target.value)}
                    rows={2}
                    maxLength={500}
                    required
                    disabled={busy}
                  />
                </label>
                {!!item.plan.warnings.length && (
                  <label className="automation-checkbox">
                    <input
                      type="checkbox"
                      checked={ack}
                      onChange={(event) => setAck(event.target.checked)}
                      disabled={busy}
                    />
                    I checked the source warnings and verified the evidence.
                  </label>
                )}
                <div className="tools-actions">
                  <button
                    className="button primary"
                    disabled={
                      busy ||
                      !reason.trim() ||
                      !item.plan.can_apply ||
                      (!!item.plan.warnings.length && !ack)
                    }
                  >
                    {busy
                      ? "Saving decision…"
                      : "Accept new drafts & duplicates"}
                  </button>
                  <button
                    type="button"
                    className="button secondary"
                    disabled={busy || !reason.trim()}
                    onClick={() => void decide("dismiss")}
                  >
                    Dismiss file
                  </button>
                </div>
                {!item.plan.can_apply && (
                  <p className="tools-muted">
                    Acceptance is paused until the source supplies a valid,
                    conflict-free file. You can dismiss this saved report with a
                    reason.
                  </p>
                )}
              </form>
            </section>
          )}
          {!canEdit && ["pending", "blocked"].includes(item.state) && (
            <p className="tools-muted">
              An owner or editor can record this file’s decision in their
              organisation workspace.
            </p>
          )}
          <section className="tools-panel">
            <details className="automation-evidence">
              <summary>Original source text</summary>
              <p className="tools-muted">
                Saved exactly as decoded from UTF-8. This evidence remains
                unchanged after a decision.
              </p>
              <pre>{item.raw_text || "(Empty file)"}</pre>
            </details>
          </section>
          <section className="tools-panel">
            <h2>Intake history</h2>
            <Audit events={detail.events} />
          </section>
        </>
      )}
    </div>
  );
}

function Audit({ events }: { events: Event[] }) {
  return (
    <ol className="automation-audit">
      {events.map((event) => (
        <li key={event.id}>
          <div>
            <strong>{fieldName(event.action)}</strong>
            <span>
              v{event.version} · {when(event.created_at)}
            </span>
          </div>
          <p>{event.reason}</p>
          <p className="tools-muted">{event.actor}</p>
          {event.after.automation_mode !== undefined && (
            <p className="tools-muted">
              {event.after.automation_mode === "review"
                ? "Review every file"
                : "Create new drafts automatically"}{" "}
              · {event.after.enabled ? "Enabled" : "Disabled"}
            </p>
          )}
        </li>
      ))}
    </ol>
  );
}
