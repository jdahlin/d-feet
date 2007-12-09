import gobject 
import gtk

from dfeet.dbus_introspector import BusWatch

from busnameview import BusNameView

class BusNameBox(gtk.VBox):
    __gsignals__ = {
        'busname-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,))
                   }

    def __init__(self, watch):
        super(BusNameBox, self).__init__()

        self.tree_view = BusNameView(watch)
        self.tree_view.connect('cursor_changed', self.busname_selected_cb)

        scroll = gtk.ScrolledWindow()
        scroll.add(self.tree_view)
        self.pack_start(scroll, True, True)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.show_all()

    def _completion_match_func(self, completion, key, iter):
        print completion, key, iter 
        return self.tree_view._is_iter_equal(completion.get_model(),
                                            iter, key)

    def busname_selected_cb(self, treeview):
        (model, iter) = treeview.get_selection().get_selected()
        if not iter:
            return

        busname = model.get_value(iter, BusWatch.BUSNAME_OBJ_COL)
        self.emit('busname-selected', busname)

    def set_filter_string(self, value):
        self.tree_view.set_filter_string(value)
        self.tree_view.refilter()

    def set_hide_private(self, hide_private):
        self.tree_view.set_hide_private(hide_private)
        self.tree_view.refilter()

    def set_sort_col(self, value):
        if value == 'Common Name':
            col = BusWatch.COMMON_NAME_COL
        elif value == 'Unique Name':
            col = BusWatch.UNIQUE_NAME_COL
        elif value == 'Process Name':
            col = BusWatch.PROCESS_NAME_COL
        else:
            raise Exception('Value "' + value + '" is not a valid sort value')

        self.tree_view.set_sort_column(col)
        #self.tree_view.sort_column_changed()

