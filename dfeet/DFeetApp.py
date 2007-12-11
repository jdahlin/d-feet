import os
import sys
import gtk
import gobject 
import _ui
import _util

import dbus_introspector
from dbus_introspector import BusWatch
from settings import Settings
from _ui.uiloader import UILoader

class DFeetApp:
    def __init__(self):
        signal_dict = {'add_session_bus': self.add_session_bus_cb,
                       'add_system_bus': self.add_system_bus_cb,
                       'add_bus_address': self.add_bus_address_cb}

        settings = Settings.get_instance()

        ui = UILoader(UILoader.UI_MAINWINDOW) 

        main_window = ui.get_root_widget()
        main_window.set_icon_name('dfeet-icon')
        main_window.connect('delete-event', self._quit_dfeet)

        self.notebook = ui.get_widget('display_notebook')
        self.notebook.show_all()

        main_window.set_default_size(int(settings.general['windowwidth']), 
                                 int(settings.general['windowheight']))

        self._load_tabs(settings)

        main_window.show()

        ui.connect_signals(signal_dict)

    def _load_tabs(self, settings):
        for bus_name in settings.general['bustabs_list']:
            if bus_name == 'Session Bus':
                self.add_bus(dbus_introspector.SESSION_BUS)
            elif bus_name == 'System Bus':
                self.add_bus(dbus_introspector.SYSTEM_BUS)
            else:
                self.add_bus(address = bus_name)

    def _add_bus_tab(self, bus_watch):
        name = bus_watch.get_bus_name()
        bus_paned = _ui.BusBox(bus_watch)
        bus_paned.show_all()
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(name), True, True)
        close_btn = gtk.Button()
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON)
        img.show()
        close_btn.set_image(img)
        close_btn.set_relief(gtk.RELIEF_NONE)
        close_btn.connect('clicked', self.close_tab_cb, bus_paned)
        hbox.pack_start(close_btn, False, False)
        hbox.show_all()

        p = self.notebook.append_page(bus_paned, hbox)
        self.notebook.set_current_page(p)
        self.notebook.set_tab_reorderable(bus_paned, True)

    def close_tab_cb(self, button, child):
        n = self.notebook.page_num(child)
        self.notebook.remove_page(n)

    def add_bus(self, bus_type=None, address=None):
        if bus_type == dbus_introspector.SESSION_BUS or bus_type == dbus_introspector.SYSTEM_BUS:
            bus_watch = BusWatch(bus_type)
            self._add_bus_tab(bus_watch)

    def add_session_bus_cb(self, action):
        self.add_bus(dbus_introspector.SESSION_BUS)

    def add_system_bus_cb(self, action):
        self.add_bus(dbus_introspector.SYSTEM_BUS)

    def add_bus_address_cb(self, action):
        pass #TODO: pop up a dialog to create arbitrary connections

    def _quit_dfeet(self, main_window, event):
        settings = Settings.get_instance()
        size = main_window.get_size()
        pos = main_window.get_position() 
    
        settings.general['windowwidth'] = size[0]
        settings.general['windowheight'] = size[1]

        n = self.notebook.get_n_pages()
        tab_list = []
        for i in xrange(n):
            child = self.notebook.get_nth_page(i)
            bus_watch = child.get_bus_watch()
            tab_list.append(bus_watch.get_bus_name())
   
        settings.general['bustabs_list'] = tab_list
         
        settings.write()

        gtk.main_quit()

if __name__ == "__main__":
    DFeetApp()
    gtk.main()
