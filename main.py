import sys
import gtk

import dbus_introspector
from dbus_introspector import BusWatch

def main(args):
    session_bus_watch = BusWatch(dbus_introspector.SESSION_BUS)

if __name__ == "__main__":
    main(sys.argv)

    gtk.main()
