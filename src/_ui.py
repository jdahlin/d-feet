import gtk
import gobject 
import gtk
import gtk.glade
import os

from dbus_introspector import BusWatch

class ServiceView(gtk.TreeView):
    def __init__(self, watch):
        super(ServiceView, self).__init__()

        self.set_property('enable-tree-lines', True)
        self.set_property('enable-search', True)
        self.watch = watch
        
        self.sort_model = gtk.TreeModelSort(self.watch)
        self.sort_model.set_sort_column_id(self.watch.UNIQUE_NAME_COL, gtk.SORT_ASCENDING)
        self.sort_model.set_sort_func(self.watch.UNIQUE_NAME_COL, self._sort_on_unique_name)

        self.filter_model = None

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Services", 
                                    renderer, 
                                    markup=watch.DISPLAY_COL)
        self.append_column(column)

        self.set_model(self.sort_model)

    def _sort_on_unique_name(self, model, iter1, iter2):
        un1 = model.get_value(iter1, model.UNIQUE_NAME_COL)
        un2 = model.get_value(iter2, model.UNIQUE_NAME_COL)

        print model
        if un1:
            un1 = float(un1[1:])

        if un2:
            un2 = float(un2[1:])

        print un1, un2

        if un1 == un2:
            return 0
        elif un1 > un2:
            return 1
        else:
            return -1
        
