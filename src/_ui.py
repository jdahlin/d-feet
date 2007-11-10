import gtk
import gobject 
import gtk
import gtk.glade
import os
import _util

from dbus_introspector import BusWatch

class BusPaned(gtk.VPaned):
    def __init__(self, watch):
        super(BusPaned, self).__init__()

        self.service_box = ServiceBox(watch)
        self.service_info_box = ServiceInfoBox()
        self.service_box.connect('service-selected', self.service_selected_cb)

        self.pack1(self.service_box)
        self.pack2(self.service_info_box)
        self.set_position(200)

    def service_selected_cb(self, service_box, service):
        self.service_info_box.set_service(service)
    
class ServiceInfoBox(gtk.VBox):
    def __init__(self):
        super(ServiceInfoBox, self).__init__()

        self.service = None

        xml = gtk.glade.XML(_util.get_glade_file(), 'info_table1')
        info_table = xml.get_widget('info_table1')
        self.name_label = xml.get_widget('name_label1')
        self.unique_name_label = xml.get_widget('unique_name_label1')
        self.process_label = xml.get_widget('process_label1')
        self.introspection_box = xml.get_widget('introspect_scrolledwindow1')

        self.introspect_tree_view = gtk.TreeView()
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Introspection Data", 
                                    renderer, text=1)
        column.set_cell_data_func(renderer, 
                                  self.cell_data_handler, 
                                  self.introspect_tree_view)

        self.introspect_tree_view.connect('row-collapsed', 
                                          self.row_collapsed_handler)
        self.introspect_tree_view.connect('row-expanded', 
                                          self.row_expanded_handler)
        
        self.introspect_tree_view.append_column(column)
        self.introspection_box.remove(self.introspection_box.get_child())
        self.introspection_box.add(self.introspect_tree_view)
        self.introspect_tree_view.show_all()

        self.add(info_table)

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

    def introspect_changed(self, service):
        #print service.common_data._introspection_data
        pass

    def set_service(self, service):
        if self.service:
            self.service.disconnect(self.service._introspect_changed_signal_id)

        self.service = service

        self.introspect_tree_view.set_model(service.common_data._introspection_data)
        if self.service:
            self.service.query_introspect()
            self.service._introspect_changed_signal_id = self.service.connect('changed', self.introspect_changed)

        self.refresh()

    def clear(self):
        self.service = None
        self.refresh()

    def refresh(self):
        name = ''
        unique_name = ''
        process_path_str = ''

        if self.service:
            name = self.service.get_display_name()
            unique_name = self.service.get_unique_name()
            process_path = self.service.get_process_path()
            process_path_str = ""
            if not process_path:
                process_path_str = 'Unkown or Remote: This process can not be found and may be remote'
            else:
                process_path_str = ' '.join(process_path)

        self.name_label.set_text(name)
        self.unique_name_label.set_text(unique_name)
        self.process_label.set_text(process_path_str)

class ServiceBox(gtk.VBox):
    __gsignals__ = {
        'service-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,))
                   }

    def __init__(self, watch):
        super(ServiceBox, self).__init__()

        signal_dict = { 
                        'hide_private_toggled' : self.hide_private_toggled_cb,
                        'filter_entry_changed': self.filter_entry_changed_cb
                      } 

        xml = gtk.glade.XML(_util.get_glade_file(), 'sort_and_filter_table1')
        filter_box = xml.get_widget('sort_and_filter_table1')
        self.pack_start(filter_box, False, False)

        self.tree_view = ServiceView(watch)
        self.tree_view.connect('cursor_changed', self.service_selected_cb)

        scroll = gtk.ScrolledWindow()
        scroll.add(self.tree_view)
        self.pack_start(scroll, True, True)

        xml.signal_autoconnect(signal_dict)

        self.show_all()

    def service_selected_cb(self, treeview):
        (model, iter) = treeview.get_selection().get_selected()
        if not iter:
            return

        service = model.get_value(iter, BusWatch.SERVICE_OBJ_COL)
        self.emit('service-selected', service)

    def filter_entry_changed_cb(self, entry, button):
        value = entry.get_text()
        if value == '':
            value = None

        self.tree_view.set_filter_string(value)
        self.tree_view.refilter()

    def hide_private_toggled_cb(self, toggle):
        self.tree_view.set_hide_private(toggle.get_active())
        self.tree_view.refilter()

    def sort_combo_changed_cb(self, combo):
        value = combo.get_active_text()
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

class ServiceView(gtk.TreeView):
    def __init__(self, watch):
        super(ServiceView, self).__init__()

        self.hide_private = False
        self.filter_string = None

        self.set_property('enable-tree-lines', True)
        self.set_property('enable-search', True)
        self.watch = watch
       
        self.filter_model = self.watch.filter_new()
        self.filter_model.set_visible_func(self._filter_cb)
        
        self.sort_model = gtk.TreeModelSort(self.filter_model)
        self.sort_model.set_sort_column_id(self.watch.COMMON_NAME_COL, gtk.SORT_ASCENDING)
        self.sort_model.set_sort_func(self.watch.UNIQUE_NAME_COL, self._sort_on_name, self.watch.UNIQUE_NAME_COL)
        self.sort_model.set_sort_func(self.watch.COMMON_NAME_COL, self._sort_on_name, self.watch.COMMON_NAME_COL)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Service Name", 
                                    renderer, 
                                    markup=watch.DISPLAY_COL
                                    )
        column.set_resizable(True)
        column.set_sort_column_id(watch.COMMON_NAME_COL)
        self.append_column(column)

        column = gtk.TreeViewColumn("Unique Name", 
                                    renderer, 
                                    text=watch.UNIQUE_NAME_COL
                                    )
        column.set_resizable(True)
        column.set_sort_column_id(watch.UNIQUE_NAME_COL)
        self.append_column(column)

        column = gtk.TreeViewColumn("Process Name", 
                                    renderer, 
                                    text=watch.PROCESS_NAME_COL
                                    )
        column.set_resizable(True)
        column.set_sort_column_id(watch.PROCESS_NAME_COL)
        self.append_column(column)

        column = gtk.TreeViewColumn("PID", 
                                    renderer, 
                                    text=watch.PROCESS_ID_COL
                                    )
        column.set_resizable(True)
        column.set_sort_column_id(watch.PROCESS_ID_COL)
        self.append_column(column)


        self.set_headers_clickable(True)
        self.set_reorderable(True)
        self.set_search_equal_func(self._search_cb)
        self.set_model(self.sort_model)

    def set_sort_column(self, col):
        self.sort_model.set_sort_column_id(col, gtk.SORT_ASCENDING)

    def set_hide_private(self, value):
        self.hide_private = value

    def set_filter_string(self, value):
        self.filter_string = value

    def refilter(self):
        self.filter_model.refilter()
        

    def _is_iter_equal(self, model, iter, key):
        (unique_name, 
         common_name, 
         process_id,
         process_path,
         is_public) = model.get(iter,
                                 BusWatch.UNIQUE_NAME_COL,
                                 BusWatch.COMMON_NAME_COL,
                                 BusWatch.PROCESS_ID_COL,
                                 BusWatch.PROCESS_PATH_COL,
                                 BusWatch.IS_PUBLIC_COL)

        if self.hide_private:
            if not is_public:
                return False

        # TODO: support filtering on introspect data
        if key:
            if (unique_name and unique_name.find(key)!=-1) or \
               (common_name and common_name.find(key)!=-1) or \
               str(process_id).startswith(key):
                return True
            
            if process_path:    
                for item in process_path:
                    if (item.find(key)!=-1):
                        return True

            return False

        return True


    def _search_cb(self, model, column, key, iter):
        return not self._is_iter_equal(model, iter, key)

    def _filter_cb(self, model, iter):
        return self._is_iter_equal(model, iter, self.filter_string)

    def _sort_on_name(self, model, iter1, iter2, col):
        un1 = model.get_value(iter1, col)
        un2 = model.get_value(iter2, col)

        # covert to integers if comparing two unique names
        if un1[0] == ':' and un2[0] == ':':
            if un1:
                un1 = un1[1:].split('.')
                un1 = tuple(map(int, un1))

            if un2:
                un2 = un2[1:].split('.')
                un2 = tuple(map(int, un2))

        elif un1[0] == ':' and un2[0] != ':':
            return 1
        elif un1[0] != ':' and un2[0] == ':':
            return -1 
        else:
            un1 = un1.split('.')
            un2 = un2.split('.')

        if un1 == un2:
            return 0
        elif un1 > un2:
            return 1
        else:
            return -1
        
