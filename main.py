import sys
import gtk
import gobject 
import _ui

import dbus_introspector
from dbus_introspector import BusWatch

def main(args):
    global session_bus_watch
    session_bus_watch = BusWatch(dbus_introspector.SESSION_BUS)
    main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    main_window.set_size_request(300, 200)
    main_window.connect('destroy',gtk.main_quit)
    session_services_view = _ui.ServiceView(session_bus_watch)
    session_services_view.show()
    scroll = gtk.ScrolledWindow()
    scroll.add(session_services_view)
    scroll.show()
    main_window.add(scroll)
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
