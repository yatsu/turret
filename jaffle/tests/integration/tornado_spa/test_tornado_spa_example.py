# -*- coding: utf-8 -*-

import os
import re
import shlex
import signal
from pathlib import Path

import pytest
from tornado.escape import to_unicode
from tornado.iostream import StreamClosedError
from tornado.process import Subprocess


@pytest.fixture(scope='module')
def tornado_spa_example_dir():
    cwd_org = Path.cwd()
    os.chdir(str(Path(__file__).parent.parent.parent.parent.parent / 'examples' / 'tornado_spa'))
    yield Path.cwd()
    os.chdir(str(cwd_org))


@pytest.mark.gen_test(timeout=30)
def test_tornado_spa_example(tornado_spa_example_dir):
    command = 'jaffle start --disable-color -y'
    proc = Subprocess(
        shlex.split(command), stdin=None, stderr=Subprocess.STREAM, preexec_fn=os.setpgrp
    )
    stdout = []
    try:
        while True:
            line_bytes = yield proc.stderr.read_until(b'\n')
            line = to_unicode(line_bytes).rstrip()
            stdout.append(line)
            if re.search(r'Kernel py_kernel \(.*\) is ready', line):
                break
    except StreamClosedError:
        pass

    os.killpg(os.getpgid(proc.proc.pid), signal.SIGINT)

    joined_stdout = '\n'.join(stdout)

    assert 'Jaffle port:' in stdout[0]
    assert 'Starting kernel: py_kernel' in stdout[1]
    assert 'Kernel started:' in stdout[2]
    assert 'Initializing jaffle.app.watchdog.WatchdogApp on py_kernel' in joined_stdout
    assert 'Initializing jaffle.app.tornado.TornadoBridgeApp on py_kernel' in joined_stdout
    assert 'Initializing jaffle.app.pytest.PyTestRunnerApp on py_kernel' in joined_stdout
