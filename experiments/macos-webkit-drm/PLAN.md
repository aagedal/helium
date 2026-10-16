# WebKit streaming integration plan

## Objective

Play Netflix and Norwegian TV 2 Play through macOS's system WebKit while using
Chromium for ordinary browsing. Keep the implementation optional and macOS-only;
other platforms can continue using Chromium. Separate streaming logins and lack
of Chromium content blocking are accepted for this experiment.

## Confirmed evidence

- [x] Build and launch the standalone WKWebView companion app in this directory.
- [x] Verify that the Safari identity setting removes TV 2 Play's browser warning.
- [x] The user confirmed successful playback in both Netflix and TV 2 Play.
- [x] Prepare an opt-in `helium-webkit-streaming` Chromium patch and add it to
  `patches/series`.
- [x] Syntax-check the new Objective-C++ implementation and modified browser
  client against the prepared Chromium headers and compiler settings.

The standalone playback result does not establish integrated playback, maximum
resolution, extended playback stability, or private browsing support. The native
window patch now compiles and links inside Helium. On macOS 27.0.1, lifecycle
diagnostics confirmed that top-level navigations opened native windows for both
services and that both pages finished loading. The user subsequently confirmed
that protected titles play correctly in both Helium-owned WebKit windows.

## 1. Build the Helium-owned streaming window

- [x] Wait until the shared Chromium build cache is idle. Do not interrupt the
  build already using it or modify its source/output directories concurrently.
- [x] Inspect `~/Developer/helium/build/fork-revision.txt`, the snapshot diff, and
  the prepared source again; they may have changed since the patch was drafted.
- [x] Reconcile this branch's `macos-webkit-streaming.patch` with that source.
  Apply only the intended changes and preserve unrelated work and compiled output.
- [x] Build using `~/Developer/helium/build/build-local.sh` and existing GN args.
  Resolve compiler, GN dependency, framework-linking, and application lifecycle
  issues before treating the integration as working.
- [x] Launch with the persistent `run-local.sh --helium-webkit-streaming`, or
  enable `chrome://flags/#helium-webkit-streaming` and restart.

The patch currently routes user/browser-initiated top-level HTTPS navigations for
Netflix and `play.tv2.no` into native windows on macOS 14+. Chromium subframes,
POST requests, private/guest profiles, unrelated sites, and older macOS versions
continue on the Chromium path. There is one reusable window per service/profile,
with a persistent WebKit data store scoped to the profile. The initiating
Chromium tab stays on its previous page, or may remain blank if newly created.

## 2. Validate the integrated window

Current smoke result: browser-started Netflix and TV 2 Play navigations both
opened a Helium-owned WebKit window and completed page loading. Verification used
`--enable-logging=stderr --vmodule=helium_webkit_streaming_mac=1`; these optional
logs record lifecycle events and numeric error codes only, not page URLs or
account data. A flag-disabled run produced Chromium Netflix history entries and no native
window-open events; the enabled run produced two native-window events and no
Chromium Netflix history entries. The smoke run used separate `/tmp` Chromium
profiles. The UI tool
could not reliably distinguish concurrent Helium instances, so interactive
lifecycle tests remain unchecked below; integrated account playback has now
been confirmed by the user.

- [ ] Confirm both services load from typed URLs, clicked links, and redirects.
  Test exact domain boundaries and ensure unrelated sites and embedded frames
  never trigger the handoff. Verify disabled-flag behavior.
- [x] Sign in again in the integrated window and play a protected title in both
  Netflix and TV 2 Play. Confirmed by the user.
- [ ] Test TV 2 live TV separately when the subscription permits.
- [ ] Test sustained picture/sound, seek, pause/resume, subtitles, fullscreen,
  display changes, and sleep/wake. Record macOS version and observed resolution.
- [ ] Test editing shortcuts, address updates, authentication redirects, popup
  flows, Back/Forward, close/reopen, and browser quit with streaming windows open.
- [ ] Confirm that closing a window stops its media and releases its web view.
- [ ] Verify login persistence after restart, isolation between Helium profiles,
  and that private/guest navigation cannot use persistent streaming sessions.
- [ ] Identify how WebKit data should be cleared and removed with a profile.
  Chromium's existing clear-browsing-data UI does not currently clear these stores.

Keep the integration a draft experiment until this stage passes. Record exact
failure codes without collecting account credentials, cookies, or license data.

## 3. Prototype WebKit inside the Helium UI

- [x] Inspect Chromium's tab/content host and macOS native view ownership before
  selecting the integration point. A WKWebView cannot replace a WebContents by
  simply changing its renderer.
- [x] Prototype hosting WKWebView beneath the existing Helium tab/address bar,
  with clear engine ownership for each tab and no transfer of live page state.
- [ ] Connect navigation, title, focus, shortcuts, fullscreen, and close behavior.
- [ ] Define engine choice on cross-domain navigation and authentication redirects.
  Keep service login/playback in the same WebKit session.
- [ ] Preserve multiple streaming tabs, profile isolation, and session restoration
  without retaining or accidentally resuming hidden media.
- [ ] Handle newly opened tabs without leaving confusing blank Chromium tabs.
- [ ] Resolve browser menu commands, downloads, permissions, accessibility,
  developer inspection, and site-data controls for the second engine.
- [ ] Decide private browsing behavior explicitly; until it is implemented and
  verified, keep it excluded from automatic WebKit routing.

The first in-tab prototype is implemented behind a separate
`helium-webkit-streaming-tabs` flag. `ContentsWebView` holds a second
`NativeViewHost` above the blank Chromium surface; per-tab `WebContents` user data
owns the native controller. The bridge is a component in development builds, so
the browser and UI share session ownership without copying profile registries.
Switching tabs removes the native host while retaining the per-tab WebKit page;
close/navigation releases that page. Removing the unused host and restoring native
view order is necessary to keep Chromium surfaces drawing after tab switches.
Hidden media is suspended; reveal pauses it before allowing playback again.
Pending handoffs are invalidated by newer Chromium navigations. Native focus is
forwarded to WebKit, and native mouse interaction activates the owning tab.

The Chromium WebContents is deliberately a blank shell. The existing native
WebKit navigation toolbar supplies the real address and Back/Forward/Reload;
omnibox/security state and browser commands are not yet integrated. HTTP(S)
service/authentication navigation stays in WebKit; an ordinary omnibox navigation
exits to Chromium. Restoring the blank shell does not recreate a WK player.
The integration checkboxes above remain open until runtime validation covers
these behaviors and the remaining browser-chrome work.

Prototype validation on macOS 27.0.1 (2026-10-16): the persistent component
build succeeds; patch parsing and dry application pass. Visual smoke tests with
isolated temporary profiles confirmed Netflix and TV 2 Play rendering under the
Helium tab strip, multiple tabs, switching to a visible Chromium page, ordinary
omnibox navigation releasing WebKit, subsequent streaming re-entry, and closing
and reopening a tab as a blank shell without recreating its WebKit player.
A flag-disabled run displayed ordinary Chromium content. The accessibility tree
omits the embedded native WebKit subtree, so screenshots were required to verify
its content; accessibility integration remains unresolved. Both tab labels and
the omnibox can still say `about:blank`. Protected in-tab playback, media
suspension/resume behavior, split-pane interaction, and profile isolation were
not verified by this smoke test. The prepared source was updated directly; the
older fork-source snapshot and its unrelated changes were preserved.

## 4. Release decision

- [ ] Repeat service playback tests inside the tab prototype.
- [ ] Check the supported macOS version range and confirm non-macOS builds remain
  unaffected by platform guards.
- [ ] Keep an experimental flag and easy fallback until integration is stable.
- [ ] Document separate logins, extension limitations, site-data controls, and
  reliance on the system WebKit version.

All PRs belong to `aagedal/helium`; do not submit this experiment upstream to
`imputnet/helium`.
