import dbus
import dbus.mainloop.glib
import gobject
import _util
import os

SESSION_BUS = 1
SYSTEM_BUS = 2

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class Error(Exception):
    pass

class BusAddressError(Error):
    def __init__(self, address):
        self.address = address

    def __str__(self):
        return repr('Bus address \'%s\' is not a valid bus address' % self.address)
        
class BusService:
    def __init__(self, unique_name, bus):
        self.unique_name = unique_name
        self.common_names = []
        self.bus = bus
        self.process_id = None
        self.process_path = None

    def add_name(self, name):
        if not (name in self.common_names):
            self.common_names.append(name)

    def remove_name(self, name):
        try:
            self.common_names.remove(name)
        except:
            pass

    def set_process_info(self, id, path):
        self.process_id = id
        self.process_path = path

    def __str__(self):
        result = self.unique_name
        result += '\n    Process ID: '
        if self.process_id:
            result += str(self.process_id)
        else:
            result += 'Unknown'

        result += '\n    Process Name: '
        if self.process_path:
            result += os.path.basename(self.process_path[0])
        else:
            result += 'Unknown'

        result += '\n    Well Known Name'
        count = len(self.common_names)
        if count == 0:
            result += ': None'
        elif count == 1:
            result += ': '
            result += self.common_names[0]
        else:
            result += 's: '
            for name in self.common_names:
                result += "\n        " + name

        return result 

class BusWatch(gobject.GObject):
    __gsignals__ = {
        'service-added' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           (gobject.TYPE_PYOBJECT,)),
        'service-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
        'service-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self, bus, address=None):
        self.bus = None
        self.services = {}

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
        service = self.services[name]
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
            if self.services.has_key(name):
                return

            self.services[name] = BusService(name, self.bus)
            self.get_unix_process_id_async_helper(name)
            self.emit('service-added', self.services[name])

        else:
            if not owner:
                owner = self.bus_interface.GetNameOwner(name)
                if owner == 'org.freedesktop.DBus':
                    return 

            # if owner still does not exist then we move on
            if not owner:
                return

            if self.services.has_key(owner):
                service = self.services[owner]
            else:
                service = BusService(owner, self.bus)
                self.services[owner] = service
                self.get_unix_process_id_async_helper(owner)
                self.emit('service-added', self.services[owner])
                

            service.add_name(name)

    def remove_service(self, name, owner=None):
        if self.services.has_key(name):
            self.services.del_key(name)
            self.emit('service-removed', self.services[name])
            
        else:
            if not owner:
                return

            # service may have been deleted already
            if self.services.has_key(owner):
                service = self.services[owner]
                service.remove_name(name)
                
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

    def get_services(self):
        return self.services
