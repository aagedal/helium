Helium Neo's first non-beta release adds automatic updates with independent GitHub and aagedal.me download sources.

Download **Helium-Neo-0.19.4.1-macOS-arm64-signed.dmg**, open it, and drag **Helium Neo** to Applications, replacing an existing copy. Requires an Apple Silicon Mac running macOS 13 or later. The experimental WebKit renderer requires macOS 14 or later.

**Users of previous betas must install this release manually once.** After browser updates are enabled in Helium services settings, Neo checks for updates on startup and daily, downloads them in the background, and uses the existing Relaunch/install-on-quit flow. GitHub is the primary source; failed feed or installer downloads retry through aagedal.me. Updates require Neo's dedicated cryptographic signature on either host.

This release includes the current Neo features: split panes and mobile previews, workspace and tab customizations, encrypted folder-based sync, and screenshot exports with source attribution, IPTC/XMP metadata, HDR JPEG XL, a remembered screenshot folder, and optional source-report ZIPs. Helium's extension proxy and other enabled services continue to use imput's infrastructure with the existing consent controls.

The installer is Developer ID signed and Apple notarized. `SHA256SUMS` covers the final stapled installer. Release feeds and `update-manifest.json` accompany the download for update delivery and verification.

Neo is an independent fork of Helium. Report Neo issues to this repository; it is not an official imput release. Split layouts and the optional WebKit renderer remain experimental.
