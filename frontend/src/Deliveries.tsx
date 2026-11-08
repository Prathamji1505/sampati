import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Plus, RefreshCw, Search } from "lucide-react";
import { api } from "./api";
import type { SessionState, Workspace, WorkspaceScope } from "./types";
import "./workspace-tools.css";
import "./relief-requests.css";
import "./deliveries.css";

type Action =
  | "approved"
  | "dispatched"
  | "delivery"
  | "return"
  | "cancelled"
  | "delivery_correction";
type Status =
  | "draft"
  | "approved"
  | "in_transit"
  | "partially_delivered"
  | "delivered"
  | "closed"
  | "cancelled";
type Shipment = {
  id: string;
  reference: string;
  issue_id: string;
  request_id: string;
  quantity: string;
  delivered: string;
  returned: string;
  unresolved: string;
  version: number;
  receiving_organisation: string;
  destination: string;
  note: string;
  status: Status;
  issue_reference: string;
  request_reference: string;
  request_status: string;
  item_code: string;
  item_name: string;
  unit: string;
  store_name: string;
  stock_version: number;
  allowed_actions: Action[];
  created_actor: string;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  dispatched_at: string | null;
};
type Evidence = {
  id: string;
  version: number;
  kind: Action | "created";
  reference: string | null;
  quantity: string | null;
  correctable_quantity: string | null;
  parent_reference: string | null;
  stock_reference: string | null;
  source_name: string;
  observed_at: string;
  received_at: string;
  actor: string;
  reason: string;
  after: {
    status: Status;
    delivered: string;
    returned: string;
    unresolved: string;
  };
};
type Detail = {
  shipment: Shipment;
  events: Evidence[];
  next_before_version: number | null;
};
type List = {
  items: Shipment[];
  total: number;
  page: number;
  total_pages: number;
  counts: Record<string, number>;
  can_edit: boolean;
};
type Issue = {
  id: string;
  reference: string;
  request_reference: string;
  item_name: string;
  unit: string;
  store_name: string;
  available: string;
  receiving_organisation: string;
  destination: string;
  compatible: boolean;
};
type Needs = {
  items: {
    id: string;
    reference: string;
    organisation: string;
    locality: string;
    quantity: string;
    delivered: string;
    remaining: string;
    allocated: string;
    unit: string;
  }[];
  total: number;
  page: number;
  total_pages: number;
};
const states: Record<Status, string> = {
  draft: "Draft",
  approved: "Approved",
  in_transit: "In transit",
  partially_delivered: "Partly delivered",
  delivered: "Delivered",
  closed: "Closed with returns",
  cancelled: "Cancelled",
};
const actions: Record<Action, string> = {
  approved: "Approve tracking record",
  dispatched: "Record dispatch evidence",
  delivery: "Confirm arrival",
  return: "Record undelivered return",
  cancelled: "Cancel unstarted shipment",
  delivery_correction: "Correct arrival quantity",
};
const help: Record<Action, string> = {
  approved:
    "Check the issue, receiver and destination. This approves the tracking record; transport operators retain dispatch authority.",
  dispatched:
    "Record evidence that the shipment actually left. Its source time must follow the approval source time. This form does not dispatch transport.",
  delivery:
    "Record a source-backed arrival quantity. Partial confirmations remain visible; quantities cannot exceed the shipment or request limit.",
  return:
    "Record undelivered supplies received back into the original store. Shipment history and inventory update in the same transaction.",
  cancelled:
    "Cancel this draft or approved record before dispatch. It frees the shipment assignment; issued stock is not automatically returned to a store.",
  delivery_correction:
    "Subtract an overstated quantity from an original arrival confirmation, with new source evidence. The original remains in history. This correction does not move inventory.",
};
const when = (value: string) => new Date(value).toLocaleString();
function localNow() {
  const date = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
const blankDraft = () => ({
  reference: "",
  issue_id: "",
  quantity: "",
  receiving_organisation: "",
  destination: "",
  note: "",
});
const blankAction = (kind: Action = "approved") => ({
  kind,
  reference: "",
  quantity: "",
  parent_event_id: "",
  source_name: "",
  observed_at: localNow(),
  reason: "",
});
const json = (body: unknown) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
function StatusLabel({ status }: { status: Status }) {
  return (
    <span className={`relief-status delivery-status-${status}`}>
      {states[status]}
    </span>
  );
}

export default function Deliveries({
  scope,
  session,
  workspace,
  onSignIn,
}: {
  scope: WorkspaceScope;
  session: SessionState | null;
  workspace: Workspace | null;
  onSignIn: () => void;
}) {
  const [mode, setMode] = useState<"list" | "new" | "detail" | "needs">("list");
  const [list, setList] = useState<List | null>(null);
  const [needs, setNeeds] = useState<Needs | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const [onlyRemaining, setOnlyRemaining] = useState(false);
  const [draft, setDraft] = useState(blankDraft);
  const [action, setAction] = useState(blankAction);
  const [key, setKey] = useState(() => crypto.randomUUID());
  const [issueQuery, setIssueQuery] = useState("");
  const [issues, setIssues] = useState<{ items: Issue[]; total: number }>({
    items: [],
    total: 0,
  });
  const [issuesLoading, setIssuesLoading] = useState(false);
  const epoch = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const isNeeds = mode === "needs";
  const canEdit =
    scope === "private" &&
    ["owner", "editor"].includes(session?.workspace?.role || "") &&
    list?.can_edit === true;
  async function load() {
    const current = ++epoch.current;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: search,
        page: String(page),
        status,
        only_remaining: String(onlyRemaining),
      });
      if (isNeeds) {
        const data = await api<Needs>(`/deliveries/needs?${params}`);
        if (current === epoch.current) {
          setNeeds(data);
          if (data.page !== page) setPage(data.page);
        }
      } else {
        const data = await api<List>(`/deliveries?${params}`);
        if (current === epoch.current) {
          setList(data);
          if (data.page !== page) setPage(data.page);
        }
      }
    } catch (problem) {
      if (current === epoch.current) setError((problem as Error).message);
    } finally {
      if (current === epoch.current) setLoading(false);
    }
  }
  useEffect(() => {
    const timer = setTimeout(() => setSearch(query), 250);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    void load();
    return () => {
      epoch.current++;
    };
  }, [search, status, page, onlyRemaining, isNeeds, workspace?.server_time]);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [mode, detail?.shipment.id]);
  useEffect(() => {
    if (mode !== "new") return;
    let alive = true;
    setIssuesLoading(true);
    const timer = setTimeout(async () => {
      try {
        const data = await api<{ items: Issue[]; total: number }>(
          `/deliveries/issues?q=${encodeURIComponent(issueQuery)}`,
        );
        if (alive) setIssues(data);
      } catch (problem) {
        if (alive) setError((problem as Error).message);
      } finally {
        if (alive) setIssuesLoading(false);
      }
    }, 250);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [mode, issueQuery]);
  function clear() {
    setError("");
    setNotice("");
  }
  async function open(id: string) {
    setBusy(true);
    setError("");
    try {
      const data = await api<Detail>(`/deliveries/${id}`);
      setDetail(data);
      setMode("detail");
      setAction(blankAction(data.shipment.allowed_actions[0] || "approved"));
      setKey(crypto.randomUUID());
    } catch (problem) {
      setError((problem as Error).message);
      throw problem;
    } finally {
      setBusy(false);
    }
  }
  function newDraft() {
    clear();
    setDraft(blankDraft());
    setKey(crypto.randomUUID());
    setIssueQuery("");
    setMode("new");
  }
  function chooseIssue(id: string) {
    const issue = issues.items.find((item) => item.id === id);
    setDraft({
      ...draft,
      issue_id: id,
      receiving_organisation: issue?.receiving_organisation || "",
      destination: issue?.destination || "",
    });
  }
  async function saveDraft(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    clear();
    try {
      const result = await api<{ shipment: Shipment; duplicate: boolean }>(
        "/deliveries",
        { method: "POST", ...json({ ...draft, submission_key: key }) },
      );
      await open(result.shipment.id);
      await load();
      setNotice(
        result.duplicate
          ? "This shipment draft was already saved. No assignment was added twice."
          : "Shipment draft saved. Review the tracking details before recording dispatch evidence.",
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveAction(event: React.FormEvent) {
    event.preventDefault();
    if (!detail) return;
    setBusy(true);
    clear();
    try {
      const date = new Date(action.observed_at);
      if (!Number.isFinite(date.getTime()))
        throw new Error("Choose a valid source date and time.");
      const quantified = ["delivery", "return", "delivery_correction"].includes(
        action.kind,
      );
      const result = await api<{ duplicate: boolean }>(
        `/deliveries/${detail.shipment.id}/events`,
        {
          method: "POST",
          ...json({
            ...action,
            quantity: quantified ? action.quantity : null,
            parent_event_id:
              action.kind === "delivery_correction"
                ? action.parent_event_id
                : null,
            expected_stock_version:
              action.kind === "return" ? detail.shipment.stock_version : null,
            expected_version: detail.shipment.version,
            submission_key: key,
            observed_at: date.toISOString(),
          }),
        },
      );
      await open(detail.shipment.id);
      await load();
      setNotice(
        result.duplicate
          ? "This evidence was already recorded. Delivery and stock quantities were not counted twice."
          : "Shipment evidence recorded. History retains its source, actor and resulting quantities.",
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function older() {
    if (!detail || detail.next_before_version === null) return;
    setBusy(true);
    setError("");
    try {
      const data = await api<Detail>(
        `/deliveries/${detail.shipment.id}?before_version=${detail.next_before_version}`,
      );
      if (data.shipment.version !== detail.shipment.version)
        throw new Error(
          "This shipment changed. Refresh its details before loading older history.",
        );
      setDetail({ ...data, events: [...detail.events, ...data.events] });
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const ship = detail?.shipment;
  const selectedIssue = issues.items.find((item) => item.id === draft.issue_id);
  const currentPage = isNeeds ? needs?.page : list?.page;
  const totalPages = isNeeds ? needs?.total_pages : list?.total_pages;
  const total = isNeeds ? needs?.total : list?.total;
  function switchView(needsView: boolean) {
    clear();
    setMode(needsView ? "needs" : "list");
    setQuery("");
    setSearch("");
    setPage(1);
  }
  return (
    <div className="workspace-tools delivery-workspace">
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
            Fictional shipment evidence · Read only. Recorded dispatch and
            source-confirmed arrivals remain separate.
          </p>
          {!session?.user && (
            <button className="button secondary" onClick={onSignIn}>
              Sign in to track deliveries
            </button>
          )}
        </div>
      )}
      <div className="tools-toolbar">
        {mode === "new" || mode === "detail" ? (
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => {
              switchView(false);
              void load();
            }}
          >
            <ArrowLeft size={15} />
            Back to shipments
          </button>
        ) : (
          <div className="tools-actions">
            <button
              className={`button ${!isNeeds ? "primary" : "secondary"}`}
              aria-pressed={!isNeeds}
              onClick={() => switchView(false)}
            >
              Shipments
            </button>
            <button
              className={`button ${isNeeds ? "primary" : "secondary"}`}
              aria-pressed={isNeeds}
              onClick={() => switchView(true)}
            >
              Request follow-up
            </button>
          </div>
        )}
        <div className="tools-actions">
          <button
            className="button secondary"
            disabled={busy || loading}
            onClick={() => {
              clear();
              void load();
            }}
          >
            <RefreshCw size={15} />
            Refresh deliveries
          </button>
          {mode === "list" && (
            <button
              className="button primary"
              disabled={!canEdit || busy}
              onClick={newDraft}
            >
              <Plus size={16} />
              New shipment
            </button>
          )}
        </div>
      </div>
      {(mode === "list" || isNeeds) && (
        <>
          <section
            className="register-panel"
            aria-label={
              isNeeds ? "Request delivery follow-up" : "Shipment register"
            }
            aria-busy={loading}
          >
            <div className="table-toolbar">
              <label className="search-field">
                <Search size={17} />
                <input
                  aria-label={
                    isNeeds ? "Search delivery needs" : "Search shipments"
                  }
                  value={query}
                  placeholder={
                    isNeeds
                      ? "Search request, organisation or locality…"
                      : "Search shipment, receiver or locality…"
                  }
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setPage(1);
                  }}
                />
              </label>
              {isNeeds ? (
                <label className="delivery-filter-check">
                  <input
                    type="checkbox"
                    checked={onlyRemaining}
                    onChange={(event) => {
                      setOnlyRemaining(event.target.checked);
                      setPage(1);
                    }}
                  />
                  Only needs awaiting delivery
                </label>
              ) : (
                <label className="select-field">
                  <select
                    aria-label="Filter shipment status"
                    value={status}
                    onChange={(event) => {
                      setStatus(event.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="all">All shipment states</option>
                    {Object.entries(states).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label} ({list?.counts[value] ?? 0})
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>
            {(isNeeds ? !needs : !list) ? (
              <p className="relief-empty" role="status">
                {loading
                  ? "Loading delivery records…"
                  : "Delivery records are unavailable. Refresh when the server is ready."}
              </p>
            ) : (
                isNeeds ? needs?.items.length === 0 : list?.items.length === 0
              ) ? (
              <div className="relief-empty">
                <h2>
                  {isNeeds
                    ? "No reviewed requests match this view."
                    : "Your shipment register starts here."}
                </h2>
                <p>
                  {isNeeds
                    ? "Review a request to follow its source-confirmed deliveries. Cancelled or unreviewed requests remain in the request register."
                    : "Start with an inventory issue against a reviewed relief request, then create a shipment draft. Issuing supplies does not confirm their arrival."}
                </p>
              </div>
            ) : (
              <>
                <p className="relief-scroll-hint">
                  Scroll the table sideways for quantities, states and details.
                </p>
                <div className="table-scroll">
                  {isNeeds ? (
                    <table className="tools-table delivery-table">
                      <thead>
                        <tr>
                          <th scope="col">Reviewed request</th>
                          <th scope="col">Organisation / locality</th>
                          <th scope="col">Requested</th>
                          <th scope="col">Confirmed delivered</th>
                          <th scope="col">Still needed</th>
                          <th scope="col">Assigned, incl. delivered</th>
                        </tr>
                      </thead>
                      <tbody>
                        {needs?.items.map((need) => (
                          <tr key={need.id}>
                            <td>
                              <strong>{need.reference}</strong>
                            </td>
                            <td>
                              {need.organisation}
                              <span className="relief-secondary">
                                {need.locality}
                              </span>
                            </td>
                            <td>
                              {need.quantity} {need.unit}
                            </td>
                            <td>
                              {need.delivered} {need.unit}
                            </td>
                            <td>
                              {need.remaining} {need.unit}
                            </td>
                            <td>
                              {need.allocated} {need.unit}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <table className="tools-table delivery-table">
                      <thead>
                        <tr>
                          <th scope="col">Shipment / request</th>
                          <th scope="col">Receiver / destination</th>
                          <th scope="col">Planned quantity</th>
                          <th scope="col">Confirmed / returned</th>
                          <th scope="col">State</th>
                          <th scope="col">History</th>
                        </tr>
                      </thead>
                      <tbody>
                        {list?.items.map((row) => (
                          <tr key={row.id}>
                            <td>
                              <strong>{row.reference}</strong>
                              <span className="relief-secondary">
                                {row.request_reference}
                              </span>
                              <small>{row.item_name}</small>
                            </td>
                            <td>
                              {row.receiving_organisation}
                              <span className="relief-secondary">
                                {row.destination}
                              </span>
                            </td>
                            <td>
                              {row.quantity} {row.unit}
                              <span className="relief-secondary">
                                {row.unresolved} unresolved
                              </span>
                            </td>
                            <td>
                              {row.delivered} delivered
                              <span className="relief-secondary">
                                {row.returned} returned ({row.unit})
                              </span>
                            </td>
                            <td>
                              <StatusLabel status={row.status} />
                            </td>
                            <td>
                              <button
                                className="button secondary"
                                disabled={busy}
                                aria-label={`Open ${row.reference} shipment`}
                                onClick={() => {
                                  clear();
                                  void open(row.id).catch(() => {});
                                }}
                              >
                                Open shipment
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </>
            )}
            <div className="table-footer relief-pagination">
              <span>
                {total ?? 0} matching {isNeeds ? "requests" : "shipments"} · 20
                per page
              </span>
              <div className="tools-actions">
                <button
                  className="button secondary"
                  disabled={loading || !currentPage || currentPage <= 1}
                  onClick={() => setPage((currentPage || 1) - 1)}
                >
                  Previous delivery records
                </button>
                <span>
                  Page {currentPage ?? 1} of {totalPages ?? 1}
                </span>
                <button
                  className="button secondary"
                  disabled={
                    loading ||
                    !currentPage ||
                    !totalPages ||
                    currentPage >= totalPages
                  }
                  onClick={() => setPage((currentPage || 1) + 1)}
                >
                  Next delivery records
                </button>
              </div>
            </div>
          </section>
          <p className="tools-muted">
            {isNeeds
              ? "Still needed = requested − net source-confirmed arrivals. Returns and corrected confirmations remain traceable. Units are never combined. This view includes currently reviewed requests."
              : "Draft → Approved → In transit. Arrival evidence determines partial or full delivery; undelivered returns resolve the remainder. Approval concerns this tracking record, and does not grant transport or flight clearance."}
          </p>
        </>
      )}
      {mode === "new" && (
        <section className="tools-panel">
          <h2 ref={heading} tabIndex={-1}>
            Create a shipment draft
          </h2>
          <p className="tools-muted">
            Choose an existing inventory issue, then record receiver and
            destination details. The draft assigns part of that issue for
            tracking. It does not move stock or dispatch transport. Details stay
            fixed; cancel an unstarted draft and create another reference to
            correct them.
          </p>
          <form className="relief-form" onSubmit={saveDraft}>
            <label>
              Shipment reference
              <input
                required
                maxLength={64}
                value={draft.reference}
                disabled={busy}
                onChange={(event) =>
                  setDraft({ ...draft, reference: event.target.value })
                }
              />
            </label>
            <label>
              Find an issued supply record
              <input
                value={issueQuery}
                placeholder="Search issue or request reference"
                disabled={busy}
                onChange={(event) => {
                  setIssueQuery(event.target.value);
                  setDraft({ ...draft, issue_id: "" });
                }}
              />
            </label>
            <label className="relief-full-field">
              Original inventory issue
              <select
                required
                value={draft.issue_id}
                disabled={busy || issuesLoading}
                onChange={(event) => chooseIssue(event.target.value)}
              >
                <option value="">
                  {issuesLoading
                    ? "Loading inventory issues…"
                    : "Choose an inventory issue"}
                </option>
                {issues.items.map((issue) => (
                  <option
                    key={issue.id}
                    value={issue.id}
                    disabled={!issue.compatible || Number(issue.available) <= 0}
                  >
                    {issue.reference} · {issue.request_reference} ·{" "}
                    {issue.available} {issue.unit} unassigned
                  </option>
                ))}
              </select>
            </label>
            <p className="tools-muted relief-full-field delivery-help">
              Showing up to 20 of {issues.total} issues against currently
              reviewed requests. Search the exact reference for an older issue.{" "}
              {selectedIssue &&
                `${selectedIssue.item_name} · ${selectedIssue.store_name} · ${selectedIssue.available} ${selectedIssue.unit} unreturned and unassigned.`}
            </p>
            <label>
              Shipment quantity{selectedIssue ? ` (${selectedIssue.unit})` : ""}
              <input
                required
                type="number"
                min="0.001"
                max="1000000000"
                step="0.001"
                value={draft.quantity}
                disabled={busy}
                onChange={(event) =>
                  setDraft({ ...draft, quantity: event.target.value })
                }
              />
            </label>
            <label>
              Receiving organisation
              <input
                required
                minLength={2}
                maxLength={120}
                value={draft.receiving_organisation}
                disabled={busy}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    receiving_organisation: event.target.value,
                  })
                }
              />
            </label>
            <label className="relief-full-field">
              Delivery destination
              <input
                required
                minLength={2}
                maxLength={160}
                value={draft.destination}
                disabled={busy}
                onChange={(event) =>
                  setDraft({ ...draft, destination: event.target.value })
                }
              />
            </label>
            <label className="relief-full-field">
              Shipment note (optional)
              <textarea
                maxLength={1000}
                rows={3}
                value={draft.note}
                disabled={busy}
                onChange={(event) =>
                  setDraft({ ...draft, note: event.target.value })
                }
              />
            </label>
            <div className="relief-form-actions">
              <button
                className="button primary"
                disabled={busy || !canEdit || issuesLoading}
              >
                {busy ? "Saving shipment…" : "Save shipment draft"}
              </button>
            </div>
          </form>
        </section>
      )}
      {mode === "detail" && detail && ship && (
        <>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2 ref={heading} tabIndex={-1}>
                {ship.reference}
              </h2>
              <StatusLabel status={ship.status} />
            </div>
            <p className="tools-muted">
              {ship.item_name} · All quantities in <strong>{ship.unit}</strong>{" "}
              · Version {ship.version}
            </p>
            <dl className="delivery-balances">
              {[
                ["Shipment quantity", ship.quantity],
                ["Confirmed delivered", ship.delivered],
                ["Returned to store", ship.returned],
                ["Unresolved", ship.unresolved],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>
                    {value} {ship.unit}
                  </dd>
                </div>
              ))}
            </dl>
            <dl className="relief-details">
              <div>
                <dt>Original inventory issue</dt>
                <dd>
                  {ship.issue_reference}
                  <small>
                    {ship.store_name} · {ship.item_code}
                  </small>
                </dd>
              </div>
              <div>
                <dt>Relief request</dt>
                <dd>
                  {ship.request_reference}
                  <small>Current request state: {ship.request_status}</small>
                </dd>
              </div>
              <div>
                <dt>Receiving organisation</dt>
                <dd>{ship.receiving_organisation}</dd>
              </div>
              <div>
                <dt>Destination</dt>
                <dd>{ship.destination}</dd>
              </div>
              <div>
                <dt>Recorded by</dt>
                <dd>
                  {ship.created_actor}
                  <small>{when(ship.created_at)}</small>
                </dd>
              </div>
              <div>
                <dt>Dispatch evidence time</dt>
                <dd>
                  {ship.dispatched_at
                    ? when(ship.dispatched_at)
                    : "Not recorded"}
                </dd>
              </div>
              {ship.note && (
                <div className="relief-full-field">
                  <dt>Shipment note</dt>
                  <dd>{ship.note}</dd>
                </div>
              )}
            </dl>
            <p className="tools-muted">
              Confirmed arrivals and undelivered returns resolve this shipment
              separately. A request changing state does not erase actual
              delivery evidence.
            </p>
            <div className="tools-actions delivery-detail-actions">
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => {
                  clear();
                  void open(ship.id).catch(() => {});
                }}
              >
                <RefreshCw size={15} />
                Refresh shipment details
              </button>
            </div>
          </section>
          {canEdit && ship.allowed_actions.length > 0 && (
            <section className="tools-panel">
              <h2>Record shipment evidence</h2>
              <form className="relief-form" onSubmit={saveAction}>
                <label>
                  Shipment action
                  <select
                    value={action.kind}
                    disabled={busy}
                    onChange={(event) =>
                      setAction({
                        ...blankAction(event.target.value as Action),
                        source_name: action.source_name,
                      })
                    }
                  >
                    {ship.allowed_actions.map((kind) => (
                      <option key={kind} value={kind}>
                        {actions[kind]}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Evidence reference
                  <input
                    required
                    maxLength={64}
                    value={action.reference}
                    disabled={busy}
                    onChange={(event) =>
                      setAction({ ...action, reference: event.target.value })
                    }
                  />
                </label>
                <p className="tools-muted relief-full-field delivery-help">
                  {help[action.kind]}
                </p>
                {action.kind === "delivery_correction" && (
                  <>
                    <label className="relief-full-field">
                      Original arrival confirmation
                      <select
                        required
                        value={action.parent_event_id}
                        disabled={busy}
                        onChange={(event) =>
                          setAction({
                            ...action,
                            parent_event_id: event.target.value,
                          })
                        }
                      >
                        <option value="">Choose a recorded arrival</option>
                        {detail.events
                          .filter(
                            (event) =>
                              event.kind === "delivery" &&
                              event.correctable_quantity !== null &&
                              Number(event.correctable_quantity) > 0,
                          )
                          .map((event) => (
                            <option key={event.id} value={event.id}>
                              {event.reference} · {event.correctable_quantity}{" "}
                              {ship.unit} uncorrected
                            </option>
                          ))}
                      </select>
                    </label>
                    <p className="tools-muted relief-full-field delivery-help">
                      Choices come from loaded history. Load older shipment
                      history to find an earlier confirmation.
                    </p>
                  </>
                )}
                {["delivery", "return", "delivery_correction"].includes(
                  action.kind,
                ) && (
                  <label>
                    Evidence quantity ({ship.unit})
                    <input
                      required
                      type="number"
                      min="0.001"
                      max="1000000000"
                      step="0.001"
                      value={action.quantity}
                      disabled={busy}
                      onChange={(event) =>
                        setAction({ ...action, quantity: event.target.value })
                      }
                    />
                  </label>
                )}
                <label>
                  Source time (your local time)
                  <input
                    required
                    type="datetime-local"
                    step="1"
                    value={action.observed_at}
                    disabled={busy}
                    onChange={(event) =>
                      setAction({ ...action, observed_at: event.target.value })
                    }
                  />
                </label>
                <label className="relief-full-field">
                  Evidence source / organisation
                  <input
                    required
                    minLength={2}
                    maxLength={120}
                    value={action.source_name}
                    disabled={busy}
                    onChange={(event) =>
                      setAction({ ...action, source_name: event.target.value })
                    }
                  />
                </label>
                <label className="relief-full-field">
                  Evidence note / reason
                  <textarea
                    required
                    rows={3}
                    maxLength={500}
                    value={action.reason}
                    disabled={busy}
                    onChange={(event) =>
                      setAction({ ...action, reason: event.target.value })
                    }
                  />
                </label>
                <div className="relief-form-actions">
                  <button className="button primary" disabled={busy}>
                    {busy ? "Recording evidence…" : "Save shipment evidence"}
                  </button>
                </div>
              </form>
            </section>
          )}
          <section className="tools-panel">
            <h2>Shipment history</h2>
            <ol className="relief-history">
              {detail.events.map((event) => (
                <li key={event.id}>
                  <div className="relief-event-heading">
                    <strong>
                      {event.kind === "created"
                        ? "Shipment draft recorded"
                        : actions[event.kind]}
                      {event.quantity !== null
                        ? ` · ${event.quantity} ${ship.unit}`
                        : ""}
                    </strong>
                    <span>
                      {event.reference || "Original issue source"} · Version{" "}
                      {event.version}
                    </span>
                  </div>
                  <p>{event.reason}</p>
                  <small>
                    {event.actor}
                    <br />
                    Source: {event.source_name} · {when(event.observed_at)}
                    <br />
                    Recorded {when(event.received_at)}
                  </small>
                  {event.parent_reference && (
                    <p className="tools-muted">
                      Corrects arrival: {event.parent_reference}
                    </p>
                  )}
                  {event.stock_reference && (
                    <p className="tools-muted">
                      Linked inventory return: {event.stock_reference}
                    </p>
                  )}
                  <p className="tools-muted">
                    After event: {states[event.after.status]} ·{" "}
                    {event.after.delivered} delivered · {event.after.returned}{" "}
                    returned · {event.after.unresolved} unresolved ({ship.unit})
                  </p>
                  {event.correctable_quantity !== null && (
                    <p className="tools-muted">
                      Currently {event.correctable_quantity} {ship.unit}{" "}
                      uncorrected from this confirmation.
                    </p>
                  )}
                </li>
              ))}
            </ol>
            {detail.next_before_version !== null && (
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => void older()}
              >
                Load older shipment history
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}
