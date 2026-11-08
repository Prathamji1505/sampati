import { ArrowRight, BookOpen } from "lucide-react";
import Brand from "./Brand";
import "./welcome.css";

export default function Welcome({
  onEnter,
  onGuide,
  onHome,
}: {
  onEnter: () => void;
  onGuide: () => void;
  onHome: () => void;
}) {
  return (
    <div className="welcome-screen">
      <a
        className="skip-link"
        href="#welcome-main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("welcome-main")?.focus();
        }}
      >
        Skip to content
      </a>
      <header className="welcome-header">
        <Brand onNavigate={onHome} />
        <span className="demo-label">LOCAL DEMO</span>
      </header>
      <main id="welcome-main" className="welcome-main" tabIndex={-1}>
        <img
          className="welcome-art"
          src="/artwork/sampati-folk-sky.png"
          alt=""
          width={2172}
          height={724}
          fetchPriority="high"
          draggable={false}
        />
        <div className="welcome-copy">
          <h1 id="welcome-title" tabIndex={-1}>
            Sampati
          </h1>
          <p className="welcome-devanagari" lang="hi">
            सम्पाति
          </p>
          <p className="welcome-purpose">
            Disaster Response &amp;
            <br />
            Relief Coordination
          </p>
          <p className="welcome-description">
            Review relief requests and aircraft reports. Keep every source and
            change in view.
          </p>
          <button className="button primary welcome-enter" onClick={onEnter}>
            Enter workspace
            <ArrowRight size={19} aria-hidden="true" />
          </button>
        </div>
      </main>
      <footer className="welcome-footer">
        <p>
          Fictional aircraft data <span aria-hidden="true">·</span> Local
          prototype
        </p>
        <button className="text-button welcome-guide" onClick={onGuide}>
          <BookOpen size={16} aria-hidden="true" />
          Read workspace guide
          <ArrowRight size={15} aria-hidden="true" />
        </button>
      </footer>
    </div>
  );
}
