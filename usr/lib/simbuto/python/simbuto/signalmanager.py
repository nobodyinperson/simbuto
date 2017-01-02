#!/usr/bin/env python3
import logging
import threading


# signal manager class
class SignalManager(threading.Thread):
    def __init__(self):
        self.signals = {} # start with empty signals

        super().__init__() # call threading.Thread's __init__() method
        self.daemon = True # run as daemon
        self.start() # automatically start

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
    def signals(self):
        """ Dict of the registered signals.
        """
        try:                   return self._signals
        except AttributeError: return {}

    @signals.setter
    def signals(self, newsignals):
        assert isinstance(newsignals, dict)
        self._signals = newsignals

    ### methods ###
    def add_signals(self, names):
        """ add new signals
        Args:
            names (list of str): Names of the new signals
        """
        for name in names: # loop over all names
            if name in self.signals: 
                continue # if we already have it, allright!
            event = threading.Event()
            self.signals[name] = {
                "event": event, # the threading signal
                "actions": [], # empty list of actions
            }
            self.logger.debug(_("Signal '{}' added").format(name))

    def remove_signals(self, names):
        """ remove signals by names
        Args:
            names (list of str): names of signals to remove
        """
        for name in names: # loop over all names
            self.signals.pop(name, None) # remove signal
            self.logger.debug(_("Signal '{}' unregistered").format(name))

    def remove_all_signals(self):
        """ Remove all registered signals
        """
        self.signals = {}
        self.logger.debug(_("All signals unregistered"))

    def connect_to_signal(self, name, action):
        """ Connect an action to a signal. If the signal doesn't exist, add it.
        Args:
            name (str): the signal name
            action (function or method that takes **kwargs): the action to be
                executed on this signal
        """
        try:
            self.signals[name]["actions"]
        except KeyError:
            self.add_signals(names=[name])
            self.logger.debug(_("Attempt to connect action '{}' to" 
                "unregistered signal '{}'.").format( action, name))

        assert callable(action)
        self.signals[name]["actions"].append(action)
        self.logger.debug(_("Connected action '{}' to signal '{}'").format(
            action, name))

    def disconnect_from_signal(self, name, action):
        """ Disconnect an action from a signal.
        Args:
            name (str): the signal name
            action (function or method that takes **kwargs): the action not to
                be executed anymore on this signal
        """
        try:
            self.signals[name]["actions"].remove(action)
            self.logger.debug(_("Disconnected action '{}' from signal '{}'"
                ).format(action, name))
        except KeyError:
            self.logger.warning(_("Attempt to disconnect action '{}'" 
                " from unregistered signal '{}'").format(action, name))
            
    def emit_signal(self, name, **data):
        """ emit a signal, optinally with data. Add the signal if necessary.
        Args:
            name (str): the signal name
            data (keyword arguments): the data passed to all actions
        """
        results = []
        try:
            signal = self.signals[name]
            event = signal["event"]
            actions = signal["actions"]
            # event.set() # set the event
            self.logger.debug(_("Signal '{}' emitted with data '{}'"
                ).format(name, data))
            for action in actions: 
                self.logger.debug(_("Calling action '{}' with data '{}'"
                    ).format(action,data))
                res = action(**data) # call every action
                results.append(res) # append the return value
            # event.clear() # clear the event
        except KeyError:
            self.logger.warning(
                _("Attempt to emit unregistered signal '{}'").format(name))
        return results
            
    # TODO: this is problematic and locks for some reason...
    def get_wait_for_signal_callback(self, name):
        """ Returns the threading.Event.wait method
        Args:
            name (str): the signal name
        Returns:
            callable: Call this to wait for the signal
        """
        try:
            signal = self.signals[name]
            event = signal["event"]
            self.logger.debug(_("Waiting for signal '{}'...").format(name))
            return event.wait # set the event
        except KeyError:
            self.logger.warning(
                _("Attempt to wait for unregistered signal '{}'").format(name))
        
