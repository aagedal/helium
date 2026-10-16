import AppKit
import WebKit

// Deliberately independent of Chromium: first establish whether production
// services accept FairPlay playback in the system WKWebView.
final class BrowserWindow: NSWindowController, WKNavigationDelegate, WKUIDelegate {
    let webView: WKWebView
    let address = NSTextField(string: "")
    let status = NSTextField(labelWithString: "Ready")
    let safariIdentity = NSButton(checkboxWithTitle: "Safari identity", target: nil, action: nil)

    init() {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.preferences.isElementFullscreenEnabled = true
        webView = WKWebView(frame: .zero, configuration: configuration)
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1200, height: 800),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable],
                              backing: .buffered, defer: false)
        super.init(window: window)
        window.title = "Helium — WebKit Playback Experiment"
        window.center()
        window.isReleasedWhenClosed = false
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.isInspectable = true

        let toolbar = NSStackView()
        toolbar.orientation = .horizontal
        toolbar.spacing = 8
        for (title, action) in [("Back", #selector(back)), ("Forward", #selector(forward)),
                                ("Reload", #selector(reload)), ("Netflix", #selector(netflix)),
                                ("TV 2 Play", #selector(tv2))] {
            toolbar.addArrangedSubview(NSButton(title: title, target: self, action: action))
        }
        address.placeholderString = "https://…"
        address.target = self
        address.action = #selector(navigate)
        address.setContentHuggingPriority(.defaultLow, for: .horizontal)
        toolbar.addArrangedSubview(address)
        safariIdentity.target = self
        safariIdentity.action = #selector(changeIdentity)
        toolbar.addArrangedSubview(safariIdentity)
        toolbar.addArrangedSubview(NSButton(title: "Diagnostics", target: self, action: #selector(diagnostics)))

        status.font = .systemFont(ofSize: 11)
        status.lineBreakMode = .byTruncatingTail
        let root = window.contentView!
        for view in [toolbar, webView, status] {
            view.translatesAutoresizingMaskIntoConstraints = false
            root.addSubview(view)
        }
        NSLayoutConstraint.activate([
            toolbar.topAnchor.constraint(equalTo: root.topAnchor, constant: 8),
            toolbar.leadingAnchor.constraint(equalTo: root.leadingAnchor, constant: 8),
            toolbar.trailingAnchor.constraint(equalTo: root.trailingAnchor, constant: -8),
            address.widthAnchor.constraint(greaterThanOrEqualToConstant: 120),
            webView.topAnchor.constraint(equalTo: toolbar.bottomAnchor, constant: 8),
            webView.leadingAnchor.constraint(equalTo: root.leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: root.trailingAnchor),
            webView.bottomAnchor.constraint(equalTo: status.topAnchor, constant: -5),
            status.leadingAnchor.constraint(equalTo: root.leadingAnchor, constant: 8),
            status.trailingAnchor.constraint(equalTo: root.trailingAnchor, constant: -8),
            status.bottomAnchor.constraint(equalTo: root.bottomAnchor, constant: -5)
        ])
        window.minSize = NSSize(width: 1050, height: 500)
        load("https://www.netflix.com/")
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }
    func load(_ value: String) {
        guard let url = URL(string: value), ["https", "http"].contains(url.scheme?.lowercased() ?? "") else { return }
        address.stringValue = value
        webView.load(URLRequest(url: url))
    }
    @objc func netflix() { load("https://www.netflix.com/") }
    @objc func tv2() { load("https://play.tv2.no/") }
    @objc func back() { webView.goBack() }
    @objc func forward() { webView.goForward() }
    @objc func reload() { webView.reload() }
    @objc func navigate() {
        let value = address.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        load(value.contains("://") ? value : "https://" + value)
    }
    @objc func changeIdentity() {
        // Compatibility experiment only; a user agent does not grant DRM trust.
        webView.customUserAgent = safariIdentity.state == .on
            ? "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
            : nil
        webView.reload()
    }
    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        status.stringValue = "Loading…"
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        address.stringValue = webView.url?.absoluteString ?? ""
        status.stringValue = "Loaded. Sign in and play a protected title; use Diagnostics during playback."
    }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        status.stringValue = error.localizedDescription
    }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        status.stringValue = error.localizedDescription
    }
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        status.stringValue = "WebKit content process terminated. Reload to retry."
    }
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        // Keep target=_blank authentication/navigation within this test session.
        if navigationAction.targetFrame == nil { webView.load(navigationAction.request) }
        return nil
    }
    @objc func diagnostics() {
        // Read only capability and media state. Do not collect cookies, tokens,
        // media URLs, or license requests. Capability alone is not playback proof.
        let script = """
        return {
          userAgent: navigator.userAgent,
          secureContext: window.isSecureContext,
          emeAPI: typeof navigator.requestMediaKeySystemAccess === 'function',
          legacyFairPlayAPI: typeof window.WebKitMediaKeys !== 'undefined',
          media: Array.from(document.querySelectorAll('video,audio')).map(v => ({
            paused: v.paused, ended: v.ended, currentTime: v.currentTime,
            readyState: v.readyState, networkState: v.networkState,
            width: v.videoWidth, height: v.videoHeight,
            mediaKeysAttached: !!(v.mediaKeys || v.webkitKeys),
            error: v.error ? {code: v.error.code, message: v.error.message} : null
          }))
        };
        """
        webView.callAsyncJavaScript(script, arguments: [:], in: nil, in: .page) { [weak self] result in
            guard let self = self, let window = self.window else { return }
            let details: String
            switch result {
            case .success(let value):
                if let data = try? JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted, .sortedKeys]),
                   let json = String(data: data, encoding: .utf8) { details = json }
                else { details = String(describing: value) }
            case .failure(let error): details = error.localizedDescription
            }
            let alert = NSAlert()
            alert.messageText = "Playback diagnostics"
            alert.informativeText = "Confirm visible video, audible sound, and advancing time. Capability detection alone does not prove protected playback. Media inside subframes is not included."
            let scroll = NSScrollView(frame: NSRect(x: 0, y: 0, width: 650, height: 300))
            scroll.hasVerticalScroller = true
            let text = NSTextView(frame: scroll.bounds)
            text.isEditable = false
            text.font = .monospacedSystemFont(ofSize: 11, weight: .regular)
            text.string = details
            scroll.documentView = text
            alert.accessoryView = scroll
            alert.beginSheetModal(for: window)
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var browser: BrowserWindow?
    func applicationDidFinishLaunching(_ notification: Notification) {
        let menu = NSMenu()
        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit Helium WebKit Experiment", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        menu.addItem(appItem)
        let editItem = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        for (title, selector, key) in [("Undo", "undo:", "z"), ("Cut", "cut:", "x"),
                                       ("Copy", "copy:", "c"), ("Paste", "paste:", "v"),
                                       ("Select All", "selectAll:", "a")] {
            editMenu.addItem(withTitle: title, action: Selector(selector), keyEquivalent: key)
        }
        editItem.submenu = editMenu
        menu.addItem(editItem)
        NSApp.mainMenu = menu
        browser = BrowserWindow()
        browser?.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.setActivationPolicy(.regular)
app.delegate = delegate
app.run()
