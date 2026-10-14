# Developer utilities for ungoogled-chromium

This is a collection of scripts written for developing on ungoogled-chromium. See the descriptions at the top of each script for more information.

## Experimental four-pane split view

`helium/ui/multi-pane-split-view.patch` is applied last in `patches/series`.
It extends the existing split collection to three or four tabs. Select three or
four ordinary tabs with Command-click (macOS) or Control-click, right-click a
selected tab, and use the existing split command. Choose either orientation
when that submenu is available. Four tabs form a 2×2 grid; three tabs form two
small panes beside one larger pane. Changing orientation changes the order in
which the grid is partitioned.

This is an **uncompiled prototype**, not a tested browser release. The patch
was checked against the Chromium version in `chromium_version.txt`, with the
existing Helium patches applied to the affected files. It does not implement
arbitrary recursive splits or an unlimited pane count.

The main divider remains resizable. The subdivisions inside each half are
equal and fixed. Exit split preserves the active tab. Closing or detaching one
pane exits the entire split, following the existing model behavior. Pair-only
reverse, close-half, and replace/swap commands are disabled for grids.
Last-session restore accepts up to four panes; recently closed windows and
Groups restore their tabs without reconstructing a grid. Grid corner styling
and animation clipping use the fallback behavior rather than the pair-specific
window corner/animation rules.

### Checks available in this repository

```sh
python3 devutils/lint.py
python3 devutils/test_multi_pane_split.py
```

The second command compiles the actual grid partition helper extracted from the
patch with C++20 and address/undefined-behavior sanitizers. It checks coverage,
non-overlap, containment, unused panes, pair compatibility, invalid pane counts,
and odd/zero/tiny dimensions across 1,344 cases. It does not compile the browser
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

The patch adds these tests to Chromium's existing `TabStripModelTest` suite:

- `FourPaneSplitSelectionAndFocus`
- `MoveWithinFourPaneSplit`
- `RestoreFourPaneSplit`

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
Server-side user-agent detection still sees the normal browser.

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

This remains an **uncompiled browser prototype**. Before shipping, verify a
responsive page with `innerWidth`, `innerHeight`, `devicePixelRatio`, viewport
metadata and touch media queries; every interval in ordinary tabs and split
panes; foreground/background refresh; POST and beforeunload handling;
disable/re-enable; switching between mobile and desktop panes; resizing;
navigation and renderer crashes; tab hibernation; closing/reopening the saved
workspace; tab reordering and group renaming; restart; inspector attachment;
and unavailable saved groups/incognito. Use a development profile.
