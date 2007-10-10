import dbus
import dbus.mainloop.glib
import gobject

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

    def add_name(self, name):
        if not (name in self.common_names):
            self.common_names.append(name)

    def remove_name(self, name):
        try:
            self.common_names.remove(name)
        except:
            pass

    def __str__(self):
        return '%s %s' % (self.unique_name, str(self.common_names))

class BusWatch(gobject.GObject):
    def __init__(self, bus, address=None):
        self.bus = None
        self.services = {}

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

        self.bus_object = self.bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        self.bus_object.ListNames(dbus_interface='org.freedesktop.DBus',
                                  reply_handler=self.list_names_handler,
                                  error_handler=self.list_names_error_handler)

    # if name is not unique and owner is set add the name to the service
    # else create a new service
    def add_service(self, name, owner=None):

        if name[0] == ':':
            if self.services.has_key(name):
                return

            self.services[name] = BusService(name, self.bus)
        elif name == 'org.freedesktop.DBus':
            # FIXME: this is a courner case which needs to be taken care of in other places too
            if self.services.has_key(name):
                return

            self.services[name] = BusService(name, self.bus)

        else:
            if not owner:
                owner = self.bus_object.GetNameOwner(name)

            # if owner still does not exist then we move on
            if not owner:
                return

            if self.services.has_key(owner):
                service = self.services[owner]
            else:
                service = BusService(owner, self.bus)
                self.services[owner] = service

            service.add_name(name)

    def remove_service(self, name, owner=None):
        if self.services.has_key(name):
            self.services.del_key(name)
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
            print "\n*************** ",name
            for key in self.services.keys():
                print str(key), ' = ', str(self.services[key])


    def list_names_error_handler(self, error):
        print "error getting service names - %s" % str(error)
