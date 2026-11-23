---
version: 1
slug: "frontend-src-workspacenavigation-tsx"
primary_target: "frontend/src/WorkspaceNavigation.tsx"
related_targets: ["frontend/src/styles.css","frontend/src/App.tsx"]
---

# Workspace navigation refinement

Mode: Operate. The user marked the crowded sidebar at approximately782×721 and requested cleaner, easier access.

## Direction contract

THESIS: Relief tasks are immediately reachable; supporting aircraft/data and workspace administration are disclosed in labelled groups instead of one long flat menu.

OWN-WORLD: Preserve Sampati's charcoal/crimson/ivory tokens, painted bird, bilingual wordmark, native controls and current-page styling. No new artwork or visual identity.

STORY: Open Overview or a relief task directly; expand Aircraft & data or Workspace settings only when needed. Current deep links reveal their group. Help and one session action remain reachable below the menu.

FIRST VIEWPORT: Compact brand and workspace chooser, seven relief destinations, two expandable utility groups and a fixed compact footer. Only the menu scrolls; the sidebar never scrolls sideways. Narrow desktop rails allow readable labels. Mobile uses the existing drawer with outside/Escape closing.

FORM: Code-led extension of the existing shell, no concept or visual-world change. Preserve route names, workspace switching, import permissions and page content. Existing DESIGN.md remains visual authority.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

Verify actual user viewport,1440,1024,390,320; all destinations through groups; active deep links/history; short-height scrolling; keyboard disclosure, mobile closing, and retained read-only demo permissions. Capture representative final states for independent review.

## Finish evidence

Finished on 23 November 2026. The actual in-app browser verified all fourteen main destinations plus help, direct-link group reveal, keyboard disclosure, Escape/outside closing with focus return and mobile route closing. Desktop, original-width, short-height and phone captures were inspected. The narrow-phone overflow check uses document client width, including classic-scrollbar space. Independent review returned ship at the sidebar scope after documentation, phone overflow and capture corrections. DESIGN.md now records the refined navigation layout; palette, fonts and painted assets are unchanged.
