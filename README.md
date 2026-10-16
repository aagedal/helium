# Helium Neo

<div align="center">
    <img src="resources/branding/app_icon/raw.png"
        title="Helium Neo" alt="Helium Neo orbital logo" width="120" />
    <p>A private Helium fork with flexible split workspaces and per-tab previews.</p>
</div>

Helium Neo builds on [Helium](https://helium.computer/) and keeps this fork's
changes and pull requests in [aagedal/helium](https://github.com/aagedal/helium).
It retains Helium's privacy-focused foundation and adds the features below.

## What this fork changes

### Split workspaces

- **Two to six panes in one tab**, with columns, rows, grids, and mixed layouts.
  Right-click a tab and use **Split Layout** to choose a preset. Existing pages
  are retained, and additional panes open new-tab pages.
- **Resizable boundaries throughout the split**, including the inner dividers
  of grids and mixed layouts. Drag a divider or focus it and use arrow keys.
- **See the active pane** with the normal sub-tab background highlight,
  including compact pinned tabs and vertical tabs. Expanded vertical pinned
  splits use icon tiles, wrapping larger splits to fit the sidebar. Click a sub-tab in the current split to select its pane.
- **Reload the focused pane** with Command-R, including bypass-cache reload.
  Explicitly selecting additional tab-strip tabs retains multiple-tab reload.
- **Pinned splits return across sessions** with their pages, layout, divider
  sizes, and each pane's mobile mode and auto-refresh interval. This works with
  new-tab startup as well as last-session restore.

### Per-tab rendering and refresh

Right-click a tab and open **Tab view**. Each setting belongs to that individual
page, including when it is part of a split.

- **Mobile preview (402 × 874)** provides a fixed portrait CSS viewport with
  3× device density and touch emulation, scaled to fit the pane.
- **Mobile preview (402 wide, full height)** keeps the mobile width and uses
  the entire pane height, with no fixed portrait-height cap. Narrow panes scale
  the preview down to fit.
- **Auto-refresh** can be turned off or set from 15 to 180 seconds in 15-second
  steps. It skips loading, discarded, crashed, and POST pages, and pending
  navigations.
- **Create desktop/mobile workspace** makes desktop and mobile copies in a
  pinned saved tab group, with a side-by-side split. The original page is kept.

Mobile previews run without opening a DevTools window. They use Chromium's
mobile viewport and touch emulation, plus an Android mobile Chromium identity
in the user agent and Client Hints. Switching between desktop and mobile reloads
eligible pages so device detection runs again. The rendering engine remains
Chromium. Per-tab settings are restored locally and are not synced between devices.

### Startup and identity

- Background session and pinned tabs load when needed, reducing startup work.
- The app uses the **Helium Neo** name and violet orbital icon, including a
  macOS icon asset that preserves the orbital artwork in the Dock.
- Separate macOS bundle, profile, and Keychain identities allow Helium Neo to
  coexist with the normal Helium release. Existing Helium profiles are not
  migrated. The local development launcher uses its own development profile.

### Screenshots with source documentation

Press **Command-Shift-S** on macOS (**Ctrl-Shift-S** on Windows/Linux), or
right-click an HTTP or HTTPS page and choose **Capture screenshot with source…**,
then drag a rectangle over the content to preserve. In a split workspace, the
shortcut uses the focused pane; the context menu uses the pane you right-clicked.
Release the mouse to capture only your rectangle. Escape cancels selection.
Press Enter instead of dragging to capture the visible pane using the keyboard.
The macOS File menu also shows the command and its shortcut. Change the binding
in **Settings → Keyboard shortcuts**, under **Capture screenshot with source**.

The review dialog records the page URL, title, capture times in UTC, selection
bounds and image dimensions. You can optionally enter a post permalink, posting
account, publication date as displayed, and notes or post text. These entries
are recorded separately from observed page details. The browser can suggest a
post permalink for Twitter/X, Instagram, Facebook, Threads and Truth Social using
visible links and the post container overlapping your selection. One clear match fills the field;
multiple matches offer a chooser. Check or edit the link before saving. The
record preserves candidate links and the chosen link's origin. Suggestions are
heuristics, not verified attribution. Posting account and publication date can
also fill from the selected post when the site exposes them. The record keeps
the displayed date, any tooltip or machine-readable timestamp, and linked
account details separate from your reviewed values. Relative dates and missing
timezones are preserved as shown. You can edit or clear any field; notes remain
manual. The screenshot capture time is always recorded separately.
For supported social timestamp links that expose the full date only on hover, the
browser briefly hovers the timestamp after capturing the pixels. It uses that
full date for the publication field and keeps the relative label separately.
If the tooltip is unavailable, the original site text remains the fallback.
For Twitter/X and Threads quote posts, a capture including the enclosing post prefers its
permalink, account and date. A crop confined to the quoted post prefers the
original. Both links remain available in the source chooser, and the embedded
record preserves their relationship and separate source details. Facebook photo
posts prefer the enclosing post's permalink, account and date; attached photo
links remain available as secondary sources, including for a photo-only crop.

Choose **PNG**, **JPEG** (quality 95), or **JPEG XL** in the review dialog. PNG
and JPEG XL use lossless compression; JPEG uses lossy compression. Each image
embeds IPTC Core fields in XMP, including a readable source description, capture
date and posting account, plus the complete source record. Capture limitations
are stored separately in Extended Description. The page title fills both Title
and Headline; the post permalink remains in Description. The browser and version
are stored in Creator Tool, and the description omits copyright and language
settings. The posting account is recorded as a source, not assumed to be the
image creator or copyright owner.

The embedded fields are arranged for photo and newsroom metadata tools:

- **Title and Headline:** the captured page title.
- **Description:** the readable source report, including the reviewed post
  permalink, account, publication date and notes when supplied.
- **Extended Description:** capture limitations, kept out of Description.
- **Source:** the reviewed posting account; the page URL is also preserved
  separately in XMP Source.
- **Date Created:** the screenshot capture time, separate from the post's
  publication date. **Creator Tool** identifies the browser and version.

The complete structured source record remains embedded in every format,
including observed values, reviewed values and how each was obtained. The ZIP's
`source.txt` retains the capture limitations alongside the readable report.

The IPTC Copyright Notice uses **Screenshot / [account] / [platform]**.
Choose **Norsk — Skjermbilde** under **Copyright text language** for
**Skjermbilde / [account] / [platform]**. The choice is remembered, and a live
preview shows the resulting text. Twitter/X uses the platform name **Twitter**.
The field stays empty when no posting account is supplied.

**Automatically preserve HDR** is on by default and remembered for your profile.
When the selected rendered pixels contain HDR brightness, the dialog automatically
chooses **16-bit JPEG XL**, including Rec.2100 PQ color information. Ordinary
SDR selections save at 8-bit. You can turn preservation off or choose PNG/JPEG
for SDR output; the dialog and embedded record identify the conversion. HDR
readback availability, detection, output depth and color encoding are recorded.
The preview and clipboard are SDR. HDR already tone-mapped by the webpage,
renderer or display pipeline cannot be recovered by screenshot capture.

**Save capture…** opens a save-location prompt. Clear **Include source report and
checksum (ZIP)** to save the image alone. Leave it checked for a ZIP containing
`screenshot.png`, `.jpg` or `.jxl`, `metadata.json` and a readable `source.txt`,
with a SHA-256 hash of the completed image. Format and ZIP choices are remembered
for your profile. **Copy image** copies pixels without the embedded source record.
A capture preserves the selected rendered region. Capture times use the computer's
clock; the hash alone does not establish authenticity or publication time.

Split layouts remain experimental. Geometry and viewport helpers have standalone
sanitizer checks; the full Chromium browser regressions require an unpruned test
build. See [developer notes and validation](devutils/README.md).

## Builds and downloads

This repository contains the fork's patches, resources, and build utilities.
Installable Apple Silicon betas are published on the
[Helium Neo releases page](https://github.com/aagedal/helium/releases). Download
the signed DMG and drag **Helium Neo** to Applications. These standalone beta
packages include their runtime libraries. Automatic updates are disabled;
install subsequent betas manually.

The [official Helium downloads](https://helium.computer/) distribute upstream
Helium and do not include Helium Neo's custom features.

For the prepared local Apple Silicon development build:

```sh
~/Developer/helium/build/build-local.sh
~/Developer/helium/build/run-local.sh
```

The launcher opens `Helium Neo.app` using a separate development profile. This
component build depends on libraries beside the app in its build output folder;
keep that folder intact. Chromium and Sparkle automatic updates are disabled in
the local development build.

Read [AGENTS.md](AGENTS.md) before modifying the shared build cache and
[devutils/README.md](devutils/README.md) for feature details, resource generation,
and validation commands.

## Upstream Helium repositories

These links describe the upstream project and its packaging, services, and tools.

### Platform packaging and tooling
- [Helium for macOS](https://github.com/imputnet/helium-macos)
- [Helium for Linux](https://github.com/imputnet/helium-linux)
- [Helium for Windows](https://github.com/imputnet/helium-windows)

### Web services
[Helium services](https://github.com/imputnet/helium-services) are Helium's
privacy-first cloud services that handle the extension proxy, !bangs, filter
lists, browser updates, crash reports, and etc. The services are self-hostable
and the repo includes exactly what we use and host, down to Ansible playbooks.

### Components
- [Helium uBlock Origin](https://github.com/imputnet/uBlock) is a
Helium-specific fork of uBlock Origin that includes our filters, defaults, and
CNAME uncloaking.

- [Helium onboarding](https://github.com/imputnet/helium-onboarding) includes
the browser setup experience seen at `helium://setup` on first launch.

- [Helium non-free assets](https://github.com/imputnet/helium-nonfree-assets)
repo handles non-free assets used in Helium, such as search engine icons and
icons of other browsers.

### Tooling
- [Chromium tarballs](https://github.com/imputnet/chromium-tarballs) creates
prepared Chromium source archives used by Helium builds.

- [Helium Prism](https://github.com/imputnet/helium-prism) is a Svelte UI
Component library used in onboarding and the landing page.

### Legal documents
[Helium Legal](https://github.com/imputnet/helium-legal) repo includes the
source for [Terms of Use](https://helium.computer/terms) and
[Privacy Policy](https://helium.computer/privacy) documents, along with their
full change history.

## Development and contributions

The [upstream macOS development guide](https://github.com/imputnet/helium-macos/blob/main/docs/building.md#development-build-and-environment)
describes the packaging toolchain. Use this private fork as the source of custom
patches and preserve the prepared local cache described above.

Changes and pull requests for Helium Neo must target
[aagedal/helium](https://github.com/aagedal/helium). Do not send AI-assisted
contributions from this fork to the official Helium repositories. Upstream's
[contribution guidelines](CONTRIBUTING.md) describe its separate policies.

## Credits

### The Chromium project
[The Chromium Project](https://www.chromium.org/) is at the core of Helium,
making it possible in the first place.

### ungoogled-chromium
Helium originally branched off
[ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium).
Special thanks to everyone behind ungoogled-chromium, they made working with
Chromium much easier.

### Other Chromium projects

Helium includes some patches from other open source Chromium projects:

- [Inox patchset](https://github.com/gcarq/inox-patchset)
- [Debian](https://tracker.debian.org/pkg/chromium-browser)
- [Bromite](https://github.com/bromite/bromite)
- [Iridium Browser](https://iridiumbrowser.de/)
- [Brave](https://github.com/brave/brave-core)

All patches are sorted by vendor in the [patches](patches/) directory of this repo.

## License
All code, patches, modified portions of imported code or patches, and
any other content that is unique to Helium and not imported from other
repositories is licensed under GPL-3.0. See [LICENSE](LICENSE).

Any content imported from other projects retains its original license (for
example, any original unmodified code imported from ungoogled-chromium remains
licensed under their [BSD 3-Clause license](LICENSE.ungoogled_chromium)).
