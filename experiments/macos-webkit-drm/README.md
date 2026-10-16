# macOS WebKit playback experiment

A standalone companion window to test whether Netflix and Norwegian TV 2 Play
accept protected playback in Apple's system WKWebView. This first stage does not
change Chromium, the shared Helium build cache, or its profiles. Requires macOS
13.3+ and Xcode command-line tools. No Widevine binaries, private APIs, or special
FairPlay credentials are included.

Build and launch from the repository root:

```sh
bash experiments/macos-webkit-drm/build.sh --run
```

The app is built into `out/Helium WebKit Experiment.app` and signed ad hoc for
local use. It uses the system WebKit and its own persistent website data store;
sign in separately from Helium and Safari. Command-C/V and other editing shortcuts
work through the Edit menu. WebKit inspection is enabled for Safari's Develop menu.

## Manual acceptance test

1. Open Netflix, sign in, and play a full protected episode or film. Trailers,
   previews, a successful login, and an EME API being present are not sufficient.
2. Confirm picture and sound for at least two minutes; seek, pause/resume, and
   enter/exit fullscreen. Open Diagnostics during playback and record the reported
   media dimensions and whether media keys are attached. Diagnostics reads only
   top-level media elements and may miss players inside frames.
3. Repeat for TV 2 Play using a protected on-demand title and a live channel if
   available in your subscription. Record each separately.
4. Quit and relaunch to check login persistence.
5. If a site rejects the default WebKit identity, try the Safari identity checkbox
   and reload. This is a fixed Safari 26 compatibility user agent, not proof of
   Safari equivalence or DRM permission. Record which setting worked.

Record macOS version, service, title/live channel, identity setting, picture/sound,
duration, fullscreen/seek results, dimensions, and exact error codes. Do not share
cookies, account credentials, or license requests. Diagnostics are shown locally
and are not written to a log. No playback has been confirmed merely by building
or launching this app.

Proceed to Chromium tab/window integration only after these manual tests pass.
This companion has no Chromium extensions or content blocking. New-window links
are loaded in the same view; popup-based authentication may require more work if
a provider relies on a separate window and window.opener.

## Initial smoke check

The app compiled, passed bundle/plist and ad-hoc signature verification, and
launched locally. Netflix's landing page loaded; diagnostics reported EME and
legacy FairPlay APIs present. TV 2 Play displayed an outdated-browser warning
with the default identity; selecting Safari identity loaded the normal welcome
page without that warning.

The user subsequently confirmed that both Netflix and TV 2 Play play without
issues in this standalone app. This confirms the feasibility of the system
WebKit route. Resolution, prolonged playback, and private browsing have not
been separately verified. Integrated playback results are recorded below.

## Helium-owned window integration

The branch also contains a patch adding the macOS-only
`helium-webkit-streaming` experimental flag. It has been applied to the prepared
source and built successfully with the persistent local build command. On macOS
27.0.1, runtime diagnostics confirmed that Netflix and TV 2 Play opened native
windows and completed page loading inside Helium. The user then confirmed
that protected titles play correctly in both integrated Helium-owned windows.
Fullscreen, extended playback, live TV, and profile lifecycle tests remain open.
On macOS 14+, enabling it routes top-level HTTPS Netflix and `play.tv2.no`
navigations to a Helium-owned WebKit window. Enable it at
`chrome://flags/#helium-webkit-streaming` and restart, or start Helium with
`--helium-webkit-streaming`.

The native window uses the Safari identity that passed the standalone test.
Each Helium profile gets its own persistent WebKit store, shared between its
streaming windows. These stores are separate from the standalone test app, so
the integrated experiment requires a fresh login. Guest/private windows remain
on Chromium. Streaming windows are separate from Chromium tabs; the initiating
tab remains at its previous page (a new tab may stay blank). There is no session
restore, Chromium history, extension support, or integration with Chromium's
clear-browsing-data controls for these WebKit windows yet.

For local lifecycle diagnostics, add
`--enable-logging=stderr --vmodule=helium_webkit_streaming_mac=1` to the launcher.
The optional messages report window opening/closing and navigation completion or
numeric failure codes without collecting page URLs, cookies, or license data.

## In-tab WebKit prototype

`macos-webkit-streaming-tabs.patch` adds a separate, macOS-only prototype. Launch
with the persistent launcher and `--helium-webkit-streaming-tabs`, or enable
`chrome://flags/#helium-webkit-streaming-tabs` and restart. This mode takes
precedence over the separate streaming-window flag.

Opening an eligible Netflix or TV 2 Play URL gives that Helium tab its own
WKWebView beneath Helium's tab strip and toolbar. Multiple streaming tabs have
independent live pages and share only their profile's existing WebKit data store.
The native Back/Forward/Reload buttons and address field inside the content area
control WebKit. Authentication and other HTTP(S) links inside WebKit stay in
WebKit; typing an ordinary URL into Helium's omnibox returns the tab to Chromium.
Private/guest profiles remain excluded.

This is a hosting prototype, not complete browser-chrome integration. Helium's
omnibox intentionally displays the blank Chromium shell (`about:blank`), and the
tab can also be labelled `about:blank`. The inner address field displays the WebKit page.
Browser Back/Forward/Reload, bookmarks, history, permission indicators, Find,
downloads, extension commands, and site-data controls are not wired to WebKit.
Use the inner navigation controls. The Chromium shell must not be interpreted as
the displayed page's security identity. Existing native-window mode is unchanged.

Switching away suspends media; returning pauses it before lifting suspension so
playback requires an explicit resume. Closing the tab or navigating it back to
Chromium releases the WebKit page. WebKit sessions are not serialized: restoring
or duplicating the blank shell must not restore a hidden player. Split panes use
separate native hosts, with native clicks activating their owning tab, but split
focus, clipping, modal overlays, fullscreen, accessibility, and protected playback
still require integrated manual verification.


The prototype builds in the persistent component cache. On macOS 27.0.1, visual
smoke tests confirmed both public service pages in tabs, tab switching alongside
Chromium pages, ordinary omnibox fallback and subsequent streaming re-entry,
and close/reopen without restoring the WebKit player. Protected playback and
hidden-media behavior have not yet been tested in this tab host. The embedded
WebKit content is absent from the current accessibility tree; this remains a
prototype limitation. See [PLAN.md](PLAN.md) for the remaining integration work.
