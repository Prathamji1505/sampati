# Welcome entry

Mode: Operate entry surface. Route: `/`. The user requested a welcome page before the existing workspace.

## Direction contract

THESIS: Introduce Sampati and make entering the working application the main action. The welcome screen belongs to the application, with no marketing claims or invented capabilities.

OWN-WORLD: Inherit the approved charcoal, crimson and ivory palette, Yatra One display lettering, bilingual identity and generated folk-style bird artwork. Reuse the existing assets and standard button vocabulary.

STORY: The visitor recognizes Sampati, understands that it brings source-reported aircraft data together, and enters the register. The existing guide is an optional secondary route.

FIRST VIEWPORT: A small brand header and local-demo marker, large Sampati title and concise introduction on the left, the bird across the right, and one crimson Enter workspace button. On phones the artwork precedes the text and the entry button spans the content width.

FORM: Code-led, focused extension of the user-approved visual world. No new visual-world selection. Seed: none (pinned existing identity and a narrowly requested entry page).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Behavior

The root shows Welcome without mounting or fetching workspace data. Enter workspace opens the private register when signed in, otherwise the demo register. Read workspace guide opens standalone `#welcome/guide` without entering a workspace or fetching aircraft data; see welcome-guide.md. The existing guide, import and history retain their in-workspace routes. Browser history and reload preserve these locations. The brand returns to Welcome. Navigation moves focus to the destination heading; skip links focus content without changing the route. No data writes happen on entry or navigation.
