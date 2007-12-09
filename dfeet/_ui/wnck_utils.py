# This module facilitates the optional use of libwnck to get application
# icon information. If the wnck module is not installed we fallback to default
# behvior

import gobject
import gtk

try:
    import wnck
    has_libwnck = True
except:
    has_libwnck = False

class IconTable:
    instance = None

    def __init__(self):
        # {pid: icon} 
        self.app_map = {}

        icon_theme = gtk.icon_theme_get_default()
        self.default_icon = icon_theme.load_icon('icon-service', 16, 0)

        if has_libwnck:
            screen = wnck.screen_get_default()
            screen.connect('application_opened', self.on_app_open)
            screen.connect('application_closed', self.on_app_close)

            for w in screen.get_windows():
                app = w.get_application()
                pid = app.get_pid()
                icon = app.get_mini_icon()

                if not self.app_map.has_key(pid):
                    self.app_map[pid] = icon

    def on_app_open(self, screen, app):
        self.app_map[app.get_pid()] = app.get_mini_icon()

    def on_app_close(self, screen, app):
        pid = app.get_pid()
        if self.app_map.has_key(pid):
            del self.app_map[pid]

    def get_icon(self, pid):
        icon = None
        if self.app_map.has_key(pid):
            icon = self.app_map[pid]

        if not icon:
            icon = self.default_icon

        return icon

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = IconTable()

        return cls.instance

