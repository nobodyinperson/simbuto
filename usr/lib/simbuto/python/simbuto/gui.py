#!/usr/bin/env python3
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from gi.repository import GdkPixbuf
from gi.repository import GLib
import logging
import os
import configparser
import signal


class SimbutoGui(object):
    def __init__(self):
        # initially set the standard logger
        self.set_logger(logging.getLogger(__name__))
        # initially set an empty configuration
        self.set_config(configparser.ConfigParser())
        # set up the quit signals
        self.setup_signals(
            signals = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP],
            handler = self.quit
        )


    def setup_signals(self, signals, handler):
        """
        This is a workaround to signal.signal(signal, handler)
        which does not work with a GLib.MainLoop() for some reason.
        Thanks to: http://stackoverflow.com/a/26457317/5433146
        args:
            signals (list of signal.SIG... signals): the signals to connect to
            handler (function): function to be executed on these signals
        """
        def install_glib_handler(sig): # add a unix signal handler
            GLib.unix_signal_add( GLib.PRIORITY_HIGH, 
                sig, # for the given signal
                handler, # on this signal, run this function
                sig # with this argument
                )

        for sig in signals: # loop over all signals
            GLib.idle_add( # 'execute'
                install_glib_handler, sig, # add a handler for this signal
                priority = GLib.PRIORITY_HIGH  )

    # build the gui
    def load_builder(self):
        # get a GTK builder
        self.builder = Gtk.Builder()
        # load the gladefile
        self.builder.add_from_file(self.config.get('gui-general','gladefile'))

    # set the config
    def set_config(self, config):
        self.config = config

    # set the logger
    def set_logger(self, logger):
        self.logger = logger

    # set up the gui
    def setup_gui(self):
        # load the builder
        self.load_builder()
        
        # define handlers
        self.handlers = {
            "CloseWindow": self.quit,
            "ShowInfoDialog": self.show_info_dialog,
            "NotYetImplemented": self.show_notyetimplemented_dialog,
            "ResetStatus": self.reset_statusbar,
            "UpdateStatus": self.update_statusbar_from_menuitem,
            }
        self.builder.connect_signals(self.handlers)

        # main window
        window = self.builder.get_object("main_applicationwindow")
        window.set_icon_from_file(self.config.get('gui-general','icon'))

        # editor
        editorheading = self.builder.get_object("editor_heading_label")
        editorheading.set_text(_("Budget editor"))

        # graph
        plotheading = self.builder.get_object("plot_heading_label")
        plotheading.set_text(_("Budget graph"))

        # statusbar
        self.reset_statusbar() # initially reset statusbar

        window.show_all()

    def empty_editor(self):
        self.logger.debug(_("emptying editor"))
        # get the textview
        textview = self.builder.get_object("editor_textview")
        textbuffer = textview.get_buffer() # get the underlying buffer
        textbuffer.set_text("") # empty the text

    def fill_editor_from_file(self, filename):
        self.logger.debug(_("trying to open file '{}' to read into editor...."
            ).format(filename))
        try: # try to read from file and set it to the editor
            with open(filename, "r") as f:
                text = f.read()
                self.logger.debug(_("contents of file '{}' were read."
                    ).format(filename))
            # get the textview
            textview = self.builder.get_object("editor_textview") 
            textbuffer = textview.get_buffer() # get the underlying buffer
            textbuffer.set_text(text) # empty the text
            self.logger.debug(_("editor was filled with contents of file '{}'"
                ).format(filename))
        except: # didn't work, empty editor
            self.logger.warning(_("Reading from file '{}' didn't work!").format(
                filename))
            self.empty_editor()

    def reset_statusbar(self, *args):
        statuslabel = self.builder.get_object("status_label")
        statuslabel.set_text(_("Simbuto - a simple budgeting tool"))

    def update_statusbar_from_menuitem(self, widget):
        stati = {
            self.builder.get_object("new_menuitem"):
                _("Create a new budget"),
            self.builder.get_object("open_menuitem"): 
                _("Open an existing budget file"),
            self.builder.get_object("save_menuitem"): 
                _("Save this budget"),
            self.builder.get_object("saveas_menuitem"): 
                _("Save this budget to another file"),
            self.builder.get_object("quit_menuitem"): 
                _("Quit Simbuto"),
            self.builder.get_object("info_menuitem"): 
                _("Display information on Simbuto"),
            }
        statuslabel = self.builder.get_object("status_label")
        statuslabel.set_text(stati.get(widget, 
            _("Simbuto - a simple budgeting tool")))

    def show_notyetimplemented_dialog(self, *args):
        # get the dialog
        dialog = self.builder.get_object("notyetimplemented_dialog")
        # link the dialog to the main window
        dialog.set_transient_for(
            self.builder.get_object("main_applicationwindow"))
        dialog.set_markup(_("This feature is currently not implemented."))
        dialog.run() # run the dialog
        dialog.hide() # only hide it, because destroying prevents re-opening
        
            
    def show_info_dialog(self, *args):
        # get the info dialog
        infodialog = self.builder.get_object("info_dialog")
        # link the dialog to the main window
        infodialog.set_transient_for(
            self.builder.get_object("main_applicationwindow"))
        # comment
        infodialog.set_comments(_("a simple budgeting tool"))
        # logo
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            self.config.get('gui-general','icon'))
        pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
        infodialog.set_logo(pixbuf)
        infodialog.run() # run the dialog
        infodialog.hide() # only hide it, because destroying prevents re-opening

    # run the gui
    def run(self):
        # can't use Gtk.main() because of a bug that prevents proper SIGINT
        # handling. use Glib.MainLoop() directly instead.
        self.mainloop = GLib.MainLoop() # main loop
        # signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.logger.debug(_("Starting GLib main loop..."))
        self.mainloop.run()
        self.logger.debug(_("GLib main loop ended."))

    # quit the gui
    def quit(self, *args):
        self.logger.debug(_("Received quitting signal."))
        self.mainloop.quit()

