# -*- coding: utf-8 -*-

from functools import wraps
from IPython.utils.capture import capture_output
import logging
import sys
from tornado import gen
from unittest.mock import patch
import zmq
from ..status import TurretStatus


def capture_method_output(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with capture_output() as cap:
            result = func(self, *args, **kwargs)

        for line in cap.stdout.split('\n'):
            text = line.strip()
            if len(text) > 0:
                self.log.info(text)

        for line in cap.stderr.split('\n'):
            text = line.strip()
            if len(text) > 0:
                self.log.warning(text)

        return result

    return wrapper


def uncache_modules_once(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        uncached = False
        __uncache_modules = self.uncache_modules

        def _uncache_modules(modules):
            nonlocal uncached
            if uncached:
                return
            __uncache_modules(modules)
            uncached = True

        with patch.object(self, 'uncache_modules', _uncache_modules):
            return func(self, *args, **kwargs)

    return wrapper


class TurretAppLogHandler(logging.StreamHandler):

    def __init__(self, app_name, socket):
        super().__init__()

        self.app_name = app_name
        self.socket = socket

    def emit(self, record):
        self.socket.send_json({
            'app_name': self.app_name,
            'type': 'log',
            'payload': dict(record.__dict__, args_type=type(record.args).__name__)
        })


class BaseTurretApp(object):

    completer_class = None

    def __init__(self, app_name, turret_conf, turret_port, turret_status):
        self.app_name = app_name
        self.turret_port = turret_port
        self.turret_conf = turret_conf
        self.turret_status = TurretStatus.from_dict(turret_status)
        self.ipython = get_ipython()  # noqa

        ctx = zmq.Context.instance()
        self.turret_socket = ctx.socket(zmq.PUSH)
        self.turret_socket.connect('tcp://127.0.0.1:{0}'.format(self.turret_port))

        self.log = logging.getLogger(app_name)
        level = turret_conf['app'][app_name].get('logger', {}).get('level', 'info')
        self.log.setLevel(getattr(logging, level.upper()))
        handler = TurretAppLogHandler(app_name, self.turret_socket)
        self.log.addHandler(handler)

    def execute(self, func, *args, **kwargs):
        future = gen.Future()
        result = self.ipython.run_cell(func.format(*args, **kwargs))
        future.set_result(result.result)
        return future

    def uncache_modules(self, modules):
        def match(mod):
            return any([mod == m or mod.startswith('{}.'.format(m)) for m in modules])

        for mod in [mod for mod in sys.modules if match(mod)]:
            self.log.debug('uncache: %s', mod)
            del sys.modules[mod]

    @classmethod
    def command_to_code(self, app_name, command):
        raise NotImplementedError('Must be implemented to support attaching')
