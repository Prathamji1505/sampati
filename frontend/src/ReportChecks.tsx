import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownToLine, Check, RefreshCw, Search } from "lucide-react";
import { api } from "./api";
import type { Workspace, WorkspaceScope } from "./types";
import "./workspace-tools.css";
import "./report-checks.css";

type Finding = {
  code: string;
  message: string;
  next_step: string;
  count: number;
  examples: {
    incoming_id: string;
    filename: string;
    source_updated_at: string;
    reported_status: string;
  }[];
};
type CheckedReport = {
  aircraft_id: string;
  display_name: string;
  reported_status: string;
  source_name: string;
  source_updated_at: string;
  source_timestamp_raw: string;
  last_import_id: string;
  freshness: string;
  result: "review" | "complete";
  findings: Finding[];
};
type CheckReport = {
  workspace_id: string;
  workspace_revision: number;
  generated_at: string;
  rule_version: string;
  freshness_hours: number;
  checks: { code: string; label: string; description: string }[];
  summary: {
    records: number;
    needs_review: number;
    complete: number;
    pending_files: number;
    pending_new_ids: number;
  };
  counts_by_code: Record<string, number>;
  records: CheckedReport[];
  meaning: string;
};
const when = (value: string) => new Date(value).toLocaleString();
const PAGE_SIZE = 20;

export default function ReportChecks({
  workspace,
  scope,
  onInspect,
  onInbox,
}: {
  workspace: Workspace | null;
  scope: WorkspaceScope;
  onInspect: (id: string) => void;
  onInbox: () => void;
}) {
  const [report, setReport] = useState<CheckReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState("all");
  const [code, setCode] = useState("all");
  const [page, setPage] = useState(0);
  const epoch = useRef(0);
  async function refresh() {
    const current = ++epoch.current;
    setLoading(true);
    try {
      const next = await api<CheckReport>("/report-checks");
      if (epoch.current === current) {
        setReport(next);
        setError("");
      }
    } catch (problem) {
      if (epoch.current === current) setError((problem as Error).message);
    } finally {
      if (epoch.current === current) setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
    return () => {
      epoch.current += 1;
    };
  }, [scope, workspace?.server_time]);
  const filtered = useMemo(
    () =>
      (report?.records || []).filter(
        (item) =>
          (result === "all" || item.result === result) &&
          (code === "all" ||
            item.findings.some((finding) => finding.code === code)) &&
          `${item.aircraft_id} ${item.display_name} ${item.source_name}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [report, result, code, query],
  );
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pages - 1);
  const visible = filtered.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  );
  const labels = Object.fromEntries(
    (report?.checks || []).map((check) => [check.code, check.label]),
  );

  function download() {
    if (!report) return;
    const body = {
      workspace_id: report.workspace_id,
      workspace_revision: report.workspace_revision,
      generated_at: report.generated_at,
      rule_version: report.rule_version,
      freshness_hours: report.freshness_hours,
      meaning: report.meaning,
      filters: { query, result, code },
      record_count: filtered.length,
      records: filtered,
    };
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(body, null, 2)], { type: "application/json" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "sampati-report-checks.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <div className="workspace-tools">
      {error && (
        <div className="message error" role="alert">
          {error}
        </div>
      )}
      <div className="tools-toolbar">
        <span>
          {loading
            ? "Checking source reports…"
            : `Checked ${report ? when(report.generated_at) : "—"} · Revision ${report?.workspace_revision ?? "—"}`}
        </span>
        <div className="tools-actions">
          <button
            className="button secondary"
            disabled={loading}
            onClick={() => void refresh()}
          >
            <RefreshCw size={15} />
            Refresh checks
          </button>
          <button
            className="button secondary"
            disabled={loading || !report}
            onClick={download}
          >
            <ArrowDownToLine size={15} />
            Export filtered results
          </button>
        </div>
      </div>
      <p className="quality-explanation">
        These checks describe source records. They do not determine aircraft
        condition, availability or flight clearance. The source’s reported
        status is preserved.
      </p>
      {(report?.summary.pending_files || 0) > 0 && (
        <div className="quality-inbox-note">
          <p>
            {report?.summary.pending_files} incoming{" "}
            {report?.summary.pending_files === 1
              ? "file awaits"
              : "files await"}{" "}
            review.
            {(report?.summary.pending_new_ids || 0) > 0 &&
              ` The inbox includes ${report?.summary.pending_new_ids} new aircraft ${report?.summary.pending_new_ids === 1 ? "ID" : "IDs"} outside the accepted register.`}
          </p>
          {scope === "private" && (
            <button className="button secondary" onClick={onInbox}>
              Open incoming inbox
            </button>
          )}
        </div>
      )}
      <section
        className="register-panel"
        aria-label="Source report checks"
        aria-busy={loading}
      >
        <div
          className="status-tabs quality-tabs"
          role="group"
          aria-label="Filter by check result"
        >
          {(
            [
              ["all", "All reports", report?.summary.records],
              ["review", "Needs review", report?.summary.needs_review],
              ["complete", "Complete reports", report?.summary.complete],
            ] as const
          ).map(([value, label, count]) => (
            <button
              key={value}
              className={result === value ? "selected" : ""}
              aria-pressed={result === value}
              onClick={() => {
                setResult(value);
                setPage(0);
              }}
            >
              {label}
              <span>{count ?? 0}</span>
            </button>
          ))}
        </div>
        <div className="table-toolbar">
          <label className="search-field">
            <Search size={17} />
            <input
              aria-label="Search report checks"
              placeholder="Search aircraft or source…"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(0);
              }}
            />
          </label>
          <label className="select-field">
            <select
              aria-label="Filter by finding"
              value={code}
              onChange={(event) => {
                setCode(event.target.value);
                setPage(0);
              }}
            >
              <option value="all">All findings</option>
              {report?.checks.map((check) => (
                <option key={check.code} value={check.code}>
                  {check.label} ({report.counts_by_code[check.code] || 0})
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="quality-scroll-hint">
          Scroll the table sideways for more report details.
        </p>
        {!report && loading ? (
          <p className="quality-empty" role="status">
            Loading report checks…
          </p>
        ) : !report ? (
          <div className="quality-empty">
            <h2>Report checks are unavailable.</h2>
            <p>Use Refresh checks to retry when the local server is ready.</p>
          </div>
        ) : !filtered.length ? (
          <div className="quality-empty">
            <h2>
              {report?.summary.records
                ? "No reports match these filters."
                : "No accepted reports to check yet."}
            </h2>
            <p>
              {report?.summary.records
                ? "Change the finding filter or search to see more reports."
                : "Confirm a dataset to see its record checks here."}
            </p>
            {report?.summary.records ? (
              <button
                className="button secondary"
                onClick={() => {
                  setQuery("");
                  setResult("all");
                  setCode("all");
                  setPage(0);
                }}
              >
                Clear filters
              </button>
            ) : null}
          </div>
        ) : (
          <div className="table-scroll">
            <table className="tools-table quality-table">
              <thead>
                <tr>
                  <th>Aircraft</th>
                  <th>Data checks</th>
                  <th>Reported status</th>
                  <th>Source report</th>
                  <th>Record</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr key={item.aircraft_id}>
                    <td>
                      <strong>{item.aircraft_id}</strong>
                      <span className="quality-secondary">
                        {item.display_name || "No display name"}
                      </span>
                    </td>
                    <td className="quality-findings">
                      {item.findings.length ? (
                        <details>
                          <summary>
                            {item.findings.length}{" "}
                            {item.findings.length === 1
                              ? "finding"
                              : "findings"}{" "}
                            · Needs review
                          </summary>
                          <ul>
                            {item.findings.map((finding) => (
                              <li key={finding.code}>
                                <strong>{labels[finding.code]}</strong>
                                <p>{finding.message}</p>
                                <p className="quality-next-step">
                                  {finding.next_step}
                                </p>
                                {finding.examples.length > 0 && (
                                  <>
                                    <small>
                                      {finding.count} pending{" "}
                                      {finding.count === 1 ? "file" : "files"};
                                      up to three shown
                                    </small>
                                    <ul className="quality-evidence">
                                      {finding.examples.map((example) => (
                                        <li key={example.incoming_id}>
                                          {example.filename} ·{" "}
                                          {when(example.source_updated_at)} ·{" "}
                                          {example.reported_status}
                                        </li>
                                      ))}
                                    </ul>
                                  </>
                                )}
                              </li>
                            ))}
                          </ul>
                        </details>
                      ) : (
                        <span className="quality-complete">
                          <Check size={14} />
                          Complete report
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={`status status-${item.reported_status}`}>
                        <span aria-hidden="true" />
                        {item.reported_status === "available"
                          ? "Reported available"
                          : item.reported_status === "unavailable"
                            ? "Unavailable"
                            : "Unknown"}
                      </span>
                    </td>
                    <td>
                      <span className="quality-source-name">
                        {item.source_name}
                      </span>
                      <time
                        className="quality-secondary"
                        dateTime={item.source_updated_at}
                      >
                        {when(item.source_updated_at)}
                      </time>
                    </td>
                    <td>
                      <button
                        className="button secondary"
                        aria-label={`Inspect ${item.aircraft_id} report`}
                        disabled={
                          !workspace?.aircraft.some(
                            (row) => row.aircraft_id === item.aircraft_id,
                          )
                        }
                        onClick={() => onInspect(item.aircraft_id)}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="table-footer quality-pagination">
          <span>
            {filtered.length} filtered{" "}
            {filtered.length === 1 ? "report" : "reports"} · {PAGE_SIZE} per
            page
          </span>
          <div className="tools-actions">
            <button
              className="button secondary"
              disabled={currentPage === 0}
              onClick={() => setPage(currentPage - 1)}
            >
              Previous
            </button>
            <span>
              Page {currentPage + 1} of {pages}
            </span>
            <button
              className="button secondary"
              disabled={currentPage >= pages - 1}
              onClick={() => setPage(currentPage + 1)}
            >
              Next
            </button>
          </div>
        </div>
      </section>
      <details className="quality-rules">
        <summary>How these checks work</summary>
        <p>
          Rules {report?.rule_version || "report-data-v1"} use one check time
          and the workspace’s {report?.freshness_hours ?? 24}-hour demo
          freshness threshold. Counts refer to aircraft reports, rather than the
          number of incoming files. A complete report can still say unavailable.
          Free-text notes are never used to guess mechanical condition.
        </p>
        <ul>
          {report?.checks.map((check) => (
            <li key={check.code}>
              <strong>{check.label}</strong>
              <span>{check.description}</span>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
