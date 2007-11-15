import os
import sys
import gtk
import gtk.glade
import gobject 
import _ui
import _util

import dbus_introspector
from dbus_introspector import BusWatch

def main(args):
    global session_bus_watch

    session_bus_watch = BusWatch(dbus_introspector.SESSION_BUS)    
    system_bus_watch = BusWatch(dbus_introspector.SYSTEM_BUS)

    glade_xml = gtk.glade.XML(_util.get_glade_file(), 'appwindow1')

    main_window = glade_xml.get_widget('appwindow1')
    main_window.connect('destroy',gtk.main_quit)

    session_bus_paned = _ui.BusPaned(session_bus_watch)
    system_bus_paned = _ui.BusPaned(system_bus_watch)    

    notebook = glade_xml.get_widget('display_notebook')
    notebook.append_page(session_bus_paned, gtk.Label('Session Bus'))
    notebook.append_page(system_bus_paned, gtk.Label('System Bus'))
    notebook.show_all()

    main_window.show()

def print_services():
    global session_bus_watch
    print '\n*************** '
    for s in session_bus_watch.service_list:
        print str(s)
    print '\n'

    return True

if __name__ == "__main__":
    main(sys.argv)
    #gobject.timeout_add(2000, print_services)
    gtk.main()
