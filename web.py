#!/usr/bin/env python3

import os
import sys
import webbrowser

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.0")

from gi.repository import Gtk, GLib, Gdk, WebKit2


class WebWindow(Gtk.Window):
    """Login form for external services"""

    def __init__(self, uri, icon=None, window_size='800x600', resizable=True, fullscreen=False, frameless=False, maximized=False, stylesheet_content="", script_content="", debug=False, external_links=False, parent=None):
        super(WebWindow, self).__init__(parent=parent)
        self.is_fullscreen = False
        self.initial_uri = uri
        self.script_content = script_content
        self.external_links = external_links

        self.set_border_width(0)
        width, height = list(map(int, window_size.split('x')))
        self.set_default_size(width, height)
        self.set_resizable(resizable)
        if not resizable:
            self.set_size_request(width, height)

        if maximized:
            self.maximize()

        self.set_position(Gtk.WindowPosition.CENTER)
        if frameless:
            self.set_decorated(False)
        if icon:
            self.set_icon_from_file(icon)

        self.connect('delete-event', Gtk.main_quit)
        self.connect('key-press-event', self.on_key_press)
        self.connect('window-state-event', self.on_window_state_change)

        scrolled_window = Gtk.ScrolledWindow()
        self.add(scrolled_window)

        wdm = WebKit2.WebsiteDataManager(
            # local_storage_directory="ls"
        )
        self.context = WebKit2.WebContext.new_with_website_data_manager(wdm)
        # self.context.set_additional_plugins_directory('plugins')

        if "http_proxy" in os.environ:
            proxy = WebKit2.NetworkProxySettings.new(os.environ["http_proxy"])
            self.context.set_network_proxy_settings(
                WebKit2.NetworkProxyMode.CUSTOM, proxy
            )
        # WebKit2.CookieManager.set_persistent_storage(
        #     self.context.get_cookie_manager(),
        #     'cookies',
        #     WebKit2.CookiePersistentStorage(0),
        # )

        self.webview = WebKit2.WebView.new_with_context(self.context)
        settings = self.webview.get_settings()
        settings.set_enable_plugins(False)
        settings.set_enable_webaudio(True)
        settings.set_enable_webgl(True)
        settings.set_enable_media_capabilities(True)
        settings.set_enable_media_stream(True)
        settings.set_enable_mediasource(True)
        settings.set_enable_accelerated_2d_canvas(True)
        settings.set_allow_file_access_from_file_urls(True)
        settings.set_enable_write_console_messages_to_stdout(True)
        settings.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.ALWAYS)

        if stylesheet_content:
            stylesheet = WebKit2.UserStyleSheet.new(
                stylesheet_content,
                WebKit2.UserContentInjectedFrames.TOP_FRAME,
                WebKit2.UserStyleLevel.USER,
                None,
                None
            )
            self.webview.get_user_content_manager().add_style_sheet(stylesheet)

        self.webview.connect("load-changed", self.on_navigation)
        self.webview.connect("notify::title", self.on_title_change)
        self.webview.connect("close", lambda ev: self.close())
        self.webview.connect("decide-policy", self.on_decide_policy)

        scrolled_window.add(self.webview)

        # self.context.get_plugins(None, self.on_get_plugins)

        if debug:
            self.webview.get_settings().props.enable_developer_extras = True
        else:
            # self.webview.connect('context-menu', lambda a, b, c, d: True)  # Disable context menu
            pass

        self.webview.load_uri(self.initial_uri)

        self.show_all()

        if fullscreen:
            self.fullscreen()

    def on_window_state_change(self, target, event):
        self.is_fullscreen = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_F11 or (bool(event.state & Gdk.ModifierType.MOD1_MASK) and event.keyval == Gdk.KEY_Return):
            if self.is_fullscreen:
                self.unfullscreen()
            else:
                self.fullscreen()
            return True

    def on_get_plugins(self, ctx, result):
        print('Plugins:')
        plugins = self.context.get_plugins_finish(result)
        for plugin in plugins:
            print(plugin.get_name(), plugin.get_path(), plugin.get_description())

    def on_navigation(self, widget, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = widget.get_uri()
            if uri == self.initial_uri and self.script_content:
                GLib.idle_add(lambda: self.webview.run_javascript(self.script_content, None, None))
            # print('uri update:', uri)

    def on_decide_policy(self, webview, decision, decision_type):
        if type(decision) == WebKit2.NavigationPolicyDecision:
            action = decision.get_navigation_action()
            if action.get_navigation_type() == WebKit2.NavigationType.LINK_CLICKED:
                uri = action.get_request().get_uri()
                if self.external_links or decision.get_frame_name() == "_blank" or uri.lower().startswith('mailto:'):
                    decision.ignore()
                    webbrowser.open(uri, 2, True)

    def on_title_change(self, webview, title):
        title = webview.get_title()
        # print('title update:', title)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--name')
    parser.add_argument('--icon')
    parser.add_argument('--window-size', default='800x600')
    parser.add_argument('--disable-resizing', action='store_true')
    parser.add_argument('--fullscreen', action='store_true')
    parser.add_argument('--frameless', action='store_true')
    parser.add_argument('--maximize-window', action='store_true')
    parser.add_argument('--devtools', action='store_true')
    parser.add_argument('--execjs', default="")
    parser.add_argument('--disable-scrolling', action='store_true')
    parser.add_argument('--hide-cursor', action='store_true')
    parser.add_argument('--remove-margin', action='store_true')
    parser.add_argument('--injectcss')
    parser.add_argument('--open-links', action='store_true')
    parser.add_argument('uri')

    args = parser.parse_args()

    execjs = []

    execjs.append('document.body.style.userSelect = "none"')
    execjs.append('document.body.style.webkitUserSelect = "none"')
    if args.disable_scrolling:
        execjs.append('document.documentElement.style.overflow = "hidden"')
        execjs.append('document.body.style.overflow = "hidden"')
    if args.hide_cursor:
        execjs.append('document.body.style.cursor = "none"')
    if args.remove_margin:
        execjs.append('document.documentElement.style.margin = "0"')
        execjs.append('document.body.style.margin = "0"')
        execjs.append('document.documentElement.style.padding = "0"')
        execjs.append('document.body.style.padding = "0"')

    execjs = ';\n'.join(execjs) + ';\n' + args.execjs

    print(args)
    sys.stdout.flush()

    uri = args.uri

    if os.path.isfile(uri):
        uri = 'file://' + uri

    # name is given by Gtk it seems like

    web = WebWindow(
        uri=uri, icon=args.icon, window_size=args.window_size,
        resizable=not args.disable_resizing, fullscreen=args.fullscreen,
        frameless=args.frameless, maximized=args.maximize_window, debug=args.devtools,
        script_content=execjs, stylesheet_content=args.injectcss, external_links=args.open_links
    )

    Gtk.main()
