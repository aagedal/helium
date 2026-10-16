#!/bin/bash
set -euo pipefail

experiment_dir="$(cd "$(dirname "$0")" && pwd)"
output_dir="$experiment_dir/out"
app_bundle="$output_dir/Helium WebKit Experiment.app"
mkdir -p "$app_bundle/Contents/MacOS" "$output_dir/module-cache"
xcrun swiftc "$experiment_dir/main.swift" -o "$app_bundle/Contents/MacOS/HeliumWebKitExperiment" \
    -framework AppKit -framework WebKit -target "$(uname -m)-apple-macosx13.3" \
    -module-cache-path "$output_dir/module-cache"
cat > "$app_bundle/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>HeliumWebKitExperiment</string>
<key>CFBundleIdentifier</key><string>no.aagedal.helium.webkit-experiment</string>
<key>CFBundleName</key><string>Helium WebKit Experiment</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleShortVersionString</key><string>0.1</string>
<key>LSMinimumSystemVersion</key><string>13.3</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --sign - "$app_bundle"
printf 'Built: %s\n' "$app_bundle"
if [[ "${1:-}" == "--run" ]]; then
    open "$app_bundle"
fi
