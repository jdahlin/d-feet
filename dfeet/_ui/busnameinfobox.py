import gobject 
import gtk

from dfeet import _util
from dfeet.introspect_data import IntrospectData, Method, Signal

from executemethoddialog import ExecuteMethodDialog
from uiloader import UILoader

class BusNameInfoBox(gtk.VBox):
    def __init__(self):
        super(BusNameInfoBox, self).__init__()

        self.busname = None

        ui = UILoader(UILoader.UI_INTROSPECTVIEW) 
        info_table = ui.get_root_widget()
        self.name_label = ui.get_widget('name_label1')
        self.unique_name_label = ui.get_widget('unique_name_label1')
        self.process_label = ui.get_widget('process_label1')
        self.introspection_box = ui.get_widget('introspect_box1')

        self.introspect_tree_view = gtk.TreeView()
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Introspection Data", 
                                    renderer, markup=1)
        column.set_cell_data_func(renderer, 
                                  self.cell_data_handler, 
                                  self.introspect_tree_view)

        self.introspect_tree_view.connect('row-collapsed', 
                                          self.row_collapsed_handler)
        self.introspect_tree_view.connect('row-expanded', 
                                          self.row_expanded_handler)

        self.introspect_tree_view.append_column(column) 
        
        scroll = gtk.ScrolledWindow()
        scroll.add(self.introspect_tree_view)
        self.introspection_box.pack_start(scroll,
                                          True, True)

        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.introspect_tree_view.show_all()

        self.add(info_table)

        self.introspect_tree_view.connect('row-activated', 
                                          self.row_activated_handler)

    def row_activated_handler(self, treeview, path, view_column):
        model = treeview.get_model() 
        iter = model.get_iter(path)

        node = model.get_value(iter, IntrospectData.SUBTREE_COL)

        # TODO: Figure out what to do with signals
        if isinstance(node, Method):
            dialog = ExecuteMethodDialog(self.busname, node)
            dialog.run()
        else:
            if treeview.row_expanded(path):
                treeview.collapse_row(path)
            else:
                treeview.expand_row(path, False)

    def row_collapsed_handler(self, treeview, iter, path):
        model = treeview.get_model()
        node = model.get(iter, model.SUBTREE_COL)[0]
        node.set_expanded(False)

    def row_expanded_handler(self, treeview, iter, path):
        model = treeview.get_model()
        node = model.get(iter, model.SUBTREE_COL)[0]
        node.set_expanded(True)

    def cell_data_handler(self, column, cell, model, iter, treeview):
        node = model.get(iter, model.SUBTREE_COL)[0]
        if node.is_expanded():
            path = model.get_path(iter)
            treeview.expand_row(path, False)

    def introspect_changed(self, busname):
        #print busname.common_data._introspection_data
        pass

    def set_busname(self, busname):
        if self.busname:
            self.busname.disconnect(self.busname._introspect_changed_signal_id)

        self.busname = busname
        self.introspect_tree_view.set_model(busname.common_data._introspection_data)
        if self.busname:
            self.busname.query_introspect()
            self.busname._introspect_changed_signal_id = self.busname.connect('changed', self.introspect_changed)

        self.refresh()

    def clear(self):
        self.busname = None
        self.refresh()

    def refresh(self):
        name = ''
        unique_name = ''
        process_path_str = ''

        if self.busname:
            name = self.busname.get_display_name()
            unique_name = self.busname.get_unique_name()
            process_path = self.busname.get_process_path()
            process_path_str = ""
            if not process_path:
                process_path_str = 'Unkown or Remote: This process can not be found and may be remote'
            else:
                process_path_str = ' '.join(process_path)

        self.name_label.set_text(name)
        self.unique_name_label.set_text(unique_name)
        self.process_label.set_text(process_path_str)
