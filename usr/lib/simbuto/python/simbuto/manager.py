#!/usr/bin/env python3
import logging
import hashlib
from . import signalmanager

# signal manager class
class SimbutoManager(object):
    def __init__(self):
        pass

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
        
