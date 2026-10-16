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
WebKit route. Resolution, prolonged playback, private browsing, and integration
inside the Chromium process have not been separately verified.

## Helium-owned window integration

The branch also contains a patch adding the macOS-only
`helium-webkit-streaming` experimental flag. It has been applied to the prepared
source and built successfully with the persistent local build command. On macOS
27.0.1, runtime diagnostics confirmed that Netflix and TV 2 Play opened native
windows and completed page loading inside Helium. Signed-in playback in these
integrated windows still requires confirmation separately from the standalone app.
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
