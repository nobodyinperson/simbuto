#!/usr/bin/env python3
# system modules
import logging
import os
import configparser
import signal
import datetime
import hashlib
import contextlib
import time

# external modules
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from gi.repository import GdkPixbuf
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Pango

# internal modules
from . import signalmanager
from . import config
from . import VERSION


class SimbutoGui(object):
    """ class for the gui
    """
    def __init__(self):
        """ class constructor
        """
        # initially set an empty configuration
        self.set_config(configparser.ConfigParser())
        # set up the quit signals
        self.setup_signals(
            signals = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP],
            handler = self.quit
        )


    ##################
    ### Properties ###
    ##################
    @property
    def logger(self):
        """ used logging.Logger. Defaults to logging.getLogger(__name__).
        May be set to a different logger.
        """
        try:
            return self._logger
        except AttributeError:
            return logging.getLogger(__name__)

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    @property
    def signalmanager(self):
        return self._signalmanager

    @signalmanager.setter
    def signalmanager(self, manager):
        assert isinstance(manager, signalmanager.SignalManager)
        self._signalmanager = manager

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

        # let the manager hash the file
        res = self.signalmanager.emit_signal("md5sum-of-file",
            filename=self.currently_edited_file) 
        md5_file = res[0] # TODO: This is a little insecure
        self.logger.debug(_("md5sum of file '{}' is '{}'").format(
            self.currently_edited_file,md5_file))
        # hash the editor text
        md5_buffer = hashlib.md5(
            self.current_editor_content.encode('utf8')).hexdigest() 
        self.logger.debug(_("md5sum of editor content is '{}'").format(
            md5_buffer))
        needs_saving = md5_file != md5_buffer 
        if needs_saving:
            self.logger.debug(_("The current budget would need saving."))
        else:
            self.logger.debug(_("The current budget doesn't need saving."))
        return needs_saving # return true if different
        
    @property
    def current_editor_content(self):
        textview = self("texteditor_textview")
        tb = textview.get_buffer() # get the underlying buffer
        start, end = tb.get_bounds()
        content = tb.get_text(start, end, True)
        return content

    @property
    def selected_start_date(self):
        """ The selected start date. You may set this to a datetime.datetime
        object.
        Returns:
            date (datetime.datetime): The start date
        """
        year,month,day = self.object("dateregion_start_calendar").get_date()
        date = datetime.datetime(year = year, month = month + 1, day = day)
        return date

    @selected_start_date.setter
    def selected_start_date(self, newdate):
        try:
            year,month,day = newdate.year, newdate.month - 1, newdate.day
        except AttributeError:
            raise TypeError("selected_start_date needs to be set to object of " 
                "datetime.datetime")
        self("dateregion_start_calendar").select_month(
            month=month,year=year)
        self("dateregion_start_calendar").select_day(day = day)

    @property
    def selected_end_date(self):
        """ The selected end date. You may set this to a datetime.datetime
        object.
        Returns:
            date (datetime.datetime): The end date
        """
        year,month,day = self.object("dateregion_end_calendar").get_date()
        date = datetime.datetime(year = year, month = month + 1, day = day)
        return date

    @selected_end_date.setter
    def selected_end_date(self, newdate):
        try:
            year,month,day = newdate.year, newdate.month - 1, newdate.day
        except AttributeError:
            raise TypeError("selected_end_date needs to be set to object of " 
                "datetime.datetime")
        self("dateregion_end_calendar").select_month(
            month=month,year=year)
        self("dateregion_end_calendar").select_day(day = day)

    @property
    def calendar_setting_in_progress(self):
        """ This is an internal property to prevent recursion in the calendar
        date setting. It is always boolean. When you set it, it is converted to
        bool.  
        """
        if hasattr(self,"_calendar_setting_in_progress"):
            return bool(self._calendar_setting_in_progress)
        else:
            return False

    @calendar_setting_in_progress.setter
    def calendar_setting_in_progress(self, value):
        self._calendar_setting_in_progress = bool(value)

    @property
    def last_window_size_allocate(self):
        try:
            return self._last_window_size_allocate
        except AttributeError:
            return 0

    @last_window_size_allocate.setter
    def last_window_size_allocate(self, value):
        self._last_window_size_allocate = float(value)

    @property
    def window_resize_is_long_ago(self):
        return self.last_window_size_allocate + 0.1 < time.time()

    ########################
    ### Context managers ###
    ########################
    @contextlib.contextmanager
    def no_calendar_recursion(self):
        old = self.calendar_setting_in_progress # old value
        self.calendar_setting_in_progress = True # lock
        try:
            yield
        finally:
            self.calendar_setting_in_progress = old # unlock

    ###############
    ### Methods ###
    ###############
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

    # get an object from the builder
    def object(self, name):
        try:
            self.builder
        except AttributeError: # builder not yet loaded
            self.load_builder()
        obj = self.builder.get_object(name)
        return obj

    # build the gui
    def load_builder(self):
        # get a GTK builder
        self.builder = Gtk.Builder()
        # load the gladefile
        self.builder.add_from_file(self.config.get('gui-general','gladefile'))

    # set the config
    def set_config(self, config):
        self.config = config

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
            "UpdateStatus": self.update_statusbar_from_widget,
            "UpdateGraphFromEditor": self.update_graph_from_editor,
            "RegionDaySelected": self.region_day_selected,
            "ResetDate": self.reset_dateregion,
            "WindowResize": self.window_resize,
            }
        self.builder.connect_signals(self.handlers)

        # translate actions
        self.actions = {
            "app.new": {"label":_("New Budget"),"short":_("New"),
                "tooltip":_("Create a new budget")},
            "app.open": {"label":_("Open Budget"),"short":_("Open"),
                "tooltip":_("Open an existing budget file")},
            "app.save": {"label":_("Save Budget"),"short":_("Save"),
                "tooltip":_("Save this budget")},
            "app.saveas": {"label":_("Save As"),"short":_("Save As"),
                "tooltip":_("Save this budget to another file")},
            "app.refresh": {"label":_("Refresh Graph"),"short":_("Refresh"),
                "tooltip":_("Refresh the budget graph")},
            "app.quit": {"label":_("Quit"),"short":_("Quit"),
                "tooltip":_("Quit Simbuto")},
            "app.about": {"label":_("About"),"short":_("About"),
                "tooltip":_("Display information on Simbuto")},
            "app.reset": {"label":_("Date Reset"),"short":_("Date Reset"),
                "tooltip":_("Reset the selected date region")},
            }
        # set the label for each action
        for action, labels in self.actions.items():
            self(action).set_label( # the label
                self.actions.get(action,{}).get("label"))
            self(action).set_short_label( # the short label
                self.actions.get(action,{}).get("short"))
            self(action).set_tooltip( # the tooltip
                self.actions.get(action,{}).get("tooltip"))
            
        # create a simbuto file filter
        self.simbuto_filefilter = Gtk.FileFilter()
        self.simbuto_filefilter.set_name(_("Simbuto budget files"))
        self.simbuto_filefilter.add_mime_type("application/x-simbuto")

        # main window
        window = self("main_applicationwindow")
        self.update_window_title_filename()
        window.set_icon_from_file(self.config.get('gui-general','icon'))

        # the menu
        # the window accelgroup
        accelgroup = self("window_accelgroup")
        # define accelerators
        accels = {
            self("new_menuitem"):    "<Control>n",
            self("open_menuitem"):   "<Control>o",
            self("save_menuitem"):   "<Control>s",
            self("saveas_menuitem"): "<Control><Shift>s",
            self("quit_menuitem"):   "<Control>q",
            self("refresh_menuitem"):["F5","<Control>r"],
            }
        # add the accelerators
        for item, accelstrs in accels.items():
            if not isinstance(accelstrs,list):
                accelstrs = [accelstrs]
            for accelstr in accelstrs:
                key, modifiers = Gtk.accelerator_parse(accelstr)
                item.add_accelerator("activate", accelgroup, key, modifiers, 
                    Gtk.AccelFlags.VISIBLE)

        # translate the basic menuitems
        menuitems = {
            "file_menuitem": _("_File"),
            "help_menuitem": _("_Help"),
            "budget_menuitem": _("_Budget"),
            }
        # set the label for each  menuitem
        for name, label in menuitems.items():
            self(name).set_label(label)

        # editor
        editorheading = self("editor_heading_label")
        editorheading.set_text(_("Budget editor"))
        editor_textview = self("texteditor_textview") # the tv
        monofont = Pango.FontDescription("monospace") # a monospace font
        editor_textview.modify_font(monofont) # set the editor to monospace

        # the notebook
        self("comforteditor_placeholder_label").set_text(_("Comfort editor " 
            "coming soon!"))
        self("editor_notebook_comforteditor_label").set_text(_("Comfort"))
        self("editor_notebook_texteditor_label").set_text(_("Text"))
        self("editor_notebook").next_page() # switch to "Text page"

        # graph
        plotheading = self("plot_heading_label")
        plotheading.set_text(_("Budget graph"))

        # statusbar
        self.reset_statusbar() # initially reset statusbar

        # calendar
        # pretend the start date was selected and let automatic range selection
        # do the rest
        self("dateregion_expander_label").set_text(_("Date range"))
        self("dateregion_start_calendar_label").set_text(_("start date"))
        self("dateregion_end_calendar_label").set_text(_("end date"))
        self.reset_dateregion() # reset dateregion

        # the notebook
        self("comforteditor_placeholder_label").set_text(_("Comfort editor " 
            "coming soon!"))

        window.show_all()

    def get_current_editor_content(self):
        return self.current_editor_content

    ###########################
    ### UI changing methods ###
    ###########################
    def new_budget(self,*args):
        if self.budget_needs_saving:
            self.wanttosave_dialog()
        self.empty_editor()

    def update_window_title_filename(self):
        window = self("main_applicationwindow")
        try:    basename = os.path.basename(self.currently_edited_file)
        except: basename = _("unsaved budget")
        window.set_title("{} - {}".format(_("Simbuto"), basename))

    def empty_editor(self):
        self.logger.debug(_("emptying editor"))
        # get the textview
        textview = self("texteditor_textview")
        textbuffer = textview.get_buffer() # get the underlying buffer
        textbuffer.set_text("") # empty the text
        self.currently_edited_file = None # no file edited currently

    def reset_statusbar(self, *args):
        statuslabel = self("status_label")
        statuslabel.set_text(_("Simbuto - a simple budgeting tool"))

    def update_statusbar_from_widget(self, widget):
        # get the action assiciated with the widget
        try: widget_action = widget.get_related_action().get_name()
        except AttributeError: widget_action = None
        # look in the actions dict to update the statusbar text
        self.update_statusbar( text = 
            self.actions.get(widget_action,{}).get("tooltip"))

    def update_statusbar(self, text = None):
        statuslabel = self("status_label")
        # if None, use default
        if isinstance(text, str): newtext = text
        else: newtext = _("Simbuto - a simple budgeting tool")
        # set the text
        statuslabel.set_text(newtext)

    def update_graph_from_editor(self, *args):
        # rect = self("plot_image").get_allocation()
        rect = self("plot_scrolledwindow").get_allocation()
        width = rect.width
        height = rect.height
        try:
            currentfile = os.path.basename(self.currently_edited_file)
        except AttributeError:
            currentfile = _("unnamed-budget")
        name =  "{}.png".format(currentfile)
        filename = os.path.join(config.personal_simbuto_dotfolder(),
            "plots",name)
        success = self.signalmanager.emit_signal("create-graph-from-text",
            filename=filename, # to this file
            text = self.current_editor_content, # this text
            width = width, height = height, # these dimensions
            start = self.selected_start_date, # this start date
            end = self.selected_end_date, # this end date
            )
        if success[0]:
            self.logger.debug(_("The graph file was obviously " 
                "sucessfully updated."))
            self.update_graph_from_file(filename)
            self.update_statusbar(_("Graph updated"))
        else:
            self.logger.debug(_("There was a problem updating the graph."))
            self.update_statusbar(_("[WARNING] There was a problem " 
                "updating the graph. Please check the input!"))
            
        return True

    def update_graph_from_file(self, filename):
        self("plot_image").set_from_file(filename)

    def reset_dateregion(self,*args):
        """ Reset the selected dateregion
        """
        self.selected_start_date = datetime.datetime.now()
        self.selected_end_date = datetime.datetime.now() + \
            datetime.timedelta(365)

    def region_day_selected(self,calendar):
        self.logger.debug(_("Date region was changed."))
        if self.calendar_setting_in_progress: 
            self.logger.debug(_("To prevent recursion I won't react to this."))
            return # we don't want recursion
        with self.no_calendar_recursion():
            # get selected start dates
            start_date = self.selected_start_date
            self.logger.debug(_("start date is now {}").format(start_date))
            end_date = self.selected_end_date
            self.logger.debug(_("end date is now {}").format(end_date))
            if start_date >= end_date: # bullshit selected
                self.logger.debug(_("End date before start date selected."))
                # start date was selected
                if calendar == self("dateregion_start_calendar"):
                    # set end date to one year later
                    self.logger.debug(_("Setting end date to one year after " 
                        "start date"))
                    self.selected_end_date = start_date+datetime.timedelta(365)
                # end date was selected
                elif calendar == self("dateregion_end_calendar"):
                    self.logger.debug(_("Setting start date to one month " 
                        "before end date"))
                    # set start date to one month earlier
                    self.selected_start_date = end_date - datetime.timedelta(30)
                else:
                    self.logger.warning(_("Somehow a date was selected from an " 
                        "unknown calendar. This should not have happened."))
            # update the graph
            self.update_graph_from_editor()

    def window_resize(self,*args):
        if self.window_resize_is_long_ago:
            self.update_graph_from_editor()
        self.last_window_size_allocate = time.time()


    ###############
    ### Dialogs ###
    ###############
    def open_file_dialog(self, *args):
        # create a dialog
        dialog = Gtk.FileChooserDialog(
            _("Please choose a file"), # title
            self("main_applicationwindow"), # parent
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
            self("main_applicationwindow"), # parent
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
        dialog = self("notyetimplemented_dialog")
        dialog.set_markup(_("This feature is currently not implemented."))
        dialog.run() # run the dialog
        dialog.hide() # only hide it, because destroying prevents re-opening

    def wanttosave_dialog(self):
        # get the info dialog
        dialog = self("wanttosave_dialog")
        dialog.set_markup(_("Do you want to save your current budget?"))
        response = dialog.run() # run the dialog
        if response == Gtk.ResponseType.YES:
            self.logger.debug(_("The user wants to save the budget to file."))
            self.save_current_budget_to_file()
        else:
            self.logger.debug(_("The user does NOT want to save the budget."))
        dialog.hide() # only hide it, because destroying prevents re-opening
        
    def show_info_dialog(self, *args):
        # get the info dialog
        infodialog = self("info_dialog")
        # comment
        infodialog.set_comments(_("a simple budgeting tool"))
        # version
        infodialog.set_version(VERSION)
        # logo
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            self.config.get('gui-general','icon'))
        pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
        infodialog.set_logo(pixbuf)
        infodialog.run() # run the dialog
        infodialog.hide() # only hide it, because destroying prevents re-opening


    ########################
    ### File IO Wrappers ###
    ########################
    def save_current_budget_to_file(self, filename = None):
        if filename is None:
            filename = self.currently_edited_file

        if filename is None:
            self.saveas_dialog()
            return

        self.logger.info(_("Saving the current budget to the file '{}'..."
            ).format(filename))
        # emit the save-to-file signal
        res = self.signalmanager.emit_signal("save-to-file",
            filename=filename,text=self.current_editor_content)
        if res == [True]:
            self.logger.info(_("Budget saved to '{}'").format(filename))
            self.currently_edited_file = filename # update currently edited file
            self("app.refresh").activate() # refresh
            self.update_statusbar(_("Budget saved to '{}'").format(filename))
        else:
            self.logger.info(_("Budget could NOT be saved to '{}'!").format(
                filename))
            self.update_statusbar(_("[WARNING] Budget could " 
                "not be saved to '{}'!").format(filename))

    def save_to_file(self, *args):
        # check if the current buffer comes from a file
        if self.currently_edited_file is None: # no file selected yet
            self.saveas_dialog() # show the saveas dialog
        else:
            self.save_current_budget_to_file()

    def fill_editor_from_file(self, filename):
        self.logger.debug(_("read file '{}' into editor....").format(filename))
        # emit the signal and get the text
        res = self.signalmanager.emit_signal("read-from-file",filename=filename)
        text = res[0]
        if text is not None:
            # get the textview
            textview = self("texteditor_textview") 
            textbuffer = textview.get_buffer() # get the underlying buffer
            textbuffer.set_text(text) # empty the text
            self.logger.debug(_("editor was filled with contents of file '{}'"
                ).format(filename))
            self.currently_edited_file = filename # set currently edited file
            self("app.refresh").activate() # refresh
        else: # didn't work, empty editor
            self.logger.warning(_("Reading from file '{}' didn't work!").format(
                filename))
            self.empty_editor()


    # run the gui
    def run(self):
        # can't use Gtk.main() because of a bug that prevents proper SIGINT
        # handling. use Glib.MainLoop() directly instead.
        self.mainloop = GLib.MainLoop() # main loop
        # signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.logger.debug(_("Starting GLib main loop..."))
        self.mainloop.run()
        self.logger.debug(_("GLib main loop ended."))

    def __call__(self, objname):
        """ When called, return the object like the builder
        """
        return self.object(objname)

    # quit the gui
    def quit(self, *args):
        self.logger.debug(_("Received quitting signal."))
        if self.budget_needs_saving:
            self.wanttosave_dialog()
        self.mainloop.quit()


class BudgetFactEditor(Gtk.Box):
    """ The budget facts editor
    """
    def __init__(self):
        # run the Gtk.Box constructor
        super().__init__(   
            orientation = Gtk.Orientation.HORIZONTAL, # orientation
            spacing = 5, # spacing
            )

    ##################
    ### Properties ###
    ##################


class SingleBudgetFactEditor(Gtk.Box):
    """ the editor for a single budget fact
    """
    def __init__(self):
        # run the Gtk.Box constructor
        super().__init__(   
            orientation = Gtk.Orientation.HORIZONTAL, # orientation
            spacing = 5, # spacing
            )
