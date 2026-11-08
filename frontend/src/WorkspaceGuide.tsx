import { ArrowRight, Clock3, ShieldCheck } from "lucide-react";

export default function WorkspaceGuide({
  freshnessHours = 24,
  onStart,
  actionLabel = "Start an import",
  disabled = false,
}: {
  freshnessHours?: number;
  onStart: () => void;
  actionLabel?: string;
  disabled?: boolean;
}) {
  return (
    <div className="guide-layout">
      <section className="guide-content">
        <h2>One file. A traceable register.</h2>
        <p>
          Sampati brings fictional civilian aircraft reports into one workspace.
          It preserves where information came from and when the source reported
          it.
        </p>
        <ol className="guide-steps">
          <li>
            <span>1</span>
            <div>
              <h3>Choose your dataset</h3>
              <p>
                Use CSV or Excel with the template’s six columns. Include an
                explicit timezone, such as Z or +05:30, in every source
                timestamp.
              </p>
            </div>
          </li>
          <li>
            <span>2</span>
            <div>
              <h3>Review every change</h3>
              <p>
                New, updated and unchanged records are separated. Invalid or
                conflicting reports prevent the whole batch from being saved.
              </p>
            </div>
          </li>
          <li>
            <span>3</span>
            <div>
              <h3>Confirm, then explore</h3>
              <p>
                Accepted records are saved to the local database. Search your
                register and open import history to trace a change.
              </p>
            </div>
          </li>
        </ol>
        <h2>Status and freshness are different.</h2>
        <p>
          “Available” is a statement from the source, not independent
          verification. A record can be reported available while its information
          is outdated.
        </p>
        <div className="guide-note">
          <Clock3 size={20} />
          <p>
            The demo marks reports older than {freshnessHours} hours, or more
            than five minutes in the future, as needing review. This is a
            project convention, not an aviation standard.
          </p>
        </div>
        <h2>Built for a local learning session.</h2>
        <p>
          Explore shared fictional records in Demo workspace, or sign in to keep
          a separate organisation register. New organisations start empty, and
          account imports stay separate from the demo. Connect a changing file
          from Data connections; incoming files wait for review. Invite
          teammates from Organisation team and save recovery codes in Account
          settings. Automation inbox checks structured relief files and proposes
          new request drafts. Owners can allow a trusted source to create drafts
          automatically; needs, stock movements and delivery evidence still need
          human review. Overview summarises accepted records using counts and rules.
          Keep this learning prototype on your own computer.
        </p>
        <button
          className="button primary"
          disabled={disabled}
          onClick={onStart}
        >
          {actionLabel}
          <ArrowRight size={16} />
        </button>
      </section>
      <aside className="guide-aside">
        <ShieldCheck size={28} strokeWidth={1.4} />
        <h3>
          Source first.
          <br />
          Changes second.
        </h3>
        <p>
          Older reports cannot silently replace newer records. Missing rows
          never delete an aircraft. Importing the same dataset twice is a no-op.
        </p>
        <p>
          Aircraft availability here does not certify airworthiness or authorise
          a flight.
        </p>
      </aside>
    </div>
  );
}
