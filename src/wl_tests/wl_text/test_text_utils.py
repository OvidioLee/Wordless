#
# Wordless: Tests - Text - Text Utilities
#
# Copyright (C) 2018-2021  Ye Lei (叶磊)
#
# This source file is licensed under GNU GPLv3.
# For details, see: https://github.com/BLKSerene/Wordless/blob/master/LICENSE.txt
#
# All other rights reserved.
#

import sys

sys.path.append('.')

from wl_tests import wl_test_init
from wl_text import wl_text_utils

main = wl_test_init.Wl_Test_Main()

SENTENCE_SRP_CYRL = 'Српски језик припада словенској групи језика породице индоевропских језика.[12]'
SENTENCE_SRP_LATN = 'Srpski jezik pripada slovenskoj grupi jezika porodice indoevropskih jezika.[12]'

def test_to_sections():
    tokens = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    token_sections = wl_text_utils.to_sections(tokens, num_sections = 5)

    assert token_sections == [[1, 2, 3], [4, 5, 6], [7, 8], [9, 10], [11, 12]]

def test_to_sections_unequal():
    tokens = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    token_sections = wl_text_utils.to_sections_unequal(tokens, section_size = 5)

    assert token_sections == [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12]]

def test_srp_cyrl_to_latn():
    tokens_srp_cyrl = SENTENCE_SRP_CYRL.split()

    assert ' '.join(wl_text_utils.to_srp_latn(tokens_srp_cyrl)) == SENTENCE_SRP_LATN

def test_srp_latn_to_cyrl():
    tokens_srp_latn = SENTENCE_SRP_LATN.split()

    assert ' '.join(wl_text_utils.to_srp_cyrl(tokens_srp_latn)) == SENTENCE_SRP_CYRL
