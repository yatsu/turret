# -*- coding: utf-8 -*-

from pathlib import Path
import re
from textwrap import dedent
from unittest.mock import call, patch
from jaffle.config.value import ConfigDict
from jaffle.config.jaffle_config import JaffleConfig


def test_jaffle_config():
    conf = JaffleConfig({})
    assert conf.namespace == {}

    namespace = {'foo': 'FOO', 'bar:': 'BAR'}
    conf = JaffleConfig(
        namespace,
        variable={'baz': 'BAZ'},
        kernel={'my_kernel': {'kernel_name': 'python3'}},
        app={'my_app': {'class': 'my.app.MyApp', 'logger': {
            'suppress_regex': ['pat1', 'pat2'],
            'replace_regex': [{'from': 'pat_from', 'to': 'pat_to'}]
        }}},
        process={'my_proc': {'command': 'my_proc'}},
        job={'my_job': {'command': 'my_job'}},
        logger={
            'level': 'debug',
            'suppress_regex': ['global_pat1', 'global_pat2'],
            'replace_regex': [{'from': 'global_pat_from', 'to': 'global_pat_to'}]
        }
    )

    assert conf.namespace == namespace
    assert conf.variable == ConfigDict({'baz': 'BAZ'}, namespace)
    assert conf.kernel == ConfigDict({'my_kernel': {'kernel_name': 'python3'}}, namespace)
    assert conf.app == ConfigDict({'my_app': {'class': 'my.app.MyApp', 'logger': {
        'suppress_regex': ['pat1', 'pat2'],
        'replace_regex': [{'from': 'pat_from', 'to': 'pat_to'}]
    }}}, namespace)
    assert conf.process == ConfigDict({'my_proc': {'command': 'my_proc'}}, namespace)
    assert conf.job == ConfigDict({'my_job': {'command': 'my_job'}}, namespace)
    assert conf.logger == ConfigDict({
        'level': 'debug',
        'suppress_regex': ['global_pat1', 'global_pat2'],
        'replace_regex': [{'from': 'global_pat_from', 'to': 'global_pat_to'}]
    }, namespace)

    assert conf.app_log_suppress_patterns == {'my_app': [
        re.compile('pat1'), re.compile('pat2')
    ]}
    assert conf.app_log_replace_patterns == {'my_app': [
        (re.compile('pat_from'), 'pat_to')
    ]}

    assert conf.global_log_suppress_patterns == [
        re.compile('global_pat1'), re.compile('global_pat2')
    ]
    assert conf.global_log_replace_patterns == [
        (re.compile('global_pat_from'), 'global_pat_to')
    ]


def test_load():
    data1 = {'kernel': {'my_kernel': {
        'kernel_name': 'python3',
        'env_pass': [],
        'foo': True
    }}}
    ns = {'HOME': '/home/foo'}
    variables = {'name': 'foo'}

    with patch.object(JaffleConfig, '_load_file', return_value=data1) as load_file:
        with patch.object(JaffleConfig, 'create') as create:
            config = JaffleConfig.load(['jaffle.hcl'], ns, variables)

    assert config is create.return_value
    load_file.assert_called_once_with('jaffle.hcl')
    create.assert_called_once_with(data1, ns, variables)

    data2 = {
        'kernel': {
            'my_kernel': {
                'kernel_name': 'pyspark',
                'env_pass': ['HOME'],
                'bar': []
            }
        },
        'app': {'my_app': True}
    }

    with patch.object(JaffleConfig, '_load_file', side_effect=[data1, data2]) as load_file:
        with patch.object(JaffleConfig, 'create') as create:
            config = JaffleConfig.load(['jaffle.hcl', 'my_jaffle.hcl'], ns, variables)

    assert config is create.return_value
    load_file.assert_has_calls([call('jaffle.hcl'), call('my_jaffle.hcl')])
    create.assert_called_once_with({
        'kernel': {
            'my_kernel': {
                'kernel_name': 'pyspark',
                'env_pass': ['HOME'],
                'foo': True,
                'bar': []
            }
        },
        'app': {'my_app': True}
    }, ns, variables)


def test_create():
    def echo(msg):
        return msg

    functions = [echo]

    with patch('jaffle.config.jaffle_config.functions', functions):
        with patch('jaffle.config.jaffle_config.VariablesNamespace') as vn:
            with patch.object(JaffleConfig, '__init__', return_value=None) as init:
                JaffleConfig.create(
                    {'kernel': {'my_kernel': {'kernel_name': 'python3'}}},
                    {'HOME': '/home/foo'},
                    {'foo': True}
                )

    init.assert_called_once_with(
        {
            'HOME': '/home/foo',
            'var': vn.return_value,
            'echo': echo,
        },
        kernel={'my_kernel': {'kernel_name': 'python3'}}
    )


def test_load_file(tmpdir):
    tmp_file = Path(tmpdir) / 'jaffle.hcl'
    with tmp_file.open('w') as f:
        f.write(dedent('''
            kernel "my_kernel" {
              kernel_name = "python3"
            }
        ''').strip())

    data = JaffleConfig._load_file(tmp_file)
    assert data == {'kernel': {'my_kernel': {'kernel_name': 'python3'}}}

    data = JaffleConfig._load_file(str(tmp_file))
    assert data == {'kernel': {'my_kernel': {'kernel_name': 'python3'}}}
