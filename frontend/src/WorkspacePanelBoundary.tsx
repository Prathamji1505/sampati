import { Component } from "react";
import type { ReactNode } from "react";

/** Keep navigation usable when a newly deployed module cannot be downloaded. */
export default class WorkspacePanelBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <section className="empty-state" role="alert">
          <h2>The workspace tools could not load</h2>
          <p>
            The application may have been updated or the connection interrupted.
            Reload this workspace to fetch the current version.
          </p>
          <button
            className="button primary"
            onClick={() => window.location.reload()}
          >
            Reload workspace
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}
