import dbus
import dbus.mainloop.glib
import gobject
import gtk
import _util
import os

SESSION_BUS = 1
SYSTEM_BUS = 2

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

def print_method(m):
    def decorator(*args):
        #print "call:", m,args
        r = m(*args)
        #print "return:", r
        return r
    return decorator

class Error(Exception):
    pass

class BusAddressError(Error):
    def __init__(self, address):
        self.address = address

    def __str__(self):
        return repr('Bus address \'%s\' is not a valid bus address' % self.address)

class InvalidColumnError(Error):
    def __init__(self, col):
        self.column = col

    def __str__(self):
        return repr('Column number \'%i\' requested but is not valid' % self.column)

class CommonServiceData:
    def __init__(self):
        self.unique_name = None
        self.bus = None
        self.process_id = None
        self.process_path = None
        self.process_name = None
        
class BusService:
    def __init__(self, unique_name, bus, common_name = None, clone_from_service = None):
        if not clone_from_service:
            self.common_data = CommonServiceData()
        else:
            self.common_data = clone_from_service.common_data

        if common_name:
            self.common_name = str(common_name)
        else:
            self.common_name = None

        self.common_data.bus = bus
        self.common_data.unique_name = str(unique_name)

        self.service_is_public = not (not common_name)

    def set_common_name(self, common_name):
        self.service_is_public = True
        self.common_name = common_name

    def clear_common_name(self):
        self.service_is_public = False
        self.common_name = None

    def is_public(self):
        return self.service_is_public

    def set_process_info(self, id, path):
        self.common_data.process_id = id
        self.common_data.process_path = path
        if path:
            self.common_data.process_name = os.path.basename(path[0])

    def get_unique_name(self):
        return self.common_data.unique_name

    def get_common_name(self):
        return self.common_name
    
    def get_process_id(self):
        return self.common_data.process_id
    
    def get_process_path(self):
        return self.common_data.process_path
    
    def get_process_name(self):
        return self.common_data.process_name

    def __str__(self):
        result = self.common_data.unique_name
        result += '\n    Process ID: '
        if self.common_data.process_id:
            result += str(self.common_data.process_id)
        else:
            result += 'Unknown'

        result += '\n    Process Name: '
        if self.common_data.process_path:
            result += self.common_data.process_name
        else:
            result += 'Unknown'

        result += '\n    Well Known Name'
        if not self.common_name:
            result += ': None'
        else:
            result += ': '
            result += self.common_name

        return result 

class BusWatch(gtk.GenericTreeModel):
    __gsignals__ = {
        'service-added' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           (gobject.TYPE_PYOBJECT,)),
        'service-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
        'service-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_STRING,))
    }

    NUM_COL = 7

    (SERVICE_OBJ_COL, 
     UNIQUE_NAME_COL,
     COMMON_NAME_COL,
     IS_PUBLIC_COL,        # has a common name
     PROCESS_ID_COL,
     PROCESS_PATH_COL,
     PROCESS_NAME_COL) = range(NUM_COL)

    COL_TYPES = (gobject.TYPE_PYOBJECT,
                 gobject.TYPE_STRING,
                 gobject.TYPE_STRING,
                 gobject.TYPE_BOOLEAN,
                 gobject.TYPE_STRING,
                 gobject.TYPE_PYOBJECT,
                 gobject.TYPE_STRING)

    def __init__(self, bus, address=None):
        self.bus = None
        self.unique_services = {}
        self.service_list = []

        super(BusWatch, self).__init__()

        if bus == SESSION_BUS:
            self.bus = dbus.SessionBus()
        elif bus == SYSTEM_BUS:
            self.bus = dbus.SystemBus()
        else:
            if not address:
                raise BusAddressError(address)
            self.bus = dbus.Connection(address)
            if not self.bus:
                raise BusAddressError(address)

        self.bus.add_signal_receiver(self.name_owner_changed_cb,
                                     dbus_interface='org.freedesktop.DBus',
                                     signal_name='NameOwnerChanged')

        bus_object = self.bus.get_object('org.freedesktop.DBus', 
                                         '/org/freedesktop/DBus')
        self.bus_interface = dbus.Interface(bus_object, 
                                            'org.freedesktop.DBus')

        self.bus_interface.ListNames(reply_handler=self.list_names_handler,
                                     error_handler=self.list_names_error_handler)

    def get_unix_process_id_cb(self, name, id):
        services = self.unique_services[name]
        if not services:
            return
        
        service = services[0]
        if not service:
            return

        process_path = _util.get_proc_from_pid(id)
        service.set_process_info(id, process_path)

    def get_unix_process_id_error_cb(self, name, error):
        print error

    # get the Unix process ID so we can associate the name
    # with a process (this will only work under Unix like OS's)
    def get_unix_process_id_async_helper(self, name):
         self.bus_interface.GetConnectionUnixProcessID(name, 
                reply_handler = lambda id: self.get_unix_process_id_cb(name, id),
                error_handler = lambda error: self.get_unix_process_id_error_cb(name, error))

    # if name is not unique and owner is set add the name to the service
    # else create a new service
    def add_service(self, name, owner=None):

        if name[0] == ':':
            if self.unique_services.has_key(name):
                return

            service = BusService(name, self.bus)
            self.unique_services[name] = [service]
            self.get_unix_process_id_async_helper(name)
            self.service_list.append(service)
            path = (self.service_list.index(service),)
            iter = self.get_iter(path)
            self.row_inserted(path, iter) 
            self.row_has_child_toggled(path, iter)

        else:
            if not owner:
                owner = self.bus_interface.GetNameOwner(name)
                if owner == 'org.freedesktop.DBus':
                    return 

            # if owner still does not exist then we move on
            if not owner:
                return

            if self.unique_services.has_key(owner):
                service = self.unique_services[owner][0]
                if service.is_public():
                    service = BusService(owner, self.bus, name, service)
                    self.unique_services[owner].append(service)
                    self.service_list.append(service)
                    path = (self.service_list.index(service),)
                    iter = self.get_iter(path)
                    self.row_inserted(path, iter)
                    self.row_has_child_toggled(path, iter)

                else:
                    service.set_common_name(name)

                
                self.emit('service-added', service)                
            else:
                service = BusService(owner, self.bus, name)
                self.unique_services[owner] = [service]
                self.service_list.append(service)
                self.get_unix_process_id_async_helper(owner)
                path = (self.service_list.index(service),)
                iter = self.get_iter(path)
                self.row_inserted(path, iter)
                self.row_has_child_toggled(path, iter)

                self.emit('service-added', service)
                
    def remove_service(self, name, owner=None):
        if not name:
            return

        if self.unique_services.has_key(name):
            services = self.unique_services[name]
            for s in services:
                self.remove_service(s.common_name, name)

            self.service_list.remove(self.unique_services[name][0])
            self.unique_services.del_key(name)
            self.emit('service-removed', name)
            
        else:
            if not owner:
                return

            # service may have been deleted already
            if self.unique_services.has_key(owner):
                services = self.unique_services[owner]
                if len(services) == 1:
                    if services[0].common_name == name:
                        services[0].clear_common_name()
                else:
                    for s in services:
                        if s.common_name == name:
                            self.unique_services[owner].remove(s)
                            self.service_list.remove(s)
                            break;

                self.emit('service-removed', name)
                
    def name_owner_changed_cb(self, name, old_owner, new_owner):

        if name[0] == ':':
            if not old_owner:
                self.add_service(self, name)
            else:
                self.remove_service(self, name)

        else :
            if old_owner:
                self.add_service(self, name, new_owner)
            
            if new_owner:
                self.remove_service(self, name, old_owner)

    def list_names_handler(self, names):
        for name in names:
            self.add_service(name)

    def list_names_error_handler(self, error):
        print "error getting service names - %s" % str(error)

    def get_service_list(self):
        return self.service_list

    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return self.NUM_COL

    def on_get_column_type(self, n):
        return self.COL_TYPES[n]

    @print_method
    def on_get_iter(self, path):
        try:
            if len(path) == 1:
                return (self.service_list[path[0]],)
            else:
                return (self.service_list[path[0]],path[1])
        except IndexError:
            return None

    @print_method
    def on_get_path(self, rowref):
        index = self.files.index(rowref[0])
        if len(rowref) == 1:
            return (index,)
        else:
            return (index, rowref[1])

    def on_get_value(self, rowref, column):
        service = rowref[0]
        child = -1
        if len(rowref) == 2:
            child = rowref[1]

        if column == self.SERVICE_OBJ_COL:
            return service
        elif column == self.UNIQUE_NAME_COL:
            if (child == 0):
                return service.get_unique_name()
        elif column == self.COMMON_NAME_COL:
            if child == -1:
                if service.is_public():
                    return service.get_common_name()
                else:
                    return service.get_unique_name()
        elif column == self.IS_PUBLIC_COL:
            return service.is_public()
        elif column == self.PROCESS_ID_COL:
            if child == 1:
                return service.get_process_id()
        elif column == self.PROCESS_PATH_COL:
            return service.get_process_path()
        elif column == self.PROCESS_NAME_COL:
            if child == 1:
                return service.get_process_name()
        else:
            raise InvalidColumnError(column) 

        return None

    @print_method
    def on_iter_next(self, rowref):
        try:
            service = rowref[0]
            child = -1
            if len(rowref) == 2:
                child = rowref[1]

            if child == 0:
                return (service, child +1)
            elif child == 1:
                return None
            else:
                i = self.service_list.index(rowref[0]) + 1
                return (self.service_list[i],)
        except IndexError:
            return None

    @print_method
    def on_iter_children(self, parent):
        if parent:
            if len(parent) == 1:
                return (parent[0], 0) 
            else:
                return None

        return (self.service_list[0],)

    @print_method
    def on_iter_has_child(self, rowref):
        if len(rowref) == 1:
            return True
        else:
            return False

    @print_method
    def on_iter_n_children(self, rowref):
        if rowref:
            if len(rowref) == 1:
                return 2
            else:
                return None

        return len(self.service_list)

    @print_method
    def on_iter_nth_child(self, parent, n):
        if parent:
            if n < 2:
                return (parent, n)
            else:
                return None
        try:
            return (self.service_list[n],)
        except IndexError:
            return None

    @print_method
    def on_iter_parent(self, child):
        return (child[0],) 

