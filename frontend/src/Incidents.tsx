import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Download, Plus, RefreshCw, Search } from "lucide-react";
import { api } from "./api";
import type { SessionState, Workspace, WorkspaceScope } from "./types";
import "./workspace-tools.css";
import "./relief-requests.css";
import "./incidents.css";

type Assessment = {
  schema_version: string;
  external_reference: string;
  title: string;
  hazard: string;
  assessment_kind: string;
  locality: string;
  observed_at: string;
  generated_at: string;
  source_name: string;
  source_url: string | null;
  summary: string;
  uncertainty: string;
  extent: { west: number; south: number; east: number; north: number };
  reported_affected_people: number | null;
};
type Status = "pending" | "reviewed" | "dismissed";
type Incident = {
  id: string;
  assessment: Assessment;
  status: Status;
  version: number;
  created_actor: string;
  received_at: string;
  updated_at: string;
  older_than_24h: boolean;
  allowed_transitions: Status[];
};
type Event = {
  id: string;
  version: number;
  actor: string;
  created_at: string;
  reason: string;
  before_status: Status | null;
  after_status: Status;
};
type Detail = {
  incident: Incident;
  events: Event[];
  next_before_version: number | null;
  linked_requests: { id: string; reference: string; status: string }[];
  linked_request_count: number;
};
type List = {
  items: Incident[];
  total: number;
  page: number;
  total_pages: number;
  counts: Record<string, number>;
  can_edit: boolean;
};
export type IncidentDraft = {
  id: string;
  reference: string;
  locality: string;
  source_name: string;
};
const labels: Record<Status, string> = {
  pending: "Needs review",
  reviewed: "Reviewed",
  dismissed: "Dismissed",
};
const when = (value: string) => new Date(value).toLocaleString();
const json = (body: unknown) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
function example(): Assessment {
  return {
    schema_version: "sampati.incident.v1",
    external_reference: `EXAMPLE-FLOOD-${Date.now().toString(36).toUpperCase()}`,
    title: "Fictional Riverside flood assessment",
    hazard: "flood",
    assessment_kind: "impact_observation",
    locality: "Fictional Riverside Ward",
    observed_at: new Date(Date.now() - 7200000).toISOString(),
    generated_at: new Date(Date.now() - 3600000).toISOString(),
    source_name: "Fictional assessment desk",
    source_url: null,
    summary:
      "Fictional assessment reports water around access roads. A local needs check is still required.",
    uncertainty:
      "Illustrative extent only. Cloud cover and local conditions have not been verified.",
    extent: { west: 85.1, south: 25.4, east: 85.2, north: 25.5 },
    reported_affected_people: null,
  };
}
function StatusLabel({ status }: { status: Status }) {
  return (
    <span
      className={`relief-status relief-status-${status === "pending" ? "submitted" : status}`}
    >
      {labels[status]}
    </span>
  );
}

export default function Incidents({
  scope,
  session,
  workspace,
  onSignIn,
  onRequest,
  onRequests,
}: {
  scope: WorkspaceScope;
  session: SessionState | null;
  workspace: Workspace | null;
  onSignIn: () => void;
  onRequest: (incident: IncidentDraft) => void;
  onRequests: () => void;
}) {
  const [list, setList] = useState<List | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [mode, setMode] = useState<"list" | "new" | "detail">("list");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [raw, setRaw] = useState("");
  const [preview, setPreview] = useState<Assessment | null>(null);
  const [target, setTarget] = useState<Status>("reviewed");
  const [reason, setReason] = useState("");
  const epoch = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const canEdit =
    scope === "private" &&
    ["owner", "editor"].includes(session?.workspace?.role || "") &&
    list?.can_edit === true;
  async function loadList() {
    const request = ++epoch.current;
    setLoading(true);
    try {
      const data = await api<List>(
        `/incidents?${new URLSearchParams({ q: search, status: filter, page: String(page) })}`,
      );
      if (request === epoch.current) {
        setList(data);
        if (data.page !== page) setPage(data.page);
      }
    } catch (problem) {
      if (request === epoch.current) setError((problem as Error).message);
    } finally {
      if (request === epoch.current) setLoading(false);
    }
  }
  useEffect(() => {
    const timer = setTimeout(() => setSearch(query), 250);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    void loadList();
    return () => {
      epoch.current++;
    };
  }, [search, filter, page, workspace?.server_time]);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [mode, detail?.incident.id]);
  async function open(id: string) {
    setBusy(true);
    setError("");
    try {
      const data = await api<Detail>(`/incidents/${id}`);
      setDetail(data);
      setMode("detail");
      setReason("");
      setTarget(data.incident.allowed_transitions[0] || "pending");
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function parse(text: string) {
    setRaw(text);
    setPreview(null);
    setError("");
    setNotice("");
  }
  function previewJson() {
    setError("");
    setPreview(null);
    try {
      if (new TextEncoder().encode(raw).length > 262144)
        throw new Error("Use a JSON assessment smaller than 256 KB.");
      const value = JSON.parse(raw);
      if (
        !value ||
        typeof value !== "object" ||
        Array.isArray(value) ||
        value.schema_version !== "sampati.incident.v1"
      )
        throw new Error(
          "Use one assessment with schema_version sampati.incident.v1. Download the contract for its fields.",
        );
      for (const key of [
        "external_reference",
        "title",
        "locality",
        "observed_at",
        "generated_at",
        "source_name",
        "summary",
        "uncertainty",
      ])
        if (typeof value[key] !== "string" || !value[key].trim())
          throw new Error(`Add a non-empty ${key} field.`);
      if (
        value.hazard !== "flood" ||
        value.assessment_kind !== "impact_observation"
      )
        throw new Error(
          "This intake accepts flood impact observations. Forecasts require a separate contract.",
        );
      if (
        !value.extent ||
        ["west", "south", "east", "north"].some(
          (key) =>
            typeof value.extent[key] !== "number" ||
            !Number.isFinite(value.extent[key]),
        )
      )
        throw new Error(
          "Provide west, south, east and north as numbers in extent.",
        );
      if (
        [value.observed_at, value.generated_at].some(
          (date) => !Number.isFinite(new Date(date).getTime()),
        )
      )
        throw new Error(
          "Provide valid dated observation and generation times.",
        );
      // This is a display preview. The server validates the complete contract on recording.
      setPreview(value as Assessment);
    } catch (problem) {
      setError(
        problem instanceof SyntaxError
          ? "The JSON could not be read. Check its quotes, commas and braces, then preview again."
          : (problem as Error).message,
      );
    }
  }
  async function record() {
    if (!preview) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const data = await api<{ incident: Incident; duplicate: boolean }>(
        "/incidents",
        { method: "POST", ...json(preview) },
      );
      await open(data.incident.id);
      await loadList();
      setNotice(
        data.duplicate
          ? "This assessment was already recorded. Its original evidence and review history are retained."
          : "Assessment recorded. Review its source and uncertainty before linking any local needs.",
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function review(event: React.FormEvent) {
    event.preventDefault();
    if (!detail) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api(`/incidents/${detail.incident.id}/review`, {
        method: "POST",
        ...json({
          status: target,
          expected_version: detail.incident.version,
          reason,
        }),
      });
      await open(detail.incident.id);
      await loadList();
      setNotice("Review decision recorded with your reason.");
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function downloadContract() {
    setError("");
    try {
      const contract = await api<object>("/incidents/contract");
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(contract, null, 2)], {
          type: "application/schema+json",
        }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = "sampati-incident-v1.schema.json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (problem) {
      setError((problem as Error).message);
    }
  }
  const item = detail?.incident;
  const assessment = item?.assessment;
  return (
    <div className="workspace-tools incident-workspace">
      {error && (
        <div className="message error" role="alert">
          {error}
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
            Fictional flood examples · Read only. No live assessment feed is
            connected.
          </p>
          {!session?.user && (
            <button className="button secondary" onClick={onSignIn}>
              Sign in to record incidents
            </button>
          )}
        </div>
      )}
      {mode === "list" && (
        <>
          <div className="tools-toolbar">
            <span>
              {loading
                ? "Loading incidents…"
                : `${list?.counts.all ?? 0} assessments in this workspace`}
            </span>
            <div className="tools-actions">
              <button
                className="button secondary"
                disabled={busy || loading}
                onClick={() => {
                  setError("");
                  void loadList();
                }}
              >
                <RefreshCw size={15} />
                Refresh incidents
              </button>
              <button
                className="button primary"
                disabled={!canEdit || busy}
                onClick={() => {
                  setRaw("");
                  setPreview(null);
                  setError("");
                  setNotice("");
                  setMode("new");
                }}
              >
                <Plus size={16} />
                Record assessment
              </button>
            </div>
          </div>
          <section
            className="register-panel"
            aria-label="Incident register"
            aria-busy={loading}
          >
            <div
              className="status-tabs relief-tabs"
              role="group"
              aria-label="Filter incidents by review status"
            >
              {(["all", "pending", "reviewed", "dismissed"] as const).map(
                (value) => (
                  <button
                    key={value}
                    className={filter === value ? "selected" : ""}
                    aria-pressed={filter === value}
                    onClick={() => {
                      setFilter(value);
                      setPage(1);
                    }}
                  >
                    {value === "all" ? "All assessments" : labels[value]}
                    <span>{list?.counts[value] ?? 0}</span>
                  </button>
                ),
              )}
            </div>
            <div className="table-toolbar">
              <label className="search-field">
                <Search size={17} />
                <input
                  aria-label="Search incidents"
                  placeholder="Search reference, source or locality…"
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setPage(1);
                  }}
                />
              </label>
            </div>
            {!list ? (
              <p className="relief-empty" role="status">
                {loading
                  ? "Loading the incident register…"
                  : "Incidents are unavailable. Refresh when the server is ready."}
              </p>
            ) : list.items.length === 0 ? (
              <div className="relief-empty">
                <h2>
                  {list.counts.all
                    ? "No assessments match these filters."
                    : "Your incident register starts here."}
                </h2>
                <p>
                  Record a dated flood assessment, inspect its evidence, then
                  review it before entering local supply needs.
                </p>
              </div>
            ) : (
              <>
                <p className="relief-scroll-hint">
                  Scroll the table sideways for source, review status and
                  assessment actions.
                </p>
                <div className="table-scroll">
                  <table className="tools-table incident-table">
                    <thead>
                      <tr>
                        <th scope="col">Assessment / locality</th>
                        <th scope="col">Observed / source</th>
                        <th scope="col">Review status</th>
                        <th scope="col">Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {list.items.map((row) => (
                        <tr key={row.id}>
                          <td>
                            <strong>{row.assessment.external_reference}</strong>
                            <span className="relief-secondary">
                              {row.assessment.title}
                            </span>
                            <span className="relief-secondary">
                              {row.assessment.locality}
                            </span>
                          </td>
                          <td>
                            {when(row.assessment.observed_at)}
                            <span className="relief-secondary">
                              {row.assessment.source_name}
                            </span>
                            {row.older_than_24h && (
                              <span className="relief-past-due">
                                Observation older than 24 hours
                              </span>
                            )}
                          </td>
                          <td>
                            <StatusLabel status={row.status} />
                          </td>
                          <td>
                            <button
                              className="button secondary"
                              disabled={busy}
                              aria-label={`Open ${row.assessment.external_reference} incident`}
                              onClick={() => {
                                setNotice("");
                                void open(row.id);
                              }}
                            >
                              Open assessment
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            <div className="table-footer relief-pagination">
              <span>{list?.total ?? 0} matching assessments</span>
              <div className="tools-actions">
                <button
                  className="button secondary"
                  disabled={loading || !list || list.page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous incidents
                </button>
                <span>
                  Page {list?.page ?? 1} of {list?.total_pages ?? 1}
                </span>
                <button
                  className="button secondary"
                  disabled={loading || !list || list.page >= list.total_pages}
                  onClick={() => setPage(page + 1)}
                >
                  Next incidents
                </button>
              </div>
            </div>
          </section>
          <p className="tools-muted">
            Start with flood impact observations. Source estimates need local
            verification. Reviewing evidence does not confirm needs or approve a
            relief mission.
          </p>
        </>
      )}
      {mode !== "list" && (
        <div className="tools-toolbar">
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => {
              setMode("list");
              setError("");
              setNotice("");
              void loadList();
            }}
          >
            <ArrowLeft size={15} />
            Back to incidents
          </button>
          <span>
            {mode === "new"
              ? "New assessment · Not saved yet"
              : `Version ${item?.version}`}
          </span>
        </div>
      )}
      {mode === "new" && (
        <section className="tools-panel">
          <div className="tools-panel-heading">
            <h2 ref={heading} tabIndex={-1}>
              Record a flood assessment
            </h2>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => parse(JSON.stringify(example(), null, 2))}
            >
              Use fictional example
            </button>
          </div>
          <p className="tools-muted">
            Paste one assessment or choose a JSON file. Preview it, then
            explicitly record it as Needs review. Other assessment tools
            can use this shared format; a live connector is not configured.
          </p>
          <div className="incident-import-actions">
            <label className="incident-file">
              Choose assessment JSON
              <input
                type="file"
                accept=".json,application/json"
                disabled={busy}
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  event.target.value = "";
                  if (!file) return;
                  if (file.size > 262144) {
                    setError("Choose a JSON file smaller than 256 KB.");
                    return;
                  }
                  try {
                    parse(await file.text());
                  } catch {
                    setError(
                      "The file could not be read. Choose it again or paste the JSON.",
                    );
                  }
                }}
              />
            </label>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => void downloadContract()}
            >
              <Download size={15} />
              Download JSON contract
            </button>
          </div>
          <label className="incident-json-label">
            Assessment JSON
            <textarea
              className="incident-json"
              value={raw}
              onChange={(event) => parse(event.target.value)}
              rows={15}
              spellCheck={false}
              disabled={busy}
              maxLength={262144}
            />
          </label>
          <button
            className="button secondary"
            disabled={busy || !raw.trim()}
            onClick={previewJson}
          >
            Preview assessment
          </button>
          {preview && (
            <div className="incident-preview">
              <h3>Assessment preview</h3>
              <dl className="relief-details">
                <div>
                  <dt>Reference / locality</dt>
                  <dd>
                    {preview.external_reference}
                    <small>{preview.locality}</small>
                  </dd>
                </div>
                <div>
                  <dt>Observed / generated</dt>
                  <dd>
                    {when(preview.observed_at)}
                    <small>{when(preview.generated_at)}</small>
                  </dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>{preview.source_name}</dd>
                </div>
                <div>
                  <dt>Evidence summary</dt>
                  <dd>{preview.summary}</dd>
                </div>
                <div className="relief-full-field">
                  <dt>Uncertainty / limitations</dt>
                  <dd>{preview.uncertainty}</dd>
                </div>
              </dl>
              <p className="tools-muted">
                Preview does not save or approve anything. The server checks the
                full contract when you record it.
              </p>
              <button
                className="button primary"
                disabled={busy || !canEdit}
                onClick={() => void record()}
              >
                {busy ? "Recording assessment…" : "Record as Needs review"}
              </button>
            </div>
          )}
        </section>
      )}
      {mode === "detail" && item && assessment && (
        <>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2 ref={heading} tabIndex={-1}>
                {assessment.title}
              </h2>
              <StatusLabel status={item.status} />
            </div>
            <p className="tools-muted">
              {assessment.external_reference} · Flood impact observation
            </p>
            <dl className="relief-details">
              <div>
                <dt>Locality</dt>
                <dd>{assessment.locality}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>
                  {assessment.source_name}
                  {assessment.source_url && (
                    <a
                      className="incident-source-link"
                      href={assessment.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Open source evidence
                    </a>
                  )}
                </dd>
              </div>
              <div>
                <dt>Observed at</dt>
                <dd>
                  {when(assessment.observed_at)}
                  {item.older_than_24h && (
                    <small className="relief-past-due">
                      Observation older than 24 hours · Check current conditions
                    </small>
                  )}
                </dd>
              </div>
              <div>
                <dt>Generated / received</dt>
                <dd>
                  {when(assessment.generated_at)}
                  <small>Received {when(item.received_at)}</small>
                </dd>
              </div>
              <div className="relief-full-field">
                <dt>Evidence summary</dt>
                <dd>{assessment.summary}</dd>
              </div>
              <div className="relief-full-field">
                <dt>Uncertainty / limitations</dt>
                <dd>{assessment.uncertainty}</dd>
              </div>
              <div>
                <dt>Reported affected people</dt>
                <dd>
                  {assessment.reported_affected_people === null
                    ? "Not reported"
                    : `${assessment.reported_affected_people.toLocaleString()} · Source estimate, unverified`}
                </dd>
              </div>
              <div>
                <dt>Reported extent (longitude / latitude)</dt>
                <dd>
                  West {assessment.extent.west}, South {assessment.extent.south}
                  <br />
                  East {assessment.extent.east}, North {assessment.extent.north}
                  <small>
                    Bounding rectangle only; not an exact flood boundary.
                  </small>
                </dd>
              </div>
              <div>
                <dt>Recorded by</dt>
                <dd>{item.created_actor}</dd>
              </div>
            </dl>
            <p className="tools-muted incident-integrity-note">
              Original evidence is retained. Record a new reference for a
              revised assessment. These observations do not predict future
              flooding.
            </p>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => void open(item.id)}
            >
              <RefreshCw size={15} />
              Refresh incident details
            </button>
          </section>
          {canEdit && (
            <section className="tools-panel">
              <h2>Review the evidence</h2>
              <p className="tools-muted">
                Reviewed means you checked the assessment’s source and
                limitations. Confirm local needs separately. Reopening or
                dismissing an assessment keeps existing requests and their
                history.
              </p>
              <form className="relief-status-form" onSubmit={review}>
                <label>
                  Review decision
                  <select
                    value={target}
                    onChange={(event) =>
                      setTarget(event.target.value as Status)
                    }
                    disabled={busy}
                  >
                    {item.allowed_transitions.map((status) => (
                      <option key={status} value={status}>
                        {labels[status]}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Reason for review decision
                  <textarea
                    required
                    maxLength={500}
                    rows={3}
                    value={reason}
                    onChange={(event) => setReason(event.target.value)}
                    disabled={busy}
                  />
                </label>
                <button className="button primary" disabled={busy}>
                  {busy ? "Saving review…" : "Record review decision"}
                </button>
              </form>
            </section>
          )}
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>Local relief needs</h2>
              {canEdit && (
                <button
                  className="button primary"
                  disabled={busy || item.status !== "reviewed"}
                  onClick={() =>
                    onRequest({
                      id: item.id,
                      reference: assessment.external_reference,
                      locality: assessment.locality,
                      source_name: assessment.source_name,
                    })
                  }
                >
                  Create linked relief request
                </button>
              )}
            </div>
            <p className="tools-muted">
              {item.status === "reviewed"
                ? "Enter needs confirmed by a local source. Supply quantities are never inferred from imagery or population estimates."
                : "Review this assessment before linking a new relief request."}
            </p>
            <p className="incident-linked-count">
              {detail.linked_request_count} linked requests
              {detail.linked_request_count > 20
                ? " · Showing the latest 20"
                : ""}
            </p>
            {detail.linked_requests.length > 0 && (
              <ul className="incident-linked-list">
                {detail.linked_requests.map((request) => (
                  <li key={request.id}>
                    <strong>{request.reference}</strong>
                    <span>{request.status}</span>
                  </li>
                ))}
              </ul>
            )}
            <button className="button secondary" onClick={onRequests}>
              Open relief requests
            </button>
          </section>
          <section className="tools-panel">
            <h2>Incident review history</h2>
            <ol className="relief-history">
              {detail.events.map((event) => (
                <li key={event.id}>
                  <div className="relief-event-heading">
                    <strong>
                      {event.before_status === null
                        ? "Assessment received"
                        : `${labels[event.before_status]} → ${labels[event.after_status]}`}
                    </strong>
                    <span>
                      Version {event.version} · {when(event.created_at)}
                    </span>
                  </div>
                  <p>{event.reason}</p>
                  <small>{event.actor}</small>
                </li>
              ))}
            </ol>
            {detail.next_before_version !== null && (
              <button
                className="button secondary"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setError("");
                  try {
                    const older = await api<Detail>(
                      `/incidents/${item.id}?before_version=${detail.next_before_version}`,
                    );
                    if (older.incident.version !== item.version) {
                      setError(
                        "This incident changed. Refresh its details before loading older history.",
                      );
                      return;
                    }
                    setDetail({
                      ...detail,
                      events: [...detail.events, ...older.events],
                      next_before_version: older.next_before_version,
                    });
                  } catch (problem) {
                    setError((problem as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Load older review history
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}
