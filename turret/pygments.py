# -*- coding: utf-8 -*-

from pygments.lexer import RegexLexer, words, bygroups, include
from pygments.token import (
    Text, Comment, Operator, Keyword, Name, String, Number, Punctuation
)

# TurretHCLLexer inherits some code from ``pygments.lexers.configs``.
# Here is the Pygments copyright:
#
#     pygments.lexers.configs
#     ~~~~~~~~~~~~~~~~~~~~~~~
#
#     Lexers for configuration file formats.
#
#     :copyright: Copyright 2006-2017 by the Pygments team, see AUTHORS.
#     :license: BSD, see LICENSE for details.


class TurretHCLLexer(RegexLexer):
    """
    Lexer for Turret HCL file.
    """

    name = 'TurretHCL'
    aliases = ['hcl']
    filenames = ['*.hcl']
    mimetypes = ['application/x-turret-hcl']

    tokens = {
        'root': [
             include('string'),
             include('punctuation'),
             include('curly'),
             include('basic'),
             include('whitespace'),
             (r'[0-9]+', Number),
        ],
        'basic': [
             (words(('true', 'false'), prefix=r'\b', suffix=r'\b'), Keyword.Type),
             (r'\s*/\*', Comment.Multiline, 'comment'),
             (r'\s*#.*\n', Comment.Single),
             (r'(.*?)(\s*)(=)', bygroups(Name.Attribute, Text, Operator)),
             (words(('logger', 'options'),
                    prefix=r'\b', suffix=r'\b'), Keyword.Reserved, 'function'),
             (words(('kernel', 'app', 'process', 'job'),
                    prefix=r'\b', suffix=r'\b'), Keyword.Declaration),
             ('\$\{', String.Interpol, 'var_builtin'),
        ],
        'function': [
             (r'(\s+)(".*")(\s+)', bygroups(Text, String, Text)),
             include('punctuation'),
             include('curly'),
        ],
        'var_builtin': [
            (r'\$\{', String.Interpol, '#push'),
            (words(('exec', 'env'),
                   prefix=r'\b', suffix=r'\b'), Name.Builtin),
            include('string'),
            include('punctuation'),
            (r'\s+', Text),
            (r'\}', String.Interpol, '#pop'),
        ],
        'string': [
            (r'(".*")', bygroups(String.Double)),
        ],
        'punctuation': [
            (r'[\[\](),.]', Punctuation),
        ],
        # Keep this seperate from punctuation - we sometimes want to use different
        # Tokens for { }
        'curly': [
            (r'\s*\{', Text.Punctuation),
            (r'\s*\}', Text.Punctuation),
        ],
        'comment': [
            (r'[^*/]', Comment.Multiline),
            (r'/\*', Comment.Multiline, '#push'),
            (r'\*/', Comment.Multiline, '#pop'),
            (r'[*/]', Comment.Multiline)
        ],
        'whitespace': [
            (r'\n', Text),
            (r'\s+', Text),
            (r'\\\n', Text),
        ],
    }
