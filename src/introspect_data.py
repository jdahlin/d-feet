import gtk
import gobject
import dbus_utils
import _util

# Big TODO: these are a bunch of similar objects that could 
#           be better represented through inheritance though
#           it was easier to conceptualize as seperate data
#           structures for now

class Method:
    # tree path = (0,x,0,y,0,z)
    def __init__(self, parent, method, insig, outsig):
        self.method = method
        self.parent = parent
        self.insig = insig
        self.outsig = outsig

    def is_open(self):
        return False

    def get_path_pos(self):
        return self.parent.index(self)

    def get_next(self):
        self.parent.get_next_child(self)

    def get_first_child(self):
        return None

    def get_nth_child(self, n):
        return None 

    def count_children(self):
        return 0

    def __str__(self):
        result = self.method + '('
        result += dbus_utils.sig_to_string(self.insig) + ')' 
            
        return result

class Signal:
    # tree path = (0,x,0,y,1,z)
    def __init__(self, parent, signal, insig):
        self.signal = signal
        self.parent = parent
        self.insig = insig

    def is_open(self):
        return False

    def get_path_pos(self):
        return self.parent.index(self)

    def get_next(self):
        self.parent.get_next_child(self)

    def get_first_child(self):
        return None

    def get_nth_child(self, n):
        return None 

    def count_children(self):
        return 0

    def __str__(self):
        result = self.signal + '('
        result += dbus_utils.sig_to_string(self.insig) + ')'

        return result

class MethodLabel:
    # tree path = (0,x,0,y,0)
    def __init__(self,parent):
        self.parent = parent
        self.method_list = []
        self.tree_open = False

    def set_is_open(self, is_open):
        self.tree_open = is_open

    def is_open(self):
        return self.tree_open

    def index(self, obj):
        return self.method_list.index(obj)

    def on_get_iter(self, path):
        method = self.method_list[path[0]]
        if len(path) == 1:
            return method
        else:
            return method.on_get_iter(path[1:])

    def get_path_pos(self):
        return 0

    def get_next(self):
        return self.parent.get_next_child(self) 

    def get_first_child(self):
        if self.method_list:
            return self.method_list[0]
        else:
            return None

    def get_next_child(self, child):
        i = self.index(child)
        try:
            return self.method_list[i+1]
        except IndexError:
            return None

    def get_nth_child(self, n):
        try:
            return self.method_list[n]
        except IndexError:
            return None

    def count_children(self):
        return len(self.method_list)

    def add(self, data):
        method_list = data.keys()
        method_list.sort()
        for method_name in method_list:
            method = Method(self, method_name, data[method_name][0], data[method_name][1])
            self.method_list.append(method)

    def __str__(self):
        return "Methods"

class SignalLabel:
    # tree path = (0,x,0,y,1)
    def __init__(self,parent):
        self.parent = parent
        self.signal_list = []
        self.tree_open = False

    def set_is_open(self, is_open):
        self.tree_open = is_open

    def is_open(self):
        return self.tree_open

    def index(self, obj):
        return self.signal_list.index(obj)

    def on_get_iter(self, path):
        signal = self.signal_list[path[0]]
        if len(path) == 1:
            return signal
        else:
            return signal.on_get_iter(path[1:])

    def get_path_pos(self):
        return 1

    def get_next(self):
        return self.parent.get_next_child(self) 

    def get_first_child(self):
        if self.signal_list:
            return self.signal_list[0]
        else:
            return None

    def get_next_child(self, child):
        i = self.index(child)
        try:
            return self.signal_list[i+1]
        except IndexError:
            return None

    def get_nth_child(self, n):
        try:
            return self.signal_list[n]
        except IndexError:
            return None

    def count_children(self):
        return len(self.signal_list)

    def add(self, data):
        signal_list = data.keys()
        signal_list.sort()
        for signal_name in signal_list:
            signal = Signal(self, signal_name, data[signal_name])
            self.signal_list.append(signal)

    def __str__(self):
        return 'Signals'

class Interface:
    # tree path = (0,x,0,y)
    def __init__(self, parent, interface):
        self.iface = interface
        self.parent = parent
        self.methods = MethodLabel(self)
        self.signals = SignalLabel(self)
        self.tree_open = False

    def set_is_open(self, is_open):
        self.tree_open = is_open

    def is_open(self):
        return self.tree_open

    def on_get_iter(self, path):
        child = None
        if path[0] == 0:
            child = self.methods
        else:
            child = self.signals

        if not child:
            return None

        if len(path) == 1:
            return child
        else:
            return child.on_get_iter(path[1:])

    def get_path_pos(self):
        return self.parent.index(self)

    def get_next(self):
        return self.parent.get_next_child(self) 

    def get_next_child(self, child):
        if child == self.methods:
            return self.signals
        else:
            return None

    def get_first_child(self):
        return self.methods

    def get_nth_child(self, n):
        if n == 0:
            return self.methods
        elif n == 1:
            return self.signals
        else:
            return None

    def count_children(self):
        return 2

    def add(self, data):
        method_data = data['methods']
        signal_data = data['signals']

        self.methods.add(method_data)
        self.signals.add(signal_data)

    def __str__(self):
        return self.iface

class InterfaceLabel:
    # tree path = (0,x,0)
    def __init__(self,parent):
        self.parent = parent
        self.interface_list = []
        self.tree_open = False

    def set_is_open(self, is_open):
        self.tree_open = is_open

    def is_open(self):
        return self.tree_open

    def index(self, obj):
        return self.interface_list.index(obj)

    def on_get_iter(self, path):
        iface = self.interface_list[path[0]]
        if len(path) == 1:
            return iface
        else:
            return iface.on_get_iter(path[1:])

    def get_path_pos(self):
        return 0

    def get_next(self):
        return None 

    def get_next_child(self, child):
        i = self.index(child)
        try:
            return self.interface_list[i+1]
        except IndexError:
            return None

    def get_first_child(self):
        if self.interface_list:
            return self.interface_list[0]
        else:
            return None

    def get_nth_child(self, n):
        try:
            return self.interface_list[n]
        except IndexError:
            return None

    def count_children(self):
        return len(self.interface_list)

    def add(self, data):
        iface_list = data.keys()
        iface_list.sort()
        for iface in iface_list:
            interface = Interface(self, iface)
            interface.add(data[iface])
            self.interface_list.append(interface)

    def __str__(self):
        return "Interfaces"

class ObjectPath:
    # tree path = (0,x)
    def __init__(self, parent, path):
        self.path = path
        self.parent = parent
        self.interfaces = InterfaceLabel(self)
        self.tree_open = False

    def set_is_open(self, is_open):
        self.tree_open = is_open

    def is_open(self):
        return self.tree_open


    def on_get_iter(self, path):
        if len(path) == 1:
            return self.interfaces
        else:
            return self.interfaces.on_get_iter(path[1:])

    def get_path_pos(self):
        return self.parent.index(self)

    def get_next(self):
        next = self.parent.get_next_child(self)
        return next 

    def get_first_child(self):
        return self.interfaces

    def get_nth_child(self, n):
        if n == 0:
            return self.interfaces
        else:
            return None

    def count_children(self):
        return 1

    def add(self, data):
        iface_data = data['interfaces']
        self.interfaces.add(iface_data) 

    def __str__(self):
        return self.path

class ObjectPathLabel:
    # tree path = (0,)
    def __init__(self, model):
        self.object_path_list = []
        self.parent = None
        self.model = model
        self.tree_open = True

    def set_is_open(self, is_open):
        self.tree_open = is_open

    def is_open(self):
        return self.tree_open

    def index(self, obj):
        return self.object_path_list.index(obj)

    def find(self, node):
        i = 0
        for path in self.object_path_list:
            spath = str(path)
            if spath >= node:
                return i 

            i+=1

        return -1

    def on_get_iter(self, path):
        op = self.object_path_list[path[0]]
        if len(path) == 1:
            return op
        else:
            return op.on_get_iter(path[1:])

    def get_path_pos(self):
        return 0

    def get_next(self):
        return None 

    def get_next_child(self, child):
        i = self.index(child)
        try:
            return self.object_path_list[i+1]
        except IndexError:
            return None

    def get_first_child(self):
        if self.object_path_list:
            return self.object_path_list[0]
        else:
            return None

    def get_nth_child(self, n):
        try:
            return self.object_path_list[n]
        except IndexError:
            return None

    def count_children(self):
        c = len(self.object_path_list)
        return c 

    def _row_changed(self):
        tree_path = (0,)
        iter = self.model.get_iter(tree_path)
        self.model.row_changed(tree_path, iter)

    def add(self, node, data):
        obj_path = ObjectPath(self, node)
        obj_path.add(data)

        if self.object_path_list:
            i = self.find(node)
            if i == -1:
                self.object_path_list.append(obj_path)
                tree_path = (0, len(self.object_path_list)-1)
                iter = self.model.get_iter(tree_path)
                self.model.row_inserted(tree_path, iter)
                return

            path = self.object_path_list[i]
            if str(path) == node:
                o = self.object_path_list.pop(i)
                tree_path = (0, i)
                self.model.row_deleted(tree_path)

            self.object_path_list.insert(i, obj_path)
            tree_path = (0, i)
            iter = self.model.get_iter(tree_path)
            self.model.row_inserted(tree_path, iter)
        else:
            self.object_path_list.append(obj_path)
            tree_path = (0, len(self.object_path_list)-1)
            iter = self.model.get_iter(tree_path)
            self.model.row_inserted(tree_path, iter)

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
        self.object_paths.add(parent_node, data)
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
        while(parent):
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


