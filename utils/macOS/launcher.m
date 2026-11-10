// Main executable of ASE Studio.app: a native window (WKWebView) around the
// ASE Studio backend. Contents/Resources/launcher.sh prepares the environment
// and execs the backend; this app shows the page it serves and stops the
// backend when the window closes.
#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>

static NSString *const kTitle = @"ASE Studio";

@interface AppDelegate : NSObject <NSApplicationDelegate, NSWindowDelegate, WKUIDelegate,
                                   WKNavigationDelegate, WKDownloadDelegate>
@property(strong) NSWindow *window;
@property(strong) WKWebView *web;
@property(strong) NSMutableArray<NSWindow *> *popups;   // e.g. the memory pop-out
@property(strong) NSTask *backend;
@property(strong) NSMutableString *backendOutput;
@property(copy) NSString *serverURL;
@property BOOL closeConfirmed;
@end

@implementation AppDelegate

- (NSString *)logPath {
    return [NSHomeDirectory() stringByAppendingPathComponent:@"Library/Logs/ASE Studio.log"];
}

- (NSString *)workspacePath {
    NSString *custom = NSProcessInfo.processInfo.environment[@"ASE_STUDIO_WORKSPACE"];
    return custom.length ? custom : [NSHomeDirectory() stringByAppendingPathComponent:@"ASE Studio"];
}

// ------------------------------------------------------------------ menu
- (NSMenuItem *)item:(NSString *)title action:(SEL)action key:(NSString *)key {
    return [[NSMenuItem alloc] initWithTitle:title action:action keyEquivalent:key];
}

- (void)buildMenu {
    NSMenu *bar = [NSMenu new];

    NSMenu *app = [[NSMenu alloc] initWithTitle:kTitle];
    [app addItem:[self item:@"About ASE Studio"
                     action:@selector(orderFrontStandardAboutPanel:) key:@""]];
    [app addItem:NSMenuItem.separatorItem];
    [app addItem:[self item:@"Open Projects Folder" action:@selector(openWorkspace:) key:@""]];
    [app addItem:[self item:@"Show Log" action:@selector(openLog:) key:@""]];
    [app addItem:NSMenuItem.separatorItem];
    [app addItem:[self item:@"Hide ASE Studio" action:@selector(hide:) key:@"h"]];
    [app addItem:NSMenuItem.separatorItem];
    [app addItem:[self item:@"Quit ASE Studio" action:@selector(terminate:) key:@"q"]];

    // Undo/redo stay with the page (it binds Cmd+Z/Cmd+Shift+Z itself).
    NSMenu *edit = [[NSMenu alloc] initWithTitle:@"Edit"];
    [edit addItem:[self item:@"Cut" action:@selector(cut:) key:@"x"]];
    [edit addItem:[self item:@"Copy" action:@selector(copy:) key:@"c"]];
    [edit addItem:[self item:@"Paste" action:@selector(paste:) key:@"v"]];
    [edit addItem:[self item:@"Select All" action:@selector(selectAll:) key:@"a"]];

    NSMenu *view = [[NSMenu alloc] initWithTitle:@"View"];
    [view addItem:[self item:@"Reload" action:@selector(reloadPage:) key:@"r"]];
    [view addItem:NSMenuItem.separatorItem];
    [view addItem:[self item:@"Actual Size" action:@selector(zoomReset:) key:@"0"]];
    [view addItem:[self item:@"Zoom In" action:@selector(zoomIn:) key:@"+"]];
    [view addItem:[self item:@"Zoom Out" action:@selector(zoomOut:) key:@"-"]];
    [view addItem:NSMenuItem.separatorItem];
    NSMenuItem *full = [self item:@"Enter Full Screen" action:@selector(toggleFullScreen:) key:@"f"];
    full.keyEquivalentModifierMask = NSEventModifierFlagCommand | NSEventModifierFlagControl;
    [view addItem:full];

    NSMenu *win = [[NSMenu alloc] initWithTitle:@"Window"];
    [win addItem:[self item:@"Minimize" action:@selector(performMiniaturize:) key:@"m"]];
    [win addItem:[self item:@"Zoom" action:@selector(performZoom:) key:@""]];
    [win addItem:[self item:@"Close" action:@selector(performClose:) key:@"w"]];
    NSApp.windowsMenu = win;

    for (NSMenu *menu in @[app, edit, view, win]) {
        NSMenuItem *top = [NSMenuItem new];
        top.submenu = menu;
        [bar addItem:top];
    }
    NSApp.mainMenu = bar;
}

- (void)openWorkspace:(id)sender {
    [NSWorkspace.sharedWorkspace openURL:[NSURL fileURLWithPath:self.workspacePath]];
}
- (void)openLog:(id)sender {
    [NSWorkspace.sharedWorkspace openURL:[NSURL fileURLWithPath:self.logPath]];
}
- (void)reloadPage:(id)sender {
    if (self.serverURL) [self.web loadRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:self.serverURL]]];
}
- (void)zoomReset:(id)sender { self.web.pageZoom = 1.0; }
- (void)zoomIn:(id)sender { self.web.pageZoom = MIN(self.web.pageZoom + 0.1, 3.0); }
- (void)zoomOut:(id)sender { self.web.pageZoom = MAX(self.web.pageZoom - 0.1, 0.5); }

// ------------------------------------------------------------------ startup
- (void)applicationDidFinishLaunching:(NSNotification *)note {
    [self buildMenu];
    self.popups = [NSMutableArray array];

    WKWebViewConfiguration *config = [WKWebViewConfiguration new];
    config.websiteDataStore = WKWebsiteDataStore.defaultDataStore;   // keeps localStorage
    self.web = [[WKWebView alloc] initWithFrame:NSZeroRect configuration:config];
    self.web.UIDelegate = self;
    self.web.navigationDelegate = self;
    [self.web loadHTMLString:
        @"<html><body style='font:15px -apple-system;color:#888;display:flex;height:100vh;"
         "margin:0;align-items:center;justify-content:center;background:Canvas'>"
         "<meta name='color-scheme' content='light dark'>Starting ASE Studio…</body></html>"
                     baseURL:nil];

    self.window = [[NSWindow alloc]
        initWithContentRect:NSMakeRect(0, 0, 1400, 900)
                  styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
                            NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable
                    backing:NSBackingStoreBuffered
                      defer:NO];
    self.window.title = kTitle;
    self.window.contentView = self.web;
    self.window.delegate = self;
    self.window.minSize = NSMakeSize(900, 600);
    [self.window center];
    self.window.frameAutosaveName = @"ASEStudioMainWindow";
    [self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];

    [self startBackend];
}

- (void)startBackend {
    NSString *script = [NSBundle.mainBundle pathForResource:@"launcher" ofType:@"sh"];
    NSPipe *pipe = [NSPipe pipe];
    self.backendOutput = [NSMutableString string];
    self.backend = [NSTask new];
    self.backend.executableURL = [NSURL fileURLWithPath:@"/bin/bash"];
    self.backend.arguments = @[script];
    self.backend.standardOutput = pipe;
    self.backend.standardError = pipe;

    __weak AppDelegate *weakSelf = self;
    pipe.fileHandleForReading.readabilityHandler = ^(NSFileHandle *handle) {
        NSData *data = handle.availableData;
        if (!data.length) { handle.readabilityHandler = nil; return; }
        NSString *text = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding] ?: @"";
        dispatch_async(dispatch_get_main_queue(), ^{ [weakSelf backendPrinted:text]; });
    };
    self.backend.terminationHandler = ^(NSTask *task) {
        dispatch_async(dispatch_get_main_queue(), ^{ [weakSelf backendExited:task.terminationStatus]; });
    };

    NSError *error = nil;
    if (![self.backend launchAndReturnError:&error]) {
        [self fatal:[NSString stringWithFormat:@"Could not start the server: %@", error.localizedDescription]];
    }
}

- (void)backendPrinted:(NSString *)text {
    [self.backendOutput appendString:text];
    if (self.serverURL) return;
    NSRegularExpression *re = [NSRegularExpression
        regularExpressionWithPattern:@"http://127\\.0\\.0\\.1:[0-9]+" options:0 error:nil];
    NSTextCheckingResult *match = [re firstMatchInString:self.backendOutput options:0
                                                   range:NSMakeRange(0, self.backendOutput.length)];
    if (match) {
        self.serverURL = [self.backendOutput substringWithRange:match.range];
        [self reloadPage:nil];
    }
}

- (void)backendExited:(int)status {
    if (self.closeConfirmed) return;
    NSString *tail = self.backendOutput.length > 1500
        ? [self.backendOutput substringFromIndex:self.backendOutput.length - 1500] : self.backendOutput;
    [self fatal:[NSString stringWithFormat:@"The ASE Studio server stopped (code %d).\n\n%@\n\nLog: %@",
                                           status, tail, self.logPath]];
}

- (void)fatal:(NSString *)message {
    NSAlert *alert = [NSAlert new];
    alert.alertStyle = NSAlertStyleCritical;
    alert.messageText = kTitle;
    alert.informativeText = message;
    [alert runModal];
    self.closeConfirmed = YES;
    [NSApp terminate:nil];
}

// ------------------------------------------------------------------ shutdown
- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)app { return YES; }

- (BOOL)applicationShouldHandleReopen:(NSApplication *)app hasVisibleWindows:(BOOL)visible {
    [self.window makeKeyAndOrderFront:nil];
    return YES;
}

// Ask before losing unsaved source edits (same hook the Linux window uses).
- (void)confirmClose:(void (^)(BOOL ok))done {
    if (self.closeConfirmed || !self.serverURL) { done(YES); return; }
    [self.web evaluateJavaScript:@"!!(window.aseHasUnsavedChanges && window.aseHasUnsavedChanges())"
               completionHandler:^(id dirty, NSError *error) {
        if (![dirty boolValue]) { done(YES); return; }
        NSAlert *alert = [NSAlert new];
        alert.messageText = @"There are unsaved changes";
        alert.informativeText = @"If you quit ASE Studio now, your source changes will be lost.";
        [alert addButtonWithTitle:@"Cancel"];
        [alert addButtonWithTitle:@"Quit Without Saving"];
        done([alert runModal] == NSAlertSecondButtonReturn);
    }];
}

- (BOOL)windowShouldClose:(NSWindow *)sender {
    if (self.closeConfirmed) return YES;
    [self confirmClose:^(BOOL ok) {
        if (!ok) return;
        self.closeConfirmed = YES;
        [self.window close];
    }];
    return NO;
}

// Pop-outs belong to the main window: they close with it.
- (void)windowWillClose:(NSNotification *)note {
    if (note.object != self.window) return;
    for (NSWindow *popup in self.popups.copy) [popup close];
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)app {
    if (self.closeConfirmed) return NSTerminateNow;
    [self confirmClose:^(BOOL ok) {
        self.closeConfirmed = ok;
        [NSApp replyToApplicationShouldTerminate:ok];
    }];
    return NSTerminateLater;
}

- (void)applicationWillTerminate:(NSNotification *)note {
    self.closeConfirmed = YES;
    if (self.backend.running) {
        [self.backend terminate];
        [self.backend waitUntilExit];
    }
}

// ------------------------------------------------------------------ web UI hooks
- (void)webView:(WKWebView *)webView runJavaScriptAlertPanelWithMessage:(NSString *)message
    initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(void))done {
    NSAlert *alert = [NSAlert new];
    alert.messageText = kTitle;
    alert.informativeText = message;
    [alert runModal];
    done();
}

- (void)webView:(WKWebView *)webView runJavaScriptConfirmPanelWithMessage:(NSString *)message
    initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(BOOL))done {
    NSAlert *alert = [NSAlert new];
    alert.messageText = kTitle;
    alert.informativeText = message;
    [alert addButtonWithTitle:@"OK"];
    [alert addButtonWithTitle:@"Cancel"];
    done([alert runModal] == NSAlertFirstButtonReturn);
}

- (void)webView:(WKWebView *)webView runJavaScriptTextInputPanelWithPrompt:(NSString *)prompt
    defaultText:(NSString *)text initiatedByFrame:(WKFrameInfo *)frame
    completionHandler:(void (^)(NSString *))done {
    NSAlert *alert = [NSAlert new];
    alert.messageText = kTitle;
    alert.informativeText = prompt;
    NSTextField *field = [[NSTextField alloc] initWithFrame:NSMakeRect(0, 0, 300, 24)];
    field.stringValue = text ?: @"";
    alert.accessoryView = field;
    [alert addButtonWithTitle:@"OK"];
    [alert addButtonWithTitle:@"Cancel"];
    done([alert runModal] == NSAlertFirstButtonReturn ? field.stringValue : nil);
}

- (void)webView:(WKWebView *)webView runOpenPanelWithParameters:(WKOpenPanelParameters *)params
    initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(NSArray<NSURL *> *))done {
    NSOpenPanel *panel = [NSOpenPanel openPanel];
    panel.allowsMultipleSelection = params.allowsMultipleSelection;
    panel.canChooseDirectories = params.allowsDirectories;
    [panel beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse r) {
        done(r == NSModalResponseOK ? panel.URLs : nil);
    }];
}

// window.open / target=_blank: pages of the Studio itself (the memory
// pop-out) open in a window of the app, everything else in the default browser.
- (WKWebView *)webView:(WKWebView *)webView createWebViewWithConfiguration:(WKWebViewConfiguration *)c
    forNavigationAction:(WKNavigationAction *)action windowFeatures:(WKWindowFeatures *)f {
    NSURL *url = action.request.URL;
    if (![url.host isEqualToString:@"127.0.0.1"]) {
        if (url) [NSWorkspace.sharedWorkspace openURL:url];
        return nil;
    }
    // WebKit's configuration shares the main view's web process and storage,
    // so BroadcastChannel keeps the pop-out in sync with the Studio.
    WKWebView *view = [[WKWebView alloc] initWithFrame:NSZeroRect configuration:c];
    view.UIDelegate = self;
    view.navigationDelegate = self;
    NSRect frame = NSMakeRect(0, 0, f.width ? f.width.doubleValue : 1050,
                              f.height ? f.height.doubleValue : 720);
    NSWindow *popup = [[NSWindow alloc]
        initWithContentRect:frame
                  styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
                            NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable
                    backing:NSBackingStoreBuffered
                      defer:NO];
    popup.releasedWhenClosed = NO;
    popup.title = kTitle;
    popup.contentView = view;
    popup.minSize = NSMakeSize(650, 400);
    [popup center];
    [self.popups addObject:popup];
    __weak AppDelegate *weakSelf = self;
    __block id observer = [NSNotificationCenter.defaultCenter
        addObserverForName:NSWindowWillCloseNotification object:popup queue:nil
                usingBlock:^(NSNotification *note) {
        [NSNotificationCenter.defaultCenter removeObserver:observer];
        [weakSelf.popups removeObject:note.object];
    }];
    [popup makeKeyAndOrderFront:nil];
    return view;
}

// window.close() from a pop-out.
- (void)webViewDidClose:(WKWebView *)webView {
    if (webView != self.web) [webView.window close];
}

- (void)webView:(WKWebView *)webView didFinishNavigation:(WKNavigation *)navigation {
    if (webView != self.web && webView.title.length) webView.window.title = webView.title;
}

- (void)webView:(WKWebView *)webView decidePolicyForNavigationAction:(WKNavigationAction *)action
    decisionHandler:(void (^)(WKNavigationActionPolicy))decide {
    NSURL *url = action.request.URL;
    if (action.shouldPerformDownload) { decide(WKNavigationActionPolicyDownload); return; }
    BOOL local = [url.host isEqualToString:@"127.0.0.1"] || [url.scheme isEqualToString:@"about"] ||
                 [url.scheme isEqualToString:@"blob"] || [url.scheme isEqualToString:@"data"];
    if (!local && action.targetFrame.isMainFrame) {
        [NSWorkspace.sharedWorkspace openURL:url];
        decide(WKNavigationActionPolicyCancel);
        return;
    }
    decide(WKNavigationActionPolicyAllow);
}

- (void)webView:(WKWebView *)webView decidePolicyForNavigationResponse:(WKNavigationResponse *)response
    decisionHandler:(void (^)(WKNavigationResponsePolicy))decide {
    NSHTTPURLResponse *http = (NSHTTPURLResponse *)response.response;
    BOOL attachment = [http isKindOfClass:NSHTTPURLResponse.class] &&
        [[http valueForHTTPHeaderField:@"Content-Disposition"] hasPrefix:@"attachment"];
    decide(attachment || !response.canShowMIMEType ? WKNavigationResponsePolicyDownload
                                                    : WKNavigationResponsePolicyAllow);
}

- (void)webView:(WKWebView *)webView navigationAction:(WKNavigationAction *)a didBecomeDownload:(WKDownload *)d {
    d.delegate = self;
}
- (void)webView:(WKWebView *)webView navigationResponse:(WKNavigationResponse *)r didBecomeDownload:(WKDownload *)d {
    d.delegate = self;
}

- (void)download:(WKDownload *)download decideDestinationUsingResponse:(NSURLResponse *)response
    suggestedFilename:(NSString *)name completionHandler:(void (^)(NSURL *))done {
    NSSavePanel *panel = [NSSavePanel savePanel];
    panel.nameFieldStringValue = name;
    panel.directoryURL = [NSFileManager.defaultManager URLsForDirectory:NSDownloadsDirectory
                                                             inDomains:NSUserDomainMask].firstObject;
    [panel beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse r) {
        if (r != NSModalResponseOK) { done(nil); return; }
        [NSFileManager.defaultManager removeItemAtURL:panel.URL error:nil];
        done(panel.URL);
    }];
}

@end

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        NSApplication *app = NSApplication.sharedApplication;
        app.activationPolicy = NSApplicationActivationPolicyRegular;
        AppDelegate *delegate = [AppDelegate new];
        app.delegate = delegate;
        [app run];
    }
    return 0;
}
