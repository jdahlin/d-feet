import os
import sys
import gtk
import gtk.glade
import gobject 
import _ui

import dbus_introspector
from dbus_introspector import BusWatch

glade_dir = os.environ['GLADE_DIR']
glade_file = glade_dir + '/dfeet.glade' 

def main(args):
    global session_bus_watch

    session_bus_watch = BusWatch(dbus_introspector.SESSION_BUS)
    glade_xml = gtk.glade.XML(glade_file)

    main_window = glade_xml.get_widget('window1')
    main_window.connect('destroy',gtk.main_quit)

    # TODO: make a UI class for each tab view
    session_services_view = _ui.ServiceView(session_bus_watch)
    session_services_view.show()
    service_list_scroll = gtk.ScrolledWindow()
    service_list_scroll.add(session_services_view)
    service_list_scroll.show()
    
    details_scroll = gtk.ScrolledWindow()
    details_scroll.show()

    pane = gtk.HPaned()
    pane.pack1(service_list_scroll)
    pane.pack2(details_scroll)
    pane.set_position(300)
    pane.show()
    
    notebook = glade_xml.get_widget('display_notebook')
    notebook.append_page(pane, gtk.Label('Session Bus'))
     
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
