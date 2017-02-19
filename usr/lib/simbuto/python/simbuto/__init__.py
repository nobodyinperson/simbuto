# -*- coding: utf-8 -*-
# System modules

# External modules

# Internal modules

# the version
VERSION = "0.1.8"

__version__ = VERSION

__all__ = []


class WithLogger(object):
    """ Class for objects with a logger
    """
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

