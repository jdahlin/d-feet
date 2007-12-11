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
    global session_bus_watch

    def __init__(self):
        settings = Settings.get_instance()

        session_bus_watch = BusWatch(dbus_introspector.SESSION_BUS)    
        system_bus_watch = BusWatch(dbus_introspector.SYSTEM_BUS)

        ui = UILoader(UILoader.UI_MAINWINDOW) 

        main_window = ui.get_root_widget()
        main_window.set_icon_name('dfeet-icon')
        main_window.connect('delete-event', self._quit_dfeet)

        session_bus_paned = _ui.BusBox(session_bus_watch)
        system_bus_paned = _ui.BusBox(system_bus_watch)    

        notebook = ui.get_widget('display_notebook')
        notebook.append_page(session_bus_paned, gtk.Label('Session Bus'))
        notebook.append_page(system_bus_paned, gtk.Label('System Bus'))
        notebook.show_all()

        main_window.set_default_size(int(settings.general['windowwidth']), 
                                 int(settings.general['windowheight']))

        main_window.show()

    def _quit_dfeet(self, main_window, event):
        settings = Settings.get_instance()
        size = main_window.get_size()
        pos = main_window.get_position() 
    
        settings.general['windowwidth'] = size[0]
        settings.general['windowheight'] = size[1]
    
        settings.write()

        gtk.main_quit()

def print_names():
    global session_bus_watch
    print '\n*************** '
    for s in session_bus_watch.name_list:
        print str(s)
    print '\n'

    return True

if __name__ == "__main__":
    DFeetApp()
    #gobject.timeout_add(2000, print_names)
    gtk.main()
