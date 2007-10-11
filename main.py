import sys
import gtk
import gobject 

import dbus_introspector
from dbus_introspector import BusWatch

def main(args):
    global session_bus_watch
    session_bus_watch = BusWatch(dbus_introspector.SESSION_BUS)

def print_services():
    global session_bus_watch
    print '\n*************** '
    for key in session_bus_watch.services.keys():
        print str(session_bus_watch.services[key])
    print '\n'

    return True

if __name__ == "__main__":
    main(sys.argv)

    gobject.timeout_add(5000, print_services)
    gtk.main()
