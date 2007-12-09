import gobject 
import gtk
import gtk.glade

from dfeet import _util

from busnamebox import BusNameBox
from busnameinfobox import BusNameInfoBox

class BusBox(gtk.VBox):
    def __init__(self, watch):
        super(BusBox, self).__init__()

        # FilterBox
        signal_dict = { 
                        'hide_private_toggled' : self.hide_private_toggled_cb,
                        'filter_entry_changed': self.filter_entry_changed_cb
                      } 

        xml = gtk.glade.XML(_util.get_glade_file(), 'sort_and_filter_table1')
        filter_box = xml.get_widget('sort_and_filter_table1')
        filter_entry = xml.get_widget('filter_entry1')
        self.pack_start(filter_box, False, False)

        self.completion = gtk.EntryCompletion()
        self.completion.set_model(watch)
        self.completion.set_inline_completion(True)

        # older gtk+ does not support this method call
        # but it is not fatal
        try:
            self.completion.set_inline_selection(True)
        except:
            pass

        filter_entry.set_completion(self.completion)

        # Content
        self.paned = gtk.HPaned()
        self.busname_box = BusNameBox(watch)
        self.busname_info_box = BusNameInfoBox()
        self.busname_box.connect('busname-selected', self.busname_selected_cb)

        self.paned.pack1(self.busname_box)
        self.paned.pack2(self.busname_info_box)
        self.paned.set_position(200)
        self.pack_start(self.paned, True, True)

        xml.signal_autoconnect(signal_dict)
        
    def busname_selected_cb(self, busname_box, busname):
        self.busname_info_box.set_busname(busname)

    def filter_entry_changed_cb(self, entry, button):
        value = entry.get_text()
        if value == '':
            value = None

        self.busname_box.set_filter_string(value)

    def hide_private_toggled_cb(self, toggle):
        a = toggle.get_active()
        if a:
            toggle.set_label("Show Private")
        else:
            toggle.set_label("Hide Private")

        self.busname_box.set_hide_private(a)

    def sort_combo_changed_cb(self, combo):
        value = combo.get_active_text()
        self.busname_box.set_sort_col(value)

