Helium Neo 0.20.3.1 lets you drop images onto the find bar, finds more lazily loaded images, and updates Chromium to 156.0.8078.79 and upstream Helium to 0.20.3.

Download **Helium-Neo-0.20.3.1-macOS-arm64-signed.dmg**, open it, and drag **Helium Neo** to Applications, replacing an existing copy. Requires an Apple Silicon Mac running macOS 13 or later. WebKit streaming tabs require macOS 14 or later. Installations of 0.19.4.1 or later with browser updates enabled receive this release automatically. Users of earlier betas must install it manually once.

**New in Neo**

- **Drop an image on the find bar:** drag an image file, or an image from a page or another app, onto the find bar to search the page for it.
- **More images found:** image search loads up to 300 lazily loaded images nearest the viewport instead of stopping 20 screens away, and handles pages that load images by script through `data-src` and `data-srcset`.

**From upstream Helium 0.20.3**

- Chromium 156.0.8078.79.
- The suggestions URL field for custom search engines saves your input again.

The installer is Developer ID signed and Apple notarized. `SHA256SUMS` covers the final stapled installer. Release feeds and `update-manifest.json` accompany the download for update delivery and verification.

Neo is an independent fork of Helium. Report Neo issues to this repository; it is not an official imput release. Split layouts, WebKit streaming and image matching remain experimental.
