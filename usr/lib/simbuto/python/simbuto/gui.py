#!/usr/bin/env python3
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from gi.repository import GdkPixbuf
from gi.repository import Gdk
from gi.repository import GLib
import logging
import os
import configparser
import signal
import hashlib


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


    ### Properties ###
    @property
    def currently_edited_file(self):
        """ The currently edited file
        """
        try:
            return self._currently_edited_file
        except AttributeError:
            return None

    @currently_edited_file.setter
    def currently_edited_file(self, value):
        self._currently_edited_file = value
        # put the file basename into the title
        self.update_window_title_filename()

    @property
    def budget_needs_saving(self):
        """ Check if the current budget needs saving
        """
        # no drama here
        if self.currently_edited_file is None \
            and self.current_editor_content == "":
            self.logger.debug(_("The current buffer is empty and no file is"
                                " specified. No saving necessary."))
            return False

        # needs saving if no filename was specified yet or file doesn't exist
        try: assert os.path.exists(self.currently_edited_file) == True
        except: 
            self.logger.debug(_(
            "Nonexistant or no file specified. Saving necessary!"))
            return True

        # otherwise compare the md5sums
        with open(self.currently_edited_file,"r") as f:
            # hash the file content
            md5_file = hashlib.md5(f.read().encode('utf-8')).hexdigest() 
        # hash the text
        md5_buffer = hashlib.md5(
            self.current_editor_content.encode('utf8')).hexdigest() 
        needs_saving = md5_file != md5_buffer 
        if needs_saving:
            self.logger.debug(_("The current budget would need saving."))
        else:
            self.logger.debug(_("The current budget doesn't need saving."))
        return needs_saving # return true if different
        
    @property
    def current_editor_content(self):
        textview = self.builder.get_object("editor_textview")
        tb = textview.get_buffer() # get the underlying buffer
        start, end = tb.get_bounds()
        content = tb.get_text(start, end, True)
        return content

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
            "NewBudget": self.new_budget,
            "OpenFileDialog": self.open_file_dialog,
            "SaveAsDialog": self.saveas_dialog,
            "SaveToFile": self.save_to_file,
            "NotYetImplemented": self.show_notyetimplemented_dialog,
            "ResetStatus": self.reset_statusbar,
            "UpdateStatus": self.update_statusbar_from_menuitem,
            }
        self.builder.connect_signals(self.handlers)

        # create a simbuto file filter
        self.simbuto_filefilter = Gtk.FileFilter()
        self.simbuto_filefilter.set_name(_("Simbuto budget files"))
        self.simbuto_filefilter.add_mime_type("application/x-simbuto")

        # main window
        window = self.builder.get_object("main_applicationwindow")
        self.update_window_title_filename()
        window.set_icon_from_file(self.config.get('gui-general','icon'))

        # the menu
        # the window accelgroup
        accelgroup = self.builder.get_object("window_accelgroup")
        # define accelerators
        accels = {
            self.builder.get_object("new_menuitem"):    "<Control>n",
            self.builder.get_object("open_menuitem"):   "<Control>o",
            self.builder.get_object("save_menuitem"):   "<Control>s",
            self.builder.get_object("saveas_menuitem"): "<Control><Shift>s",
            self.builder.get_object("quit_menuitem"):   "<Control>q",
            }
        # add the accelerators
        for item, accelstr in accels.items():
            key, modifiers = Gtk.accelerator_parse(accelstr)
            item.add_accelerator("activate", accelgroup, key, modifiers, 
                Gtk.AccelFlags.VISIBLE)

        # editor
        editorheading = self.builder.get_object("editor_heading_label")
        editorheading.set_text(_("Budget editor"))

        # graph
        plotheading = self.builder.get_object("plot_heading_label")
        plotheading.set_text(_("Budget graph"))

        # statusbar
        self.reset_statusbar() # initially reset statusbar

        window.show_all()

    def new_budget(self,*args):
        if self.budget_needs_saving:
            self.wanttosave_dialog()
        self.empty_editor()

    def update_window_title_filename(self):
        window = self.builder.get_object("main_applicationwindow")
        try:    basename = os.path.basename(self.currently_edited_file)
        except: basename = _("unsaved budget")
        window.set_title("{} - {}".format(_("Simbuto"), basename))

    def wanttosave_dialog(self):
        # get the info dialog
        dialog = self.builder.get_object("wanttosave_dialog")
        dialog.set_markup(_("Do you want to save your current budget?"))
        response = dialog.run() # run the dialog
        if response == Gtk.ResponseType.YES:
            self.logger.debug(_("The user wants to save the budget to file."))
            self.save_current_budget_to_file()
        else:
            self.logger.debug(_("The user does NOT want to save the budget."))
        dialog.hide() # only hide it, because destroying prevents re-opening

    def empty_editor(self):
        self.logger.debug(_("emptying editor"))
        # get the textview
        textview = self.builder.get_object("editor_textview")
        textbuffer = textview.get_buffer() # get the underlying buffer
        textbuffer.set_text("") # empty the text
        self.currently_edited_file = None # no file edited currently

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
            self.currently_edited_file = filename # set currently edited file
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

    def open_file_dialog(self, *args):
        # create a dialog
        dialog = Gtk.FileChooserDialog(
            _("Please choose a file"), # title
            self.builder.get_object("main_applicationwindow"), # parent
            Gtk.FileChooserAction.OPEN, # Action
            # Buttons (obviously not possible with glade!?)
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )

        # add the filter
        dialog.add_filter(self.simbuto_filefilter)

        response = dialog.run() # run the dialog
        if response == Gtk.ResponseType.OK: # file selected
            filename = dialog.get_filename()
            self.logger.debug(_("File '{}' selected").format(filename))
            # fill the editor
            self.fill_editor_from_file(filename)
        elif response == Gtk.ResponseType.CANCEL: # cancelled
            self.logger.debug(_("File selection cancelled"))
        else: # something else
            self.logger.debug(_("File selection dialog was closed"))
            
        dialog.destroy() # destroy the dialog, we don't need it anymore
        
    def saveas_dialog(self, *args):
        # create a dialog
        dialog = Gtk.FileChooserDialog(
            _("Please select a saving destination"), # title
            self.builder.get_object("main_applicationwindow"), # parent
            Gtk.FileChooserAction.SAVE, # Action
            # Buttons (obviously not possible with glade!?)
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            )

        # add the filter
        dialog.add_filter(self.simbuto_filefilter)

        response = dialog.run() # run the dialog
        if response == Gtk.ResponseType.OK: # file selected
            filename = dialog.get_filename()
            self.logger.debug(_("File '{}' selected").format(filename))
            # save
            self.save_current_budget_to_file(filename)
        elif response == Gtk.ResponseType.CANCEL: # cancelled
            self.logger.debug(_("File selection cancelled"))
        else: # something else
            self.logger.debug(_("File selection dialog was closed"))
            
        dialog.destroy() # destroy the dialog, we don't need it anymore

    def show_notyetimplemented_dialog(self, *args):
        # get the dialog
        dialog = self.builder.get_object("notyetimplemented_dialog")
        dialog.set_markup(_("This feature is currently not implemented."))
        dialog.run() # run the dialog
        dialog.hide() # only hide it, because destroying prevents re-opening
        
            
    def show_info_dialog(self, *args):
        # get the info dialog
        infodialog = self.builder.get_object("info_dialog")
        # comment
        infodialog.set_comments(_("a simple budgeting tool"))
        # logo
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            self.config.get('gui-general','icon'))
        pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
        infodialog.set_logo(pixbuf)
        infodialog.run() # run the dialog
        infodialog.hide() # only hide it, because destroying prevents re-opening

    def save_current_budget_to_file(self, filename = None):
        if filename is None:
            filename = self.currently_edited_file

        if filename is None:
            self.saveas_dialog()
            return

        self.logger.info(_("Saving the current budget to the file '{}'..."
            ).format(filename))
        with open(filename, "w") as f:
            f.write(self.current_editor_content)
        self.currently_edited_file = filename

    def save_to_file(self, *args):
        # check if the current buffer comes from a file
        if self.currently_edited_file is None: # no file selected yet
            self.saveas_dialog() # show the saveas dialog
        else:
            self.save_current_budget_to_file()

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
        if self.budget_needs_saving:
            self.wanttosave_dialog()
        self.mainloop.quit()

