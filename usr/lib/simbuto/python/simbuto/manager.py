#!/usr/bin/env python3
import logging
import hashlib
import datetime
from rpy2.rinterface import RRuntimeError
from rpy2.robjects import r as R # be able to talk to R
from . import signalmanager

# signal manager class
class SimbutoManager(object):
    def __init__(self):
        # source R functions
        R.source("/usr/lib/simbuto/r/simbuto-functions.R")

    ### Properties ###
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


    ### methods ###
    def read_text_from_file(self, filename):
        """ Read text from the given file in utf-8
        Args:
            filename (path): the path to save the text to
        Returns:
            text (str or None): The text read. None if reading didn't work.
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
            self.logger.debug(_("Read {} characters from file '{}'").format(
                len(text),filename))
            return text
        except:
            self.logger.warning(
                _("Reading from file '{}' didn't work!").format(filename))
            return None

    def save_text_to_file(self, filename, text):
        """ Save the given text to file in utf-8
        Args:
            filename (path): the path to save the text to
            text (str): the text to save
        Returns:
            success (bool): True if it worked, False otherwise
        """
        self.logger.debug(_("Saving {} characters to file '{}'...").format(
            len(text),filename))
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            self.logger.debug(_("Saved {} characters to file '{}'").format(
                len(text),filename))
            return True
        except:
            self.logger.warning(
                _("Saving {} characters to file '{}' didn't work!").format(
                len(text),filename))
            return False

    ### md5sums differ ###
    def md5sum_of_file(self, filename):
        """ Return the given file's md5sum in hexdigits
        Args:
            filename (path): the file to calculate the md5sum from
        Returns:
            md5sum (str): the md5sum of the file
        """
        try:
            with open(filename,"r") as f:
                # hash the file content
                md5 = hashlib.md5(f.read().encode('utf-8')).hexdigest() 
            self.logger.debug(_("md5sum of file '{}' is '{}'").format(
                filename,md5))
            return md5
        except OSError:
            self.logger.warning(_("Calculating md5sum of file '{}' " 
                "didn't work!").format(filename))
            return None
        

    ################
    ### Plotting ###
    ################
    def create_png_graph_from_text(self, text, filename, 
        width = 600, height = 400, 
        start = datetime.datetime.now(), 
        end = datetime.datetime.now() + datetime.timedelta(365),
        ensemble_size = 100,
        use_ensemble = False):
        """ Create a png graph from simbuto csv-like text
        Args:
            text (str): the csv-like simbuto budget
            filename (path): the output png file path
            width, height [Optional(int)]: width and height of the png file.
                Defaults to 600x400px.
            start [Optional(datetime.datetime)]: the start day of the budget
                calculation and plotting. Defaults to the current day.
            end [Optional(datetime.datetime)]: the end time of the budget
                calculation and plotting. Defaults to the current day plus one
                year.
            use_ensemble [Optional(bool)]: calculat an ensemble? Defaults to
                False.
            ensemble_size [Optional(int)]: The ensemble size to use. Defaults to 
                100.
        Returns:
            success (bool): True if graph png file was created, False otherwise
        """
        start_date = R("as.Date('{}-{}-{}')".format(
            start.year,start.month,start.day))
        end_date = R("as.Date('{}-{}-{}')".format(
            end.year,end.month,end.day))
        if not use_ensemble:
            ensemble_size = R("NULL")
        try:
            # append newline
            if not text.endswith("\n"): text += "\n"
            # create the budget from text
            budget_frame = R.read_budget_from_text(text = text)
            # create the timeseries from the budget
            timeseries_frame = R.timeseries_from_budget(budget = budget_frame,
                start = start_date, end = end_date, ensemble_size=ensemble_size)
            # plot to png
            R.plot_budget_timeseries_to_png(filename=filename,
                timeseries = timeseries_frame, width = width, height = height)
            return True
        except RRuntimeError:
            self.logger.warning(_("R could not read from text"))
            return False
