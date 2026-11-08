import { useEffect, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { api } from "./api";

type Summary = {
  generated_at: string;
  needs_total: number;
  needs: {
    id: string;
    reference: string;
    locality: string;
    item_name: string;
    unit: string;
    quantity: string;
    remaining: string;
    needed_by: string;
    overdue: boolean;
  }[];
  attention: Record<string, number>;
  method: string;
};
type Destination =
  "incidents" | "relief" | "automation" | "deliveries" | "inventory";
const rows: [string, string, Destination][] = [
  ["incidents", "Incidents awaiting review", "incidents"],
  ["requests", "Draft or submitted requests", "relief"],
  ["intake", "Intake files awaiting a decision", "automation"],
  ["shipments", "Shipments awaiting resolution", "deliveries"],
  ["stock_positions", "Recorded stock positions", "inventory"],
];

export default function ReliefOverview({
  onOpen,
}: {
  onOpen?: (view: Destination) => void;
}) {
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function refresh() {
    setLoading(true);
    try {
      setData(await api<Summary>("/overview/relief"));
      setError("");
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
  }, []);
  function download() {
    if (!data) return;
    const url = URL.createObjectURL(
      new Blob(
        [
          JSON.stringify(
            { schema_version: "sampati.relief-overview.v1", ...data },
            null,
            2,
          ),
        ],
        { type: "application/json" },
      ),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "sampati-relief-overview.json";
    link.click();
    URL.revokeObjectURL(url);
  }
  return (
    <>
      <section className="tools-panel">
        <div className="tools-panel-heading">
          <h2>Relief work awaiting attention</h2>
          <div className="tools-actions">
            <button
              className="button secondary"
              disabled={loading}
              onClick={() => void refresh()}
            >
              <RefreshCw size={15} />
              Refresh relief overview
            </button>
            <button
              className="button secondary"
              disabled={!data || loading}
              onClick={download}
            >
              <Download size={15} />
              Export relief overview
            </button>
          </div>
        </div>
        {error && (
          <p className="message error" role="alert">
            {error}
          </p>
        )}
        {loading && !data && <p role="status">Loading relief records…</p>}
        {data && (
          <>
            <p className="tools-muted">
              A handover view of your organisation’s recorded work. Updated{" "}
              {new Date(data.generated_at).toLocaleString()}.
            </p>
            <div className="table-scroll">
              <table className="tools-table">
                <thead>
                  <tr>
                    <th scope="col">Work queue</th>
                    <th scope="col">Records</th>
                    <th scope="col">Next step</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(([key, label, destination]) => (
                    <tr key={key}>
                      <td>{label}</td>
                      <td>{data.attention[key]}</td>
                      <td>
                        <button
                          className="button secondary"
                          onClick={() => onOpen?.(destination)}
                        >
                          Open{" "}
                          {destination === "relief"
                            ? "requests"
                            : destination === "automation"
                              ? "inbox"
                              : destination === "deliveries"
                                ? "shipments"
                                : destination}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>
      {data && (
        <section className="tools-panel">
          <h2>Reviewed needs still awaiting delivery</h2>
          <p className="tools-muted">
            {data.needs_total} needs have an unconfirmed remainder. Showing the
            earliest 20 deadlines. Stock issues and shipment drafts do not count
            as arrivals.
          </p>
          {data.needs.length ? (
            <div className="table-scroll">
              <table className="tools-table">
                <thead>
                  <tr>
                    <th scope="col">Request</th>
                    <th scope="col">Locality &amp; supply</th>
                    <th scope="col">Still needed</th>
                    <th scope="col">Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {data.needs.map((need) => (
                    <tr key={need.id}>
                      <td>{need.reference}</td>
                      <td>
                        {need.locality}
                        <span className="relief-secondary">
                          {need.item_name}
                        </span>
                      </td>
                      <td>
                        {need.remaining} of {need.quantity} {need.unit}
                      </td>
                      <td>
                        {new Date(need.needed_by).toLocaleString()}
                        {need.overdue && (
                          <span className="relief-past-due">
                            Past recorded deadline
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="tools-muted">
              No reviewed requests with a recorded delivery remainder. Check
              draft requests and intake files before interpreting this as an
              absence of needs.
            </p>
          )}
          <p className="tools-muted">{data.method}</p>
        </section>
      )}
    </>
  );
}
