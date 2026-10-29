Helium Neo 0.20.2.1 can find an image on the page or in your other tabs, and updates Chromium to 156.0.8078.73 and upstream Helium to 0.20.2.

Download **Helium-Neo-0.20.2.1-macOS-arm64-signed.dmg**, open it, and drag **Helium Neo** to Applications, replacing an existing copy. Requires an Apple Silicon Mac running macOS 13 or later. WebKit streaming tabs require macOS 14 or later. Installations of 0.19.4.1 or later with browser updates enabled receive this release automatically. Users of earlier betas must install it manually once.

**New in Neo**

- **Find an image on the page:** press Command-F and paste a copied image into the empty find field, or click the image button in the find bar to paste or choose an image file. The find bar counts visually matching images and outlines them; Enter, Shift-Enter and the arrow buttons scroll to each match. Matching compares appearance, so resized, recompressed and cropped copies are found. Images are compared locally and never uploaded.
- **Find an image in other tabs:** right-click an image and choose **Find this image in other tabs** to switch to the tab where it appears. **Find chosen image on this page** in a page's context menu searches for it again.

**From upstream Helium 0.20.2**

- Chromium 156.0.8078.73.
- Bangs load faster and more reliably, and cached bangs are no longer used when bangs are turned off.

The installer is Developer ID signed and Apple notarized. `SHA256SUMS` covers the final stapled installer. Release feeds and `update-manifest.json` accompany the download for update delivery and verification.

Neo is an independent fork of Helium. Report Neo issues to this repository; it is not an official imput release. Split layouts, WebKit streaming and image matching remain experimental.
