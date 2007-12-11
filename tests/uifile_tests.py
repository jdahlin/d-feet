#!/usr/bin/env python 
import gtk

main_ui = gtk.Builder()
main_ui.add_from_file("../ui/default-actiongroup.ui")
main_ui.add_from_file("../ui/mainwindow.ui")

win = main_ui.get_object("appwindow1")
win.show_all()

filterbox_ui = gtk.Builder()
filterbox_ui.add_from_file("../ui/filterbox.ui")

filterbox_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
filterbox = filterbox_ui.get_object("filterbox_table1")
filterbox_win.add(filterbox)
filterbox_win.show_all()

introspectview_ui = gtk.Builder()
introspectview_ui.add_from_file("../ui/introspectview.ui")

introspectview_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
introspectview = introspectview_ui.get_object("introspectview_table1")
introspectview_win.add(introspectview)
introspectview_win.show_all()

executedialog_ui = gtk.Builder()
executedialog_ui.add_from_file("../ui/executedialog.ui")

executedialog_win = executedialog_ui.get_object("executedialog1")
executedialog_win.show_all()

gtk.main()
