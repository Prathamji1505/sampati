import type { WorkspaceScope } from "./types";

let workspaceScope: WorkspaceScope = "demo";
let csrfToken: string | null = null;

export function configureApi(scope: WorkspaceScope, csrf: string | null) {
  workspaceScope = scope;
  csrfToken = csrf;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const dataRequest =
    /^\/(workspace|imports|overview|report-checks|relief-requests|incidents|exports|sources|team)(\/|\?|$)/.test(
      path,
    );
  const privateRequest = dataRequest && workspaceScope === "private";
  const prefix =
    dataRequest && workspaceScope === "demo" ? "/api/demo" : "/api";
  const headers = new Headers(options?.headers);
  if (
    options?.method &&
    !["GET", "HEAD"].includes(options.method.toUpperCase())
  ) {
    headers.set("X-Sampati-Request", "1");
    if (csrfToken && (privateRequest || path.startsWith("/auth/")))
      headers.set("X-CSRF-Token", csrfToken);
  }
  let response: Response;
  try {
    response = await fetch(prefix + path, {
      ...options,
      headers,
      credentials: "same-origin",
    });
  } catch {
    throw new ApiError(
      "The local server could not be reached. Check that the application is running, then retry.",
      0,
    );
  }
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail))
        detail =
          "Some details are not valid. Check the form fields and try again.";
    } catch {
      /* A non-JSON server response uses the fallback below. */
    }
    if (
      (privateRequest ||
        path === "/auth/security" ||
        path === "/auth/password") &&
      response.status === 401
    )
      window.dispatchEvent(new Event("sampati:session-expired"));
    throw new ApiError(
      detail ||
        `The request could not be completed (${response.status}). Please retry.`,
      response.status,
    );
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new Error(
      "The server returned an unexpected response. Check the backend and retry.",
    );
  }
}

export async function downloadRegister(
  format: "csv" | "xlsx" | "json",
  params = "",
) {
  const prefix = workspaceScope === "demo" ? "/api/demo" : "/api";
  const response = await fetch(
    `${prefix}/exports/register.${format}${params ? `?${params}` : ""}`,
    { credentials: "same-origin" },
  );
  if (!response.ok)
    throw new Error(
      "The export could not be downloaded. Refresh your session and retry.",
    );
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = `sampati-register.${format}`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
