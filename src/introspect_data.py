import gtk
import gobject
import dbus_utils
import _util

class Node:
    def __init__(self, model, parent = None):
        self.child_list = []
        self.parent = parent
        self.model = model
        self.expanded = False

    def set_expanded(self, expanded):
        self.expanded = expanded

    def is_expanded(self):
        expanded = False
        if self.child_list:
            expanded = self.expanded

        return expanded

    def index(self, child):
        return self.child_list.index(child)

    def on_get_iter(self, path):
        try:
            op = self.child_list[path[0]]
            if len(path) == 1:
                return op
            else:
                return op.on_get_iter(path[1:])
        except IndexError:
            return None

    def get_path_pos(self):
        pos = 0
        if self.parent:
            pos = self.parent.index(self)

        return pos

    def get_next(self):
        next = None
        if self.parent:
            next = self.parent.get_next_child(self)

        return next

    def get_next_child(self, child):
        i = self.index(child)
        try:
            return self.child_list[i+1]
        except IndexError:
            return None

    def get_first_child(self):
        if self.child_list:
            return self.child_list[0]
        else:
            return None

    def get_nth_child(self, n):
        try:
            return self.child_list[n]
        except IndexError:
            return None

    def count_children(self):
        c = len(self.child_list)
        return c

    def _row_changed(self, path):
        iter = self.model.get_iter(path)
        self.model.row_changed(path, iter)

    def _row_inserted(self, path):
        iter = self.model.get_iter(path)
        self.model.row_inserted(path, iter)

    def _calculate_path(self, last_path_pos):
        p = [self.get_path_pos()]
        parent = self.parent
        while parent:
            p.insert(0, parent.get_path_pos())
            parent = parent.parent

        p.append(last_path_pos)

        return tuple(p)

    def append(self, child):
        self.child_list.append(child)
        path = self._calculate_path(self.count_children()-1)
        self._row_inserted(path)

    def insert(self, i, child):
        self.child_list.insert(i, child)
        path = (0, i)
        self._row_inserted(path)

    def add(self, data):
        # every node needs to figure this out for themselves 
        pass

class Method(Node):
    # tree path = (0,x,0,y,0,z)
    def __init__(self, model, parent, method, insig, outsig):
        self.method = method
        self.insig = insig
        self.outsig = outsig
        
        Node.__init__(self, model, parent)

    def __str__(self):
        result = self.method + '('
        result += dbus_utils.sig_to_string(self.insig) + ')' 
            
        return result

class Signal(Node):
    # tree path = (0,x,0,y,1,z)
    def __init__(self, model, parent, signal, insig):
        self.signal = signal
        self.insig = insig

        Node.__init__(self, model, parent)

    def __str__(self):
        result = self.signal + '('
        result += dbus_utils.sig_to_string(self.insig) + ')'

        return result

class MethodLabel(Node):
    # tree path = (0,x,0,y,0)
    def __init__(self, model, parent):
        Node.__init__(self, model, parent)

    def add(self, data):
        method_list = data.keys()
        method_list.sort()
        for method_name in method_list:
            method = Method(self, self.model, method_name, data[method_name][0], data[method_name][1])
            self.append(method)

    def __str__(self):
        return "Methods"

class SignalLabel(Node):
    # tree path = (0,x,0,y,1)
    def __init__(self, model, parent):
        Node.__init__(self, model, parent)

    def add(self, data):
        signal_list = data.keys()
        signal_list.sort()
        for signal_name in signal_list:
            signal = Signal(self, self.model, signal_name, data[signal_name])
            self.append(signal)

    def __str__(self):
        return 'Signals'

class Interface(Node):
    # tree path = (0,x,0,y)
    def __init__(self, model, parent, interface):
        self.iface = interface
        Node.__init__(self, model, parent)

    def add(self, data):
        method_data = data['methods']
        signal_data = data['signals']

        methods = MethodLabel(self.model, self)
        self.append(methods)
        methods.add(method_data)

        signals = SignalLabel(self.model, self)
        self.append(signals)
        signals.add(signal_data)

    def __str__(self):
        return self.iface

class InterfaceLabel(Node):
    # tree path = (0,x,0)
    def __init__(self, model, parent):
        Node.__init__(self, model, parent)

    def add(self, data):
        iface_list = data.keys()
        iface_list.sort()
        for iface in iface_list:
            interface = Interface(self.model, self, iface)
            self.append(interface)
            interface.add(data[iface])            

    def __str__(self):
        return "Interfaces"

class ObjectPath(Node):
    # tree path = (0,x)
    def __init__(self, model, parent, path):
        self.path = path

        Node.__init__(self, model, parent)

    def add(self, data):
        iface_data = data['interfaces']

        interfaces = InterfaceLabel(self.model, self)
        self.append(interfaces)
        interfaces.add(iface_data)

    def __str__(self):
        return self.path

class ObjectPathLabel(Node):
    # tree path = (0,)
    def __init__(self, model):
        #super(Node, self).__init__(model)
        Node.__init__(self, model)
        self.set_expanded(True)

    def find(self, node):
        i = 0
        for path in self.child_list:
            spath = str(path)
            if spath >= node:
                return i 

            i+=1

        return -1

    def get_path_pos(self):
        return 0

    def _row_changed(self):
        tree_path = (0,)
        iter = self.model.get_iter(tree_path)
        self.model.row_changed(tree_path, iter)

    def add(self, data, node):
        obj_path = ObjectPath(self.model, self, node)

        if self.child_list:
            i = self.find(node)
            if i == -1:
                self.append(obj_path)
                obj_path.add(data)
                return

            # TODO: figure out a more generic way to handle
            #       similar data.  BTW we are going to 
            #       emit changed signals instead of a delete
            #       and add
            path = self.child_list[i]
            if str(path) == node:
                o = self.child_list.pop(i)
                tree_path = (0, i)
                self.model.row_deleted(tree_path)

            self.insert(i, obj_path)
        else:
            self.append(obj_path)

        obj_path.add(data)        

    def __str__(self):
        return "Object Paths"

class IntrospectData(gtk.GenericTreeModel):
    NUM_COL = 2 

    (SUBTREE_COL, 
     DISPLAY_COL) = range(NUM_COL)

    COL_TYPES = (gobject.TYPE_PYOBJECT,
                 gobject.TYPE_STRING)

    """
    Path Values:
        (0,)          - "Object Paths"
        (0,x)         - object path
        (0,x,0)       - "Interfaces"
        (0,x,0,y)     - interface
        (0,x,0,y,0)   - "Methods"
        (0,x,0,y,1)   - "Signals"
        (0,x,0,y,0,z) - method signature
        (0,x,0,y,1,z) - signal signature
    
    """ 
    
    def __init__(self):
        super(IntrospectData, self).__init__()

        self.object_paths = ObjectPathLabel(self)

    def append(self, parent_node, data):
        self.object_paths.add(data, parent_node)
        del(data)

    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return self.NUM_COL

    def on_get_column_type(self, n):
        return self.COL_TYPES[n]

    def on_get_iter(self, path):
        if len(path) == 1:
            if path[0] > 0:
                return None
            return self.object_paths
        else:
            return self.object_paths.on_get_iter(path[1:])

    def on_get_path(self, rowref):
        pl = [rowref.get_path_pos()]
        parent = rowref.parent
        while parent:
            pl.insert(0, parent.get_path_pos())
            parent = parent.parent

        return tuple(pl)

    def on_get_value(self, rowref, column):
        if column == self.SUBTREE_COL:
            return rowref
        elif column == self.DISPLAY_COL:
            return str(rowref)
        else:
            raise InvalidColumnError(column) 

        return None

    def on_iter_next(self, rowref):
        try:
            return rowref.get_next()
        except:
            return None

    def on_iter_children(self, parent):
        if parent:
            return parent.get_first_child()

        return self.object_paths

    def on_iter_has_child(self, rowref):
        if rowref.get_first_child():
            return True
        else:
            return False

    def on_iter_n_children(self, rowref):
        if rowref:
            rowref.count_children()

        return 1 

    def on_iter_nth_child(self, parent, n):
        if parent:
            parent.get_nth_child(n)
        
        if n == 0:
            return self.object_paths
        else:
            return None
    
    def on_iter_parent(self, child):
        return child.parent

    def __str__(self):
        result = str(self.object_paths) + '\n'
        for op in self.object_paths.object_path_list:
            result += '\t' + str(op) + '\n'
            result += '\t\t' + str(op.interfaces) + '\n'
            for iface in op.interfaces.interface_list:
                result += '\t\t\t' + str(iface) + '\n'
                result += '\t\t\t\t' + str(iface.methods) + '\n'
                for method in iface.methods.method_list:
                    result += '\t\t\t\t\t' + str(method) + '\n'
                result += '\t\t\t\t' + str(iface.signals) + '\n'
                for signal in iface.signals.signal_list:
                    result += '\t\t\t\t\t' + str(signal) + '\n'

        return result


