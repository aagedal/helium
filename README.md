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
mobile viewport and touch emulation; the rendering engine and browser user agent
remain Chromium's. Per-tab settings are restored locally and are not synced
between devices.

### Startup and identity

- Background session and pinned tabs load when needed, reducing startup work.
- The app uses the **Helium Neo** name and violet orbital icon, including a
  macOS icon asset that preserves the orbital artwork in the Dock.
- Separate macOS bundle, profile, and Keychain identities allow Helium Neo to
  coexist with the normal Helium release. Existing Helium profiles are not
  migrated. The local development launcher uses its own development profile.

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
