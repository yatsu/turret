# -*- coding: utf-8 -*-

import filelock
import json
import logging
from pathlib import Path
from traitlets.config.application import Application
from traitlets import Bool, Unicode, default
from ..logging import LogFormatter


aliases = {
    'log-level': 'Application.log_level',
    'log-datefmt': 'Application.log_datefmt',
    'log-format': 'Application.log_format'
}

flags = {
    'debug': (
        {'Application': {'log_level': logging.DEBUG}},
        'set log level to logging.DEBUG (maximize logging output)'
    ),
    'y': (
        {'TurretBaseCommand': {'answer_yes': True}},
        'Answer yes to any questions instead of prompting.'
    )
}


class TurretBaseCommand(Application):
    """
    Turret base command.
    """
    name = 'turret'
    description = 'Turret'

    aliases = aliases
    flags = flags

    _log_formatter_cls = LogFormatter

    @default('log')
    def _log_default(self):
        log = logging.getLogger('turret')
        log.setLevel(self.log_level)
        log.propagate = False
        formatter = self._log_formatter_cls(fmt=self.log_format, datefmt=self.log_datefmt)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        log.addHandler(handler)
        return log

    @default('log_level')
    def _log_level_default(self):
        return logging.INFO

    @default('log_datefmt')
    def _default_log_datefmt(self):
        return "%H:%M:%S"

    @default('log_format')
    def _log_format_default(self):
        return '%(asctime)s.%(msecs).03d %(name)12s %(levelname)1.1s %(message)s'

    config_file = Unicode(config=True, help='Config file path.')

    answer_yes = Bool(False, config=True, help='Answer yes to any prompts.')

    data_dir = Unicode(config=True, help='Data directory path.')

    def _data_dir_default(self):
        return str(Path.cwd() / '.turret')

    runtime_dir = Unicode(config=True, help='Runtime directory path.')

    def _runtime_dir_default(self):
        return str(Path(self.data_dir) / 'runtime')

    @property
    def sessions_file(self):
        return Path(self.runtime_dir) / 'sessions.json'

    @property
    def sessions_lock_file(self):
        return Path(self.runtime_dir) / 'sessions.json.lock'

    @property
    def sessions_file_lock(self):
        return filelock.FileLock(self.sessions_lock_file)

    def kernel_connection_file(self, kernel_id):
        return Path(self.runtime_dir) / 'kernel-{}.json'.format(kernel_id)

    def write_sessions_file(self, sessions):
        with self.sessions_file_lock.acquire(timeout=5):
            with self.sessions_file.open('w') as f:
                json.dump(sessions, f, indent=2)

    def remove_sessions_file(self):
        with self.sessions_file_lock.acquire(timeout=5):
            self.sessions_file.unlink()

    def read_sessions_file(self):
        with self.sessions_file_lock.acquire(timeout=5):
            with self.sessions_file.open() as f:
                return json.load(f)
