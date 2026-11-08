import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Plus, RefreshCw, Search } from "lucide-react";
import { api } from "./api";
import type { SessionState, Workspace, WorkspaceScope } from "./types";
import "./workspace-tools.css";
import "./relief-requests.css";
import "./inventory.css";

type Item = {
  id: string;
  code: string;
  name: string;
  category: string;
  unit: string;
};
type Location = { id: string; code: string; name: string; locality: string };
type Catalog = {
  items: Item[];
  locations: Location[];
  can_edit: boolean;
  catalog_limit: number;
};
type Position = {
  id: string | null;
  item: Item;
  location: Location;
  on_hand: string;
  reserved: string;
  available: string;
  version: number;
  updated_at: string | null;
  latest_report: {
    reference: string;
    quantity: string;
    source_name: string;
    observed_at: string;
    received_at: string;
  } | null;
};
type Kind =
  | "receipt"
  | "reserve"
  | "release"
  | "issue"
  | "return"
  | "report"
  | "adjustment_in"
  | "adjustment_out";
type RecordEntry = {
  id: string;
  sequence: number;
  reference: string;
  kind: Kind;
  quantity: string;
  remaining_quantity: string | null;
  parent_id: string | null;
  parent_reference: string | null;
  request_reference: string | null;
  source_name: string;
  observed_at: string;
  observed_at_raw: string;
  received_at: string;
  actor: string;
  reason: string;
  after: { on_hand: string; reserved: string; available: string };
};
type Detail = {
  position: Position;
  records: RecordEntry[];
  next_before_sequence: number | null;
};
type StockList = {
  items: Position[];
  total: number;
  page: number;
  total_pages: number;
};
type Need = {
  id: string;
  reference: string;
  organisation: string;
  quantity: string;
  remaining: string;
  unit: string;
  allocation_warning: boolean;
};
const categories: Record<string, string> = {
  food: "Food",
  water: "Water",
  medicine: "Medical supplies",
  shelter: "Shelter supplies",
  other: "Other supplies",
};
const units = ["items", "boxes", "kits", "litres", "kilograms", "packs"];
const kinds: Record<Kind, string> = {
  receipt: "Receipt",
  reserve: "Reservation",
  release: "Release reservation",
  issue: "Issue reserved supplies",
  return: "Return issued supplies",
  report: "Source count report",
  adjustment_in: "Adjustment in",
  adjustment_out: "Adjustment out",
};
const explanation: Record<Kind, string> = {
  receipt:
    "Add supplies received into this store. Enter the source receipt and its time.",
  reserve:
    "Hold available supplies for a reviewed relief request. Category and unit must match; this does not approve dispatch.",
  release:
    "Free the unused part of an earlier reservation. It does not change recorded on-hand stock.",
  issue:
    "Record supplies leaving this store against an earlier reservation. An issue does not confirm delivery.",
  return:
    "Record supplies received back against an original issue. Returns cannot exceed its unreturned quantity.",
  report:
    "Keep a source-reported count without changing ledger stock. A reported count is not a receipt or adjustment.",
  adjustment_in:
    "Record a reasoned increase to correct the ledger. Retain the source evidence and original events.",
  adjustment_out:
    "Record a reasoned decrease to correct the ledger. Reserved stock must be released before removing it.",
};
const when = (value: string) => new Date(value).toLocaleString();
function localNow() {
  const date = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
const initialEvent = () => ({
  reference: "",
  kind: "receipt" as Kind,
  quantity: "",
  parent_id: "",
  request_id: "",
  source_name: "",
  observed_at: localNow(),
  reason: "",
});
const json = (body: unknown) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export default function Inventory({
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
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [list, setList] = useState<StockList | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [mode, setMode] = useState<"list" | "catalog" | "choose" | "detail">(
    "list",
  );
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [chosenItem, setChosenItem] = useState("");
  const [chosenLocation, setChosenLocation] = useState("");
  const [itemForm, setItemForm] = useState({
    code: "",
    name: "",
    category: "water",
    unit: "packs",
  });
  const [locationForm, setLocationForm] = useState({
    code: "",
    name: "",
    locality: "",
  });
  const [eventForm, setEventForm] = useState(initialEvent);
  const [key, setKey] = useState(() => crypto.randomUUID());
  const [needQuery, setNeedQuery] = useState("");
  const [needs, setNeeds] = useState<{ items: Need[]; total: number }>({
    items: [],
    total: 0,
  });
  const [needsLoading, setNeedsLoading] = useState(false);
  const [needsError, setNeedsError] = useState("");
  const epoch = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const canEdit =
    scope === "private" &&
    ["owner", "editor"].includes(session?.workspace?.role || "") &&
    catalog?.can_edit === true;
  async function load() {
    const current = ++epoch.current;
    setLoading(true);
    try {
      const [nextCatalog, nextList] = await Promise.all([
        api<Catalog>("/inventory/catalog"),
        api<StockList>(
          `/inventory?${new URLSearchParams({ q: search, page: String(page) })}`,
        ),
      ]);
      if (current === epoch.current) {
        setCatalog(nextCatalog);
        setList(nextList);
        if (nextList.page !== page) setPage(nextList.page);
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
  }, [search, page, workspace?.server_time]);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [mode]);
  useEffect(() => {
    let alive = true;
    if (eventForm.kind !== "reserve" || !detail || !canEdit) {
      setNeeds({ items: [], total: 0 });
      return;
    }
    setNeedsLoading(true);
    setNeedsError("");
    const timer = setTimeout(async () => {
      try {
        const result = await api<{ items: Need[]; total: number }>(
          `/inventory/requests?${new URLSearchParams({ item_id: detail.position.item.id, q: needQuery })}`,
        );
        if (alive) setNeeds(result);
      } catch (problem) {
        if (alive) setNeedsError((problem as Error).message);
      } finally {
        if (alive) setNeedsLoading(false);
      }
    }, 250);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [
    eventForm.kind,
    detail?.position.item.id,
    detail?.position.version,
    needQuery,
    canEdit,
  ]);
  function clearMessages() {
    setError("");
    setNotice("");
  }
  function resetEvent() {
    setEventForm(initialEvent());
    setKey(crypto.randomUUID());
    setNeedQuery("");
  }
  async function open(itemId: string, locationId: string) {
    setBusy(true);
    setError("");
    try {
      const data = await api<Detail>(
        `/inventory/position?${new URLSearchParams({ item_id: itemId, location_id: locationId })}`,
      );
      setDetail(data);
      setMode("detail");
      resetEvent();
    } catch (problem) {
      setError((problem as Error).message);
      throw problem;
    } finally {
      setBusy(false);
    }
  }
  async function saveCatalog(
    event: React.FormEvent,
    kind: "item" | "location",
  ) {
    event.preventDefault();
    setBusy(true);
    clearMessages();
    try {
      await api(`/inventory/${kind === "item" ? "items" : "locations"}`, {
        method: "POST",
        ...json(kind === "item" ? itemForm : locationForm),
      });
      if (kind === "item")
        setItemForm({ code: "", name: "", category: "water", unit: "packs" });
      else setLocationForm({ code: "", name: "", locality: "" });
      await load();
      setNotice(
        `${kind === "item" ? "Supply item" : "Storage location"} saved. Catalog identities and units remain fixed.`,
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveRecord(event: React.FormEvent) {
    event.preventDefault();
    if (!detail) return;
    setBusy(true);
    clearMessages();
    try {
      const observed = new Date(eventForm.observed_at);
      if (!Number.isFinite(observed.getTime()))
        throw new Error("Choose a valid source date and time.");
      const result = await api<{ duplicate: boolean }>("/inventory/records", {
        method: "POST",
        ...json({
          ...eventForm,
          item_id: detail.position.item.id,
          location_id: detail.position.location.id,
          observed_at: observed.toISOString(),
          parent_id: eventForm.parent_id || null,
          request_id:
            eventForm.kind === "reserve" ? eventForm.request_id : null,
          expected_version: detail.position.version,
          submission_key: key,
        }),
      });
      await open(detail.position.item.id, detail.position.location.id);
      await load();
      setNotice(
        result.duplicate
          ? "This event was already recorded. No stock or history was added twice."
          : "Stock event recorded. The ledger preserves its source, actor and resulting balances.",
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function olderHistory() {
    if (!detail || detail.next_before_sequence === null) return;
    setBusy(true);
    setError("");
    try {
      const next = await api<Detail>(
        `/inventory/position?${new URLSearchParams({ item_id: detail.position.item.id, location_id: detail.position.location.id, before_sequence: String(detail.next_before_sequence) })}`,
      );
      if (next.position.version !== detail.position.version)
        throw new Error(
          "This stock position changed. Refresh its details before loading older history.",
        );
      setDetail({ ...next, records: [...detail.records, ...next.records] });
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const position = detail?.position;
  const parentKind = eventForm.kind === "return" ? "issue" : "reserve";
  const parents =
    detail?.records.filter(
      (record) =>
        record.kind === parentKind &&
        record.remaining_quantity !== null &&
        Number(record.remaining_quantity) > 0,
    ) || [];
  return (
    <div className="workspace-tools inventory-workspace">
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
            Fictional inventory · Read only. Ledger quantities and
            source-reported counts are separate.
          </p>
          {!session?.user && (
            <button className="button secondary" onClick={onSignIn}>
              Sign in to record stock
            </button>
          )}
        </div>
      )}
      <div className="tools-toolbar">
        {mode === "list" ? (
          <span>{list?.total ?? 0} item / location balances</span>
        ) : (
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => {
              setMode("list");
              clearMessages();
              void load();
            }}
          >
            <ArrowLeft size={15} />
            Back to stock register
          </button>
        )}
        <div className="tools-actions">
          <button
            className="button secondary"
            disabled={busy || loading}
            onClick={() => {
              clearMessages();
              void load();
            }}
          >
            <RefreshCw size={15} />
            Refresh inventory
          </button>
          {mode !== "catalog" && (
            <button
              className="button secondary"
              disabled={busy || !catalog}
              onClick={() => {
                clearMessages();
                setMode("catalog");
              }}
            >
              Items and locations
            </button>
          )}
          {mode === "list" && (
            <button
              className="button primary"
              disabled={
                !canEdit ||
                busy ||
                !catalog?.items.length ||
                !catalog?.locations.length
              }
              onClick={() => {
                setChosenItem(catalog?.items[0]?.id || "");
                setChosenLocation(catalog?.locations[0]?.id || "");
                clearMessages();
                setMode("choose");
              }}
            >
              <Plus size={16} />
              Record stock
            </button>
          )}
        </div>
      </div>
      {mode === "list" && (
        <>
          <section
            className="register-panel"
            aria-label="Aid stock register"
            aria-busy={loading}
          >
            <div className="table-toolbar">
              <label className="search-field">
                <Search size={17} />
                <input
                  aria-label="Search inventory"
                  placeholder="Search item, store or locality…"
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
                  ? "Loading stock records…"
                  : "Inventory is unavailable. Refresh when the server is ready."}
              </p>
            ) : list.items.length === 0 ? (
              <div className="relief-empty">
                <h2>
                  {search
                    ? "No stock positions match this search."
                    : "Your aid inventory starts here."}
                </h2>
                <p>
                  {catalog?.items.length && catalog?.locations.length
                    ? "Choose Record stock to add the first receipt or source count."
                    : "Add a supply item and storage location, then record receipts. Source counts do not add usable stock."}
                </p>
                <button
                  className="button secondary"
                  disabled={!catalog}
                  onClick={() => {
                    clearMessages();
                    setMode("catalog");
                  }}
                >
                  Open items and locations
                </button>
              </div>
            ) : (
              <>
                <p className="relief-scroll-hint">
                  Scroll the table sideways for balances, source counts and
                  history.
                </p>
                <div className="table-scroll">
                  <table className="tools-table inventory-table">
                    <thead>
                      <tr>
                        <th scope="col">Supply item / unit</th>
                        <th scope="col">Storage location</th>
                        <th scope="col">Recorded on hand</th>
                        <th scope="col">Reserved</th>
                        <th scope="col">Available</th>
                        <th scope="col">Latest source count</th>
                        <th scope="col">History</th>
                      </tr>
                    </thead>
                    <tbody>
                      {list.items.map((row) => (
                        <tr key={row.id}>
                          <td>
                            <strong>{row.item.code}</strong>
                            <span className="relief-secondary">
                              {row.item.name}
                            </span>
                            <small>
                              {categories[row.item.category]} · {row.item.unit}
                            </small>
                          </td>
                          <td>
                            {row.location.name}
                            <span className="relief-secondary">
                              {row.location.locality}
                            </span>
                          </td>
                          <td className="relief-quantity">{row.on_hand}</td>
                          <td className="relief-quantity">{row.reserved}</td>
                          <td className="relief-quantity">{row.available}</td>
                          <td>
                            {row.latest_report ? (
                              <>
                                {row.latest_report.quantity} {row.item.unit}
                                <span className="relief-secondary">
                                  {when(row.latest_report.observed_at)}
                                </span>
                                <small>{row.latest_report.source_name}</small>
                              </>
                            ) : (
                              <span className="tools-muted">
                                No count reported
                              </span>
                            )}
                          </td>
                          <td>
                            <button
                              className="button secondary"
                              disabled={busy}
                              aria-label={`Open ${row.item.code} at ${row.location.code}`}
                              onClick={() => {
                                clearMessages();
                                void open(row.item.id, row.location.id).catch(
                                  () => {},
                                );
                              }}
                            >
                              Open stock
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
              <span>{list?.total ?? 0} matching positions · 20 per page</span>
              <div className="tools-actions">
                <button
                  className="button secondary"
                  disabled={loading || !list || list.page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous stock
                </button>
                <span>
                  Page {list?.page ?? 1} of {list?.total_pages ?? 1}
                </span>
                <button
                  className="button secondary"
                  disabled={loading || !list || list.page >= list.total_pages}
                  onClick={() => setPage(page + 1)}
                >
                  Next stock
                </button>
              </div>
            </div>
          </section>
          <p className="tools-muted">
            Available = recorded on hand − reserved. Units stay fixed per item.
            Ledger entries are user-recorded events; source counts retain their
            own observation times and never overwrite balances. An issue is not
            a delivery confirmation.
          </p>
        </>
      )}
      {mode === "choose" && (
        <section className="tools-panel">
          <h2 ref={heading} tabIndex={-1}>
            Choose supplies and storage
          </h2>
          <p className="tools-muted">
            Open a stock position to inspect its balances and history before
            recording a movement or count.
          </p>
          <form
            className="relief-form"
            onSubmit={(event) => {
              event.preventDefault();
              void open(chosenItem, chosenLocation).catch(() => {});
            }}
          >
            <label>
              Supply item
              <select
                required
                value={chosenItem}
                disabled={busy}
                onChange={(event) => setChosenItem(event.target.value)}
              >
                {catalog?.items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.code} · {item.name} ({item.unit})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Storage location
              <select
                required
                value={chosenLocation}
                disabled={busy}
                onChange={(event) => setChosenLocation(event.target.value)}
              >
                {catalog?.locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.code} · {location.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="relief-form-actions">
              <button className="button primary" disabled={busy}>
                Open stock position
              </button>
            </div>
          </form>
        </section>
      )}
      {mode === "catalog" && (
        <>
          <section className="tools-panel">
            <h2 ref={heading} tabIndex={-1}>
              Supply items
            </h2>
            <p className="tools-muted">
              Each code has one category and unit. Catalog identities remain
              fixed so older movements retain their meaning. Use a new code for
              a different item or unit. Up to {catalog?.catalog_limit ?? 500}{" "}
              items per organisation.
            </p>
            {canEdit && (
              <form
                className="relief-form"
                onSubmit={(event) => void saveCatalog(event, "item")}
              >
                <label>
                  Item code
                  <input
                    required
                    maxLength={64}
                    value={itemForm.code}
                    disabled={busy}
                    onChange={(event) =>
                      setItemForm({ ...itemForm, code: event.target.value })
                    }
                  />
                </label>
                <label>
                  Item name
                  <input
                    required
                    minLength={2}
                    maxLength={160}
                    value={itemForm.name}
                    disabled={busy}
                    onChange={(event) =>
                      setItemForm({ ...itemForm, name: event.target.value })
                    }
                  />
                </label>
                <label>
                  Supply category
                  <select
                    value={itemForm.category}
                    disabled={busy}
                    onChange={(event) =>
                      setItemForm({ ...itemForm, category: event.target.value })
                    }
                  >
                    {Object.entries(categories).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Fixed unit
                  <select
                    value={itemForm.unit}
                    disabled={busy}
                    onChange={(event) =>
                      setItemForm({ ...itemForm, unit: event.target.value })
                    }
                  >
                    {units.map((unit) => (
                      <option key={unit} value={unit}>
                        {unit}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="relief-form-actions">
                  <button className="button primary" disabled={busy}>
                    Save supply item
                  </button>
                </div>
              </form>
            )}
            <p className="relief-scroll-hint inventory-catalog-hint">
              Scroll the item table sideways to inspect fixed units.
            </p>
            <div className="inventory-catalog-scroll table-scroll">
              <table className="tools-table">
                <thead>
                  <tr>
                    <th scope="col">Code / item</th>
                    <th scope="col">Category</th>
                    <th scope="col">Fixed unit</th>
                  </tr>
                </thead>
                <tbody>
                  {catalog?.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.code}</strong>
                        <span className="relief-secondary">{item.name}</span>
                      </td>
                      <td>{categories[item.category]}</td>
                      <td>{item.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!catalog?.items.length && (
              <p className="tools-muted">No supply items recorded.</p>
            )}
          </section>
          <section className="tools-panel">
            <h2>Storage locations</h2>
            <p className="tools-muted">
              Keep a separate balance for each item and location. This prototype
              records stores; transfer workflows and batch/expiry tracking
              remain separate work.
            </p>
            {canEdit && (
              <form
                className="relief-form"
                onSubmit={(event) => void saveCatalog(event, "location")}
              >
                <label>
                  Location code
                  <input
                    required
                    maxLength={64}
                    value={locationForm.code}
                    disabled={busy}
                    onChange={(event) =>
                      setLocationForm({
                        ...locationForm,
                        code: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  Location name
                  <input
                    required
                    minLength={2}
                    maxLength={120}
                    value={locationForm.name}
                    disabled={busy}
                    onChange={(event) =>
                      setLocationForm({
                        ...locationForm,
                        name: event.target.value,
                      })
                    }
                  />
                </label>
                <label className="relief-full-field">
                  Storage locality
                  <input
                    required
                    minLength={2}
                    maxLength={160}
                    value={locationForm.locality}
                    disabled={busy}
                    onChange={(event) =>
                      setLocationForm({
                        ...locationForm,
                        locality: event.target.value,
                      })
                    }
                  />
                </label>
                <div className="relief-form-actions">
                  <button className="button primary" disabled={busy}>
                    Save storage location
                  </button>
                </div>
              </form>
            )}
            <p className="relief-scroll-hint inventory-catalog-hint">
              Scroll the location table sideways for the full locality.
            </p>
            <div className="inventory-catalog-scroll table-scroll">
              <table className="tools-table">
                <thead>
                  <tr>
                    <th scope="col">Code / store</th>
                    <th scope="col">Locality</th>
                  </tr>
                </thead>
                <tbody>
                  {catalog?.locations.map((location) => (
                    <tr key={location.id}>
                      <td>
                        <strong>{location.code}</strong>
                        <span className="relief-secondary">
                          {location.name}
                        </span>
                      </td>
                      <td>{location.locality}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!catalog?.locations.length && (
              <p className="tools-muted">No storage locations recorded.</p>
            )}
          </section>
        </>
      )}
      {mode === "detail" && detail && position && (
        <>
          <section className="tools-panel">
            <div className="tools-panel-heading">
              <h2 ref={heading} tabIndex={-1}>
                {position.item.name}
              </h2>
              <span>
                {position.item.code} · {position.location.code} · Version{" "}
                {position.version}
              </span>
            </div>
            <p className="tools-muted">
              {position.location.name} · {position.location.locality} · All
              quantities in <strong>{position.item.unit}</strong>.
            </p>
            <dl className="inventory-balances">
              <div>
                <dt>Recorded on hand</dt>
                <dd>
                  {position.on_hand} {position.item.unit}
                </dd>
              </div>
              <div>
                <dt>Reserved</dt>
                <dd>
                  {position.reserved} {position.item.unit}
                </dd>
              </div>
              <div>
                <dt>Available to reserve</dt>
                <dd>
                  {position.available} {position.item.unit}
                </dd>
              </div>
            </dl>
            <div className="inventory-source-count">
              <h3>Latest source-reported count</h3>
              {position.latest_report ? (
                <p>
                  {position.latest_report.quantity} {position.item.unit} ·{" "}
                  {position.latest_report.source_name}
                  <span className="relief-secondary">
                    Observed {when(position.latest_report.observed_at)} ·
                    Received {when(position.latest_report.received_at)}
                  </span>
                </p>
              ) : (
                <p>No source count recorded.</p>
              )}
              <p className="tools-muted">
                A separate report, not an update to stock. Compare its source
                time with subsequent movements before reconciling differences.
              </p>
            </div>
            <div className="tools-actions">
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => {
                  clearMessages();
                  void open(position.item.id, position.location.id).catch(
                    () => {},
                  );
                }}
              >
                <RefreshCw size={15} />
                Refresh stock details
              </button>
            </div>
          </section>
          {canEdit && (
            <section className="tools-panel">
              <h2>Record a stock event</h2>
              <p className="tools-muted">
                Each saved event is retained. Corrections use a new, reasoned
                adjustment. Confirm the source before saving; nothing is
                dispatched by this form.
              </p>
              <form className="relief-form" onSubmit={saveRecord}>
                <label>
                  Event type
                  <select
                    value={eventForm.kind}
                    disabled={busy}
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        kind: event.target.value as Kind,
                        parent_id: "",
                        request_id: "",
                      })
                    }
                  >
                    {Object.entries(kinds).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Event reference
                  <input
                    required
                    maxLength={64}
                    value={eventForm.reference}
                    disabled={busy}
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        reference: event.target.value,
                      })
                    }
                  />
                </label>
                <p className="tools-muted relief-full-field inventory-event-help">
                  {explanation[eventForm.kind]}
                </p>
                {eventForm.kind === "reserve" && (
                  <>
                    <label className="relief-full-field">
                      Find a reviewed request
                      <input
                        value={needQuery}
                        placeholder="Search request reference or organisation"
                        disabled={busy}
                        onChange={(event) => {
                          setNeedQuery(event.target.value);
                          setEventForm({ ...eventForm, request_id: "" });
                        }}
                      />
                    </label>
                    <label className="relief-full-field">
                      Reviewed relief request
                      <select
                        required
                        value={eventForm.request_id}
                        disabled={busy || needsLoading}
                        onChange={(event) =>
                          setEventForm({
                            ...eventForm,
                            request_id: event.target.value,
                          })
                        }
                      >
                        <option value="">
                          {needsLoading
                            ? "Loading reviewed requests…"
                            : "Choose a reviewed request"}
                        </option>
                        {needs.items.map((need) => (
                          <option
                            key={need.id}
                            value={need.id}
                            disabled={
                              need.allocation_warning ||
                              Number(need.remaining) <= 0
                            }
                          >
                            {need.reference} · {need.organisation} ·{" "}
                            {need.remaining} {need.unit} remaining
                            {need.allocation_warning
                              ? " · Check earlier units"
                              : ""}
                          </option>
                        ))}
                      </select>
                    </label>
                    <p className="tools-muted relief-full-field inventory-event-help">
                      Showing up to 20 of {needs.total} reviewed requests with
                      matching category/unit. Search a specific reference for
                      older needs. Selection does not infer that an item is a
                      suitable substitute.
                    </p>
                    {needsError && (
                      <div
                        className="message error relief-full-field"
                        role="alert"
                      >
                        {needsError}
                      </div>
                    )}
                  </>
                )}
                {["release", "issue", "return"].includes(eventForm.kind) && (
                  <>
                    <label className="relief-full-field">
                      {eventForm.kind === "return"
                        ? "Original issue"
                        : "Original reservation"}
                      <select
                        required
                        value={eventForm.parent_id}
                        disabled={busy}
                        onChange={(event) =>
                          setEventForm({
                            ...eventForm,
                            parent_id: event.target.value,
                          })
                        }
                      >
                        <option value="">Choose an earlier record</option>
                        {parents.map((record) => (
                          <option key={record.id} value={record.id}>
                            {record.reference} · {record.request_reference} ·{" "}
                            {record.remaining_quantity} {position.item.unit}{" "}
                            remaining
                          </option>
                        ))}
                      </select>
                    </label>
                    <p className="tools-muted relief-full-field inventory-event-help">
                      Choices come from the history loaded below. Load older
                      history to find earlier reservations or issues.
                    </p>
                  </>
                )}
                <label>
                  Quantity ({position.item.unit})
                  <input
                    required
                    type="number"
                    min={eventForm.kind === "report" ? "0" : "0.001"}
                    max="1000000000"
                    step="0.001"
                    value={eventForm.quantity}
                    disabled={busy}
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        quantity: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  Source time (your local time)
                  <input
                    required
                    type="datetime-local"
                    step="1"
                    value={eventForm.observed_at}
                    disabled={busy}
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        observed_at: event.target.value,
                      })
                    }
                  />
                </label>
                <label className="relief-full-field">
                  Source or receipt name
                  <input
                    required
                    minLength={2}
                    maxLength={120}
                    value={eventForm.source_name}
                    disabled={busy}
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        source_name: event.target.value,
                      })
                    }
                  />
                </label>
                <label className="relief-full-field">
                  Reason / evidence note
                  <textarea
                    required
                    maxLength={500}
                    rows={3}
                    value={eventForm.reason}
                    disabled={busy}
                    onChange={(event) =>
                      setEventForm({ ...eventForm, reason: event.target.value })
                    }
                  />
                </label>
                <div className="relief-form-actions">
                  <button className="button primary" disabled={busy}>
                    {busy ? "Recording stock…" : "Record stock event"}
                  </button>
                </div>
              </form>
            </section>
          )}
          <section className="tools-panel">
            <h2>Stock history</h2>
            <p className="tools-muted">
              Newest recorded event first. Source time may be earlier than
              receipt time. Balances follow recording order; reports do not
              alter them.
            </p>
            {!detail.records.length ? (
              <p className="tools-muted">
                No stock events recorded at this location.
              </p>
            ) : (
              <ol className="relief-history inventory-history">
                {detail.records.map((record) => (
                  <li key={record.id}>
                    <div className="relief-event-heading">
                      <strong>
                        {kinds[record.kind]} · {record.quantity}{" "}
                        {position.item.unit}
                      </strong>
                      <span>
                        {record.reference} · Event {record.sequence}
                      </span>
                    </div>
                    <p>{record.reason}</p>
                    <small>
                      {record.actor}
                      <br />
                      Source: {record.source_name} · {when(record.observed_at)}
                      <br />
                      Recorded {when(record.received_at)}
                      {record.request_reference && (
                        <>
                          <br />
                          Relief request: {record.request_reference}
                        </>
                      )}
                    </small>
                    {record.parent_reference && (
                      <p className="tools-muted">
                        Against original record: {record.parent_reference}
                      </p>
                    )}
                    <p className="inventory-after">
                      After event: {record.after.on_hand} on hand ·{" "}
                      {record.after.reserved} reserved ·{" "}
                      {record.after.available} available ({position.item.unit})
                    </p>
                    {record.remaining_quantity !== null && (
                      <p className="tools-muted">
                        Currently {record.remaining_quantity}{" "}
                        {position.item.unit}{" "}
                        {record.kind === "issue"
                          ? "unreturned"
                          : "unissued / unreleased"}
                        .
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            )}
            {detail.next_before_sequence !== null && (
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => void olderHistory()}
              >
                Load older stock history
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}
