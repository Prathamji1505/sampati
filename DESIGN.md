---
name: "SAMPATI · सम्पाति"
description: "Disaster Response & Relief Coordination"
colors:
  accent: "#b72e48"
  accent-hover: "#ca3653"
  accent-text: "#f292a4"
  accent-soft: "#391c27"
  on-accent: "#fff8f5"
  saffron: "#d6a05a"
  ink: "#f2ede7"
  muted: "#b3adb0"
  ground: "#101013"
  nav: "#0a0a0d"
  surface: "#17171b"
  surface-raised: "#222126"
  surface-hover: "#2c292f"
  skeleton-highlight: "#343039"
  line: "#363239"
  control-line: "#6c6570"
  focus: "#f292a4"
  success: "#87c5a6"
  success-soft: "#172b24"
  success-line: "#365c49"
  warning: "#dfb16c"
  warning-soft: "#302619"
  warning-line: "#685333"
  error: "#f09a9d"
  error-soft: "#341c23"
  error-line: "#6a3542"
typography:
  headline:
    fontFamily: '"Yatra One", "DM Sans", sans-serif'
    fontSize: "38px"
    fontWeight: 400
    lineHeight: 1.25
    letterSpacing: "0.01em"
  title:
    fontFamily: '"DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "18px"
    fontWeight: 550
    letterSpacing: "-0.3px"
  body:
    fontFamily: '"DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: '"DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.2
  button:
    fontFamily: '"DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "12px"
    fontWeight: 550
  wordmark:
    fontFamily: '"Yatra One", "DM Sans", sans-serif'
    fontSize: "25px"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "0.04em"
  devanagari:
    fontFamily: '"Nirmala UI", "Noto Sans Devanagari", sans-serif'
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1.5
rounded:
  tag: "4px"
  select: "5px"
  control: "6px"
  navigation: "7px"
  dropzone: "8px"
  panel: "10px"
  dialog: "12px"
spacing:
  "4": "4px"
  "8": "8px"
  "12": "12px"
  "16": "16px"
  "20": "20px"
  "24": "24px"
  "32": "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "10px 15px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "10px 15px"
  button-secondary-hover:
    backgroundColor: "{colors.surface-hover}"
  button-text:
    textColor: "{colors.accent-text}"
    padding: "5px 0"
  input-search:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 10px"
    width: "300px"
  navigation-active:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.navigation}"
    padding: "10px 14px"
  tag-available:
    backgroundColor: "{colors.success-soft}"
    textColor: "{colors.success}"
    typography: "{typography.label}"
    rounded: "{rounded.tag}"
    padding: "5px 7px"
  panel-import:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "25px"
  dropzone:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.dropzone}"
    padding: "35px 20px"
---

# Design System: SAMPATI · सम्पाति

## Overview

**Creative North Star: "Source first."**

SAMPATI · सम्पाति pairs a quiet black-and-charcoal workspace with crimson actions, warm ivory text and restrained saffron. The approved descriptor is “Disaster Response & Relief Coordination”. A folk-style soaring-bird emblem, Yatra One display lettering and an approved crimson/ivory/gold panorama express the identity in the header; the interface stays focused on scanning reports and completing an import.

This documents the implemented local, fictional aircraft-report prototype. The descriptor names the broader project and does not imply that future operations, live feeds or AI capabilities exist. This approved theme supersedes the provisional Airframe name, ink-blue navigation and white reading surfaces; the table, sidebar, import workflow and source-first principles remain.

**Key Characteristics:**

- Task-focused hierarchy and compact, structured data.
- Bilingual bird identity and an illustrated header with restrained gold.
- Tonal surfaces, clear borders and visible keyboard focus.
- Reported status and report freshness shown separately.

## Colors

The palette combines warm crimson with near-black neutrals. Frontmatter values are normative and mirror the CSS custom properties in `frontend/src/styles.css`; the unused `soft` alias is omitted.

### Primary

Crimson `accent` identifies primary actions. `accent-hover` supplies pointer feedback, `accent-text` keeps small links and selection readable on dark surfaces, and `accent-soft` anchors selected navigation and steps. `on-accent` is the primary-button text.

### Secondary

Saffron `saffron` belongs to the Devanagari identity and the restrained gold details in the approved bird artwork. It is a small brand detail.

### Neutral

`nav` is the darkest shell layer; `ground` is the canvas; `surface` contains the work; `surface-raised` distinguishes headers and controls. `surface-hover` provides secondary-button feedback. `ink` and `muted` establish reading hierarchy. `line` separates content, while `control-line` makes field and secondary-button boundaries clearer.

Success, warning and error each use foreground, soft-fill and border tokens. These semantic roles retain text labels. The warning family also marks stale and future-dated reports. `focus` is the keyboard outline, and `skeleton-highlight` supports loading feedback.

**The Identity Accent Rule.** Reserve saffron for identity and the approved artwork; use crimson for actions and the semantic families for data states.

## Typography

Yatra One is the public display family for the Latin wordmark and page h1 only, using `--font-display`. It loads locally with `font-display: swap` from the unmodified `frontend/public/fonts/yatra-one/YatraOne-Regular.ttf`; preserve the bundled SIL OFL 1.1 licence. It replaces the privately retained personal-use prototype font for GitHub publication while preserving the folk-art identity.

DM Sans remains the family for tables, body copy, controls and other headings. Hindi identity text uses Nirmala UI, then Noto Sans Devanagari and sans-serif. Keep `lang="hi"` on the Devanagari wordmark.

The hierarchy is compact and clear: headline for page headings, title for empty/import headings, body for supporting reading, label for status, and button for the standard action. The guide uses a longer reading line (up to 65ch). Timestamps and change totals use tabular numerals.

The headline and wordmark frontmatter records their desktop roles. At the wide breakpoint, page headings grow to 42px; at 850px and below, they become 32px. The Latin wordmark becomes 21px with 0.02em tracking at 850px and below, then 19px with 0.04em tracking at 640px and below. The mobile lockup retains both scripts in a tighter stack. Existing small metadata is an implementation detail, not the recommended scale for new body text or important instructions.

**The Reading Hierarchy Rule.** Keep instructions and decisions at the established reading scale; do not borrow tiny metadata styles for essential content.

## Layout

Retain the fixed desktop sidebar, workspace top bar, page heading with action, and one clear work area. The register places status filters and search above the table. Import remains a page with selection, validation, before/after review and explicit confirmation. History remains a separate view.

The page-heading region has a minimum height of 200px on desktop and 185px at 850px and below. Its copy occupies up to 52% of the desktop width, leaving room for the bird on the right. At 640px and below, copy may use 88% and the import action sits beneath the heading text.

The standard sidebar is 236px wide, with a matching content offset and 38px horizontal workspace inset. It narrows to 210px at 1180px and 185px at 850px. At 640px and below, the sidebar becomes a menu drawer under the 64px header; the compact bilingual brand occupies the header and the content offset disappears. Mobile main content uses 18px horizontal padding.

Import has a flexible work column and a 240px help column. At 850px and below it becomes one column and hides the help aside. At 1600px and above, workspace insets expand to 52px. Spacing uses the recurring frontmatter steps with component-specific insets where observed; it is not a rigid grid.

Tables scroll inside their own region. Preserve their column relationships rather than compressing data into illegibility. Toolbars wrap, status tabs can scroll, and long filenames and detail values wrap. Coarse-pointer controls use larger targets and form text that avoids mobile keyboard zoom.

## Elevation & Depth

Tonal layering and thin borders establish depth. Data panels are flat at rest. The detail dialog and open mobile drawer alone use structural shadows, with a dark dialog backdrop. The decorative panorama sits behind the page-heading region on the main shell: a dark horizontal scrim protects text and a bottom fade merges it into the canvas. Its band is 250px high on desktop and 220px at 640px and below; data panels retain their opaque surfaces. Exact shadows, motion, breakpoints and header-layer details live in the sidecar.

State transitions are brief background/border changes; loading skeletons pulse and refresh icons rotate. No decorative entrance animation is used. Reduced-motion preferences disable animation and transitions.

## Shapes

Use gently rounded, restrained geometry: compact tags, controls, navigation and larger work panels follow the frontmatter radius roles. Dots, avatars and step counters are circular.

The identity uses `/artwork/sampati-emblem.png`, a transparent PNG bird emblem displayed at 48px on desktop, 31px at the tablet breakpoint and 36px in the compact mobile lockup. Preserve its alpha and contain the full silhouette. The approved panorama is `/artwork/sampati-folk-sky.png`: a soaring bird on the right with quieter space for text on the left. The original drawing supplied the folk-art style only. Asset provenance and exact prompts are recorded in `frontend/public/artwork/provenance.json` and embedded in both PNGs.

The current painted emblem was explicitly approved on 8 November 2026. Its layered feathers, fine brown ink lines, warm pigment texture and gold details are part of the identity. Retain this old folk-art treatment. Approval and the exact logo prompt are recorded in `frontend/public/artwork/logo-provenance.json`. The shared brand image and browser icon use the same version query, `?v=b7e5b47f`, so browsers fetch the approved asset after the previous logo is replaced.

## Components

- **Buttons:** Crimson primary actions, bordered charcoal secondary actions, and rose text links. Standard buttons have a minimum height of 40px; coarse pointers raise this to 44px. Primary hover brightens crimson; secondary hover uses the hover surface and muted border. Pressed buttons move down 1px. Disabled controls lower opacity and use a not-allowed cursor.
- **Fields:** Search and selects use visible control borders and tonal fills. Preserve labels and the global focus outline (3px, offset 4px; search input offset 1px). Fine-pointer hover styles are gated to devices that support hover.
- **Navigation:** Muted default items brighten on hover. Active navigation uses the soft crimson surface, ivory text and rose icon. Keep current-view semantics and the compact mobile menu.
- **Status and freshness:** Text accompanies each dot or tag. Available uses success; unavailable uses warning; unknown uses neutral. Freshness is a separate indicator and never certifies availability or airworthiness.
- **Panels and tables:** Work panels use a surface fill, thin divider border and panel radius. Table headers use the raised surface; row hover is tonal. Keep aligned timestamps and the source-and-freshness relationship.
- **Import:** Dashed upload boundary, numbered progress, actionable validation and a review table showing previous/incoming values. Dragging uses the soft crimson surface. Confirmation stays explicit; empty, loading, disabled and error states remain visible.
- **Identity:** Use the transparent bird emblem with the Yatra One SAMPATI wordmark and सम्पाति. Keep the descriptor in the desktop sidebar and the bilingual compact lockup in the mobile header. The approved panorama belongs behind the page-heading region, with its text scrim and bottom fade.

## Do's and Don'ts

### Do:

- **Do** keep scanning, source context and import completion ahead of decoration.
- **Do** preserve the bilingual wordmark and the approved descriptor.
- **Do** use text as well as color for status, freshness and validation.
- **Do** keep keyboard focus visible and honor reduced motion.
- **Do** label fictional local data honestly and preview changes before confirmation.

### Don't:

- **Don't** use saffron as a general action, status or chart color.
- **Don't** collapse reported status and freshness into one signal.
- **Don't** add decorative entrance motion to this workflow.
- **Don't** turn tiny metadata sizes into a target for new reading content.
- **Don't** imply live tracking, AI decisions, flight authorization or airworthiness certification.
