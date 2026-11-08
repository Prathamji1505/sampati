import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  ClipboardCheck,
  PackagePlus,
  Waves,
  ChevronDown,
  ChevronRight,
  CircleAlert,
  Clock3,
  Database,
  FileCheck2,
  FileSpreadsheet,
  FolderOpen,
  History,
  Info,
  LayoutList,
  BarChart3,
  Plug,
  Users,
  Settings,
  LogIn,
  LogOut,
  Menu,
  Plane,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import { api, configureApi, downloadRegister } from "./api";
import AuthScreen from "./AuthScreen";
import WorkspaceTools from "./WorkspaceTools";
import ReportChecks from "./ReportChecks";
import ReliefRequests from "./ReliefRequests";
import Incidents from "./Incidents";
import type { IncidentDraft } from "./Incidents";
import Brand from "./Brand";
import Welcome from "./Welcome";
import WelcomeGuide from "./WelcomeGuide";
import WorkspaceGuide from "./WorkspaceGuide";
import type {
  Aircraft,
  Change,
  ImportBatch,
  Preview,
  ReportedStatus,
  Workspace,
  SessionState,
  WorkspaceScope,
} from "./types";

type View =
  | "aircraft"
  | "upload"
  | "history"
  | "guide"
  | "overview"
  | "checks"
  | "relief"
  | "incidents"
  | "sources"
  | "team"
  | "account";
type Route =
  "welcome" | "welcomeGuide" | "login" | "register" | "recover" | View;
const routeFragments: Record<Route, string> = {
  welcome: "",
  welcomeGuide: "welcome/guide",
  aircraft: "workspace",
  upload: "import",
  history: "history",
  guide: "guide",
  login: "login",
  register: "register",
  recover: "recover",
  overview: "overview",
  checks: "checks",
  relief: "relief",
  incidents: "incidents",
  sources: "sources",
  team: "team",
  account: "account",
};
const pageNames: Record<Route, string> = {
  welcome: "Welcome",
  welcomeGuide: "Workspace guide",
  aircraft: "Aircraft register",
  upload: "Import dataset",
  history: "Import history",
  guide: "Workspace guide",
  login: "Sign in",
  register: "Create account",
  recover: "Recover account",
  overview: "Workspace overview",
  checks: "Report checks",
  relief: "Relief requests",
  incidents: "Incident review",
  sources: "Data connections",
  team: "Organisation team",
  account: "Account settings",
};
function currentRoute(): Route {
  const fragment = window.location.hash.slice(1).replace(/^demo\//, "");
  return (
    (Object.keys(routeFragments) as Route[]).find(
      (route) => routeFragments[route] === fragment,
    ) ?? "welcome"
  );
}
function currentScope(): WorkspaceScope {
  return window.location.hash.startsWith("#demo/") ? "demo" : "private";
}
const statusLabels: Record<ReportedStatus, string> = {
  available: "Reported available",
  unavailable: "Unavailable",
  unknown: "Unknown",
};
const shortStatus: Record<ReportedStatus, string> = {
  available: "Available",
  unavailable: "Unavailable",
  unknown: "Unknown",
};
const dateFormat = new Intl.DateTimeFormat(undefined, {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});
function date(value: string) {
  return dateFormat.format(new Date(value));
}
function ago(value: string) {
  const minutes = Math.round((Date.now() - new Date(value).getTime()) / 60000);
  if (minutes < -5) return "Future-dated";
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 1440) return `${Math.floor(minutes / 60)} hr ago`;
  const days = Math.floor(minutes / 1440);
  return `${days} ${days === 1 ? "day" : "days"} ago`;
}
function Status({ value }: { value: ReportedStatus }) {
  return (
    <span className={`status status-${value}`}>
      <span aria-hidden="true" />
      {statusLabels[value]}
    </span>
  );
}
function Freshness({ item }: { item: Aircraft }) {
  return (
    <span className={`freshness freshness-${item.freshness}`}>
      <span aria-hidden="true" />
      {item.freshness === "current"
        ? "Current report"
        : item.freshness === "future"
          ? "Check timestamp"
          : "Needs review"}
    </span>
  );
}

export default function App() {
  const [route, setRoute] = useState<Route>(currentRoute);
  const [scope, setScope] = useState<WorkspaceScope>(currentScope);
  const [session, setSession] = useState<SessionState | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [sessionMessage, setSessionMessage] = useState("");
  const sessionEpoch = useRef(0);
  configureApi(scope, session?.csrf_token ?? null);

  function announceAuthChange() {
    try {
      localStorage.setItem("sampati-auth-event", String(Date.now()));
    } catch {
      /* Session credentials are never stored here. */
    }
  }

  useEffect(() => {
    async function followSession() {
      const epoch = ++sessionEpoch.current;
      try {
        const next = await api<SessionState>("/auth/session");
        if (epoch === sessionEpoch.current) setSession(next);
      } catch (problem) {
        if (epoch === sessionEpoch.current)
          setSessionMessage((problem as Error).message);
      } finally {
        if (epoch === sessionEpoch.current) setSessionLoading(false);
      }
    }
    const expired = () => {
      sessionEpoch.current += 1;
      setSession(null);
      setSessionMessage(
        "Your session has ended. Sign in again to continue in your private workspace.",
      );
    };
    const changedInAnotherTab = (event: StorageEvent) => {
      if (event.key === "sampati-auth-event") void followSession();
    };
    void followSession();
    window.addEventListener("focus", followSession);
    window.addEventListener("storage", changedInAnotherTab);
    window.addEventListener("sampati:session-expired", expired);
    const sessionTimer = window.setInterval(() => {
      if (document.visibilityState === "visible") void followSession();
    }, 30000);
    return () => {
      window.removeEventListener("focus", followSession);
      window.removeEventListener("storage", changedInAnotherTab);
      window.removeEventListener("sampati:session-expired", expired);
      window.clearInterval(sessionTimer);
    };
  }, []);

  useEffect(() => {
    const followLocation = () => {
      setRoute(currentRoute());
      setScope(currentScope());
    };
    window.addEventListener("popstate", followLocation);
    window.addEventListener("hashchange", followLocation);
    return () => {
      window.removeEventListener("popstate", followLocation);
      window.removeEventListener("hashchange", followLocation);
    };
  }, []);

  useEffect(() => {
    document.title = `${pageNames[route]} · Sampati · सम्पाति`;
    const frame = requestAnimationFrame(() => {
      document
        .getElementById(
          route === "welcome"
            ? "welcome-title"
            : route === "login" || route === "register" || route === "recover"
              ? "auth-title"
              : "page-title",
        )
        ?.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    });
    return () => cancelAnimationFrame(frame);
  }, [route]);

  function navigate(next: Route, nextScope: WorkspaceScope = scope) {
    const isDataView =
      next !== "welcome" &&
      next !== "welcomeGuide" &&
      next !== "login" &&
      next !== "register" &&
      next !== "recover";
    const fragment = `${isDataView && nextScope === "demo" ? "demo/" : ""}${routeFragments[next]}`;
    window.history.pushState(
      null,
      "",
      `${window.location.pathname}${window.location.search}${fragment ? `#${fragment}` : ""}`,
    );
    setRoute(next);
    setScope(nextScope);
  }

  function authenticated(next: SessionState) {
    sessionEpoch.current += 1;
    setSession(next);
    setSessionMessage("");
    announceAuthChange();
    navigate("aircraft", "private");
  }

  function updateSession(next: SessionState) {
    sessionEpoch.current += 1;
    setSession(next);
    announceAuthChange();
  }

  async function selectWorkspace(value: string) {
    if (value === "demo" || value === "private") {
      navigate("aircraft", value);
      return;
    }
    const next = await api<SessionState>("/auth/workspace", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_id: value }),
    });
    updateSession(next);
    navigate("aircraft", "private");
  }

  async function signOut() {
    await api("/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    sessionEpoch.current += 1;
    setSession(null);
    setSessionMessage("");
    announceAuthChange();
    navigate("aircraft", "demo");
  }

  if (route === "welcome") {
    return (
      <Welcome
        onEnter={() => navigate("aircraft", session?.user ? "private" : "demo")}
        onGuide={() => navigate("welcomeGuide")}
        onHome={() => navigate("welcome")}
      />
    );
  }
  if (route === "welcomeGuide") {
    return (
      <WelcomeGuide
        onHome={() => navigate("welcome")}
        onEnter={() => navigate("aircraft", session?.user ? "private" : "demo")}
      />
    );
  }
  if (
    route === "login" ||
    route === "register" ||
    route === "recover" ||
    (scope === "private" && (!session?.user || sessionLoading))
  ) {
    return (
      <AuthScreen
        key={
          route === "register"
            ? "register"
            : route === "recover"
              ? "recover"
              : "login"
        }
        mode={
          route === "register"
            ? "register"
            : route === "recover"
              ? "recover"
              : "login"
        }
        loading={sessionLoading}
        message={sessionMessage}
        onAuthenticated={authenticated}
        onModeChange={(mode) => {
          setSessionMessage("");
          navigate(mode);
        }}
        onDemo={() => navigate("aircraft", "demo")}
        onHome={() => navigate("welcome")}
      />
    );
  }
  return (
    <Workspace
      key={
        scope === "demo"
          ? "demo"
          : `${session?.user?.id}:${session?.workspace?.id}`
      }
      view={route}
      onNavigate={navigate}
      onHome={() => navigate("welcome")}
      scope={scope}
      session={session}
      onSwitchScope={selectWorkspace}
      onSessionUpdated={updateSession}
      onSignIn={() => {
        setSessionMessage("");
        navigate("login");
      }}
      onSignOut={signOut}
    />
  );
}

function Workspace({
  view,
  onNavigate,
  onHome,
  scope,
  session,
  onSwitchScope,
  onSignIn,
  onSignOut,
  onSessionUpdated,
}: {
  view: View;
  onNavigate: (view: View) => void;
  onHome: () => void;
  scope: WorkspaceScope;
  session: SessionState | null;
  onSwitchScope: (scope: string) => Promise<void>;
  onSessionUpdated: (session: SessionState) => void;
  onSignIn: () => void;
  onSignOut: () => Promise<void>;
}) {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [incidentDraft, setIncidentDraft] = useState<IncidentDraft | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ReportedStatus | "all">("all");
  const [freshness, setFreshness] = useState("all");
  const [sort, setSort] = useState<"id" | "recent">("id");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [working, setWorking] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [selectedAircraft, setSelectedAircraft] = useState<Aircraft | null>(
    null,
  );
  const [selectedImport, setSelectedImport] = useState<{
    import: ImportBatch;
    changes: Change[];
  } | null>(null);
  const [mobileNav, setMobileNav] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const canImport = scope === "demo" || session?.workspace?.role !== "viewer";

  async function leaveAccount() {
    setWorking(true);
    try {
      await onSignOut();
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setWorking(false);
    }
  }

  async function refresh(initial = false) {
    if (!initial) setRefreshing(true);
    try {
      setWorkspace(await api<Workspace>("/workspace"));
      setError("");
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }
  useEffect(() => {
    void refresh(true);
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 30000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    setMobileNav(false);
    setSelectedAircraft(null);
    setSelectedImport(null);
  }, [view]);
  useEffect(() => {
    if (selectedAircraft || selectedImport) dialogRef.current?.showModal();
    else dialogRef.current?.close();
  }, [selectedAircraft, selectedImport]);

  function navigate(next: View) {
    onNavigate(next);
    setMobileNav(false);
    setError("");
  }
  async function inspect(file: File) {
    setWorking(true);
    setError("");
    setNotice("");
    setPreview(null);
    navigate("upload");
    try {
      const body = new FormData();
      body.append("file", file);
      setPreview(
        await api<Preview>("/imports/preview", { method: "POST", body }),
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setWorking(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }
  async function sample() {
    setWorking(true);
    setError("");
    setNotice("");
    navigate("upload");
    try {
      const response = await fetch("/api/examples/sample.csv");
      if (!response.ok)
        throw new Error(
          "The sample could not be loaded. Check the server and retry.",
        );
      await inspect(
        new File([await response.blob()], "fictional-fleet.csv", {
          type: "text/csv",
        }),
      );
    } catch (problem) {
      setError((problem as Error).message);
      setWorking(false);
    }
  }
  async function confirm() {
    if (!preview?.token) return;
    setWorking(true);
    setError("");
    try {
      const result = await api<{ import: ImportBatch; duplicate: boolean }>(
        "/imports/confirm",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: preview.token, rows: preview.rows }),
        },
      );
      setNotice(
        result.duplicate
          ? "This dataset was already imported. No records were changed."
          : `Import complete. ${result.import.new_count} added, ${result.import.updated_count} updated, ${result.import.unchanged_count} unchanged.`,
      );
      setPreview(null);
      await refresh();
      navigate("aircraft");
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setWorking(false);
    }
  }
  async function openImport(id: string) {
    setError("");
    setWorking(true);
    try {
      setSelectedImport(await api(`/imports/${id}`));
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setWorking(false);
    }
  }
  async function exportView(format: "csv" | "xlsx" | "json") {
    setWorking(true);
    setError("");
    try {
      await downloadRegister(
        format,
        new URLSearchParams({ q: query, status, freshness }).toString(),
      );
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setWorking(false);
    }
  }
  function closeDetails() {
    setSelectedAircraft(null);
    setSelectedImport(null);
  }

  const records = workspace?.aircraft ?? [];
  const counts = {
    all: records.length,
    available: records.filter((row) => row.reported_status === "available")
      .length,
    unavailable: records.filter((row) => row.reported_status === "unavailable")
      .length,
    unknown: records.filter((row) => row.reported_status === "unknown").length,
  };
  const filtered = useMemo(
    () =>
      records
        .filter(
          (row) =>
            (status === "all" || row.reported_status === status) &&
            (freshness === "all" ||
              (freshness === "review"
                ? row.freshness !== "current"
                : row.freshness === "current")) &&
            `${row.aircraft_id} ${row.display_name} ${row.source_name}`
              .toLowerCase()
              .includes(query.toLowerCase()),
        )
        .sort((a, b) =>
          sort === "id"
            ? a.aircraft_id.localeCompare(b.aircraft_id)
            : new Date(b.source_updated_at).getTime() -
              new Date(a.source_updated_at).getTime(),
        ),
    [records, status, freshness, query, sort],
  );
  const reviewCount = records.filter(
    (row) => row.freshness !== "current",
  ).length;
  const titles = {
    aircraft: "Aircraft register",
    upload: preview ? "Review your import" : "Import a dataset",
    history: "Import history",
    guide: "Your workspace, explained",
    overview: "Workspace overview",
    checks: "Report checks",
    relief: "Relief requests",
    incidents: "Incident review",
    sources: "Data connections",
    team: "Organisation team",
    account: "Account settings",
  };
  const subtitles = {
    aircraft:
      "A clear view of your fleet’s reported status. Every record, with its source.",
    upload: "Check the details before anything changes in your register.",
    history: "A traceable record of the datasets you’ve confirmed.",
    guide: "Start with a file. Keep the source. Review every change.",
    overview:
      "Accepted records, source freshness and the details that need attention.",
    checks:
      "Understand which source reports need attention, with reasons and evidence.",
    relief:
      "Record civilian supply needs, review their details and follow every change.",
    incidents:
      "Review flood assessments and their evidence before recording local relief needs.",
    sources:
      "Connect changing datasets. Review incoming updates before accepting them.",
    team: "Invite teammates and give each person the access they need.",
    account: "Manage your password and keep recovery codes somewhere private.",
  };

  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Skip to content
      </a>
      <aside className={`sidebar ${mobileNav ? "nav-open" : ""}`}>
        <Brand onNavigate={onHome} />
        <p className="brand-description">
          Disaster Response &amp;
          <br />
          Relief Coordination
        </p>
        <div className="workspace-switch">
          <span className="workspace-avatar">
            {scope === "demo"
              ? "D"
              : (session?.workspace?.name[0] || "O").toUpperCase()}
          </span>
          <div className="workspace-choice">
            <label className="sr-only" htmlFor="workspace-choice">
              Workspace
            </label>
            <select
              id="workspace-choice"
              value={
                scope === "demo" ? "demo" : session?.workspace?.id || "private"
              }
              onChange={(event) => {
                void onSwitchScope(event.target.value).catch((problem) =>
                  setError((problem as Error).message),
                );
              }}
            >
              <option value="demo">Demo workspace</option>
              {(session?.workspaces?.length
                ? session.workspaces
                : session?.workspace
                  ? [session.workspace]
                  : []
              ).map((choice) => (
                <option key={choice.id} value={choice.id}>
                  {choice.name}
                </option>
              ))}
              {!session?.user && (
                <option value="private">Sign in to a private workspace</option>
              )}
            </select>
            <small>
              {scope === "demo"
                ? "Fictional shared records"
                : "Private organisation"}{" "}
              · Local
            </small>
          </div>
          <ChevronDown size={14} aria-hidden="true" />
        </div>
        <div className="nav-group-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {(
            [
              { key: "incidents", label: "Incident review", icon: Waves },
              { key: "relief", label: "Relief requests", icon: PackagePlus },
              { key: "aircraft", label: "Aircraft register", icon: LayoutList },
              { key: "upload", label: "Import dataset", icon: Upload },
              { key: "history", label: "Import history", icon: History },
              { key: "overview", label: "Overview", icon: BarChart3 },
              { key: "checks", label: "Report checks", icon: ClipboardCheck },
              { key: "sources", label: "Data connections", icon: Plug },
              { key: "team", label: "Organisation team", icon: Users },
              { key: "account", label: "Account settings", icon: Settings },
            ] as const
          ).map((item) => (
            <button
              key={item.key}
              className={`nav-item ${view === item.key ? "active" : ""}`}
              aria-current={view === item.key ? "page" : undefined}
              onClick={() => navigate(item.key)}
              disabled={item.key === "upload" && !canImport}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
              {item.key === "aircraft" && (
                <span className="nav-count">{counts.all}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button
            className={`nav-item ${view === "guide" ? "active" : ""}`}
            aria-current={view === "guide" ? "page" : undefined}
            onClick={() => navigate("guide")}
          >
            <BookOpen size={18} />
            Workspace guide
          </button>
          <div className="demo-context">
            <ShieldCheck size={19} />
            <div>
              <strong>A space to learn.</strong>
              <p>Fictional records. Real workflow.</p>
            </div>
          </div>
          <div className="local-user">
            <span className="user-avatar">
              {session?.user?.display_name[0]?.toUpperCase() || "D"}
            </span>
            <div>
              <strong title={session?.user?.display_name}>
                {session?.user?.display_name || "Demo visitor"}
              </strong>
              <small>
                {session?.user
                  ? `@${session.user.username}`
                  : "Explore with sample data"}
              </small>
            </div>
            <button
              className="icon-button account-session-button"
              aria-label={session?.user ? "Sign out" : "Sign in"}
              title={session?.user ? "Sign out" : "Sign in"}
              disabled={working}
              onClick={session?.user ? () => void leaveAccount() : onSignIn}
            >
              {session?.user ? <LogOut size={17} /> : <LogIn size={17} />}
            </button>
          </div>
          {!session?.user && (
            <button
              className="button secondary sidebar-signin"
              onClick={onSignIn}
            >
              Sign in or create an account
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="icon-button menu-button"
              onClick={() => setMobileNav(!mobileNav)}
              aria-label="Toggle navigation"
              aria-expanded={mobileNav}
            >
              <Menu size={20} />
            </button>
            <Brand compact onNavigate={onHome} />
            <span className="breadcrumb-root">Workspace</span>
            <ChevronRight size={14} />
            <strong>
              {view === "aircraft"
                ? "Aircraft"
                : view === "upload"
                  ? "Import"
                  : view === "history"
                    ? "History"
                    : view === "guide"
                      ? "Guide"
                      : pageNames[view]}
            </strong>
          </div>
          <div className="topbar-meta">
            <span className="demo-label">
              {scope === "demo" ? "DEMO" : "PRIVATE"}
            </span>
            <span className="connection">
              <span className={workspace && !error ? "connected" : ""} />
              {workspace
                ? scope === "demo"
                  ? "Local demo"
                  : "Organisation workspace"
                : "Connecting"}
            </span>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <div className="page-heading">
            <div className="heading-copy">
              <h1 id="page-title" tabIndex={-1}>
                {titles[view]}
              </h1>
              <p>{subtitles[view]}</p>
            </div>
            {view === "aircraft" && (
              <button
                className="button primary"
                disabled={!canImport}
                onClick={() => {
                  setPreview(null);
                  navigate("upload");
                }}
              >
                <Plus size={18} />
                Import dataset
              </button>
            )}
          </div>
          {notice && (
            <div className="message success" role="status">
              <CheckCircle2 size={19} />
              <span>{notice}</span>
              <button
                className="icon-button"
                onClick={() => setNotice("")}
                aria-label="Dismiss notification"
              >
                <X size={16} />
              </button>
            </div>
          )}
          {error && (
            <div className="message error" role="alert">
              <CircleAlert size={19} />
              <span>{error}</span>
              {view === "aircraft" && (
                <button className="text-button" onClick={() => void refresh()}>
                  Retry
                </button>
              )}
            </div>
          )}
          {scope === "private" && (
            <div className="private-workspace-note">
              <ShieldCheck size={15} />
              <span>{workspace?.name || session?.workspace?.name}</span>
              <span className="private-role">{session?.workspace?.role}</span>
              <span>Separate from the demo and other organisations</span>
            </div>
          )}
          {view === "upload" && !canImport && (
            <div className="message error" role="alert">
              Your organisation role is view-only. An owner or editor can import
              records.
            </div>
          )}
          {view === "incidents" && (
            <Incidents
              scope={scope}
              session={session}
              workspace={workspace}
              onSignIn={onSignIn}
              onRequest={(incident) => {
                setIncidentDraft(incident);
                navigate("relief");
              }}
              onRequests={() => {
                setIncidentDraft(null);
                navigate("relief");
              }}
            />
          )}
          {view === "relief" && (
            <ReliefRequests
              incidentDraft={incidentDraft}
              onIncidentDraftUsed={() => setIncidentDraft(null)}
              scope={scope}
              session={session}
              workspace={workspace}
              onSignIn={onSignIn}
            />
          )}
          {view === "checks" && (
            <ReportChecks
              workspace={workspace}
              scope={scope}
              onInspect={(id) => {
                const item = workspace?.aircraft.find(
                  (row) => row.aircraft_id === id,
                );
                if (item) setSelectedAircraft(item);
              }}
              onInbox={() => navigate("sources")}
            />
          )}
          {(["overview", "sources", "team", "account"] as View[]).includes(
            view,
          ) && (
            <WorkspaceTools
              key={view}
              view={view as "overview" | "sources" | "team" | "account"}
              scope={scope}
              session={session}
              workspace={workspace}
              onSessionUpdated={onSessionUpdated}
              onSignIn={onSignIn}
              onRefresh={() => void refresh()}
              onPreview={(value) => {
                setPreview(value);
                navigate("upload");
              }}
              onInspect={(item) => setSelectedAircraft(item)}
            />
          )}

          {view === "aircraft" && (
            <>
              <div className="register-context">
                <span>
                  <Database size={15} />
                  {records.length} aircraft in your register
                </span>
                <span className="context-right">
                  {workspace?.imports[0] ? (
                    <>Last import {ago(workspace.imports[0].confirmed_at)}</>
                  ) : (
                    "Your first import starts here"
                  )}
                  <button
                    className={`icon-button ${refreshing ? "is-refreshing" : ""}`}
                    aria-label="Refresh register"
                    onClick={() => void refresh()}
                    disabled={refreshing}
                  >
                    <RefreshCw size={15} />
                  </button>
                </span>
              </div>
              <section className="register-panel" aria-label="Aircraft records">
                <div
                  className="status-tabs"
                  role="group"
                  aria-label="Filter by reported status"
                >
                  {(
                    ["all", "available", "unavailable", "unknown"] as const
                  ).map((item) => (
                    <button
                      key={item}
                      className={status === item ? "selected" : ""}
                      aria-pressed={status === item}
                      onClick={() => setStatus(item)}
                    >
                      {item === "all" ? "All aircraft" : shortStatus[item]}
                      <span>{counts[item]}</span>
                    </button>
                  ))}
                </div>
                <div className="table-toolbar">
                  <label className="search-field">
                    <Search size={17} />
                    <input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Search aircraft or source…"
                      aria-label="Search aircraft or source"
                    />
                  </label>
                  <div className="filter-controls">
                    <label className="select-field">
                      <Clock3 size={15} />
                      <select
                        value={freshness}
                        onChange={(event) => setFreshness(event.target.value)}
                        aria-label="Filter by report freshness"
                      >
                        <option value="all">All report ages</option>
                        <option value="current">Current reports</option>
                        <option value="review">Needs review</option>
                      </select>
                    </label>
                    <label className="select-field sort-field">
                      <select
                        value={sort}
                        onChange={(event) =>
                          setSort(event.target.value as "id" | "recent")
                        }
                        aria-label="Sort aircraft"
                      >
                        <option value="id">Aircraft ID</option>
                        <option value="recent">Most recent report</option>
                      </select>
                    </label>
                  </div>
                </div>
                <div className="register-exports">
                  <span>
                    Refreshes every 30 seconds while this tab is visible.
                  </span>
                  <div className="tools-actions">
                    {(["xlsx", "csv", "json"] as const).map((format) => (
                      <button
                        key={format}
                        className="text-button"
                        disabled={working || loading}
                        onClick={() => void exportView(format)}
                      >
                        <ArrowDownToLine size={14} />
                        Export{" "}
                        {format === "xlsx" ? "Excel" : format.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
                {loading ? (
                  <div
                    className="table-skeleton"
                    aria-label="Loading aircraft"
                    aria-busy="true"
                  >
                    {Array.from({ length: 5 }, (_, index) => (
                      <div key={index}>
                        <span />
                        <span />
                        <span />
                      </div>
                    ))}
                  </div>
                ) : !records.length ? (
                  <div className="empty-state">
                    <div className="empty-illustration">
                      <FileSpreadsheet size={39} strokeWidth={1.3} />
                      <span>
                        <Plane size={16} />
                      </span>
                    </div>
                    <h2>Your register is ready for its first aircraft.</h2>
                    <p>
                      Upload your CSV or Excel file to bring the records
                      together.
                      <br />
                      Or explore the workflow with a fictional sample fleet.
                    </p>
                    <div className="empty-actions">
                      <button
                        className="button primary"
                        onClick={() => void sample()}
                        disabled={working || !canImport}
                      >
                        <Plane size={17} />
                        Try sample data
                        <ArrowRight size={16} />
                      </button>
                      <button
                        className="button secondary"
                        disabled={!canImport}
                        onClick={() => {
                          setPreview(null);
                          navigate("upload");
                        }}
                      >
                        <Upload size={16} />
                        Upload a dataset
                      </button>
                    </div>
                    <span className="empty-note">
                      <ShieldCheck size={14} />
                      You’ll review the sample before anything is saved.
                    </span>
                  </div>
                ) : !filtered.length ? (
                  <div className="empty-state filtered-empty">
                    <Search size={30} strokeWidth={1.4} />
                    <h2>No aircraft match these filters.</h2>
                    <p>Try a different search or clear your filters.</p>
                    <button
                      className="button secondary"
                      onClick={() => {
                        setQuery("");
                        setStatus("all");
                        setFreshness("all");
                      }}
                    >
                      Clear filters
                    </button>
                  </div>
                ) : (
                  <div className="table-scroll">
                    <table className="aircraft-table">
                      <thead>
                        <tr>
                          <th scope="col">Aircraft</th>
                          <th scope="col">Reported status</th>
                          <th scope="col">Source</th>
                          <th scope="col">Source updated</th>
                          <th scope="col">Report freshness</th>
                          <th scope="col">
                            <span className="sr-only">Details</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((item) => (
                          <tr key={item.aircraft_id}>
                            <td>
                              <div className="aircraft-cell">
                                <span className="aircraft-icon">
                                  <Plane size={18} strokeWidth={1.6} />
                                </span>
                                <div>
                                  <button
                                    className="record-link"
                                    onClick={() => setSelectedAircraft(item)}
                                  >
                                    {item.aircraft_id}
                                  </button>
                                  <span>
                                    {item.display_name || "Unnamed aircraft"}
                                  </span>
                                </div>
                              </div>
                            </td>
                            <td>
                              <Status value={item.reported_status} />
                            </td>
                            <td>
                              <span className="source-name">
                                {item.source_name}
                              </span>
                            </td>
                            <td>
                              <span
                                className="time-primary"
                                title={date(item.source_updated_at)}
                              >
                                {ago(item.source_updated_at)}
                              </span>
                              <span className="time-secondary">
                                {date(item.source_updated_at)}
                              </span>
                            </td>
                            <td>
                              <Freshness item={item} />
                            </td>
                            <td>
                              <button
                                className="icon-button row-arrow"
                                aria-label={`View ${item.aircraft_id} details`}
                                onClick={() => setSelectedAircraft(item)}
                              >
                                <ChevronRight size={17} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                <div className="table-footer">
                  <span>
                    {records.length
                      ? `Showing ${filtered.length} of ${records.length} aircraft`
                      : "No records imported yet"}
                  </span>
                  <span>
                    <span className="tiny-dot" />
                    Source-reported information
                  </span>
                </div>
              </section>
              <div className="register-footnotes">
                <p>
                  <Info size={15} />
                  {reviewCount ? `${reviewCount} reports need review. ` : ""}
                  Reports older than {workspace?.freshness_hours ?? 24} hours
                  need review. This is a demo setting.
                </p>
                <button
                  className="text-button"
                  onClick={() => navigate("guide")}
                >
                  How this works
                  <ArrowRight size={14} />
                </button>
              </div>
              <div className="source-disclaimer">
                This workspace uses fictional civilian aircraft data. Reported
                availability is not an airworthiness certification.
              </div>
            </>
          )}

          {view === "upload" && canImport && (
            <div className="import-layout">
              <section className="import-main">
                <div className="import-steps" aria-label="Import progress">
                  <span className={!preview ? "current-step" : ""}>
                    <span>{preview ? <Check size={13} /> : "1"}</span>Select a
                    file
                  </span>
                  <div />
                  <span className={preview ? "current-step" : ""}>
                    <span>2</span>Review & confirm
                  </span>
                </div>
                {!preview ? (
                  <>
                    <div
                      className={`dropzone ${dragging ? "dragging" : ""}`}
                      onDragOver={(event) => {
                        event.preventDefault();
                        setDragging(true);
                      }}
                      onDragLeave={() => setDragging(false)}
                      onDrop={(event) => {
                        event.preventDefault();
                        setDragging(false);
                        const file = event.dataTransfer.files[0];
                        if (file && !working) void inspect(file);
                      }}
                    >
                      <div className="upload-symbol">
                        <Upload size={30} strokeWidth={1.4} />
                      </div>
                      <h2>
                        {working
                          ? "Checking your dataset…"
                          : "Bring your records together."}
                      </h2>
                      <p>
                        Drag a CSV or Excel file here, or choose one from your
                        computer.
                      </p>
                      <button
                        className="button primary"
                        disabled={working}
                        onClick={() => inputRef.current?.click()}
                      >
                        <FolderOpen size={17} />
                        {working ? "Validating file…" : "Choose dataset file"}
                      </button>
                      <span className="file-limits">
                        CSV or .xlsx · Up to 1 MiB · 2,000 records
                      </span>
                      <input
                        ref={inputRef}
                        type="file"
                        accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        aria-label="Choose aircraft dataset file"
                        onChange={(event) => {
                          const file = event.target.files?.[0];
                          if (file) void inspect(file);
                        }}
                        className="sr-only"
                        tabIndex={-1}
                      />
                    </div>
                    <div className="sample-option">
                      <span className="sample-icon">
                        <Plane size={21} />
                      </span>
                      <div>
                        <h3>Just getting started?</h3>
                        <p>Explore an import with 12 fictional aircraft.</p>
                      </div>
                      <button
                        className="button secondary"
                        disabled={working}
                        onClick={() => void sample()}
                      >
                        Use sample
                        <ArrowRight size={15} />
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="file-summary">
                      <span className="file-icon">
                        <FileSpreadsheet size={23} />
                      </span>
                      <div>
                        <strong>{preview.filename}</strong>
                        <span>
                          {preview.row_count} parsed records · Nothing saved yet
                        </span>
                      </div>
                      <button
                        className="text-button"
                        disabled={working}
                        onClick={() => {
                          setPreview(null);
                          setError("");
                        }}
                      >
                        Choose another file
                      </button>
                    </div>
                    <div
                      className={`review-banner ${preview.valid ? "review-valid" : "review-invalid"}`}
                      role={preview.valid ? "status" : "alert"}
                    >
                      {preview.valid ? (
                        <CheckCircle2 size={22} />
                      ) : (
                        <CircleAlert size={22} />
                      )}
                      <div>
                        <h2>
                          {preview.already_imported
                            ? "This dataset is already in your history."
                            : preview.valid
                              ? "Your dataset is ready to review."
                              : "A few things need your attention."}
                        </h2>
                        <p>
                          {preview.already_imported
                            ? "Confirming will leave your current records unchanged."
                            : preview.valid
                              ? "Review the changes below. Your register updates only after confirmation."
                              : "No records will be saved. Fix the issues below, then upload your file again."}
                        </p>
                      </div>
                    </div>
                    {preview.errors.length > 0 && (
                      <div className="validation-errors">
                        <h3>
                          {preview.errors.length} validation{" "}
                          {preview.errors.length === 1 ? "issue" : "issues"}
                        </h3>
                        <ul>
                          {preview.errors.map((item, index) => (
                            <li key={index}>
                              <span>
                                {item.row ? `Row ${item.row}` : "File"}
                                <small>{item.field}</small>
                              </span>
                              <p>{item.message}</p>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {preview.changes.length > 0 && (
                      <>
                        <div className="change-counts">
                          <span>
                            <span className="count-new">
                              {preview.counts.new}
                            </span>
                            New aircraft
                          </span>
                          <span>
                            <span className="count-updated">
                              {preview.counts.updated}
                            </span>
                            Updated
                          </span>
                          <span>
                            <span>{preview.counts.unchanged}</span>Unchanged
                          </span>
                          {preview.counts.blocked > 0 && (
                            <span>
                              <span className="count-blocked">
                                {preview.counts.blocked}
                              </span>
                              Blocked
                            </span>
                          )}
                        </div>
                        <div className="table-scroll preview-scroll">
                          <table className="review-table">
                            <thead>
                              <tr>
                                <th>Aircraft</th>
                                <th>Change</th>
                                <th>Previous status</th>
                                <th>Incoming status</th>
                              </tr>
                            </thead>
                            <tbody>
                              {preview.changes.map((change) => (
                                <tr key={change.aircraft_id}>
                                  <td>
                                    <strong>{change.aircraft_id}</strong>
                                    <small>{change.after.display_name}</small>
                                  </td>
                                  <td>
                                    <span
                                      className={`change-label change-${change.action}`}
                                    >
                                      {change.action}
                                    </span>
                                  </td>
                                  <td>
                                    {change.before ? (
                                      <Status
                                        value={change.before.reported_status}
                                      />
                                    ) : (
                                      <span className="muted">
                                        No existing record
                                      </span>
                                    )}
                                  </td>
                                  <td>
                                    <Status
                                      value={change.after.reported_status}
                                    />
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <details className="change-details">
                          <summary>Inspect complete field changes</summary>
                          {preview.changes
                            .filter(
                              (change) =>
                                change.action === "new" ||
                                change.action === "updated" ||
                                change.action === "blocked",
                            )
                            .map((change) => (
                              <div
                                className="field-diff"
                                key={change.aircraft_id}
                              >
                                <h3>{change.aircraft_id}</h3>
                                <dl>
                                  {Object.entries(change.after)
                                    .filter(
                                      ([key, value]) =>
                                        change.before?.[
                                          key as keyof typeof change.before
                                        ] !== value,
                                    )
                                    .map(([key, value]) => (
                                      <div key={key}>
                                        <dt>{key.replaceAll("_", " ")}</dt>
                                        <dd>
                                          {change.before && (
                                            <>
                                              <span className="old-value">
                                                {String(
                                                  change.before[
                                                    key as keyof typeof change.before
                                                  ],
                                                ) || "(empty)"}
                                              </span>
                                              <ArrowRight size={13} />
                                            </>
                                          )}
                                          <span>
                                            {String(value) || "(empty)"}
                                          </span>
                                        </dd>
                                      </div>
                                    ))}
                                </dl>
                              </div>
                            ))}
                        </details>
                      </>
                    )}
                    <div className="confirm-bar">
                      <span>
                        <ShieldCheck size={16} />
                        {preview.valid
                          ? "Your confirmation is required."
                          : "Your saved records are unchanged."}
                      </span>
                      <button
                        className="button primary"
                        disabled={!preview.valid || working}
                        onClick={() => void confirm()}
                      >
                        <Check size={17} />
                        {working
                          ? "Saving import…"
                          : preview.already_imported
                            ? "Confirm no changes"
                            : "Confirm import"}
                      </button>
                    </div>
                  </>
                )}
              </section>
              <aside className="import-help">
                <h2>
                  A good file starts with
                  <br />a clear structure.
                </h2>
                <p>
                  Use the template to keep your column names and timestamps
                  consistent.
                </p>
                <a
                  className="button secondary download-template"
                  href="/api/examples/template.csv"
                  download
                >
                  <ArrowDownToLine size={16} />
                  Download CSV template
                </a>
                <a
                  className="button secondary download-template"
                  href="/api/examples/template.xlsx"
                  download
                >
                  <ArrowDownToLine size={16} />
                  Download Excel template
                </a>
                <h3>Required columns</h3>
                <ul className="column-list">
                  {[
                    "aircraft_id",
                    "display_name",
                    "reported_status",
                    "source_updated_at",
                    "source_name",
                    "note",
                  ].map((name) => (
                    <li key={name}>
                      <Check size={12} />
                      <code>{name}</code>
                    </li>
                  ))}
                </ul>
                <p className="help-small">
                  All headers are required. Display name and note may be blank.
                </p>
                <div className="import-trust">
                  <ShieldCheck size={18} />
                  <p>
                    Previewing a file changes nothing. Invalid batches are
                    rejected together.
                  </p>
                </div>
                <a
                  className="text-button"
                  href="/api/examples/invalid.csv"
                  download
                >
                  Download an error example
                  <ArrowDownToLine size={13} />
                </a>
              </aside>
            </div>
          )}

          {view === "history" && (
            <section className="history-panel">
              <div className="panel-title">
                <h2>
                  Confirmed imports{" "}
                  <span>{workspace?.imports.length ?? 0}</span>
                </h2>
                <button
                  className="button secondary"
                  onClick={() => void refresh()}
                  disabled={refreshing}
                >
                  <RefreshCw size={15} />
                  Refresh
                </button>
              </div>
              {!workspace?.imports.length ? (
                <div className="empty-state">
                  <History size={35} strokeWidth={1.3} />
                  <h2>Your import history will live here.</h2>
                  <p>
                    Confirm your first dataset to start a traceable history.
                  </p>
                  <button
                    className="button primary"
                    onClick={() => navigate("upload")}
                  >
                    Import a dataset
                    <ArrowRight size={15} />
                  </button>
                </div>
              ) : (
                <div className="history-list">
                  {workspace.imports.map((batch) => (
                    <button
                      className="history-row"
                      key={batch.id}
                      onClick={() => void openImport(batch.id)}
                      disabled={working}
                    >
                      <span className="file-icon">
                        <FileCheck2 size={22} />
                      </span>
                      <div>
                        <strong>{batch.filename}</strong>
                        <span>
                          {date(batch.confirmed_at)} · {batch.actor}
                        </span>
                      </div>
                      <div className="history-counts">
                        <span>
                          <b>{batch.new_count}</b> added
                        </span>
                        <span>
                          <b>{batch.updated_count}</b> updated
                        </span>
                        <span>{batch.unchanged_count} unchanged</span>
                      </div>
                      <span className="import-revision">v{batch.revision}</span>
                      <ChevronRight size={18} />
                    </button>
                  ))}
                </div>
              )}
              <div className="table-footer">
                <span>Up to 50 most recent confirmed imports</span>
                <span>Repeat datasets don’t create new entries.</span>
              </div>
            </section>
          )}

          {view === "guide" && (
            <WorkspaceGuide
              freshnessHours={workspace?.freshness_hours}
              disabled={!canImport}
              onStart={() => {
                setPreview(null);
                navigate("upload");
              }}
            />
          )}
        </main>
        <footer className="app-footer">
          <span>SAMPATI · Disaster relief workspace</span>
          <span>Fictional data · Local demo</span>
        </footer>
      </div>
      <dialog
        ref={dialogRef}
        className="detail-dialog"
        onCancel={closeDetails}
        onClick={(event) => {
          if (event.target === event.currentTarget) closeDetails();
        }}
        aria-labelledby="detail-title"
      >
        <div className="dialog-heading">
          <div>
            <span className="dialog-icon">
              {selectedAircraft ? <Plane size={21} /> : <History size={21} />}
            </span>
            <h2 id="detail-title">
              {selectedAircraft?.aircraft_id ||
                selectedImport?.import.filename ||
                "Record details"}
            </h2>
          </div>
          <button
            className="icon-button"
            onClick={closeDetails}
            aria-label="Close details"
          >
            <X size={20} />
          </button>
        </div>
        {selectedAircraft && (
          <div className="dialog-content">
            <h3>{selectedAircraft.display_name || "Unnamed aircraft"}</h3>
            <div className="detail-statuses">
              <Status value={selectedAircraft.reported_status} />
              <Freshness item={selectedAircraft} />
            </div>
            <dl className="record-details">
              <div>
                <dt>Source</dt>
                <dd>{selectedAircraft.source_name}</dd>
              </div>
              <div>
                <dt>Source updated</dt>
                <dd>
                  {date(selectedAircraft.source_updated_at)}
                  <small>{selectedAircraft.source_timestamp_raw}</small>
                </dd>
              </div>
              <div>
                <dt>Received by Sampati</dt>
                <dd>{date(selectedAircraft.received_at)}</dd>
              </div>
              <div>
                <dt>Source note</dt>
                <dd>{selectedAircraft.note || "No note supplied."}</dd>
              </div>
            </dl>
            <button
              className="button secondary"
              onClick={() => {
                setSelectedAircraft(null);
                void openImport(selectedAircraft.last_import_id);
              }}
            >
              View source import
              <ArrowRight size={15} />
            </button>
            <p className="detail-footnote">
              This is source-reported fictional information, not an
              airworthiness certification.
            </p>
          </div>
        )}
        {selectedImport && (
          <div className="dialog-content">
            <p className="muted">
              Confirmed {date(selectedImport.import.confirmed_at)} by{" "}
              {selectedImport.import.actor}
            </p>
            <div className="history-detail-summary">
              {selectedImport.import.new_count} added ·{" "}
              {selectedImport.import.updated_count} updated ·{" "}
              {selectedImport.import.unchanged_count} unchanged
            </div>
            {selectedImport.changes.map((change) => (
              <div className="audit-change" key={change.aircraft_id}>
                <div>
                  <strong>{change.aircraft_id}</strong>
                  <span className={`change-label change-${change.action}`}>
                    {change.action}
                  </span>
                </div>
                <p>
                  {change.before
                    ? `${shortStatus[change.before.reported_status]} → ${shortStatus[change.after.reported_status]}`
                    : `Added as ${shortStatus[change.after.reported_status].toLowerCase()}`}
                </p>
                <details>
                  <summary>Inspect saved values</summary>
                  <pre>
                    {JSON.stringify(
                      { before: change.before, after: change.after },
                      null,
                      2,
                    )}
                  </pre>
                </details>
              </div>
            ))}
          </div>
        )}
      </dialog>
    </div>
  );
}
