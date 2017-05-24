# -*- coding: utf-8 -*-
# system modules
import logging
import configparser
import datetime
import locale

# external modules
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk

# internal modules
from .. import signalmanager
from .. import config
from .. import VERSION
from .. import WithLogger


class BudgetFactEditor(Gtk.Box,WithLogger):
    """ The budget facts editor
    """
    def __init__(self):
        # run the Gtk.Box constructor
        super().__init__(   
            orientation = Gtk.Orientation.VERTICAL, # orientation
            spacing = 5, # spacing
            )


class SingleBudgetFactEditor(Gtk.Box,WithLogger):
    """ the editor for a single budget fact
    """
    def __init__(self):
        # run the Gtk.Box constructor
        super().__init__(   
            orientation = Gtk.Orientation.HORIZONTAL, # orientation
            spacing = 5, # spacing
            )

