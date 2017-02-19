#!/usr/bin/env python3
# system modules
import logging

# internal modules
from . import WithLogger

# signal manager class
class SignalManager(WithLogger):
    def __init__(self):
        self.signals = {} # start with empty signals

    ##################
    ### Properties ###
    ##################
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
            self.signals[name] = {
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
                " unregistered signal '{}'.").format( action, name))

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
            actions = signal["actions"]
            self.logger.debug(_("Signal '{}' emitted with data '{}'"
                ).format(name, data))
            for action in actions: 
                self.logger.debug(_("Calling action '{}' with data '{}'"
                    ).format(action,data))
                res = action(**data) # call every action
                results.append(res) # append the return value
        except KeyError:
            self.logger.warning(
                _("Attempt to emit unregistered signal '{}'").format(name))
        return results
