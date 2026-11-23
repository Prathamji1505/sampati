import { useEffect, useState } from "react";
import {
  BarChart3,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  History,
  Inbox,
  LayoutList,
  PackagePlus,
  Plane,
  Plug,
  Settings,
  Truck,
  Upload,
  Users,
  Warehouse,
  Waves,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type WorkspaceView =
  | "aircraft"
  | "upload"
  | "history"
  | "guide"
  | "overview"
  | "checks"
  | "relief"
  | "incidents"
  | "inventory"
  | "deliveries"
  | "automation"
  | "response"
  | "sources"
  | "team"
  | "account";

type NavItem = { key: WorkspaceView; label: string; icon: LucideIcon };
type Group = "aircraft" | "workspace";
const reliefItems: NavItem[] = [
  { key: "overview", label: "Overview", icon: BarChart3 },
  { key: "response", label: "Response preparation", icon: Plane },
  { key: "incidents", label: "Incident review", icon: Waves },
  { key: "relief", label: "Relief requests", icon: PackagePlus },
  { key: "inventory", label: "Aid inventory", icon: Warehouse },
  { key: "deliveries", label: "Delivery tracking", icon: Truck },
  { key: "automation", label: "Automation inbox", icon: Inbox },
];
const groups: {
  key: Group;
  label: string;
  icon: LucideIcon;
  items: NavItem[];
}[] = [
  {
    key: "aircraft",
    label: "Aircraft & data",
    icon: LayoutList,
    items: [
      { key: "aircraft", label: "Aircraft register", icon: LayoutList },
      { key: "upload", label: "Import dataset", icon: Upload },
      { key: "history", label: "Import history", icon: History },
      { key: "checks", label: "Report checks", icon: ClipboardCheck },
      { key: "sources", label: "Data connections", icon: Plug },
    ],
  },
  {
    key: "workspace",
    label: "Workspace settings",
    icon: Settings,
    items: [
      { key: "team", label: "Organisation team", icon: Users },
      { key: "account", label: "Account settings", icon: Settings },
    ],
  },
];
const groupFor = (view: WorkspaceView) =>
  groups.find((group) => group.items.some((item) => item.key === view))?.key ??
  null;

export default function WorkspaceNavigation({
  view,
  onNavigate,
  canImport,
  aircraftCount,
}: {
  view: WorkspaceView;
  onNavigate: (view: WorkspaceView) => void;
  canImport: boolean;
  aircraftCount: number;
}) {
  const [expanded, setExpanded] = useState<Group | null>(() => groupFor(view));
  // Direct links and browser history reveal the current route's group.
  useEffect(() => {
    setExpanded(groupFor(view));
  }, [view]);
  useEffect(() => {
    if (expanded) {
      const items = document.getElementById(`nav-${expanded}`);
      const current = items?.querySelector<HTMLElement>(
        "[aria-current='page']",
      );
      (current ?? items)?.scrollIntoView({ block: "nearest" });
    }
  }, [expanded, view]);
  function itemButton(item: NavItem) {
    return (
      <button
        key={item.key}
        className={`nav-item ${view === item.key ? "active" : ""}`}
        aria-current={view === item.key ? "page" : undefined}
        onClick={() => onNavigate(item.key)}
        disabled={item.key === "upload" && !canImport}
      >
        <item.icon size={18} aria-hidden="true" />
        <span className="nav-item-label">{item.label}</span>
        {item.key === "aircraft" && (
          <span className="nav-count">{aircraftCount}</span>
        )}
      </button>
    );
  }
  return (
    <nav className="workspace-navigation" aria-label="Main navigation">
      <div
        className="nav-primary"
        role="group"
        aria-label="Relief coordination"
      >
        {reliefItems.map(itemButton)}
      </div>
      <div className="nav-utilities">
        {groups.map((group) => {
          const open = expanded === group.key;
          const current = group.items.find((item) => item.key === view);
          return (
            <div className="nav-section" key={group.key}>
              <button
                className={`nav-group-toggle ${current ? "contains-current" : ""}`}
                aria-expanded={open}
                aria-controls={`nav-${group.key}`}
                onClick={() => setExpanded(open ? null : group.key)}
              >
                <group.icon size={18} aria-hidden="true" />
                <span>
                  {group.label}
                  {current && !open && <small>Current: {current.label}</small>}
                </span>
                {open ? (
                  <ChevronDown size={15} aria-hidden="true" />
                ) : (
                  <ChevronRight size={15} aria-hidden="true" />
                )}
              </button>
              <div
                id={`nav-${group.key}`}
                className="nav-subitems"
                hidden={!open}
                role="group"
                aria-label={group.label}
              >
                {group.items.map(itemButton)}
              </div>
            </div>
          );
        })}
      </div>
    </nav>
  );
}
