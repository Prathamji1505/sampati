import { ArrowLeft } from "lucide-react";
import Brand from "./Brand";
import WorkspaceGuide from "./WorkspaceGuide";
import "./welcome.css";
import "./welcome-guide.css";

export default function WelcomeGuide({
  onHome,
  onEnter,
}: {
  onHome: () => void;
  onEnter: () => void;
}) {
  return (
    <div className="public-guide-page">
      <a
        className="skip-link"
        href="#public-guide-main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("public-guide-main")?.focus();
        }}
      >
        Skip to content
      </a>
      <header className="welcome-header">
        <Brand onNavigate={onHome} />
        <button className="button secondary" onClick={onHome}>
          <ArrowLeft size={16} aria-hidden="true" />
          Back to welcome
        </button>
      </header>
      <main id="public-guide-main" className="public-guide-main" tabIndex={-1}>
        <div className="public-guide-heading">
          <h1 id="page-title" tabIndex={-1}>
            Your workspace, explained
          </h1>
          <p>Learn how Sampati works before you enter your workspace.</p>
        </div>
        <WorkspaceGuide onStart={onEnter} actionLabel="Enter workspace" />
      </main>
      <footer className="welcome-footer public-guide-footer">
        <div>
          <strong>
            SAMPATI · <span lang="hi">सम्पाति</span>
          </strong>
          <p>Source first. Every change, traceable.</p>
        </div>
        <p>Fictional aircraft data · Local prototype</p>
      </footer>
    </div>
  );
}
