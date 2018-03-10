# -*- coding: utf-8 -*-

from functools import partial
from pathlib import Path
from watchdog.observers import Observer
from ..base import BaseTurretApp
from .handler import WatchdogHandler


class WatchdogApp(BaseTurretApp):
    """
    Turret app which runs Watchdog in a kernel.
    """

    def __init__(self, app_name, turret_conf, turret_port, turret_status, handlers=[]):
        """
        Initializes WatchdogApp.

        Parameters
        ----------
        app_name : str
            App name defined in turret.hcl.
        turret_conf : dict
            Turret conf constructed from turret.hcl.
        turret_port : int
            TCP port for Turret ZMQ channel.
        turret_status : dict
            Turret status.
        handlers : list
            Watchdog handler definitions.
        """
        super().__init__(app_name, turret_conf, turret_port, turret_status)

        self.handlers = handlers
        self.observer = Observer()

        for handler in self.handlers:
            wh = WatchdogHandler(
                self.log, self.execute,
                handler.get('functions', []),
                patterns=handler.get('patterns', []),
                ignore_patterns=handler.get('ignore_patterns', []),
                ignore_directories=handler.get('ignore_directories', False),
                case_sensitive=handler.get('case_sensitive', False),
                uncache_modules=partial(self.uncache_modules, handler.get('uncache', []))
            )
            self.observer.schedule(wh, str(Path.cwd()), recursive=True)

        self.observer.start()