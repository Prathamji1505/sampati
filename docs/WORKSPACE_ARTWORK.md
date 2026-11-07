# Workspace cloud background

The user found the separate feather ornament forced and unnatural. The refinement removes both foreground placements and continues the painting with a quiet bank of clouds growing out of the workspace's lower-left and bottom edges.

- Asset: `frontend/public/artwork/sampati-cloud-edge.png`.
- Source: built-in ImageGen, guided by the approved Sampati panorama's cloud drawing style. The exact generation prompt is in `frontend/public/artwork/cloud-edge-provenance.json` and embedded in the PNG.
- Placement: a background pseudo-element on `.main-shell`, anchored to the bottom of the canvas. Screen blending removes the black image ground; low opacity and a vertical mask fade the clouds into the interface.
- The sidebar stays clear. There is no foreground image, reserved ornament space, extra footer row or responsive duplicate.
- The background ignores pointer events and creates no accessibility-tree content. Opaque data panels remain in front. Mobile uses the same background with lower opacity and height.

The welcome page, upper bird illustration, palette, lettering and control system retain their existing treatments. This is an ordinary extension of the incumbent design system; `DESIGN.md` and `.impeccable/design.json` are preserved.

## Verification

On 7 November 2026, the 1440×900 desktop and 390×844 mobile full-page captures were opened and checked for natural edge integration, readable content and a clear sidebar. Valid captures: `.impeccable/review/cloud-edge-desktop.png` and `cloud-edge-mobile.png`.

Formatting passed after the decorative JSX/CSS edit. The manual design detector returned no findings, and the shipping raster scan reported three rasters with no missing prompt provenance. Both foreground image nodes and their obsolete styles/assets were removed.

Subsequent multi-size and interaction checks were interrupted by concurrent unrelated work. Initially the app imported a not-yet-created `WorkspaceTools` module; a final build retry after that file appeared reports JSX syntax errors in `WorkspaceTools.tsx`. Vite's error overlay invalidated the later captures; they were discarded. No successful full build or final navigation check is claimed for this revision. The parallel feature files are preserved.

The fresh focused finish review returned **Ship** for this narrow visual refinement. It independently inspected both valid captures and matching source and found no material visual defects. Its approval covers the lower-edge treatment, decorative semantics and incumbent identity at those two viewports; intermediate widths, other states and live interactions were not independently verified.

The subsequent workspace-tools integration resolved the temporary `WorkspaceTools.tsx` syntax errors described above. The production build, complete tool browser workflow and touch-enabled register smoke check now pass with the cloud background retained. Current evidence is recorded in docs/VERIFICATION.md; the earlier interrupted captures are not used as passing evidence.
