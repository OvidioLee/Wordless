#
# Wordless: Packaging - spec File
#
# Copyright (C) 2018-2021  Ye Lei (叶磊)
#
# This source file is licensed under GNU GPLv3.
# For details, see: https://github.com/BLKSerene/Wordless/blob/master/LICENSE.txt
#
# All other rights reserved.
#

import os
import platform
import sys

import PyInstaller

block_cipher = None
datas = []

# AttaCut
datas.extend(PyInstaller.utils.hooks.collect_data_files('attacut'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('ssg'))
# botok
datas.extend(PyInstaller.utils.hooks.collect_data_files('botok'))
# jieba
datas.extend(PyInstaller.utils.hooks.collect_data_files('jieba'))
# langdetect
datas.extend(PyInstaller.utils.hooks.collect_data_files('langdetect'))
# nagisa
datas.extend(PyInstaller.utils.hooks.collect_data_files('nagisa', include_py_files = True))
# pkuseg
datas.extend(PyInstaller.utils.hooks.collect_data_files('pkuseg'))
# Python-scfsuite
datas.extend(PyInstaller.utils.hooks.collect_data_files('pycrfsuite', include_py_files = True))
# pymorphy2
datas.extend(PyInstaller.utils.hooks.collect_data_files('pymorphy2_dicts_ru'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('pymorphy2_dicts_uk'))
# PyThaiNLP
datas.extend(PyInstaller.utils.hooks.collect_data_files('pythainlp'))
# SacreMoses
datas.extend(PyInstaller.utils.hooks.collect_data_files('sacremoses'))
# spaCy
datas.extend(PyInstaller.utils.hooks.collect_data_files('spacy.lang', include_py_files = True))
datas.extend(PyInstaller.utils.hooks.collect_data_files('spacy_lookups_data'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('da_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('de_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('el_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('en_core_web_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('es_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('fr_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('it_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('lt_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('nb_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('nl_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('pl_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('pt_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('ro_core_news_sm'))
datas.extend(PyInstaller.utils.hooks.collect_data_files('thinc'))
# Tokenizer
datas.extend(PyInstaller.utils.hooks.collect_data_files('tokenizer'))
# Underthesea
datas.extend(PyInstaller.utils.hooks.collect_data_files('underthesea'))
# wordcloud
datas.extend(PyInstaller.utils.hooks.collect_data_files('wordcloud'))

# Custom data files
datas.extend([
    ('src/imgs', 'imgs'),
    ('src/lemmatization', 'lemmatization'),
    ('src/stop_word_lists', 'stop_word_lists'),
    ('src/wl_acks', 'wl_acks'),

    ('src/CHANGELOG.md', '.'),
    ('src/VERSION', '.'),
    ('LICENSE.txt', '.')
])

# Data files for macOS
if platform.system() == 'Darwin':
    datas.extend(PyInstaller.utils.hooks.collect_data_files('PIL', include_py_files = True))

# Hidden imports
hiddenimports = [
    # AttaCut
    'attacut.models.seq_sy_ch_conv_concat',

    # pymorphy2
    'pymorphy2_dicts_ru',
    'pymorphy2_dicts_uk',

    # spaCy
    'spacy.kb',
    'spacy.lexeme',
    'spacy.matcher._schemas',
    'spacy.morphology',
    'spacy.parts_of_speech',
    'spacy.syntax._beam_utils',
    'spacy.syntax._parser_model',
    'spacy.syntax.arc_eager',
    'spacy.syntax.ner',
    'spacy.syntax.nn_parser',
    'spacy.syntax.stateclass',
    'spacy.syntax.transition_system',
    'spacy.tokens._retokenize',
    'spacy.tokens.morphanalysis',
    'spacy.tokens.underscore',

    'blis',
    'blis.py',

    'cymem',
    'cymem.cymem',

    'murmurhash',

    'preshed.maps',

    'srsly.msgpack.util',

    'thinc.extra.search',
    'thinc.linalg',
    'thinc.neural._aligned_alloc',
    'thinc.neural._custom_kernels',

    # spaCy models
    'da_core_news_sm',
    'de_core_news_sm',
    'el_core_news_sm',
    'en_core_web_sm',
    'es_core_news_sm',
    'fr_core_news_sm',
    'it_core_news_sm',
    'lt_core_news_sm',
    'nb_core_news_sm',
    'nl_core_news_sm',
    'pl_core_news_sm',
    'pt_core_news_sm',
    'ro_core_news_sm'
]

# Runtime hooks
runtime_hooks = [
    'wl_runtime_hook_pymorphy2.py'
]

# Exclusions
if platform.system() in ['Windows', 'Linux']:
    excludes = []
elif platform.system() == 'Darwin':
    excludes = [
        'PIL'
    ]

# Icons
if platform.system() in ['Windows', 'Linux']:
    icon = 'src/imgs/wl_icon.ico'
elif platform.system() == 'Darwin':
    icon = 'src/imgs/wl_icon.icns'

a = Analysis(
    ['src/wl_main.py'],
    pathex = [],
    binaries = [],
    datas = datas,
    hiddenimports = hiddenimports,
    hookspath = [],
    runtime_hooks = runtime_hooks,
    excludes = excludes,
    win_no_prefer_redirects = False,
    win_private_assemblies = False,
    cipher = block_cipher,
    noarchive = False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher = block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries = True,
    name = 'Wordless',
    debug = False,
    bootloader_ignore_signals = False,
    strip = False,
    upx = True,
    console = True,
    icon = icon
)

# Collect data files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip = False,
    upx = True,
    name = 'Wordless'
)

# Bundle application on macOS
if platform.system() == 'Darwin':
    app = BUNDLE(
        exe,
        name = 'Wordless.app',
        icon = icon,
        bundle_identifier = None,
        info_plist = {
           'NSHighResolutionCapable': 'True'
        }
    )
