# Helium AI Agent Guidelines

- The official Helium repo (https://github.com/imputnet/helium) does not permit AI agent usage for new contributors. This (https://github.com/aagedal/helium) is a private fork where we can use AI. But we must not make PRs that are sent back to the official repo. We can only make PRs for this forked repo.

## Persistent local macOS build

`[user_home]` means the current user’s home directory (for example, `$HOME` in shell commands). Resolve this placeholder before using the paths below.

- Reuse `[user_home]/Developer/helium/build` for local Apple Silicon builds. It contains the prepared Chromium source, downloaded toolchains, and compiled outputs. Preserve it when creating or removing worktrees; do not create a fresh Chromium checkout for routine changes.
- Build command: `[user_home]/Developer/helium/build/build-local.sh`. Launch command: `[user_home]/Developer/helium/build/run-local.sh` (uses a separate development profile).
- Prepared source: `build/macos/build/src`; compiled output: `build/macos/build/src/out/Default`; app: `build/macos/build/src/out/Default/Helium.app`, all relative to `[user_home]/Developer/helium`.
- `build/fork-source` preserves the fork source used for the build, including local compiler fixes. `build/macos/helium-chromium` points to this snapshot. Check `build/fork-revision.txt` and the snapshot's Git diff before changing it. The main checkout or a new worktree may be at a different revision.
- The build command compiles the existing prepared source. Updating repository patches or the snapshot does **not** apply them to Chromium automatically. Reconcile and apply the intended changes to the existing source tree before rebuilding; retain unrelated compiled outputs.
- Only one build/agent may modify the shared source and output directories at a time. Do not run reset, initial setup, or the platform release build script against this cache without checking for destructive steps; `prepare_sources` deletes the output directory.
- Keep the Python environment at `build/venv` and the existing GN arguments. This is a component development build with debug symbols and precompiled headers disabled; both Chromium and Sparkle automatic updaters are disabled. The app depends on libraries in its build output directory.
- Worktrees can symlink their `build` directory to the persistent cache. Use the persistent launch command after restarting the development app so it no longer depends on an old worktree path.
