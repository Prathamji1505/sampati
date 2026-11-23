import {
  cloneElement,
  isValidElement,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import type { FormEvent, ReactNode } from "react";
import {
  ArrowRight,
  Download,
  Plus,
  RefreshCw,
  Trash2,
  Upload,
} from "lucide-react";
import { api } from "./api";
import "./response-planner.css";

type Signal = {
  id: string;
  reference: string;
  title: string;
  locality: string;
  state: string;
  version: number;
  kind: string;
  severity: string;
  certainty: string;
  source_name: string;
  source_url: string;
  observed_at: string;
  expires_at: string;
  description: string;
};
type Support = {
  cargo_allowance_kg: string;
  crew: string;
  maintenance: string;
  fuel: string;
  source_name: string;
  observed_at: string;
  version: number;
};
type Aircraft = {
  aircraft_id: string;
  display_name: string;
  reported_status: string;
  source_updated_at: string;
  support: Support | null;
};
type Catalog = {
  aircraft: Aircraft[];
  aircraft_limit_exceeded: boolean;
  can_edit: boolean;
  can_manage_sources: boolean;
  rule_version: string;
  freshness_hours: number;
};
type Item = {
  id: string;
  name: string;
  code: string;
  category: string;
  unit: string;
};
type Store = { id: string; name: string; locality: string };
type Need = {
  id: string;
  reference: string;
  locality: string;
  quantity: string;
  unit: string;
  item_name: string;
};
type Source = {
  id: string;
  name: string;
  enabled: boolean;
  version: number;
  ingest_path: string;
};
type Page<T> = { items: T[]; page: number; total: number; total_pages: number };
type Allocation = {
  request_id: string;
  reference: string;
  proposed: string;
  shortfall: string;
  unit: string;
  weight_kg: string;
};
type Evaluation = {
  status: string;
  rule_version: string;
  evaluation_hash: string;
  evaluated_at: string;
  cargo_kg: string;
  selected_aircraft: string | null;
  blockers: { code: string; message: string; subject: string | null }[];
  allocations: Allocation[];
  candidates: {
    aircraft_id: string;
    eligible: boolean;
    reasons: string[];
    cargo_allowance_kg: string | null;
  }[];
  workflow: { order: number; title: string; state: string; route: string }[];
  limitations: string[];
};
type PlanSummary = {
  id: string;
  title: string;
  state: string;
  snapshot_status: string;
  created_at: string;
};
type Plan = PlanSummary & {
  version: number;
  snapshot: {
    decision: Evaluation;
    facts: {
      signal: Signal;
      needs: { request_id: string; reference: string }[];
    };
  };
  inputs: PlanInput;
};
type PlanDetail = {
  plan: Plan;
  current: Evaluation;
  is_current: boolean;
  effective_state: string;
  events: { version: number; actor: string; action: string; reason: string }[];
};
type Line = {
  key: string;
  request_id: string;
  item_id: string;
  location_id: string;
  unit_weight_kg: string;
  weight_source: string;
  item_name_confirmed: boolean;
};
type PlanInput = {
  title: string;
  signal_id: string;
  needs: Omit<Line, "key">[];
  conditions: {
    weather: string;
    destination_access: string;
    source_name: string;
    observed_at: string;
  };
};
type Tab = "warnings" | "planner" | "aircraft" | "connections";
const emptyPage = <T,>(): Page<T> => ({
  items: [],
  total: 0,
  page: 1,
  total_pages: 1,
});
const localTime = (value?: string) => {
  const now = value ? new Date(value) : new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
};
const iso = (value: FormDataEntryValue | null) =>
  new Date(String(value)).toISOString();
// Native minute-resolution controls must not truncate an existing evidence time.
const evidenceTime = (value: FormDataEntryValue | null, original?: string) =>
  original && localTime(original) === String(value) ? original : iso(value);
const when = (value: string) => new Date(value).toLocaleString();
const text = (data: FormData, name: string) =>
  String(data.get(name) || "").trim();
const readable = (value: string) => value.replaceAll("_", " ");

function Field({ title, children }: { title: string; children: ReactNode }) {
  const labelId = useId();
  return (
    <label className="response-field">
      <span id={labelId}>{title}</span>
      {isValidElement<{ "aria-labelledby"?: string }>(children)
        ? cloneElement(children, { "aria-labelledby": labelId })
        : children}
    </label>
  );
}
function CheckField({
  name,
  title,
  value = "unknown",
}: {
  name: string;
  title: string;
  value?: string;
}) {
  return (
    <Field title={title}>
      <select name={name} defaultValue={value} required>
        <option value="unknown">Not confirmed</option>
        <option value="confirmed">Reported confirmed</option>
        <option value="hold">Reported hold</option>
      </select>
    </Field>
  );
}
function Pager({
  page,
  onPage,
}: {
  page: Page<unknown>;
  onPage: (page: number) => void;
}) {
  return (
    <div className="response-pager">
      <span>
        {page.total} records · Page {page.page} of {page.total_pages}
      </span>
      <button
        className="button secondary"
        disabled={page.page <= 1}
        onClick={() => onPage(page.page - 1)}
      >
        Previous page
      </button>
      <button
        className="button secondary"
        disabled={page.page >= page.total_pages}
        onClick={() => onPage(page.page + 1)}
      >
        Next page
      </button>
    </div>
  );
}

export default function ResponsePlanner({
  onNavigate,
}: {
  onNavigate: (view: "relief" | "inventory" | "deliveries" | "upload") => void;
}) {
  const [tab, setTab] = useState<Tab>("warnings");
  const [visited, setVisited] = useState<Partial<Record<Tab, boolean>>>({
    warnings: true,
  });
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [signals, setSignals] = useState<Page<Signal>>(emptyPage);
  const [plans, setPlans] = useState<Page<PlanSummary>>(emptyPage);
  const [inventory, setInventory] = useState<{
    items: Item[];
    locations: Store[];
  }>({ items: [], locations: [] });
  const [chosenSignal, setChosenSignal] = useState<Signal | null>(null);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const epoch = useRef(0);

  async function load(signalPage = signals.page, planPage = plans.page) {
    const request = ++epoch.current;
    try {
      const [nextCatalog, nextSignals, nextPlans, stock] = await Promise.all([
        api<Catalog>("/response/catalog"),
        api<Page<Signal>>(`/response/signals?page=${signalPage}`),
        api<Page<PlanSummary>>(`/response/plans?page=${planPage}`),
        api<typeof inventory>("/inventory/catalog"),
      ]);
      if (epoch.current !== request) return;
      setCatalog(nextCatalog);
      setSignals(nextSignals);
      setPlans(nextPlans);
      setInventory(stock);
      setLoadError("");
    } catch (problem) {
      if (epoch.current === request) setLoadError((problem as Error).message);
    } finally {
      if (epoch.current === request) setLoading(false);
    }
  }
  useEffect(() => {
    void load();
    return () => {
      epoch.current++;
    };
  }, []);
  // Only the visible warning register refreshes; forms and saved evaluations stay put.
  useEffect(() => {
    if (tab !== "warnings") return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void load();
    }, 30000);
    return () => window.clearInterval(timer);
  }, [tab, signals.page, plans.page]);
  const canEdit = catalog?.can_edit ?? false;
  const changeTab = (next: Tab) => {
    setVisited((current) => ({ ...current, [next]: true }));
    setTab(next);
  };
  const announce = (message: string) => {
    setError("");
    setNotice(message);
    void load();
  };

  return (
    <section
      className="response-workspace"
      aria-label="Civilian response preparation"
    >
      <div className="response-intro">
        <div>
          <h2>Prepare a civilian response</h2>
          <p>
            Bring a warning, reviewed needs, supplies and dated operator reports
            together. Each decision shows its evidence and unresolved checks.
          </p>
        </div>
        <button
          className="button secondary"
          onClick={() => void load()}
          disabled={loading}
        >
          <RefreshCw size={16} aria-hidden="true" /> Refresh evidence
        </button>
      </div>
      <div className="response-tabs" aria-label="Response workspace sections">
        {(
          [
            ["warnings", "Warnings & news"],
            ["planner", "Workflow planner"],
            ["aircraft", "Aircraft support"],
            ["connections", "Warning connections"],
          ] as [Tab, string][]
        ).map(([key, title]) => (
          <button
            key={key}
            aria-pressed={tab === key}
            onClick={() => {
              changeTab(key);
              setError("");
              setNotice("");
            }}
          >
            {title}
          </button>
        ))}
      </div>
      {(error || loadError) && (
        <div className="response-message response-error" role="alert">
          {error || loadError}{" "}
          <button
            className="button secondary"
            onClick={() => (error ? setError("") : void load())}
          >
            {error ? "Dismiss message" : "Retry loading"}
          </button>
        </div>
      )}
      {notice && (
        <p className="response-message" role="status">
          {notice}
        </p>
      )}
      {!canEdit && !loading && (
        <p className="response-message">
          {catalog?.can_manage_sources === false
            ? "This view is read-only. Sign in with an owner/editor role in your own organisation to record warnings and prepare workflows."
            : "Your organisation permissions control changes."}
        </p>
      )}
      {loading ? (
        <div className="response-loading" role="status">
          Loading warning, aircraft and supply evidence…
        </div>
      ) : (
        <>
          {visited.warnings && (
            <div hidden={tab !== "warnings"}>
              <Warnings
                page={signals}
                canEdit={canEdit}
                onPage={(page) => void load(page)}
                onError={setError}
                onDone={announce}
                onPrepare={(signal) => {
                  setChosenSignal(signal);
                  changeTab("planner");
                }}
              />
            </div>
          )}
          {visited.planner && (
            <div hidden={tab !== "planner"}>
              <Planner
                signals={signals.items}
                chosenSignal={chosenSignal}
                plans={plans}
                inventory={inventory}
                canEdit={canEdit}
                onPage={(page) => void load(signals.page, page)}
                onDone={announce}
                onError={setError}
                onNavigate={onNavigate}
              />
            </div>
          )}
          {visited.aircraft && (
            <div hidden={tab !== "aircraft"}>
              <AircraftReports
                aircraft={catalog?.aircraft ?? []}
                exceeded={catalog?.aircraft_limit_exceeded ?? false}
                canEdit={canEdit}
                onDone={announce}
                onError={setError}
                onImport={() => onNavigate("upload")}
              />
            </div>
          )}
          {tab === "connections" && (
            <Connections
              canManage={catalog?.can_manage_sources ?? false}
              onError={setError}
            />
          )}
        </>
      )}
      <p className="response-footnote">
        {catalog?.rule_version} · Source-age policy: {catalog?.freshness_hours}{" "}
        hours. A reviewed workflow is a preparation record. It does not reserve
        supplies, book an aircraft or authorise flight.
      </p>
    </section>
  );
}

function Warnings({
  page,
  canEdit,
  onPage,
  onError,
  onDone,
  onPrepare,
}: {
  page: Page<Signal>;
  canEdit: boolean;
  onPage: (p: number) => void;
  onError: (s: string) => void;
  onDone: (s: string) => void;
  onPrepare: (s: Signal) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<{
    id: string;
    events: PlanDetail["events"];
  } | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    try {
      const payload = Object.fromEntries(
        [
          "reference",
          "kind",
          "title",
          "locality",
          "severity",
          "certainty",
          "source_name",
          "source_url",
          "description",
        ].map((key) => [key, text(data, key)]),
      );
      await api("/response/signals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...payload,
          observed_at: iso(data.get("observed_at")),
          expires_at: iso(data.get("expires_at")),
        }),
      });
      form.reset();
      onDone(
        "Warning recorded as unreviewed. Verify its evidence before planning.",
      );
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(file: File) {
    setBusy(true);
    try {
      if (file.size > 65536)
        throw new Error("Use a warning JSON file smaller than 64 KiB.");
      await api("/response/signals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(JSON.parse(await file.text())),
      });
      onDone("Warning JSON received for human verification.");
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function review(event: FormEvent<HTMLFormElement>, signal: Signal) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      await api(`/response/signals/${signal.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: text(data, "state"),
          reason: text(data, "reason"),
          expected_version: signal.version,
        }),
      });
      setHistory(null);
      onDone("Warning review recorded with your reason.");
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="response-section-heading">
        <div>
          <h3>Warning register</h3>
          <p>
            Incoming reports stay unverified until a person checks them. News
            text never becomes an aircraft or stock instruction.
          </p>
        </div>
        {canEdit && (
          <label className="button secondary response-upload">
            <Upload size={16} aria-hidden="true" /> Import warning JSON
            <input
              type="file"
              accept=".json,application/json"
              disabled={busy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                e.target.value = "";
                if (file) void upload(file);
              }}
            />
          </label>
        )}
      </div>
      {!page.items.length && (
        <div className="response-empty">
          <h3>No warning reports yet</h3>
          <p>
            Record a dated warning below, import structured JSON, or connect an
            authorised source. Incoming reports will appear here within the
            30-second visible-page refresh.
          </p>
        </div>
      )}
      <div className="response-register">
        {page.items.map((signal) => (
          <details key={signal.id} className="response-record">
            <summary>
              <span>
                <strong>{signal.title}</strong>
                <span>
                  {signal.reference} · {signal.locality} · {signal.severity} ·{" "}
                  {signal.kind}
                </span>
              </span>
              <span
                className={`response-state ${signal.state === "verified" ? "response-good" : ""}`}
              >
                {readable(signal.state)}
              </span>
            </summary>
            <div className="response-record-body">
              <p>{signal.description}</p>
              <dl className="response-evidence">
                <div>
                  <dt>Reported by</dt>
                  <dd>{signal.source_name}</dd>
                </div>
                <div>
                  <dt>Observed</dt>
                  <dd>{when(signal.observed_at)}</dd>
                </div>
                <div>
                  <dt>Expires</dt>
                  <dd>{when(signal.expires_at)}</dd>
                </div>
                <div>
                  <dt>Source certainty</dt>
                  <dd>{signal.certainty}</dd>
                </div>
              </dl>
              {signal.source_url && (
                <a
                  href={signal.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open source reference
                </a>
              )}
              <div className="response-actions">
                <button
                  className="button secondary"
                  onClick={() => onPrepare(signal)}
                >
                  Prepare this response{" "}
                  <ArrowRight size={16} aria-hidden="true" />
                </button>
                <button
                  className="button secondary"
                  disabled={busy}
                  onClick={async () => {
                    try {
                      const data = await api<{ events: PlanDetail["events"] }>(
                        `/response/signals/${signal.id}`,
                      );
                      setHistory({ id: signal.id, events: data.events });
                    } catch (problem) {
                      onError((problem as Error).message);
                    }
                  }}
                >
                  Read warning history
                </button>
              </div>
              {canEdit && (
                <form onSubmit={(e) => void review(e, signal)}>
                  <fieldset disabled={busy}>
                    <div className="response-form-grid">
                      <Field title="Warning decision">
                        <select name="state" required defaultValue="verified">
                          <option value="verified">
                            Evidence verified for preparation
                          </option>
                          <option value="dismissed">Dismiss this report</option>
                        </select>
                      </Field>
                      <Field title="Warning review reason">
                        <input
                          name="reason"
                          required
                          minLength={3}
                          maxLength={500}
                        />
                      </Field>
                    </div>
                    <button className="button primary" type="submit">
                      Record warning review
                    </button>
                  </fieldset>
                </form>
              )}
              {history?.id === signal.id && <History events={history.events} />}
            </div>
          </details>
        ))}
      </div>
      <Pager page={page} onPage={onPage} />
      {canEdit && (
        <details className="response-add">
          <summary>Record a warning or news report</summary>
          <form onSubmit={(e) => void submit(e)}>
            <fieldset disabled={busy}>
              <div className="response-form-grid">
                <Field title="Warning reference">
                  <input
                    name="reference"
                    required
                    maxLength={64}
                    pattern="[A-Za-z0-9][A-Za-z0-9._/\-]*"
                  />
                </Field>
                <Field title="Report type">
                  <select name="kind">
                    <option value="warning">Warning</option>
                    <option value="news">News report</option>
                  </select>
                </Field>
                <Field title="Warning title">
                  <input name="title" required minLength={3} maxLength={160} />
                </Field>
                <Field title="Affected locality">
                  <input
                    name="locality"
                    required
                    minLength={2}
                    maxLength={160}
                  />
                </Field>
                <Field title="Reported severity">
                  <select name="severity" defaultValue="unknown">
                    {["unknown", "minor", "moderate", "severe", "extreme"].map(
                      (s) => (
                        <option key={s}>{s}</option>
                      ),
                    )}
                  </select>
                </Field>
                <Field title="Reported certainty">
                  <select name="certainty" defaultValue="unknown">
                    {[
                      "unknown",
                      "observed",
                      "likely",
                      "possible",
                      "unlikely",
                    ].map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </Field>
                <Field title="Warning source">
                  <input
                    name="source_name"
                    required
                    minLength={2}
                    maxLength={120}
                  />
                </Field>
                <Field title="Source reference URL (optional)">
                  <input name="source_url" type="url" maxLength={1000} />
                </Field>
                <Field title="Warning observed at (local time)">
                  <input
                    name="observed_at"
                    type="datetime-local"
                    defaultValue={localTime()}
                    required
                  />
                </Field>
                <Field title="Warning expires at (local time)">
                  <input name="expires_at" type="datetime-local" required />
                </Field>
              </div>
              <Field title="Reported warning details">
                <textarea
                  name="description"
                  required
                  minLength={3}
                  maxLength={3000}
                  rows={3}
                />
              </Field>
              <button className="button primary" type="submit">
                Record unreviewed warning
              </button>
            </fieldset>
          </form>
        </details>
      )}
    </>
  );
}

function AircraftReports({
  aircraft,
  exceeded,
  canEdit,
  onDone,
  onError,
  onImport,
}: {
  aircraft: Aircraft[];
  exceeded: boolean;
  canEdit: boolean;
  onDone: (s: string) => void;
  onError: (s: string) => void;
  onImport: () => void;
}) {
  const [selected, setSelected] = useState<Aircraft | null>(null);
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<PlanDetail["events"]>([]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      await api(
        `/response/aircraft/${encodeURIComponent(selected.aircraft_id)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            expected_version: selected.support?.version ?? 0,
            cargo_allowance_kg: text(data, "cargo_allowance_kg"),
            crew: text(data, "crew"),
            maintenance: text(data, "maintenance"),
            fuel: text(data, "fuel"),
            source_name: text(data, "source_name"),
            observed_at: evidenceTime(
              data.get("observed_at"),
              selected.support?.observed_at,
            ),
            reason: text(data, "reason"),
          }),
        },
      );
      setSelected(null);
      setHistory([]);
      onDone(
        "Dated aircraft support report saved. The aircraft register status was preserved.",
      );
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="response-section-heading">
        <div>
          <h3>Aircraft support evidence</h3>
          <p>
            A reported available aircraft still needs dated cargo, crew,
            maintenance and fuel information from its operator. These records
            support preparation and do not certify readiness.
          </p>
        </div>
        <button className="button secondary" onClick={onImport}>
          Import aircraft reports
        </button>
      </div>
      {exceeded && (
        <p role="alert" className="response-message">
          The register exceeds this planner’s 500-aircraft limit. Evaluation
          will pause rather than silently omit aircraft.
        </p>
      )}
      {!aircraft.length && (
        <p className="response-empty">
          Import your organisation’s aircraft reports first. Then record their
          operator-supplied support details here.
        </p>
      )}
      <p className="response-table-hint">
        Scroll the table to view all columns.
      </p>
      <div
        className="response-table-wrap"
        tabIndex={0}
        role="region"
        aria-label="Aircraft support table"
      >
        <table>
          <caption>Reported aircraft and support information</caption>
          <thead>
            <tr>
              <th>Aircraft</th>
              <th>Reported status</th>
              <th>Cargo allowance</th>
              <th>Support observation</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {aircraft.map((a) => (
              <tr key={a.aircraft_id}>
                <th scope="row">
                  {a.aircraft_id}
                  <small>{a.display_name}</small>
                </th>
                <td>
                  {a.reported_status}
                  <small>{when(a.source_updated_at)}</small>
                </td>
                <td>
                  {a.support
                    ? `${a.support.cargo_allowance_kg} kg`
                    : "Not reported"}
                </td>
                <td>
                  {a.support
                    ? when(a.support.observed_at)
                    : "No support report"}
                </td>
                <td>
                  <button
                    className="button secondary"
                    disabled={busy}
                    onClick={() => {
                      setSelected(a);
                      setHistory([]);
                    }}
                  >
                    Inspect {a.aircraft_id}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected && (
        <section
          className="response-editor"
          aria-label="Aircraft support report"
        >
          <h3>{selected.aircraft_id} · Operator support report</h3>
          {canEdit ? (
            <form
              key={`${selected.aircraft_id}-${selected.support?.version ?? 0}`}
              onSubmit={(e) => void submit(e)}
            >
              <fieldset disabled={busy}>
                <div className="response-form-grid">
                  <Field title="Reported cargo allowance (kg)">
                    <input
                      name="cargo_allowance_kg"
                      inputMode="decimal"
                      type="number"
                      required
                      min="0.001"
                      max="1000000"
                      step="0.001"
                      defaultValue={selected.support?.cargo_allowance_kg}
                    />
                  </Field>
                  <Field title="Support source">
                    <input
                      name="source_name"
                      required
                      minLength={2}
                      maxLength={120}
                      defaultValue={selected.support?.source_name}
                    />
                  </Field>
                  <CheckField
                    name="crew"
                    title="Crew report"
                    value={selected.support?.crew}
                  />
                  <CheckField
                    name="maintenance"
                    title="Maintenance report"
                    value={selected.support?.maintenance}
                  />
                  <CheckField
                    name="fuel"
                    title="Fuel report"
                    value={selected.support?.fuel}
                  />
                  <Field title="Support observed at (local time)">
                    <input
                      name="observed_at"
                      type="datetime-local"
                      defaultValue={localTime(selected.support?.observed_at)}
                      required
                    />
                  </Field>
                </div>
                <Field title="Support change reason">
                  <input name="reason" required minLength={3} maxLength={500} />
                </Field>
                <p>
                  Record the operator’s reported cargo allowance for
                  preparation. Aircraft-specific load, range, volume and flight
                  restrictions require the operator’s separate assessment.
                </p>
                <button className="button primary" type="submit">
                  Save support evidence
                </button>
              </fieldset>
            </form>
          ) : (
            <p>
              {selected.support
                ? `Crew: ${selected.support.crew}; maintenance: ${selected.support.maintenance}; fuel: ${selected.support.fuel}; source: ${selected.support.source_name}.`
                : "No operator support report has been recorded."}
            </p>
          )}
          <div className="response-actions">
            <button
              className="button secondary"
              onClick={async () => {
                try {
                  const result = await api<{ events: PlanDetail["events"] }>(
                    `/response/aircraft/${encodeURIComponent(selected.aircraft_id)}/history`,
                  );
                  setHistory(result.events);
                } catch (problem) {
                  onError((problem as Error).message);
                }
              }}
            >
              Read support history
            </button>
            <button
              className="button secondary"
              onClick={() => {
                setSelected(null);
                setHistory([]);
              }}
            >
              Close support report
            </button>
          </div>
          {history.length > 0 && <History events={history} />}
        </section>
      )}
    </>
  );
}

function Planner({
  signals,
  chosenSignal,
  plans,
  inventory,
  canEdit,
  onPage,
  onDone,
  onError,
  onNavigate,
}: {
  signals: Signal[];
  chosenSignal: Signal | null;
  plans: Page<PlanSummary>;
  inventory: { items: Item[]; locations: Store[] };
  canEdit: boolean;
  onPage: (p: number) => void;
  onDone: (s: string) => void;
  onError: (s: string) => void;
  onNavigate: (v: "relief" | "inventory" | "deliveries" | "upload") => void;
}) {
  const [query, setQuery] = useState("");
  const [requests, setRequests] = useState<Page<Need>>(emptyPage);
  const [lines, setLines] = useState<Line[]>([]);
  const [busy, setBusy] = useState(false);
  const [analysis, setAnalysis] = useState<{
    decision: Evaluation;
    inputs: PlanInput;
  } | null>(null);
  const [detail, setDetail] = useState<PlanDetail | null>(null);
  const [builderDefaults, setBuilderDefaults] = useState<{
    inputs: PlanInput;
    signal: Signal;
    requestNames: Record<string, string>;
  } | null>(null);
  const [builderEpoch, setBuilderEpoch] = useState(0);
  const builderRef = useRef<HTMLFormElement>(null);
  const saveKey = useRef(crypto.randomUUID());
  const signalChoices = [
    ...new Map(
      [
        ...(builderDefaults ? [builderDefaults.signal] : []),
        ...(chosenSignal ? [chosenSignal] : []),
        ...signals,
      ].map((signal) => [signal.id, signal]),
    ).values(),
  ];
  function invalidate() {
    setAnalysis(null);
    setDetail(null);
    saveKey.current = crypto.randomUUID();
  }
  useEffect(() => {
    invalidate();
    setBuilderDefaults(null);
    setBuilderEpoch((value) => value + 1);
  }, [chosenSignal?.id]);
  function useSavedInputs() {
    if (!detail) return;
    const { inputs, snapshot } = detail.plan;
    invalidate();
    setBuilderDefaults({
      inputs,
      signal: { ...snapshot.facts.signal, state: "saved reference" },
      requestNames: Object.fromEntries(
        snapshot.facts.needs.map((need) => [need.request_id, need.reference]),
      ),
    });
    setLines(
      inputs.needs.map((line) => ({ ...line, key: crypto.randomUUID() })),
    );
    setBuilderEpoch((value) => value + 1);
    setQuery("");
    onDone(
      "Saved inputs loaded for a new draft. Original context dates were preserved; check current evidence and evaluate again.",
    );
    requestAnimationFrame(() => {
      builderRef.current?.scrollIntoView({ block: "start" });
      builderRef.current
        ?.querySelector<HTMLInputElement>('[name="title"]')
        ?.focus({ preventScroll: true });
    });
  }
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      try {
        const result = await api<Page<Need>>(
          `/relief-requests?status=reviewed&q=${encodeURIComponent(query)}`,
          { signal: controller.signal },
        );
        if (!controller.signal.aborted) setRequests(result);
      } catch (problem) {
        if (!controller.signal.aborted) onError((problem as Error).message);
      }
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);
  function change(key: string, patch: Partial<Line>) {
    invalidate();
    setLines((current) =>
      current.map((line) => (line.key === key ? { ...line, ...patch } : line)),
    );
  }
  async function evaluate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setDetail(null);
    try {
      const inputs: PlanInput = {
        title: text(data, "title"),
        signal_id: text(data, "signal_id"),
        needs: lines.map(({ key: _key, ...line }) => line),
        conditions: {
          weather: text(data, "weather"),
          destination_access: text(data, "destination_access"),
          source_name: text(data, "source_name"),
          observed_at: evidenceTime(
            data.get("observed_at"),
            builderDefaults?.inputs.conditions.observed_at,
          ),
        },
      };
      const decision = await api<Evaluation>("/response/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(inputs),
      });
      setAnalysis({ decision, inputs });
      onDone(
        "Workflow evaluated against current evidence. Read its checks before saving.",
      );
    } catch (problem) {
      onError((problem as Error).message);
      setAnalysis(null);
    } finally {
      setBusy(false);
    }
  }
  async function openPlan(id: string) {
    setBusy(true);
    try {
      setDetail(await api<PlanDetail>(`/response/plans/${id}`));
      setAnalysis(null);
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function savePlan() {
    if (!analysis) return;
    setBusy(true);
    try {
      const data = await api<{ plan: Plan }>("/response/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...analysis.inputs,
          submission_key: saveKey.current,
          evaluation_hash: analysis.decision.evaluation_hash,
        }),
      });
      await openPlan(data.plan.id);
      onDone(
        "Preparation draft saved with its original evidence. Resources remain unreserved.",
      );
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function review(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      await api(`/response/plans/${detail.plan.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          expected_version: detail.plan.version,
          evaluation_hash: detail.current.evaluation_hash,
          reason: text(data, "reason"),
        }),
      });
      await openPlan(detail.plan.id);
      onDone(
        "Coordinator review recorded. Stock reservation and operator dispatch approval remain separate actions.",
      );
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const result = detail?.current ?? analysis?.decision;
  return (
    <>
      <div className="response-section-heading">
        <div>
          <h3>Design a response workflow</h3>
          <p>
            Map exact supplies to reviewed requests in the affected locality.
            The rules propose uncommitted quantities in earliest-deadline order
            and choose the smallest reported aircraft allowance that fits.
          </p>
        </div>
        <button
          className="button secondary"
          onClick={() => onNavigate("relief")}
        >
          Review supply needs
        </button>
      </div>
      {canEdit && (
        <form
          className="response-editor"
          key={builderEpoch}
          ref={builderRef}
          onSubmit={(e) => void evaluate(e)}
          onChangeCapture={invalidate}
        >
          <fieldset disabled={busy}>
            <div className="response-form-grid">
              <Field title="Workflow title">
                <input
                  name="title"
                  required
                  minLength={3}
                  maxLength={160}
                  defaultValue={builderDefaults?.inputs.title}
                />
              </Field>
              <Field title="Warning for this workflow">
                <select
                  name="signal_id"
                  key={chosenSignal?.id ?? "none"}
                  defaultValue={
                    builderDefaults?.inputs.signal_id ?? chosenSignal?.id ?? ""
                  }
                  required
                >
                  <option value="">Select a warning</option>
                  {signalChoices.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.reference} · {s.locality} · {s.state}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <Field title="Find a reviewed request">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by request reference or locality"
                maxLength={200}
              />
            </Field>
            <p className="response-help">
              Showing {requests.items.length} of {requests.total} matching
              reviewed requests. Narrow the search to find older records.
            </p>
            {lines.map((line, index) => (
              <fieldset key={line.key} className="response-need">
                <legend>Supply need {index + 1}</legend>
                <div className="response-form-grid">
                  <Field title={`Request for need ${index + 1}`}>
                    <select
                      value={line.request_id}
                      required
                      onChange={(e) =>
                        change(line.key, {
                          request_id: e.target.value,
                          item_name_confirmed: false,
                        })
                      }
                    >
                      <option value="">Select a reviewed need</option>
                      {line.request_id &&
                        !requests.items.some(
                          (r) => r.id === line.request_id,
                        ) && (
                          <option value={line.request_id}>
                            Saved request ·{" "}
                            {builderDefaults?.requestNames[line.request_id] ??
                              line.request_id}
                          </option>
                        )}
                      {requests.items.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.reference} · {r.item_name} · {r.quantity} {r.unit}{" "}
                          · {r.locality}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field title={`Catalog item for need ${index + 1}`}>
                    <select
                      value={line.item_id}
                      required
                      onChange={(e) =>
                        change(line.key, {
                          item_id: e.target.value,
                          item_name_confirmed: false,
                        })
                      }
                    >
                      <option value="">Select the exact supply</option>
                      {inventory.items.map((i) => (
                        <option key={i.id} value={i.id}>
                          {i.code} · {i.name} · {i.unit}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field title={`Store for need ${index + 1}`}>
                    <select
                      value={line.location_id}
                      required
                      onChange={(e) =>
                        change(line.key, { location_id: e.target.value })
                      }
                    >
                      <option value="">Select a supply store</option>
                      {inventory.locations.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.name} · {l.locality}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field title={`Kilograms per unit for need ${index + 1}`}>
                    <input
                      type="number"
                      inputMode="decimal"
                      min="0.001"
                      max="1000000"
                      step="0.001"
                      required
                      value={line.unit_weight_kg}
                      onChange={(e) =>
                        change(line.key, { unit_weight_kg: e.target.value })
                      }
                    />
                  </Field>
                  <Field title={`Weight source for need ${index + 1}`}>
                    <input
                      required
                      minLength={2}
                      maxLength={120}
                      value={line.weight_source}
                      onChange={(e) =>
                        change(line.key, { weight_source: e.target.value })
                      }
                    />
                  </Field>
                </div>
                <label className="response-checkbox">
                  <input
                    type="checkbox"
                    checked={line.item_name_confirmed}
                    onChange={(e) =>
                      change(line.key, {
                        item_name_confirmed: e.target.checked,
                      })
                    }
                  />{" "}
                  I checked that this item is the exact supply requested.
                </label>
                <button
                  className="button secondary"
                  type="button"
                  onClick={() => {
                    invalidate();
                    setLines((current) =>
                      current.filter((l) => l.key !== line.key),
                    );
                  }}
                >
                  <Trash2 size={16} aria-hidden="true" /> Remove need{" "}
                  {index + 1}
                </button>
              </fieldset>
            ))}
            <button
              className="button secondary"
              type="button"
              disabled={lines.length >= 50}
              onClick={() => {
                invalidate();
                setLines((current) => [
                  ...current,
                  {
                    key: crypto.randomUUID(),
                    request_id: "",
                    item_id: "",
                    location_id: "",
                    unit_weight_kg: "",
                    weight_source: "",
                    item_name_confirmed: false,
                  },
                ]);
              }}
            >
              <Plus size={16} aria-hidden="true" /> Add supply need
            </button>
            <h4>Operator and destination context</h4>
            <div className="response-form-grid">
              <CheckField
                name="weather"
                title="Weather assessment"
                value={builderDefaults?.inputs.conditions.weather}
              />
              <CheckField
                name="destination_access"
                title="Destination access assessment"
                value={builderDefaults?.inputs.conditions.destination_access}
              />
              <Field title="Context report source">
                <input
                  name="source_name"
                  defaultValue={builderDefaults?.inputs.conditions.source_name}
                  required
                  minLength={2}
                  maxLength={120}
                />
              </Field>
              <Field title="Context observed at (local time)">
                <input
                  name="observed_at"
                  type="datetime-local"
                  defaultValue={localTime(
                    builderDefaults?.inputs.conditions.observed_at,
                  )}
                  required
                />
              </Field>
            </div>
            <button
              className="button primary"
              type="submit"
              disabled={!lines.length || !signalChoices.length}
            >
              {busy ? "Checking evidence…" : "Evaluate response workflow"}
            </button>
          </fieldset>
        </form>
      )}
      {detail && (
        <div className="response-message">
          <strong>
            {detail.plan.title} · {readable(detail.effective_state)}
          </strong>
          <p>
            {detail.is_current
              ? "Current checks match the saved evidence snapshot."
              : "Evidence or freshness changed since this draft was saved. The original snapshot is preserved. Load its saved inputs, check the current sources, then evaluate and save a new draft before review."}
          </p>
          {canEdit && (
            <button
              className="button secondary"
              disabled={busy}
              onClick={useSavedInputs}
            >
              Use saved inputs for a new draft
            </button>
          )}
        </div>
      )}
      {result && (
        <section className="response-result" aria-label="Workflow evaluation">
          <Result
            result={result}
            onNavigate={onNavigate}
            coordinatorReviewed={
              detail?.plan.state === "reviewed" && detail.is_current
            }
            requiresNewDraft={detail !== null && !detail.is_current}
          />
          {analysis && canEdit && (
            <button
              className="button primary"
              disabled={busy}
              onClick={() => void savePlan()}
            >
              Save preparation draft
            </button>
          )}
          {detail && (
            <>
              <button
                className="button secondary"
                onClick={() => {
                  const url = URL.createObjectURL(
                    new Blob([JSON.stringify(detail, null, 2)], {
                      type: "application/json",
                    }),
                  );
                  const link = document.createElement("a");
                  link.href = url;
                  link.download = `sampati-preparation-${detail.plan.id}.json`;
                  link.click();
                  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
                }}
              >
                <Download size={16} aria-hidden="true" /> Export preparation
                record
              </button>
              {canEdit && detail.plan.state === "draft" && (
                <form onSubmit={(e) => void review(e)}>
                  <fieldset
                    disabled={
                      busy ||
                      !detail.is_current ||
                      detail.current.status !== "reviewable"
                    }
                  >
                    <Field title="Coordinator review reason">
                      <input
                        name="reason"
                        required
                        minLength={3}
                        maxLength={500}
                      />
                    </Field>
                    <button className="button primary" type="submit">
                      Record coordinator review
                    </button>
                  </fieldset>
                </form>
              )}
              <details>
                <summary>Saved evidence and review history</summary>
                <p>
                  The original saved result was{" "}
                  {detail.plan.snapshot.decision.status}, evaluated at{" "}
                  {when(detail.plan.snapshot.decision.evaluated_at)}. The export
                  includes original evidence and the current evaluation.
                </p>
                <History events={detail.events} />
              </details>
            </>
          )}
        </section>
      )}
      <h3>Saved preparation records</h3>
      <p>
        Saved states record review history. Open a record to check its evidence
        against the current workspace.
      </p>
      {!plans.items.length && (
        <p className="response-empty">
          No saved workflows yet. Evaluate a need above and save its explained
          preparation draft.
        </p>
      )}
      <div className="response-register">
        {plans.items.map((plan) => (
          <button
            className="response-plan-row"
            key={plan.id}
            disabled={busy}
            onClick={() => void openPlan(plan.id)}
          >
            <span>
              <strong>{plan.title}</strong>
              <small>
                {when(plan.created_at)} · Last saved result:{" "}
                {plan.snapshot_status}
              </small>
            </span>
            <span>
              {readable(plan.state)} <ArrowRight size={16} aria-hidden="true" />
            </span>
          </button>
        ))}
      </div>
      <Pager page={plans} onPage={onPage} />
    </>
  );
}

function Result({
  result,
  onNavigate,
  coordinatorReviewed = false,
  requiresNewDraft = false,
}: {
  result: Evaluation;
  onNavigate: (v: "relief" | "inventory" | "deliveries" | "upload") => void;
  coordinatorReviewed?: boolean;
  requiresNewDraft?: boolean;
}) {
  return (
    <>
      <div className="response-section-heading">
        <div>
          <h3>
            {requiresNewDraft
              ? "Current evidence needs a new draft"
              : coordinatorReviewed
                ? "Coordinator review recorded"
                : result.status === "reviewable"
                  ? "Ready for coordinator review"
                  : "Resolve these checks before review"}
          </h3>
          <p>
            {result.cargo_kg} kg proposed cargo · Aircraft candidate:{" "}
            {result.selected_aircraft ?? "none"} · {when(result.evaluated_at)}
          </p>
        </div>
        <span
          className={`response-state ${result.status === "reviewable" && !requiresNewDraft ? "response-good" : ""}`}
        >
          {requiresNewDraft
            ? "New draft required"
            : coordinatorReviewed
              ? "Reviewed · evidence current"
              : result.status}
        </span>
      </div>
      {result.blockers.length > 0 && (
        <ul className="response-blockers">
          {result.blockers.map((b, i) => (
            <li key={`${b.code}-${i}`}>
              <strong>{readable(b.code)}</strong>
              <span>
                {b.message}
                {b.subject &&
                  ` (${result.allocations.find((a) => a.request_id === b.subject)?.reference ?? b.subject})`}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="response-table-hint">
        Scroll the table to view all columns.
      </p>
      <div
        className="response-table-wrap"
        tabIndex={0}
        role="region"
        aria-label="Proposed supply table"
      >
        <table>
          <caption>Proposed supply quantities</caption>
          <thead>
            <tr>
              <th>Request</th>
              <th>Proposed</th>
              <th>Shortfall</th>
              <th>Cargo mass</th>
            </tr>
          </thead>
          <tbody>
            {result.allocations.map((a) => (
              <tr key={a.request_id}>
                <th scope="row">{a.reference}</th>
                <td>
                  {a.proposed} {a.unit}
                </td>
                <td>
                  {a.shortfall} {a.unit}
                </td>
                <td>{a.weight_kg} kg</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h4>Response workflow</h4>
      <ol className="response-steps">
        {result.workflow.map((step) => (
          <li key={step.order}>
            <div>
              <strong>{step.title}</strong>
              <span>
                {step.order === 6 && coordinatorReviewed
                  ? "review recorded"
                  : readable(step.state)}
              </span>
            </div>
            {["relief", "inventory", "deliveries"].includes(step.route) && (
              <button
                className="button secondary"
                onClick={() =>
                  onNavigate(
                    step.route as "relief" | "inventory" | "deliveries",
                  )
                }
              >
                Open {step.route}
              </button>
            )}
          </li>
        ))}
      </ol>
      <details>
        <summary>Why aircraft were included or excluded</summary>
        {!result.candidates.length && (
          <p>No aircraft are registered in this organisation.</p>
        )}
        {result.candidates.map((a) => (
          <p key={a.aircraft_id}>
            <strong>{a.aircraft_id}</strong> ·{" "}
            {a.eligible
              ? "Reported evidence fits this preparation"
              : a.reasons.map(readable).join(", ")}{" "}
            · {a.cargo_allowance_kg ?? "Unknown"} kg allowance
          </p>
        ))}
      </details>
      <ul className="response-limits">
        {result.limitations.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </>
  );
}

function History({ events }: { events: PlanDetail["events"] }) {
  return (
    <div className="response-history">
      <h4>Recorded history</h4>
      {events.map((event) => (
        <p key={event.version}>
          <strong>
            v{event.version} · {readable(event.action)}
          </strong>
          <span>{event.reason}</span>
          <small>{event.actor}</small>
        </p>
      ))}
    </div>
  );
}

function Connections({
  canManage,
  onError,
}: {
  canManage: boolean;
  onError: (s: string) => void;
}) {
  const [sources, setSources] = useState<Source[]>([]);
  const [secret, setSecret] = useState<(Source & { token: string }) | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");
  useEffect(() => {
    let active = true;
    void api<{ items: Source[] }>("/response/sources")
      .then((data) => {
        if (active) setSources(data.items);
      })
      .catch((problem) => {
        if (active) onError(problem.message);
      });
    return () => {
      active = false;
    };
  }, []);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const name = text(new FormData(form), "name");
    setBusy(true);
    try {
      const source = await api<Source & { token: string }>(
        "/response/sources",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name }),
        },
      );
      setSecret(source);
      const { token: _privateToken, ...publicSource } = source;
      setSources((current) => [...current, publicSource]);
      form.reset();
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function change(source: Source, rotate = false) {
    setBusy(true);
    try {
      const data = await api<Source & { token?: string }>(
        `/response/sources/${source.id}${rotate ? "/rotate" : ""}`,
        {
          method: rotate ? "POST" : "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            expected_version: source.version,
            reason,
            ...(!rotate ? { enabled: !source.enabled } : {}),
          }),
        },
      );
      const { token: _privateToken, ...publicSource } = data;
      setSources((current) =>
        current.map((s) => (s.id === source.id ? publicSource : s)),
      );
      if (data.token) setSecret(data as Source & { token: string });
      else if (secret?.id === source.id) setSecret(null);
    } catch (problem) {
      onError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <h3>Connect structured warning reports</h3>
      <p>
        Authorised adapters can send warning/news JSON to a warning-only
        endpoint. The key can queue evidence, and every report still needs human
        verification. General news scraping and public feeds are not connected
        automatically.
      </p>
      {canManage && (
        <form onSubmit={(e) => void create(e)}>
          <fieldset disabled={busy}>
            <Field title="Warning connector name">
              <input name="name" required minLength={2} maxLength={100} />
            </Field>
            <button className="button primary" type="submit">
              Create warning connection
            </button>
          </fieldset>
        </form>
      )}
      {secret && (
        <div className="response-secret">
          <strong>Save this source key privately; it is shown only now.</strong>
          <code>{secret.token}</code>
          <p>
            POST structured warning JSON to <code>{secret.ingest_path}</code>{" "}
            with <code>Authorization: Bearer YOUR_PRIVATE_KEY</code>.
          </p>
          <button className="button secondary" onClick={() => setSecret(null)}>
            Hide source key
          </button>
        </div>
      )}
      <p>
        The local adapter is <code>scripts/watch_warnings.py</code>. It watches
        authorised JSON exports and sends new files for review. See the
        response-planning guide for the schema and environment-variable setup.
      </p>
      {canManage && (
        <Field title="Connector change reason">
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            minLength={3}
            maxLength={500}
          />
        </Field>
      )}
      {!sources.length && (
        <p className="response-empty">
          No warning connectors have been created for this organisation.
        </p>
      )}
      {sources.map((source) => (
        <div key={source.id} className="response-source">
          <div>
            <strong>{source.name}</strong>
            <p>
              {source.enabled ? "Enabled" : "Disabled"} · Warning-only · Version{" "}
              {source.version}
            </p>
            <code>{source.ingest_path}</code>
          </div>
          {canManage && (
            <div className="response-actions">
              <button
                className="button secondary"
                disabled={busy || reason.trim().length < 3}
                onClick={() => void change(source)}
              >
                {source.enabled ? "Disable connector" : "Enable connector"}
              </button>
              <button
                className="button secondary"
                disabled={busy || reason.trim().length < 3}
                onClick={() => void change(source, true)}
              >
                Rotate source key
              </button>
            </div>
          )}
        </div>
      ))}
    </>
  );
}
