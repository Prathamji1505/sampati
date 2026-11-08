import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Check,
  ChevronRight,
  Plus,
  RefreshCw,
  Search,
} from "lucide-react";
import { api } from "./api";
import type { SessionState, Workspace, WorkspaceScope } from "./types";
import type { IncidentDraft } from "./Incidents";
import "./workspace-tools.css";
import "./relief-requests.css";

type Status = "draft" | "submitted" | "reviewed" | "cancelled";
type ReliefRequest = {
  id: string;
  incident_id: string | null;
  incident_reference: string | null;
  intake_id: string | null;
  reference: string;
  requesting_organisation: string;
  locality: string;
  category: string;
  item_name: string;
  quantity: string;
  unit: string;
  needed_by: string;
  needed_by_raw: string;
  source_name: string;
  note: string;
  status: Status;
  version: number;
  created_actor: string;
  created_at: string;
  updated_at: string;
  past_deadline: boolean;
  allowed_transitions: Status[];
};
type Audit = {
  id: string;
  version: number;
  action: string;
  actor: string;
  created_at: string;
  reason: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown>;
};
type Detail = {
  request: ReliefRequest;
  events: Audit[];
  next_before_version: number | null;
};
type RequestList = {
  items: ReliefRequest[];
  total: number;
  counts: Record<string, number>;
  page: number;
  page_size: number;
  total_pages: number;
  server_time: string;
  can_edit: boolean;
  is_demo: boolean;
};
type FormFields = {
  reference: string;
  requesting_organisation: string;
  locality: string;
  category: string;
  item_name: string;
  quantity: string;
  unit: string;
  needed_by: string;
  source_name: string;
  note: string;
};
const statusLabels: Record<Status, string> = {
  draft: "Draft",
  submitted: "Submitted",
  reviewed: "Reviewed",
  cancelled: "Cancelled",
};
const categoryLabels: Record<string, string> = {
  food: "Food",
  water: "Water",
  medicine: "Medical supplies",
  shelter: "Shelter supplies",
  other: "Other supplies",
};
const unitLabels: Record<string, string> = {
  items: "Items",
  boxes: "Boxes",
  kits: "Kits",
  litres: "Litres",
  kilograms: "Kilograms",
  packs: "Packs",
};
const fieldLabels: Record<string, string> = {
  reference: "Request reference",
  requesting_organisation: "Requesting organisation",
  locality: "Locality",
  category: "Supply category",
  item_name: "Supply description",
  quantity: "Quantity",
  unit: "Unit",
  needed_by: "Needed by",
  source_name: "Source or report name",
  note: "Note",
  status: "Status",
};
const when = (value: string) => new Date(value).toLocaleString();
function localInputTime(value: string | number) {
  const date = new Date(value);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
function blankForm(): FormFields {
  return {
    reference: "",
    requesting_organisation: "",
    locality: "",
    category: "food",
    item_name: "",
    quantity: "",
    unit: "boxes",
    needed_by: localInputTime(
      Math.floor((Date.now() + 86400000) / 60000) * 60000,
    ),
    source_name: "",
    note: "",
  };
}
const json = (body: unknown) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
function StatusLabel({ value }: { value: Status }) {
  return (
    <span className={`relief-status relief-status-${value}`}>
      {statusLabels[value]}
    </span>
  );
}
function auditValue(field: string, value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  if (field === "needed_by") return when(String(value));
  if (field === "status") return statusLabels[value as Status] || String(value);
  if (field === "category")
    return categoryLabels[String(value)] || String(value);
  if (field === "unit") return unitLabels[String(value)] || String(value);
  return String(value);
}

export default function ReliefRequests({
  scope,
  session,
  workspace,
  onSignIn,
  incidentDraft,
  onIncidentDraftUsed,
  initialRequestId,
  onInitialRequestUsed,
  onIntake,
}: {
  scope: WorkspaceScope;
  session: SessionState | null;
  workspace: Workspace | null;
  onSignIn: () => void;
  initialRequestId?: string | null;
  onInitialRequestUsed?: () => void;
  onIntake?: (id: string) => void;
  incidentDraft?: IncidentDraft | null;
  onIncidentDraftUsed?: () => void;
}) {
  const [list, setList] = useState<RequestList | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<"list" | "new" | "detail" | "edit">("list");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [form, setForm] = useState<FormFields>(blankForm);
  const [submissionKey, setSubmissionKey] = useState(() => crypto.randomUUID());
  const [linkedIncident, setLinkedIncident] = useState<IncidentDraft | null>(
    null,
  );
  const [editReason, setEditReason] = useState("");
  const [targetStatus, setTargetStatus] = useState<Status>("submitted");
  const [statusReason, setStatusReason] = useState("");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(1);
  const listEpoch = useRef(0);
  const canEdit =
    scope === "private" &&
    ["owner", "editor"].includes(session?.workspace?.role || "") &&
    list?.can_edit === true;

  useEffect(() => {
    if (!incidentDraft || !canEdit) return;
    setLinkedIncident(incidentDraft);
    setForm({
      ...blankForm(),
      locality: incidentDraft.locality,
      source_name: incidentDraft.source_name,
    });
    setSubmissionKey(crypto.randomUUID());
    setDetail(null);
    setError("");
    setNotice("");
    setMode("new");
    onIncidentDraftUsed?.();
  }, [incidentDraft, canEdit]);

  async function loadList() {
    const current = ++listEpoch.current;
    setListLoading(true);
    try {
      const data = await api<RequestList>(
        `/relief-requests?${new URLSearchParams({ q: search, status, category, page: String(page) })}`,
      );
      if (listEpoch.current === current) {
        setList(data);
        setListError("");
        if (data.page !== page) setPage(data.page);
      }
    } catch (problem) {
      if (listEpoch.current === current)
        setListError((problem as Error).message);
    } finally {
      if (listEpoch.current === current) setListLoading(false);
    }
  }
  useEffect(() => {
    const timer = setTimeout(() => setSearch(query), 250);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    void loadList();
    return () => {
      listEpoch.current += 1;
    };
  }, [scope, search, status, category, page, workspace?.server_time]);
  useEffect(() => {
    setTargetStatus(detail?.request.allowed_transitions[0] || "submitted");
    setStatusReason("");
  }, [detail?.request.id, detail?.request.version]);

  async function fetchDetail(id: string) {
    const next = await api<Detail>(`/relief-requests/${id}`);
    setDetail(next);
    setMode("detail");
  }
  async function openDetail(id: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fetchDetail(id);
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (initialRequestId) {
      void openDetail(initialRequestId);
      onInitialRequestUsed?.();
    }
  }, [initialRequestId]);
  function openNew() {
    setLinkedIncident(null);
    setForm(blankForm());
    setSubmissionKey(crypto.randomUUID());
    setDetail(null);
    setEditReason("");
    setError("");
    setNotice("");
    setMode("new");
  }
  function openEdit() {
    if (!detail) return;
    const item = detail.request;
    setForm({
      reference: item.reference,
      requesting_organisation: item.requesting_organisation,
      locality: item.locality,
      category: item.category,
      item_name: item.item_name,
      quantity: item.quantity,
      unit: item.unit,
      needed_by: localInputTime(item.needed_by),
      source_name: item.source_name,
      note: item.note,
    });
    setEditReason("");
    setError("");
    setNotice("");
    setMode("edit");
  }
  function back() {
    setMode("list");
    setError("");
    void loadList();
  }
  function fillExample() {
    setForm({
      ...blankForm(),
      reference: `EXAMPLE-${Date.now().toString(36).toUpperCase()}`,
      requesting_organisation: "Fictional Community Relief Desk",
      locality: "Fictional River Ward",
      category: "water",
      item_name: "Drinking-water packs",
      quantity: "50",
      unit: "packs",
      source_name: "Fictional community desk register",
      note: "Fictional learning example; no real request or delivery.",
      ...(linkedIncident
        ? {
            locality: linkedIncident.locality,
            source_name: linkedIncident.source_name,
          }
        : {}),
    });
  }
  async function saveForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const date = new Date(form.needed_by);
      if (!Number.isFinite(date.getTime()))
        throw new Error("Choose a valid needed-by date and time.");
      const old = mode === "edit" ? detail?.request : null;
      const { reference, ...fields } = form;
      const needed_by =
        old && date.getTime() === new Date(old.needed_by).getTime()
          ? old.needed_by_raw
          : date.toISOString();
      const result = old
        ? await api<{ request: ReliefRequest; unchanged: boolean }>(
            `/relief-requests/${old.id}`,
            {
              method: "PATCH",
              ...json({
                ...fields,
                needed_by,
                expected_version: old.version,
                reason: editReason,
              }),
            },
          )
        : await api<{ request: ReliefRequest; duplicate: boolean }>(
            "/relief-requests",
            {
              method: "POST",
              ...json({
                ...fields,
                reference,
                needed_by,
                submission_key: submissionKey,
                incident_id: linkedIncident?.id ?? null,
              }),
            },
          );
      await fetchDetail(result.request.id);
      await loadList();
      setNotice(
        old
          ? "Request details saved. The history records any changes."
          : "Draft saved. Submit it when the details are ready for review.",
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function updateStatus(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api<{ request: ReliefRequest }>(
        `/relief-requests/${detail.request.id}/status`,
        {
          method: "POST",
          ...json({
            status: targetStatus,
            expected_version: detail.request.version,
            reason: statusReason,
          }),
        },
      );
      await fetchDetail(result.request.id);
      await loadList();
      setNotice(`Status updated to ${statusLabels[result.request.status]}.`);
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function olderEvents() {
    if (!detail?.next_before_version) return;
    setBusy(true);
    setError("");
    try {
      const older = await api<Detail>(
        `/relief-requests/${detail.request.id}?before_version=${detail.next_before_version}`,
      );
      if (older.request.version !== detail.request.version)
        setNotice(
          "A newer request version exists. Refresh details before making changes.",
        );
      setDetail({
        ...detail,
        events: [
          ...detail.events,
          ...older.events.filter(
            (event) => !detail.events.some((old) => old.id === event.id),
          ),
        ],
        next_before_version: older.next_before_version,
      });
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const item = detail?.request;
  function field(
    name: keyof FormFields,
    label: string,
    options: {
      max?: number;
      min?: number;
      type?: string;
      placeholder?: string;
    } = {},
  ) {
    return (
      <label>
        {label}
        <input
          name={name}
          value={form[name]}
          onChange={(event) => setForm({ ...form, [name]: event.target.value })}
          required={name !== "note"}
          maxLength={options.max}
          minLength={options.min}
          type={options.type || "text"}
          placeholder={options.placeholder}
          disabled={busy}
          readOnly={name === "reference" && mode === "edit"}
          autoComplete="off"
        />
      </label>
    );
  }

  return (
    <div className="workspace-tools relief-workspace">
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
      {scope === "demo" && (
        <div className="relief-demo-note">
          <p>
            Fictional examples · Read only.{" "}
            {session?.user
              ? "Select your organisation to record and review requests."
              : "Sign in to record and review your organisation’s requests."}
          </p>
          {!session?.user && (
            <button className="button secondary" onClick={onSignIn}>
              Sign in to create requests
            </button>
          )}
        </div>
      )}
      {mode === "list" && (
        <>
          <div className="tools-toolbar">
            <span>
              {listLoading
                ? "Loading requests…"
                : `${list?.counts.all ?? 0} requests in this workspace`}
            </span>
            <div className="tools-actions">
              <button
                className="button secondary"
                disabled={busy || listLoading}
                onClick={() => void loadList()}
              >
                <RefreshCw size={15} />
                Refresh requests
              </button>
              <button
                className="button primary"
                disabled={!canEdit || busy}
                onClick={openNew}
              >
                <Plus size={16} />
                New request
              </button>
            </div>
          </div>
          {listError && (
            <div className="message error" role="alert">
              {listError}
            </div>
          )}
          <section
            className="register-panel"
            aria-label="Relief request register"
            aria-busy={listLoading}
          >
            <div
              className="status-tabs relief-tabs"
              role="group"
              aria-label="Filter relief requests by status"
            >
              {(
                ["all", "draft", "submitted", "reviewed", "cancelled"] as const
              ).map((value) => (
                <button
                  key={value}
                  className={status === value ? "selected" : ""}
                  aria-pressed={status === value}
                  onClick={() => {
                    setStatus(value);
                    setPage(1);
                  }}
                >
                  {value === "all" ? "All requests" : statusLabels[value]}
                  <span>{list?.counts[value] ?? 0}</span>
                </button>
              ))}
            </div>
            <div className="table-toolbar">
              <label className="search-field">
                <Search size={17} />
                <input
                  aria-label="Search relief requests"
                  placeholder="Search reference, supplies or locality…"
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setPage(1);
                  }}
                />
              </label>
              <label className="select-field">
                <select
                  aria-label="Filter relief supply category"
                  value={category}
                  onChange={(event) => {
                    setCategory(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="all">All supply categories</option>
                  {Object.entries(categoryLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {!list && listLoading ? (
              <p className="relief-empty" role="status">
                Loading the request register…
              </p>
            ) : !list ? (
              <div className="relief-empty">
                <h2>Requests are unavailable.</h2>
                <p>Use Refresh requests when the local server is ready.</p>
              </div>
            ) : list.items.length === 0 ? (
              <div className="relief-empty">
                <h2>
                  {list.counts.all
                    ? "No requests match these filters."
                    : "Your relief request register starts here."}
                </h2>
                <p>
                  {list.counts.all
                    ? "Change the search, status or supply category to see more requests."
                    : canEdit
                      ? "Record a fictional supply need, then submit it for review."
                      : "An owner or editor can record the first request."}
                </p>
                {list.counts.all > 0 ? (
                  <button
                    className="button secondary"
                    onClick={() => {
                      setQuery("");
                      setSearch("");
                      setStatus("all");
                      setCategory("all");
                      setPage(1);
                    }}
                  >
                    Clear request filters
                  </button>
                ) : (
                  canEdit && (
                    <button className="button primary" onClick={openNew}>
                      Create first request
                    </button>
                  )
                )}
              </div>
            ) : (
              <>
                <p className="relief-scroll-hint">
                  Scroll the table sideways for more request details.
                </p>
                <div className="table-scroll">
                  <table className="tools-table relief-table">
                    <thead>
                      <tr>
                        <th>Request</th>
                        <th>Organisation and locality</th>
                        <th>Quantity</th>
                        <th>Needed by</th>
                        <th>Status</th>
                        <th>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {list.items.map((request) => (
                        <tr key={request.id}>
                          <td>
                            <strong>{request.reference}</strong>
                            <span className="relief-secondary">
                              {request.item_name}
                            </span>
                            <small>{categoryLabels[request.category]}</small>
                          </td>
                          <td>
                            {request.requesting_organisation}
                            <span className="relief-secondary">
                              {request.locality}
                            </span>
                          </td>
                          <td className="relief-quantity">
                            {request.quantity} {request.unit}
                          </td>
                          <td>
                            <time dateTime={request.needed_by}>
                              {when(request.needed_by)}
                            </time>
                            {request.past_deadline && (
                              <span className="relief-past-due">
                                Past deadline
                              </span>
                            )}
                          </td>
                          <td>
                            <StatusLabel value={request.status} />
                          </td>
                          <td>
                            <button
                              className="button secondary"
                              disabled={busy}
                              aria-label={`Open ${request.reference} request`}
                              onClick={() => void openDetail(request.id)}
                            >
                              View
                              <ChevronRight size={14} />
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
              <span>{list?.total ?? 0} matching requests · 20 per page</span>
              <div className="tools-actions">
                <button
                  className="button secondary"
                  disabled={listLoading || !list || list.page <= 1}
                  onClick={() => setPage((list?.page || 1) - 1)}
                >
                  Previous requests
                </button>
                <span>
                  Page {list?.page ?? 1} of {list?.total_pages ?? 1}
                </span>
                <button
                  className="button secondary"
                  disabled={
                    listLoading || !list || list.page >= list.total_pages
                  }
                  onClick={() => setPage((list?.page || 1) + 1)}
                >
                  Next requests
                </button>
              </div>
            </div>
          </section>
          <p className="tools-muted">
            Draft → Submitted → Reviewed. A review checks the request details;
            it does not confirm stock, dispatch or delivery. Quantities retain
            their stated units.
          </p>
        </>
      )}

      {(mode === "new" || mode === "edit") && (
        <>
          <div className="tools-toolbar">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => (mode === "edit" ? setMode("detail") : back())}
            >
              <ArrowLeft size={15} />
              {mode === "edit" ? "Back to request" : "Back to requests"}
            </button>
            <span>
              {mode === "edit"
                ? `Editing draft · Version ${item?.version}`
                : "New request · Not saved yet"}
            </span>
          </div>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>
                {mode === "edit"
                  ? "Correct request details"
                  : "Record a relief request"}
              </h2>
              {mode === "new" && (
                <button
                  type="button"
                  className="button secondary"
                  disabled={busy}
                  onClick={fillExample}
                >
                  Use fictional example
                </button>
              )}
            </div>
            <p className="tools-muted">
              Use fictional organisation and supply details in this prototype.
              Record quantities in their original units. The request reference
              stays fixed after creation.
            </p>
            <form className="relief-form" onSubmit={saveForm}>
              {mode === "new" && linkedIncident && (
                <p className="tools-muted relief-full-field">
                  Linked incident: <strong>{linkedIncident.reference}</strong>.
                  Confirm the local source and supply quantities before saving.
                  The assessment does not establish these needs.
                </p>
              )}
              {field("reference", "Request reference", {
                max: 64,
                placeholder: "For example, REL-2026-001",
              })}
              {field("requesting_organisation", "Requesting organisation", {
                min: 2,
                max: 120,
              })}
              {field("locality", "Delivery locality", { min: 2, max: 160 })}
              <label>
                Supply category
                <select
                  value={form.category}
                  onChange={(event) =>
                    setForm({ ...form, category: event.target.value })
                  }
                  disabled={busy}
                >
                  {Object.entries(categoryLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {field("item_name", "Supply description", {
                min: 2,
                max: 160,
                placeholder: "For example, drinking-water packs",
              })}
              <label>
                Quantity
                <input
                  name="quantity"
                  type="number"
                  min="0.001"
                  max="1000000000"
                  step="0.001"
                  required
                  value={form.quantity}
                  onChange={(event) =>
                    setForm({ ...form, quantity: event.target.value })
                  }
                  disabled={busy}
                />
              </label>
              <label>
                Unit
                <select
                  value={form.unit}
                  onChange={(event) =>
                    setForm({ ...form, unit: event.target.value })
                  }
                  disabled={busy}
                >
                  {Object.entries(unitLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Needed by (your local time)
                <input
                  name="needed_by"
                  type="datetime-local"
                  step="1"
                  required
                  value={form.needed_by}
                  onChange={(event) =>
                    setForm({ ...form, needed_by: event.target.value })
                  }
                  disabled={busy}
                />
              </label>
              {field("source_name", "Source or report name", {
                min: 2,
                max: 120,
                placeholder: "For example, community desk register",
              })}
              <label className="relief-full-field">
                Request note (optional)
                <textarea
                  value={form.note}
                  onChange={(event) =>
                    setForm({ ...form, note: event.target.value })
                  }
                  maxLength={1000}
                  rows={3}
                  disabled={busy}
                />
              </label>
              {mode === "edit" && (
                <label className="relief-full-field">
                  Reason for correction
                  <textarea
                    value={editReason}
                    onChange={(event) => setEditReason(event.target.value)}
                    maxLength={500}
                    minLength={1}
                    required
                    rows={2}
                    disabled={busy}
                  />
                </label>
              )}
              <div className="relief-form-actions">
                <button className="button primary" disabled={busy || !canEdit}>
                  {busy
                    ? "Saving request…"
                    : mode === "edit"
                      ? "Save correction"
                      : "Save draft"}
                </button>
                <button
                  type="button"
                  className="button secondary"
                  disabled={busy}
                  onClick={() => (mode === "edit" ? setMode("detail") : back())}
                >
                  Cancel editing
                </button>
              </div>
            </form>
          </section>
        </>
      )}

      {mode === "detail" && item && detail && (
        <>
          {item.intake_id && onIntake && (
            <div className="relief-demo-note">
              <p>
                This request was created from a saved relief file. Inspect its
                source text, validation and intake decision.
              </p>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => onIntake(item.intake_id!)}
              >
                View intake evidence
              </button>
            </div>
          )}
          {item.incident_reference && (
            <p className="tools-muted">
              Linked incident: <strong>{item.incident_reference}</strong>.
              Request quantities are recorded independently of the assessment.
              Recheck the incident for subsequent review changes.
            </p>
          )}
          <div className="tools-toolbar">
            <button className="button secondary" disabled={busy} onClick={back}>
              <ArrowLeft size={15} />
              Back to requests
            </button>
            <div className="tools-actions">
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => void openDetail(item.id)}
              >
                <RefreshCw size={15} />
                Refresh details
              </button>
              {canEdit && item.status === "draft" && (
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={openEdit}
                >
                  Edit draft
                </button>
              )}
            </div>
          </div>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>{item.reference}</h2>
              <StatusLabel value={item.status} />
            </div>
            <dl className="relief-details">
              <div>
                <dt>Requesting organisation</dt>
                <dd>{item.requesting_organisation}</dd>
              </div>
              <div>
                <dt>Delivery locality</dt>
                <dd>{item.locality}</dd>
              </div>
              <div>
                <dt>Supplies requested</dt>
                <dd>
                  {item.quantity} {item.unit} · {item.item_name}
                  <small>{categoryLabels[item.category]}</small>
                </dd>
              </div>
              <div>
                <dt>Needed by</dt>
                <dd>
                  {when(item.needed_by)}
                  {item.past_deadline && (
                    <span className="relief-past-due">Past deadline</span>
                  )}
                  <small>Original timestamp: {item.needed_by_raw}</small>
                </dd>
              </div>
              <div>
                <dt>Source or report name</dt>
                <dd>{item.source_name}</dd>
              </div>
              <div>
                <dt>Recorded by</dt>
                <dd>
                  {item.created_actor}
                  <small>
                    {when(item.created_at)} · Version {item.version}
                  </small>
                </dd>
              </div>
              {item.note && (
                <div className="relief-full-field">
                  <dt>Request note</dt>
                  <dd>{item.note}</dd>
                </div>
              )}
            </dl>
          </section>
          {canEdit && item.allowed_transitions.length > 0 && (
            <section className="tools-panel">
              <h2>Review and status</h2>
              <p className="tools-muted">
                Reviewed means the request details were checked. It does not
                record a delivery. Return to Draft before correcting details;
                cancellation is final.
              </p>
              <form className="relief-status-form" onSubmit={updateStatus}>
                <label>
                  Next status
                  <select
                    value={targetStatus}
                    onChange={(event) =>
                      setTargetStatus(event.target.value as Status)
                    }
                    disabled={busy}
                  >
                    {item.allowed_transitions.map((value) => (
                      <option key={value} value={value}>
                        {value === "draft"
                          ? "Draft — return for changes"
                          : statusLabels[value]}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Reason for status change
                  <textarea
                    rows={2}
                    maxLength={500}
                    minLength={1}
                    required
                    value={statusReason}
                    onChange={(event) => setStatusReason(event.target.value)}
                    disabled={busy}
                  />
                </label>
                <button className="button primary" disabled={busy}>
                  {busy ? "Saving status…" : "Update status"}
                </button>
              </form>
            </section>
          )}
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2>Request history</h2>
              <span>
                Showing {detail.events.length} of {item.version} recorded events
              </span>
            </div>
            <ol className="relief-history">
              {detail.events.map((event) => (
                <li key={event.id}>
                  <div className="relief-event-heading">
                    <strong>
                      {event.action === "created"
                        ? "Draft recorded"
                        : event.action === "edited"
                          ? "Details corrected"
                          : "Status changed"}
                    </strong>
                    <span>Version {event.version}</span>
                  </div>
                  <p>{event.reason}</p>
                  <small>
                    {event.actor} · {when(event.created_at)}
                  </small>
                  <details>
                    <summary>View recorded changes</summary>
                    <dl>
                      {Object.keys(fieldLabels)
                        .filter(
                          (field) =>
                            JSON.stringify(event.before?.[field]) !==
                            JSON.stringify(event.after[field]),
                        )
                        .map((field) => (
                          <div key={field}>
                            <dt>{fieldLabels[field]}</dt>
                            <dd>
                              {event.before && (
                                <span className="relief-before">
                                  {auditValue(field, event.before[field])}{" "}
                                  →{" "}
                                </span>
                              )}
                              {auditValue(field, event.after[field])}
                            </dd>
                          </div>
                        ))}
                    </dl>
                  </details>
                </li>
              ))}
            </ol>
            {detail.next_before_version !== null && (
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => void olderEvents()}
              >
                Load older history
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}
