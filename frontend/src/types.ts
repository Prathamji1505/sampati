export type ReportedStatus = "available" | "unavailable" | "unknown";
export type CsvRow = {
  aircraft_id: string;
  display_name: string;
  reported_status: ReportedStatus;
  source_updated_at: string;
  source_name: string;
  note: string;
};
export type Aircraft = CsvRow & {
  received_at: string;
  source_timestamp_raw: string;
  last_import_id: string;
  freshness: "current" | "stale" | "future";
};
export type ImportBatch = {
  id: string;
  filename: string;
  actor: string;
  received_at: string;
  confirmed_at: string;
  row_count: number;
  new_count: number;
  updated_count: number;
  unchanged_count: number;
  revision: number;
};
export type Change = {
  row?: number;
  aircraft_id: string;
  action: "new" | "updated" | "unchanged" | "blocked";
  before: CsvRow | null;
  after: CsvRow;
};
export type Preview = {
  valid: boolean;
  filename: string;
  row_count: number;
  rows: CsvRow[];
  errors: { row: number; field: string; message: string }[];
  changes: Change[];
  counts: { new: number; updated: number; unchanged: number; blocked: number };
  already_imported: boolean;
  token: string | null;
};
export type Workspace = {
  id: string;
  is_demo: boolean;
  name: string;
  revision: number;
  freshness_hours: number;
  aircraft: Aircraft[];
  imports: ImportBatch[];
  server_time: string;
};

export type WorkspaceScope = "demo" | "private";
export type SessionState = {
  user: { id: string; username: string; display_name: string } | null;
  workspace: {
    id: string;
    name: string;
    role: "owner" | "editor" | "viewer";
  } | null;
  csrf_token: string | null;
  expires_at: string | null;
  workspaces: {
    id: string;
    name: string;
    role: "owner" | "editor" | "viewer";
  }[];
};
