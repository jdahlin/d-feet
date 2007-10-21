import gtk
import gobject 
import gtk
import os

from dbus_introspector import BusWatch

# lets put it all in one treeview for now
# but there are better ways to display the data
class ServiceView(gtk.TreeView):
    def __init__(self, watch):
        super(ServiceView, self).__init__()

        self.watch = watch
        self.sort_view = None
        self.filter_view = None

        renderer = gtk.CellRendererText()

        column = gtk.TreeViewColumn("Service", renderer, text=BusWatch.COMMON_NAME_COL)
        self.append_column(column)

        self.set_expander_column(column)
        
        column = gtk.TreeViewColumn("Unique Name", renderer, text=BusWatch.UNIQUE_NAME_COL)
        self.append_column(column)

        column = gtk.TreeViewColumn("Process", renderer, text=BusWatch.PROCESS_NAME_COL)
        self.append_column(column)

        column = gtk.TreeViewColumn("PID", renderer, text=BusWatch.PROCESS_ID_COL)
        self.append_column(column)


        self.set_model(self.watch)
        self.expand_all()
