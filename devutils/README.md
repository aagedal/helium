# Developer utilities for ungoogled-chromium

This is a collection of scripts written for developing on ungoogled-chromium. See the descriptions at the top of each script for more information.

## Experimental multi-pane split view

`helium/ui/multi-pane-split-view.patch` extends the base split implementation;
the actions and layout-options patches are applied after it in `patches/series`.
It extends the existing split collection to three or four tabs. Select three or
four ordinary tabs with Command-click (macOS) or Control-click, right-click a
selected tab, and use the existing split command. Choose either orientation
when that submenu is available. Four tabs form a 2×2 grid; three tabs form two
small panes beside one larger pane. Changing orientation changes the order in
which the grid is partitioned.

This remains an experimental feature with a six-pane limit. Geometry checks
cover all layout presets; full browser integration testing remains required
before shipping. Local macOS builds reuse the prepared cache documented in
`AGENTS.md`.

Every divider is resizable, including subdivisions inside each half. Drag a
boundary or focus its handle and use the arrow keys. Pane sizes stay with the
split when switching tabs and are restored with the last session. Exit split preserves the active tab. Closing or detaching one
pane exits the entire split, following the existing model behavior. Pair-only
reverse, close-half, and replace/swap commands are disabled for grids.
Last-session restore accepts up to six panes; recently closed windows and
Groups restore their tabs without reconstructing a grid. Grid corner styling
and animation clipping use the fallback behavior rather than the pair-specific
window corner/animation rules.

Right-click a tab and open **Split Layout** to create or rearrange a split:

- **Three Columns / Three Rows**: a 1×3 or 3×1 strip.
- **Four Columns / Four Rows**: a 1×4 or 4×1 strip.
- **2 × 2 Grid**: the original four-pane grid.
- Mixed layouts: one pane beside two or three stacked panes, or one pane above
  two or three side-by-side panes, with mirrored variants for each.

The action retains existing pages and fills spare panes with new-tab pages.
It acts on the right-clicked tab, even when other tabs are selected. Changing
an existing layout keeps the split and its pages. Choices with fewer panes than
the current split are disabled. Every boundary has a native resize handle. Choosing a layout resets the main
divider to its default ratio and the subdivisions to equal sizes. Layout choices persist in last-session restore;
older session files default to the original grid arrangement.

These choices are implemented by `helium/ui/split-layout-options.patch`.
It adds browser coverage for in-place rearrangement and a session round-trip
regression for every arrangement. Full browser/session test execution still
requires an unpruned Chromium test tree.

`helium/ui/four-pane-split-actions.patch` also fixes grid accessibility labels:
it avoids passing indices 2 and 3 to the pair-only label formatter, which
aborted the browser when creating a grid. The layout-options patch uses
indexed pane labels that work across all shapes.
Browser regressions cover creation, expansion, and both label orientations.

### Checks available in this repository

```sh
python3 devutils/lint.py
python3 devutils/test_multi_pane_split.py
```

The second command compiles the actual grid partition helper extracted from the
patch with C++20 and address/undefined-behavior sanitizers. It checks coverage,
non-overlap, containment, unused panes, pair compatibility, invalid pane counts,
and odd/zero/tiny dimensions across 11,200 cases. An additional 400 resize cases
check both orientations, all presets, minimum sizes, gutter placement, and
adjacent-pane resizing that leaves the other panes unchanged. It does not compile the browser
or prove that tab activation and session integration work.

To test the complete production header in an already patched source tree:

```sh
python3 devutils/test_multi_pane_split.py --source-tree /path/to/build/src
```

### Browser validation still required

Use the [Helium macOS development build workflow](https://github.com/imputnet/helium-macos/blob/main/docs/building.md#development-build-and-environment).
The packaging repository supplies `dev.sh`, Chromium downloads and the build
toolchain; this core repository alone does not build a browser. Its
`helium-chromium` submodule must contain this private fork's changes and match
the packaging version. After installing that workflow's dependencies, use
`source dev.sh`, `he setup`, `he build`, and `he run`. Use the development
profile provided by `he run` when testing.

The grid patch adds these tests to Chromium's existing `TabStripModelTest` suite:

- `FourPaneSplitSelectionAndFocus`
- `MoveWithinFourPaneSplit`
- `RestoreFourPaneSplit`

The follow-up actions patch adds these `TabMenuModelBrowserTest` regressions:

- `FourPaneSplitAccessibleLabels`
- `CreateAndExpandFourPaneSplit`
- `ChangePaneArrangementInPlace`
- `SplitLayoutSubmenu`

Run those tests and the existing split model tests in a Chromium build. Before
shipping, also check two/three/four panes in both orientations; click and
keyboard activation in every pane; the toolbar's URL; switching between grids,
pairs and ordinary tabs; resizing; devtools and modal dialogs in each pane;
exit/close/detach; pinned/grouped tabs; vertical/horizontal tab strips;
fullscreen; right-to-left layout; and restart/recently-closed restore.
All contributions and any future PR must stay within the private fork.

## Mobile preview workspaces and per-tab auto-refresh

`helium/ui/tab-preview-workspaces.patch` extends the four-pane prototype.
Right-click an individual tab and open **Tab view**:

- **Mobile preview (402 × 874)** toggles a fixed portrait viewport with 3×
  device density and mobile viewport/touch emulation. The page is centered and
  scaled down to fit its pane, keeping its CSS viewport unchanged when the
  window or divider is resized. It uses Chromium's emulation API without
  opening a DevTools window, device toolbar, or console.
- **Create desktop/mobile workspace** creates two copies of the page in a
  named **Desktop + mobile** saved tab group, pins that group, and splits the
  copies side by side with more space for desktop. The original tab is retained.
  Rename the group using the normal group menu. This action requires a regular
  profile with saved groups enabled.
- **Auto-refresh** offers **Off** and every 15 seconds through 180 seconds
  (15, 30, 45, …, 180). It applies only to the right-clicked tab, even if several
  tabs are selected or belong to one split. Off is the default.

The preset matches the 402 × 874 CSS-pixel dimensions corresponding to the
[standard iPhone 17's 1206 × 2622 display](https://support.apple.com/en-us/125089)
at 3× density. This is a Chromium responsive preview: it does not emulate
Safari/WebKit, an iPhone user agent, browser bars, or a screen cutout.
`helium/ui/mobile-preview-device-identity.patch` adds an Android mobile Chromium
user agent and matching Client Hints to both mobile modes. HTTP requests and
JavaScript device detection see a mobile device, while other panes retain their
desktop identity. Switching between desktop and mobile reloads eligible HTTP(S)
GET pages; POST pages are not automatically resubmitted. Changing only the mobile
height does not reload. Restored panes receive their identity before loading.

Tab settings are included in session snapshots and recently closed tab data
and copied when a tab is discarded. Refresh skips loading, crashed, discarded,
non-HTTP(S), and POST pages. Closing a tab destroys its timer. Mobile preview
does not take over an already attached inspector; attachment/protocol failures
clear the toggle. Normal developer tools remain available when explicitly
opened.

Saved groups store tab settings locally using stable saved-tab IDs. Reopening
a preview workspace reconstructs its desktop/mobile pair when both saved tabs
still exist, including after reordering or renaming. These extra settings and
the pair layout are local to the profile and are not synced to other devices.
Reopened workspaces use the default side-by-side orientation and 65/35 divider;
last-session restore retains the normal split layout/ratio. Creation during
saved-group service initialization still needs browser validation.

### Validation

```sh
python3 devutils/lint.py
python3 devutils/test_multi_pane_split.py
python3 devutils/test_tab_preview.py
```

The preview check compiles the production fit/interval helper with C++20 and
address/undefined-behavior sanitizers, exercising 132 viewport cases and
601 interval values. It does not compile the browser or exercise a timer.
The patch adds `PaneSettingsTest.*` to Chromium's existing unit-test target,
covering timer deadlines, interval replacement, Off, independent tabs, tab
destruction, loading/POST/discard skips, and valid/invalid restoration.
Run those tests in the build environment described above.

The Apple Silicon development build compiles these features, but full Chromium
browser and timer test execution still requires an unpruned test tree. Before
shipping, verify a
responsive page with `innerWidth`, `innerHeight`, `devicePixelRatio`, viewport
metadata and touch media queries; every interval in ordinary tabs and split
panes; foreground/background refresh; POST and beforeunload handling;
disable/re-enable; switching between mobile and desktop panes; resizing;
navigation and renderer crashes; tab hibernation; closing/reopening the saved
workspace; tab reordering and group renaming; restart; inspector attachment;
and unavailable saved groups/incognito. Use a development profile.

## Stability review (October 2026)

`helium/ui/pane-stability.patch` is applied after the layout-options patch. It
keeps tab-specific split menus attached to the original tab and split identities
when indices change, and disables actions, labels, and icons after that split
disappears. Toolbar/divider menus still resolve the active tab lazily because
they are created before tabs exist and reused across splits. Browser regressions
cover index changes, split removal, menu reuse, and an empty tab-strip model.

Selecting an unchanged auto-refresh interval preserves its deadline and avoids
redundant session writes and view invalidation. Refresh also skips pending
navigations. Mobile preview resizing updates device metrics without resending
unchanged touch settings; attachment and page changes still configure both.
Two additional `PaneSettingsTest` regressions cover timer deadlines and pending
navigation.

The upstream archive-layer merge and build-dependency pruning changes have
regression coverage in `utils/tests/test_prepared_sources.py`. Run the utility
checks with pytest installed:

```sh
PYTHONPATH=utils python3 -m pytest -o addopts='' utils/tests
python3 -m pytest -o addopts='' devutils/tests
```

Review validation: all 12 utility/developer tests passed, patch lint passed,
the five feature patches and upstream Web Store patch reversed and reapplied
without fuzz against the cached source, and both sanitizer helper checks passed
against the production headers. The persistent macOS component build passed,
including the merged upstream Web Store resources, and a fresh-profile headless
startup/rendering smoke test passed. Both the pane-settings unit-test source and
tab-menu browser-test source compiled independently using their generated
Chromium commands; this also fixed existing `NavigationSimulator::CreateFromPending`
and `chrome::NewTab` test API mismatches. A Chromium regression-test build stopped
at missing pruned test data (`chrome/test/data/extensions/extension_api_unittest/
api_features.json`); the new browser and timer regressions remain unexecuted.

## Helium Neo branding

The private fork builds as `Helium Neo.app`. Its macOS bundle identifier and
normal profile directory name are `no.aagedal.helium-neo`; its Keychain entry is
`Helium Neo Storage Key` (account `Helium Neo`). Existing Helium profiles and keys
are not migrated. The local launcher retains the existing `build/dev-profile`.

`utils/name_substitution.py` applies the display name and macOS identities after
platform patches. For the existing prepared cache, run it from this worktree:

```sh
python3 utils/name_substitution.py --sub -t "$HOME/Developer/helium/build/macos/build/src"
```

Then use the persistent `build-local.sh` described in `AGENTS.md`. Do not run
`prepare_sources` against the cache. The persistent launcher must target
`out/Default/Helium Neo.app/Contents/MacOS/Helium Neo` after rebuilding.

## Resizable multi-pane dividers

`helium/ui/resizable-multi-pane-splits.patch` adds the missing native resize
handles for the inner boundaries of three/four-pane layouts, reserves gutters
between those panes, and gives multi-pane rows usable minimum sizes. It keeps
pane weights in split visual data and appends them to session commands; old
sessions retain equal subdivisions. Selecting another preset resets the weights.
The ordinary two-pane divider keeps its existing behavior.

The patch also extends `SplitPaneArrangementSaved` to round-trip custom weights
and adds `SplitPaneSizesSurviveTabActivation` and
`CustomSplitPaneSizesRestored`. Those Chromium tests require an
unpruned test build; the standalone geometry harness runs in this repository.

Local validation: the component browser compiled successfully; all geometry,
resize, viewport and refresh harness checks passed. Native keyboard resizing
was checked in three columns, three rows and both halves of a grid. A clean
browser restart preserved a diagnostic pane at 556 × 457, including its custom
main ratio and inner weights. Pointer-drag automation was inconclusive, so a
hands-on drag check remains recommended before making a standalone release.

## Helium Neo orbital icon

The private fork uses a violet orbital mark instead of Helium's blue asterisk.
`resources/branding/product_logo.svg` is the full-color master. The transparent
foreground and modern macOS appearance settings live in
`resources/branding/macos/AppIcon.icon`. Both the classic `app.icns` and modern
`Assets.car` are checked in; the common resource list overrides the platform
repository's icons after platform resources are copied.

On macOS, regenerate the PNGs, wordmarks, Chromium vector paths, ICNS, and asset
catalog using Pillow, librsvg and Xcode:

```sh
~/Developer/helium/build/venv/bin/python3 devutils/generate_neo_icons.py
```

Then run `utils/generate_resources.py` and `utils/replace_resources.py` against
the prepared source before the incremental build. Do not recreate the cache.

## Five- and six-pane layouts

`helium/ui/extended-pane-layouts.patch` raises the split capacity to six and adds
these **Split Layout** choices:

- **3 × 2 Grid**: three columns in each of two rows (six pages).
- **Two Stacked Left + Three Columns**: two stacked pages in the leftmost
  column and three full-height pages beside it (five pages).

Every boundary uses the existing native resize behavior. The mixed layout starts
with one quarter of the width for the stacked column; its right side is divided
into three columns. Changing presets retains existing pages and fills new panes
with new tabs. A preset with fewer panes remains disabled for a larger split.

Sizes and arrangements persist in the session. The extra two pane weights are
an optional tail in the session data, so older four-pane sessions still restore
with equal defaults for unused panes. Regression coverage includes exact layout
geometry, every divider in every arrangement, six-pane focus/activation, and
browser restore tests for both new presets. Full Chromium browser test execution
requires an unpruned test build.

Local verification of the expanded presets: the component browser built, both
menu choices created their expected five/six panes, native keyboard resizing
worked in both mixed axes and on the final sixth-pane boundary, and a clean
restart reproduced all saved split visual data exactly. The older four-pane
session restored its original 556 × 457 diagnostic pane; the new five-pane
session retained its 291 × 457 diagnostic pane. No normal browser profile was
used for these checks.

## Pinned split and mobile view persistence

`helium/ui/pinned-split-pane-state.patch` fixes reload selection for every split
size (two through six panes). Command-R and bypass-cache reload affect the active
pane when a single split is selected. Explicitly selecting additional tab-strip
tabs retains Chromium's multiple-tab reload behavior.

Pinned-tab startup now saves and restores split membership, orientation,
arrangement, main ratio, all inner divider weights, and each tab's mobile mode
and auto-refresh interval. This also works when startup opens a new-tab page
rather than restoring the last session. Legacy URL-only pinned entries still
open as ordinary pinned tabs. These settings remain local to the profile.

**Tab view → Mobile preview (402 wide, full height)** is an additional mobile
mode. It keeps a 402 CSS-pixel width and 3× device density, uses the entire pane
height, and scales down only when the pane is narrower than 402 pixels. Its CSS
height follows the available height without the portrait preset's 874-pixel cap.
The fixed **Mobile preview (402 × 874)** remains available. Selecting either mode
replaces the other; selecting the checked mode returns to desktop rendering.

The preview harness checks both modes, including tall and narrow panes. Chromium
regressions cover normal/bypass reload for every active pane and split capacity,
mobile/refresh setting round trips, and pinned split startup reconstruction with
custom sizes and per-tab settings. Full regression execution still requires the
unpruned Chromium test dependencies described above.

The modern macOS icon uses a 1024-pixel transparent raster of the vector
foreground inside Icon Composer. Apple's SVG importer filled the stroked orbit
and reduced its size, producing the oval seen in the Dock. The generator now
supplies `AppIcon.icon/Assets/logo.png` from `Assets/logo.svg`; both the modern
asset catalog and classic ICNS retain the orbital design. To verify the actual
modern rendering, use Icon Composer's bundled `ictool --export-image`, rather
than inspecting only the fallback PNG or ICNS.

Validation for these changes: the persistent Apple Silicon component build
passed, patch lint and reverse-application checks passed, and both standalone
sanitizer harnesses passed against the repository patches and prepared source.
The reload browser test, pinned-startup browser test, and pane-settings unit-test
sources compiled independently with Chromium's generated commands. Full browser
regressions were not executed. Native UI automation failed with
`Sky Computer Use native pipe closed before response`, so keyboard/restart UI
checks remain unverified. A seeded-profile smoke attempt was inconclusive because
Chromium's protected preferences discarded the injected pinned-tab entries.
Apple's Icon Composer renderer reproduced the old filled oval and verified the
corrected orbital foreground; the built app's asset catalog matches the new
checked-in catalog.

## Mobile device identity and active split indication

`mobile-preview-device-identity.patch` supplements both mobile viewport modes
with per-pane Android Chromium identification in HTTP headers, Client Hints,
and navigator properties. Enabling/disabling mobile mode reloads eligible GET
pages; restoring settings and changing mobile height do not start another load.
The browser regression in `TabMenuModelBrowserTest.MobilePreviewDeviceIdentity`
checks echoed request headers, JavaScript identity, desktop-pane isolation,
height changes, and returning to desktop.

`split-active-pane-indicator.patch` uses the normal theme-aware active-tab
background for the actual active sub-tab and inactive backgrounds for its
siblings. The highlight remains visible while the toolbar or a context menu has focus. Clicking another
sub-tab within the current split explicitly selects that pane; returning from
another tab still restores the split's last focused pane.

Validation: both changes compiled in the persistent Apple Silicon component
build; the browser regression source compiled using its generated Chromium
command. The full browser-test executable was not built/run in this pruned
cache. Native app checks confirmed mobile HTTP/JavaScript identity, TV 2's
latest-news strip, desktop/mobile isolation, and selection indication in
two-pane and compact pinned three-pane splits. Clicking a pinned sub-tab selected its corresponding pane after restart. A restored inactive
saved split showed blank contents during the additional session-restore check;
that restore path remains unverified.

The split indicator uses existing theme background states rather than a custom
underline or thicker pane outline. The revised component app built successfully,
and native checks confirmed the highlight follows compact pinned sub-tab selection.
The old downloaded installer contained the malformed modern macOS icon catalog;
macOS resolved the current running build to the correct orbital icon.

## Vertical pinned split tabs

`vertical-pinned-split-tabs.patch` applies active-pane background highlighting
and direct sub-tab selection to the vertical tab implementation. Each pinned
sub-tab paints its own theme background rather than sharing the first pane's
background. In an expanded sidebar, pinned split icons share a row and wrap
when the sidebar cannot fit all panes; the collapsed sidebar keeps its vertical
icon stack. Expanding/collapsing invalidates the split layout.

`PinnedSplitTabViewTest.ExpandedTilesAndSelection` covers two through six panes,
multiple sidebar widths, non-overlapping bounds, direct selection and style
state, and the collapsed stack.

Validation: the persistent Apple Silicon app build and independent Chromium
browser-test source compilation passed. Native UI checks verified the expanded
three-pane pinned icon row, per-pane selection, the collapsed icon stack, and
expanding back to a row. Full browser-test execution remains unavailable in the
pruned cache.
