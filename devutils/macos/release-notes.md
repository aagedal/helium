Helium Neo 0.20.1.1 updates to Chromium 156.0.8078.47 and the latest Helium, and adds page change monitoring.

Download **Helium-Neo-0.20.1.1-macOS-arm64-signed.dmg**, open it, and drag **Helium Neo** to Applications, replacing an existing copy. Requires an Apple Silicon Mac running macOS 13 or later. The experimental WebKit renderer requires macOS 14 or later. Installations of 0.19.4.1 with browser updates enabled receive this release automatically. Users of earlier betas must install it manually once.

**New in Neo**

- **Page change monitoring:** under **Tab view**, monitor a page's article text or a selected section for changes. A tab indicator signals a change; **Review page changes…** shows the removed and added text. Optionally save a screenshot and/or PDF automatically on each change, with a JSON source record and SHA-256 checksum.
- **More auto-refresh intervals:** auto-refresh now offers intervals from 5 seconds to 1 hour, with an optional ±5% variation for each refresh. Automatic reloads are rate-limited across the browser.
- **Identifiable screenshot filenames:** saved screenshots include the capture time (UTC), the source hostname and the page title.

**From upstream Helium**

- Chromium 156.0.8078.47.
- Zen mode fixes: expand on hover now works with zen mode, the sidebar no longer bounces at the window edge, hover corners update when the sidebar switches sides, and closing a zen-mode window no longer crashes.
- New flag to hide the native window buttons. Refreshed browser layout and appearance settings.
- Fixed canvas image-data noise writing past its pixel buffer.

The installer is Developer ID signed and Apple notarized. `SHA256SUMS` covers the final stapled installer. Release feeds and `update-manifest.json` accompany the download for update delivery and verification.

Neo is an independent fork of Helium. Report Neo issues to this repository; it is not an official imput release. Split layouts and the optional WebKit renderer remain experimental.
