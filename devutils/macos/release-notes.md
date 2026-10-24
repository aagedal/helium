Helium Neo 0.20.1.2 lets you choose the profile that opens links from other apps, plays streaming services in WebKit tabs by default, and keeps background tabs running like Chrome. Chromium (156.0.8078.47) and upstream Helium are unchanged from 0.20.1.1.

Download **Helium-Neo-0.20.1.2-macOS-arm64-signed.dmg**, open it, and drag **Helium Neo** to Applications, replacing an existing copy. Requires an Apple Silicon Mac running macOS 13 or later. WebKit streaming tabs require macOS 14 or later. Installations of 0.19.4.1 or later with browser updates enabled receive this release automatically. Users of earlier betas must install it manually once.

**New in Neo**

- **Choose where links from other apps open:** links from apps such as Slack or Mail normally open in the window you used last. Turn on **Open links from other apps in this profile** under **Settings › Behavior**, or use **Open links from other apps here** in a profile's menu in the profile picker, to always open them in one profile. Off by default.
- **WebKit streaming tabs on by default:** Netflix, TV 2 Play, HBO Max and Disney+ play in Helium tabs using macOS's WebKit, with Helium's address bar and navigation buttons. These pages use separate logins per profile and don't run extensions or content blocking. Turn it off with `chrome://flags/#helium-webkit-streaming-tabs`.
- **Background tabs keep running:** tab freezing is now off by default, matching Chrome, so sites in background tabs are no longer paused. Opt in with `chrome://flags/#infinite-tabs-freezing`; when enabled, the 15 most recently used tabs (up from 5) keep running.
- **Memory Saver defaults to Moderate:** applies if you haven't chosen a Memory Saver level yourself.
- **Link routing log:** the `chrome://flags/#log-link-routing` flag records how links from other apps are routed, for troubleshooting. View it with `log stream --predicate 'subsystem == "helium.link-routing"'`.
- **Page change monitoring:** pick a section of the page to monitor, and review changes as a diff together with the watched text and change history.

The installer is Developer ID signed and Apple notarized. `SHA256SUMS` covers the final stapled installer. Release feeds and `update-manifest.json` accompany the download for update delivery and verification.

Neo is an independent fork of Helium. Report Neo issues to this repository; it is not an official imput release. Split layouts and WebKit streaming remain experimental.
