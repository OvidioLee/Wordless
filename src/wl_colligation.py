#
# Wordless: Colligation
#
# Copyright (C) 2018-2021  Ye Lei (叶磊)
#
# This source file is licensed under GNU GPLv3.
# For details, see: https://github.com/BLKSerene/Wordless/blob/master/LICENSE.txt
#
# All other rights reserved.
#

import collections
import copy
import operator
import re
import time

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import nltk
import numpy

from wl_checking import wl_checking_file
from wl_dialogs import wl_dialog_misc, wl_msg_box
from wl_figs import wl_fig, wl_fig_freq, wl_fig_stat
from wl_measures import wl_measures_statistical_significance
from wl_text import wl_matching, wl_pos_tagging, wl_text, wl_token_processing, wl_word_detokenization
from wl_utils import wl_misc, wl_sorting, wl_threading
from wl_widgets import wl_layout, wl_msg, wl_table, wl_widgets

class Wl_Table_Colligation(wl_table.Wl_Table_Data_Filter_Search):
    def __init__(self, parent):
        super().__init__(
            parent,
            tab = 'colligation',
            headers = [
                parent.tr('Rank'),
                parent.tr('Node'),
                parent.tr('Collocate'),
                parent.tr('Number of\nFiles Found'),
                parent.tr('Number of\nFiles Found %')
            ],
            headers_int = [
                parent.tr('Rank'),
                parent.tr('Number of\nFiles Found')
            ],
            headers_pct = [
                parent.tr('Number of\nFiles Found %')
            ],
            sorting_enabled = True
        )

        self.name = 'colligation'

        self.button_generate_table = QPushButton(self.tr('Generate Table'), self)
        self.button_generate_fig = QPushButton(self.tr('Generate Figure'), self)

        self.button_generate_table.clicked.connect(lambda: generate_table(self.main, self))
        self.button_generate_fig.clicked.connect(lambda: generate_fig(self.main))

    def toggle_breakdown(self):
        settings = self.main.settings_custom['colligation']['table_settings']

        self.setUpdatesEnabled(False)

        for col in self.cols_breakdown | self.cols_breakdown_position:
            if col in self.cols_breakdown and col in self.cols_breakdown_position:
                if settings['show_breakdown_file'] and settings['show_breakdown_position']:
                    self.showColumn(col)
                else:
                    self.hideColumn(col)
            elif col in self.cols_breakdown:
                if settings['show_breakdown_file']:
                    self.showColumn(col)
                else:
                    self.hideColumn(col)
            elif col in self.cols_breakdown_position:
                if settings['show_breakdown_position']:
                    self.showColumn(col)
                else:
                    self.hideColumn(col)

        self.setUpdatesEnabled(True)

    def clear_table(self, count = 1):
        super().clear_table(count)

        self.cols_breakdown_position = set()

class Wrapper_Colligation(wl_layout.Wl_Wrapper):
    def __init__(self, main):
        super().__init__(main)

        # Table
        self.table_colligation = Wl_Table_Colligation(self)

        layout_results = wl_layout.Wl_Layout()
        layout_results.addWidget(self.table_colligation.label_number_results, 0, 0)
        layout_results.addWidget(self.table_colligation.button_results_filter, 0, 2)
        layout_results.addWidget(self.table_colligation.button_results_search, 0, 3)

        layout_results.setColumnStretch(1, 1)

        self.wrapper_table.layout().addLayout(layout_results, 0, 0, 1, 5)
        self.wrapper_table.layout().addWidget(self.table_colligation, 1, 0, 1, 5)
        self.wrapper_table.layout().addWidget(self.table_colligation.button_generate_table, 2, 0)
        self.wrapper_table.layout().addWidget(self.table_colligation.button_generate_fig, 2, 1)
        self.wrapper_table.layout().addWidget(self.table_colligation.button_export_selected, 2, 2)
        self.wrapper_table.layout().addWidget(self.table_colligation.button_export_all, 2, 3)
        self.wrapper_table.layout().addWidget(self.table_colligation.button_clear, 2, 4)

        # Token Settings
        self.group_box_token_settings = QGroupBox(self.tr('Token Settings'), self)

        (self.checkbox_words,
         self.checkbox_lowercase,
         self.checkbox_uppercase,
         self.checkbox_title_case,
         self.checkbox_nums,
         self.checkbox_puncs,

         self.checkbox_treat_as_lowercase,
         self.checkbox_lemmatize_tokens,
         self.checkbox_filter_stop_words,

         self.token_checkbox_ignore_tags,
         self.checkbox_use_tags) = wl_widgets.wl_widgets_token_settings(self)

        self.checkbox_words.stateChanged.connect(self.token_settings_changed)
        self.checkbox_lowercase.stateChanged.connect(self.token_settings_changed)
        self.checkbox_uppercase.stateChanged.connect(self.token_settings_changed)
        self.checkbox_title_case.stateChanged.connect(self.token_settings_changed)
        self.checkbox_nums.stateChanged.connect(self.token_settings_changed)
        self.checkbox_puncs.stateChanged.connect(self.token_settings_changed)

        self.checkbox_treat_as_lowercase.stateChanged.connect(self.token_settings_changed)
        self.checkbox_lemmatize_tokens.stateChanged.connect(self.token_settings_changed)
        self.checkbox_filter_stop_words.stateChanged.connect(self.token_settings_changed)

        self.token_checkbox_ignore_tags.stateChanged.connect(self.token_settings_changed)
        self.checkbox_use_tags.stateChanged.connect(self.token_settings_changed)

        self.group_box_token_settings.setLayout(wl_layout.Wl_Layout())
        self.group_box_token_settings.layout().addWidget(self.checkbox_words, 0, 0)
        self.group_box_token_settings.layout().addWidget(self.checkbox_lowercase, 0, 1)
        self.group_box_token_settings.layout().addWidget(self.checkbox_uppercase, 1, 0)
        self.group_box_token_settings.layout().addWidget(self.checkbox_title_case, 1, 1)
        self.group_box_token_settings.layout().addWidget(self.checkbox_nums, 2, 0)
        self.group_box_token_settings.layout().addWidget(self.checkbox_puncs, 2, 1)

        self.group_box_token_settings.layout().addWidget(wl_layout.Wl_Separator(self), 3, 0, 1, 2)

        self.group_box_token_settings.layout().addWidget(self.checkbox_treat_as_lowercase, 4, 0, 1, 2)
        self.group_box_token_settings.layout().addWidget(self.checkbox_lemmatize_tokens, 5, 0, 1, 2)
        self.group_box_token_settings.layout().addWidget(self.checkbox_filter_stop_words, 6, 0, 1, 2)

        self.group_box_token_settings.layout().addWidget(wl_layout.Wl_Separator(self), 7, 0, 1, 2)

        self.group_box_token_settings.layout().addWidget(self.token_checkbox_ignore_tags, 8, 0)
        self.group_box_token_settings.layout().addWidget(self.checkbox_use_tags, 8, 1)

        # Search Settings
        self.group_box_search_settings = QGroupBox(self.tr('Search Settings'), self)

        (self.label_search_term,
         self.checkbox_multi_search_mode,

         self.stacked_widget_search_term,
         self.line_edit_search_term,
         self.list_search_terms,

         self.label_separator,

         self.checkbox_ignore_case,
         self.checkbox_match_inflected_forms,
         self.checkbox_match_whole_words,
         self.checkbox_use_regex,

         self.search_checkbox_ignore_tags,
         self.checkbox_match_tags) = wl_widgets.wl_widgets_search_settings(
            self,
            tab = 'colligation'
        )

        (self.label_context_settings,
         self.button_context_settings) = wl_widgets.wl_widgets_context_settings(
            self,
            tab = 'colligation'
        )

        self.group_box_search_settings.setCheckable(True)

        self.group_box_search_settings.toggled.connect(self.search_settings_changed)

        self.checkbox_multi_search_mode.stateChanged.connect(self.search_settings_changed)
        self.line_edit_search_term.textChanged.connect(self.search_settings_changed)
        self.line_edit_search_term.returnPressed.connect(self.table_colligation.button_generate_table.click)
        self.list_search_terms.itemChanged.connect(self.search_settings_changed)

        self.checkbox_ignore_case.stateChanged.connect(self.search_settings_changed)
        self.checkbox_match_inflected_forms.stateChanged.connect(self.search_settings_changed)
        self.checkbox_match_whole_words.stateChanged.connect(self.search_settings_changed)
        self.checkbox_use_regex.stateChanged.connect(self.search_settings_changed)

        self.search_checkbox_ignore_tags.stateChanged.connect(self.search_settings_changed)
        self.checkbox_match_tags.stateChanged.connect(self.search_settings_changed)

        layout_context_settings = wl_layout.Wl_Layout()
        layout_context_settings.addWidget(self.label_context_settings, 0, 0)
        layout_context_settings.addWidget(self.button_context_settings, 0, 1)

        layout_context_settings.setColumnStretch(1, 1)

        self.group_box_search_settings.setLayout(wl_layout.Wl_Layout())
        self.group_box_search_settings.layout().addWidget(self.label_search_term, 0, 0)
        self.group_box_search_settings.layout().addWidget(self.checkbox_multi_search_mode, 0, 1, Qt.AlignRight)
        self.group_box_search_settings.layout().addWidget(self.stacked_widget_search_term, 1, 0, 1, 2)
        self.group_box_search_settings.layout().addWidget(self.label_separator, 2, 0, 1, 2)

        self.group_box_search_settings.layout().addWidget(self.checkbox_ignore_case, 3, 0, 1, 2)
        self.group_box_search_settings.layout().addWidget(self.checkbox_match_inflected_forms, 4, 0, 1, 2)
        self.group_box_search_settings.layout().addWidget(self.checkbox_match_whole_words, 5, 0, 1, 2)
        self.group_box_search_settings.layout().addWidget(self.checkbox_use_regex, 6, 0, 1, 2)

        self.group_box_search_settings.layout().addWidget(self.search_checkbox_ignore_tags, 7, 0, 1, 2)
        self.group_box_search_settings.layout().addWidget(self.checkbox_match_tags, 8, 0, 1, 2)

        self.group_box_search_settings.layout().addWidget(wl_layout.Wl_Separator(self), 9, 0, 1, 2)

        self.group_box_search_settings.layout().addLayout(layout_context_settings, 10, 0, 1, 2)

        # Generation Settings
        self.group_box_generation_settings = QGroupBox(self.tr('Generation Settings'))

        self.label_window = QLabel(self.tr('Collocational Window:'), self)
        (self.checkbox_window_sync,
         self.label_window_left,
         self.spin_box_window_left,
         self.label_window_right,
         self.spin_box_window_right) = wl_widgets.wl_widgets_window(self)

        (self.label_test_significance,
         self.combo_box_test_significance) = wl_widgets.wl_widgets_test_significance(self)
        (self.label_measure_effect_size,
         self.combo_box_measure_effect_size) = wl_widgets.wl_widgets_measure_effect_size(self)

        (self.label_settings_measures,
         self.button_settings_measures) = wl_widgets.wl_widgets_settings_measures(
            self,
            tab = self.tr('Statistical Significance')
        )

        self.combo_box_test_significance.addItems(list(self.main.settings_global['tests_significance']['collocation'].keys()))
        self.combo_box_measure_effect_size.addItems(list(self.main.settings_global['measures_effect_size']['collocation'].keys()))

        self.checkbox_window_sync.stateChanged.connect(self.generation_settings_changed)
        self.spin_box_window_left.valueChanged.connect(self.generation_settings_changed)
        self.spin_box_window_right.valueChanged.connect(self.generation_settings_changed)

        self.combo_box_test_significance.currentTextChanged.connect(self.generation_settings_changed)
        self.combo_box_measure_effect_size.currentTextChanged.connect(self.generation_settings_changed)

        layout_settings_measures = wl_layout.Wl_Layout()
        layout_settings_measures.addWidget(self.label_settings_measures, 0, 0)
        layout_settings_measures.addWidget(self.button_settings_measures, 0, 1)

        layout_settings_measures.setColumnStretch(1, 1)

        self.group_box_generation_settings.setLayout(wl_layout.Wl_Layout())
        self.group_box_generation_settings.layout().addWidget(self.label_window, 0, 0, 1, 3)
        self.group_box_generation_settings.layout().addWidget(self.checkbox_window_sync, 0, 3, Qt.AlignRight)
        self.group_box_generation_settings.layout().addWidget(self.label_window_left, 1, 0)
        self.group_box_generation_settings.layout().addWidget(self.spin_box_window_left, 1, 1)
        self.group_box_generation_settings.layout().addWidget(self.label_window_right, 1, 2)
        self.group_box_generation_settings.layout().addWidget(self.spin_box_window_right, 1, 3)

        self.group_box_generation_settings.layout().addWidget(wl_layout.Wl_Separator(self), 2, 0, 1, 4)

        self.group_box_generation_settings.layout().addWidget(self.label_test_significance, 3, 0, 1, 4)
        self.group_box_generation_settings.layout().addWidget(self.combo_box_test_significance, 4, 0, 1, 4)
        self.group_box_generation_settings.layout().addWidget(self.label_measure_effect_size, 5, 0, 1, 4)
        self.group_box_generation_settings.layout().addWidget(self.combo_box_measure_effect_size, 6, 0, 1, 4)

        self.group_box_generation_settings.layout().addWidget(wl_layout.Wl_Separator(self), 7, 0, 1, 4)

        self.group_box_generation_settings.layout().addLayout(layout_settings_measures, 8, 0, 1, 4)

        self.group_box_generation_settings.layout().setColumnStretch(1, 1)
        self.group_box_generation_settings.layout().setColumnStretch(3, 1)

        # Table Settings
        self.group_box_table_settings = QGroupBox(self.tr('Table Settings'))

        (self.checkbox_show_pct,
         self.checkbox_show_cumulative,
         self.checkbox_show_breakdown_file) = wl_widgets.wl_widgets_table_settings(
            self,
            table = self.table_colligation
        )

        self.checkbox_show_breakdown_file.setText(self.tr('Show breakdown by file'))
        self.checkbox_show_breakdown_position = QCheckBox(self.tr('Show breakdown by span position'), self)

        self.checkbox_show_pct.stateChanged.connect(self.table_settings_changed)
        self.checkbox_show_cumulative.stateChanged.connect(self.table_settings_changed)
        self.checkbox_show_breakdown_position.stateChanged.connect(self.table_settings_changed)
        self.checkbox_show_breakdown_position.stateChanged.connect(self.table_colligation.toggle_breakdown)
        self.checkbox_show_breakdown_file.stateChanged.connect(self.table_settings_changed)
        self.checkbox_show_breakdown_file.stateChanged.connect(self.table_colligation.toggle_breakdown)

        self.group_box_table_settings.setLayout(wl_layout.Wl_Layout())
        self.group_box_table_settings.layout().addWidget(self.checkbox_show_pct, 0, 0)
        self.group_box_table_settings.layout().addWidget(self.checkbox_show_cumulative, 1, 0)
        self.group_box_table_settings.layout().addWidget(self.checkbox_show_breakdown_position, 2, 0)
        self.group_box_table_settings.layout().addWidget(self.checkbox_show_breakdown_file, 3, 0)

        # Figure Settings
        self.group_box_fig_settings = QGroupBox(self.tr('Figure Settings'), self)

        (self.label_graph_type,
         self.combo_box_graph_type,
         self.label_use_file,
         self.combo_box_use_file,
         self.label_use_data,
         self.combo_box_use_data,

         self.checkbox_use_pct,
         self.checkbox_use_cumulative) = wl_widgets.wl_widgets_fig_settings(
            self,
            collocation = True
        )

        self.label_rank = QLabel(self.tr('Rank:'), self)
        (self.label_rank_min,
         self.spin_box_rank_min,
         self.checkbox_rank_min_no_limit,
         self.label_rank_max,
         self.spin_box_rank_max,
         self.checkbox_rank_max_no_limit) = wl_widgets.wl_widgets_filter(
            self,
            filter_min = 1,
            filter_max = 100000
        )

        self.combo_box_graph_type.currentTextChanged.connect(self.fig_settings_changed)
        self.combo_box_use_file.currentTextChanged.connect(self.fig_settings_changed)
        self.combo_box_use_data.currentTextChanged.connect(self.fig_settings_changed)
        self.checkbox_use_pct.stateChanged.connect(self.fig_settings_changed)
        self.checkbox_use_cumulative.stateChanged.connect(self.fig_settings_changed)

        self.spin_box_rank_min.valueChanged.connect(self.fig_settings_changed)
        self.checkbox_rank_min_no_limit.stateChanged.connect(self.fig_settings_changed)
        self.spin_box_rank_max.valueChanged.connect(self.fig_settings_changed)
        self.checkbox_rank_max_no_limit.stateChanged.connect(self.fig_settings_changed)

        layout_fig_settings_combo_boxes = wl_layout.Wl_Layout()
        layout_fig_settings_combo_boxes.addWidget(self.label_graph_type, 0, 0)
        layout_fig_settings_combo_boxes.addWidget(self.combo_box_graph_type, 0, 1)
        layout_fig_settings_combo_boxes.addWidget(self.label_use_file, 1, 0)
        layout_fig_settings_combo_boxes.addWidget(self.combo_box_use_file, 1, 1)
        layout_fig_settings_combo_boxes.addWidget(self.label_use_data, 2, 0)
        layout_fig_settings_combo_boxes.addWidget(self.combo_box_use_data, 2, 1)

        layout_fig_settings_combo_boxes.setColumnStretch(1, 1)

        self.group_box_fig_settings.setLayout(wl_layout.Wl_Layout())
        self.group_box_fig_settings.layout().addLayout(layout_fig_settings_combo_boxes, 0, 0, 1, 3)
        self.group_box_fig_settings.layout().addWidget(self.checkbox_use_pct, 1, 0, 1, 3)
        self.group_box_fig_settings.layout().addWidget(self.checkbox_use_cumulative, 2, 0, 1, 3)
        
        self.group_box_fig_settings.layout().addWidget(wl_layout.Wl_Separator(self), 3, 0, 1, 3)

        self.group_box_fig_settings.layout().addWidget(self.label_rank, 4, 0, 1, 3)
        self.group_box_fig_settings.layout().addWidget(self.label_rank_min, 5, 0)
        self.group_box_fig_settings.layout().addWidget(self.spin_box_rank_min, 5, 1)
        self.group_box_fig_settings.layout().addWidget(self.checkbox_rank_min_no_limit, 5, 2)
        self.group_box_fig_settings.layout().addWidget(self.label_rank_max, 6, 0)
        self.group_box_fig_settings.layout().addWidget(self.spin_box_rank_max, 6, 1)
        self.group_box_fig_settings.layout().addWidget(self.checkbox_rank_max_no_limit, 6, 2)

        self.group_box_fig_settings.layout().setColumnStretch(1, 1)

        self.wrapper_settings.layout().addWidget(self.group_box_token_settings, 0, 0)
        self.wrapper_settings.layout().addWidget(self.group_box_search_settings, 1, 0)
        self.wrapper_settings.layout().addWidget(self.group_box_generation_settings, 2, 0)
        self.wrapper_settings.layout().addWidget(self.group_box_table_settings, 3, 0)
        self.wrapper_settings.layout().addWidget(self.group_box_fig_settings, 4, 0)

        self.wrapper_settings.layout().setRowStretch(5, 1)

        self.load_settings()

    def load_settings(self, defaults = False):
        if defaults:
            settings = copy.deepcopy(self.main.settings_default['colligation'])
        else:
            settings = copy.deepcopy(self.main.settings_custom['colligation'])

        # Token Settings
        self.checkbox_words.setChecked(settings['token_settings']['words'])
        self.checkbox_lowercase.setChecked(settings['token_settings']['lowercase'])
        self.checkbox_uppercase.setChecked(settings['token_settings']['uppercase'])
        self.checkbox_title_case.setChecked(settings['token_settings']['title_case'])
        self.checkbox_nums.setChecked(settings['token_settings']['nums'])
        self.checkbox_puncs.setChecked(settings['token_settings']['puncs'])

        self.checkbox_treat_as_lowercase.setChecked(settings['token_settings']['treat_as_lowercase'])
        self.checkbox_lemmatize_tokens.setChecked(settings['token_settings']['lemmatize_tokens'])
        self.checkbox_filter_stop_words.setChecked(settings['token_settings']['filter_stop_words'])

        self.token_checkbox_ignore_tags.setChecked(settings['token_settings']['ignore_tags'])
        self.checkbox_use_tags.setChecked(settings['token_settings']['use_tags'])

        # Search Settings
        self.group_box_search_settings.setChecked(settings['search_settings']['search_settings'])

        self.checkbox_multi_search_mode.setChecked(settings['search_settings']['multi_search_mode'])

        if not defaults:
            self.line_edit_search_term.setText(settings['search_settings']['search_term'])
            self.list_search_terms.load_items(settings['search_settings']['search_terms'])

        self.checkbox_ignore_case.setChecked(settings['search_settings']['ignore_case'])
        self.checkbox_match_inflected_forms.setChecked(settings['search_settings']['match_inflected_forms'])
        self.checkbox_match_whole_words.setChecked(settings['search_settings']['match_whole_words'])
        self.checkbox_use_regex.setChecked(settings['search_settings']['use_regex'])

        self.search_checkbox_ignore_tags.setChecked(settings['search_settings']['ignore_tags'])
        self.checkbox_match_tags.setChecked(settings['search_settings']['match_tags'])

        # Context Settings
        if defaults:
            self.main.wl_context_settings_colligation.load_settings(defaults = True)

        # Generation Settings
        self.checkbox_window_sync.setChecked(settings['generation_settings']['window_sync'])

        if settings['generation_settings']['window_left'] < 0:
            self.spin_box_window_left.setPrefix('L')
            self.spin_box_window_left.setValue(-settings['generation_settings']['window_left'])
        else:
            self.spin_box_window_left.setPrefix('R')
            self.spin_box_window_left.setValue(settings['generation_settings']['window_left'])

        if settings['generation_settings']['window_right'] < 0:
            self.spin_box_window_right.setPrefix('L')
            self.spin_box_window_right.setValue(-settings['generation_settings']['window_right'])
        else:
            self.spin_box_window_right.setPrefix('R')
            self.spin_box_window_right.setValue(settings['generation_settings']['window_right'])

        self.combo_box_test_significance.setCurrentText(settings['generation_settings']['test_significance'])
        self.combo_box_measure_effect_size.setCurrentText(settings['generation_settings']['measure_effect_size'])

        # Table Settings
        self.checkbox_show_pct.setChecked(settings['table_settings']['show_pct'])
        self.checkbox_show_cumulative.setChecked(settings['table_settings']['show_cumulative'])
        self.checkbox_show_breakdown_position.setChecked(settings['table_settings']['show_breakdown_position'])
        self.checkbox_show_breakdown_file.setChecked(settings['table_settings']['show_breakdown_file'])

        # Figure Settings
        self.combo_box_graph_type.setCurrentText(settings['fig_settings']['graph_type'])
        self.combo_box_use_file.setCurrentText(settings['fig_settings']['use_file'])
        self.combo_box_use_data.setCurrentText(settings['fig_settings']['use_data'])
        self.checkbox_use_pct.setChecked(settings['fig_settings']['use_pct'])
        self.checkbox_use_cumulative.setChecked(settings['fig_settings']['use_cumulative'])

        self.spin_box_rank_min.setValue(settings['fig_settings']['rank_min'])
        self.checkbox_rank_min_no_limit.setChecked(settings['fig_settings']['rank_min_no_limit'])
        self.spin_box_rank_max.setValue(settings['fig_settings']['rank_max'])
        self.checkbox_rank_max_no_limit.setChecked(settings['fig_settings']['rank_max_no_limit'])

        self.token_settings_changed()
        self.search_settings_changed()
        self.generation_settings_changed()
        self.table_settings_changed()
        self.fig_settings_changed()

    def token_settings_changed(self):
        settings = self.main.settings_custom['colligation']['token_settings']

        settings['words'] = self.checkbox_words.isChecked()
        settings['lowercase'] = self.checkbox_lowercase.isChecked()
        settings['uppercase'] = self.checkbox_uppercase.isChecked()
        settings['title_case'] = self.checkbox_title_case.isChecked()
        settings['nums'] = self.checkbox_nums.isChecked()
        settings['puncs'] = self.checkbox_puncs.isChecked()

        settings['treat_as_lowercase'] = self.checkbox_treat_as_lowercase.isChecked()
        settings['lemmatize_tokens'] = self.checkbox_lemmatize_tokens.isChecked()
        settings['filter_stop_words'] = self.checkbox_filter_stop_words.isChecked()

        settings['ignore_tags'] = self.token_checkbox_ignore_tags.isChecked()
        settings['use_tags'] = self.checkbox_use_tags.isChecked()

        # Check if searching is enabled
        if self.group_box_search_settings.isChecked():
            self.checkbox_match_tags.token_settings_changed()
        else:
            self.group_box_search_settings.setChecked(True)

            self.checkbox_match_tags.token_settings_changed()

            self.group_box_search_settings.setChecked(False)
        
        self.main.wl_context_settings_colligation.token_settings_changed()

    def search_settings_changed(self):
        settings = self.main.settings_custom['colligation']['search_settings']

        settings['search_settings'] = self.group_box_search_settings.isChecked()

        settings['multi_search_mode'] = self.checkbox_multi_search_mode.isChecked()
        settings['search_term'] = self.line_edit_search_term.text()
        settings['search_terms'] = self.list_search_terms.get_items()

        settings['ignore_case'] = self.checkbox_ignore_case.isChecked()
        settings['match_inflected_forms'] = self.checkbox_match_inflected_forms.isChecked()
        settings['match_whole_words'] = self.checkbox_match_whole_words.isChecked()
        settings['use_regex'] = self.checkbox_use_regex.isChecked()

        settings['ignore_tags'] = self.search_checkbox_ignore_tags.isChecked()
        settings['match_tags'] = self.checkbox_match_tags.isChecked()

    def generation_settings_changed(self):
        settings = self.main.settings_custom['colligation']['generation_settings']

        settings['window_sync'] = self.checkbox_window_sync.isChecked()

        if self.spin_box_window_left.prefix() == 'L':
            settings['window_left'] = - self.spin_box_window_left.value()
        else:
            settings['window_left'] = self.spin_box_window_left.value()
            
        if self.spin_box_window_right.prefix() == 'L':
            settings['window_right'] = - self.spin_box_window_right.value()
        else:
            settings['window_right'] = self.spin_box_window_right.value()

        settings['test_significance'] = self.combo_box_test_significance.currentText()
        settings['measure_effect_size'] = self.combo_box_measure_effect_size.currentText()

        # Use Data
        use_data_old = self.main.settings_custom['colligation']['fig_settings']['use_data']

        text_test_significance = settings['test_significance']
        text_measure_effect_size = settings['measure_effect_size']

        self.combo_box_use_data.clear()

        for i in range(settings['window_left'], settings['window_right'] + 1):
            if i < 0:
                self.combo_box_use_data.addItem(f'L{-i}')
            elif i > 0:
                self.combo_box_use_data.addItem(f'R{i}')

        self.combo_box_use_data.addItem(self.tr('Frequency'))

        self.combo_box_use_data.addItems(
            [col
             for col in self.main.settings_global['tests_significance']['collocation'][text_test_significance]['cols']
             if col]
        )
        self.combo_box_use_data.addItem(self.main.settings_global['measures_effect_size']['collocation'][text_measure_effect_size]['col'])

        if self.combo_box_use_data.findText(use_data_old) > -1:
            self.combo_box_use_data.setCurrentText(use_data_old)
        else:
            self.combo_box_use_data.setCurrentText(self.main.settings_default['colligation']['fig_settings']['use_data'])

    def table_settings_changed(self):
        settings = self.main.settings_custom['colligation']['table_settings']

        settings['show_pct'] = self.checkbox_show_pct.isChecked()
        settings['show_cumulative'] = self.checkbox_show_cumulative.isChecked()
        settings['show_breakdown_position'] = self.checkbox_show_breakdown_position.isChecked()
        settings['show_breakdown_file'] = self.checkbox_show_breakdown_file.isChecked()

    def fig_settings_changed(self):
        settings = self.main.settings_custom['colligation']['fig_settings']

        settings['graph_type'] = self.combo_box_graph_type.currentText()
        settings['use_file'] = self.combo_box_use_file.currentText()
        settings['use_data'] = self.combo_box_use_data.currentText()
        settings['use_pct'] = self.checkbox_use_pct.isChecked()
        settings['use_cumulative'] = self.checkbox_use_cumulative.isChecked()

        settings['rank_min'] = self.spin_box_rank_min.value()
        settings['rank_min_no_limit'] = self.checkbox_rank_min_no_limit.isChecked()
        settings['rank_max'] = self.spin_box_rank_max.value()
        settings['rank_max_no_limit'] = self.checkbox_rank_max_no_limit.isChecked()

class Wl_Worker_Colligation(wl_threading.Wl_Worker):
    worker_done = pyqtSignal(dict, dict, dict)

    def __init__(self, main, dialog_progress, update_gui):
        super().__init__(main, dialog_progress, update_gui)

        self.colligations_freqs_files = []
        self.colligations_stats_files = []
        self.nodes_text = {}

    def run(self):
        texts = []
        colligations_freqs_files_all = []

        settings = self.main.settings_custom['colligation']
        files = self.main.wl_files.get_selected_files()

        window_left = settings['generation_settings']['window_left']
        window_right = settings['generation_settings']['window_right']

        # Calculate window size
        if window_left < 0 and window_right > 0:
            window_size = window_right - window_left
        else:
            window_size = window_right - window_left + 1

        # Frequency
        for i, file in enumerate(files):
            colligations_freqs_file = {}
            colligations_freqs_file_all = {}

            text = wl_text.Wl_Text(self.main, file)

            # Generate POS tags for files that are not POS tagged already
            if file['tagged'] == 'No':
                tokens_tagged = wl_pos_tagging.wl_pos_tag(self.main, text.tokens_flat, text.lang)

                text.tags = [[(f'_{tag}' if tag else '')] for _, tag in tokens_tagged]

            # Modify text types
            if file['tagged'] == 'No':
                text.tagged = 'Yes'

            text = wl_token_processing.wl_process_tokens_colligation(
                text,
                token_settings = settings['token_settings']
            )

            tokens = text.tokens_flat

            search_terms = wl_matching.match_search_terms(
                self.main, tokens,
                lang = text.lang,
                tokenized = text.tokenized,
                tagged = text.tagged,
                token_settings = settings['token_settings'],
                search_settings = settings['search_settings']
            )

            (search_terms_inclusion,
             search_terms_exclusion) = wl_matching.match_search_terms_context(
                self.main, tokens,
                lang = text.lang,
                tokenized = text.tokenized,
                tagged = text.tagged,
                token_settings = settings['token_settings'],
                context_settings = settings['context_settings']
            )

            if search_terms:
                len_search_term_min = min([len(search_term) for search_term in search_terms])
                len_search_term_max = max([len(search_term) for search_term in search_terms])
            else:
                len_search_term_min = 1
                len_search_term_max = 1

            for ngram_size in range(len_search_term_min, len_search_term_max + 1):
                if ngram_size not in colligations_freqs_files_all:
                    colligations_freqs_file_all[ngram_size] = collections.Counter()

                for i, ngram in enumerate(nltk.ngrams(tokens, ngram_size)):
                    # Extract collocates
                    if window_left < 0 and window_right > 0:
                        for j, collocate in enumerate(reversed(text.tags[max(0, i + window_left) : i])):
                            if wl_matching.check_context(
                                i, tokens,
                                context_settings = settings['context_settings'],
                                search_terms_inclusion = search_terms_inclusion,
                                search_terms_exclusion = search_terms_exclusion
                            ):
                                if (ngram, collocate) not in colligations_freqs_file:
                                    colligations_freqs_file[(ngram, collocate)] = [0] * window_size

                                colligations_freqs_file[(ngram, collocate)][abs(window_left) - 1 - j] += 1

                            colligations_freqs_file_all[ngram_size][(ngram, collocate)] += 1

                        for j, collocate in enumerate(text.tags[i + ngram_size : i + ngram_size + window_right]):
                            if wl_matching.check_context(
                                i, tokens,
                                context_settings = settings['context_settings'],
                                search_terms_inclusion = search_terms_inclusion,
                                search_terms_exclusion = search_terms_exclusion
                            ):
                                if (ngram, collocate) not in colligations_freqs_file:
                                    colligations_freqs_file[(ngram, collocate)] = [0] * window_size

                                colligations_freqs_file[(ngram, collocate)][abs(window_left) + j] += 1

                            colligations_freqs_file_all[ngram_size][(ngram, collocate)] += 1
                    elif window_left < 0 and window_right < 0:
                        for j, collocate in enumerate(reversed(text.tags[max(0, i + window_left) : max(0, i + window_right + 1)])):
                            if wl_matching.check_context(
                                i, tokens,
                                context_settings = settings['context_settings'],
                                search_terms_inclusion = search_terms_inclusion,
                                search_terms_exclusion = search_terms_exclusion
                            ):
                                if (ngram, collocate) not in colligations_freqs_file:
                                    colligations_freqs_file[(ngram, collocate)] = [0] * window_size

                                colligations_freqs_file[(ngram, collocate)][window_size - 1 - j] += 1

                            colligations_freqs_file_all[ngram_size][(ngram, collocate)] += 1
                    elif window_left > 0 and window_right > 0:
                        for j, collocate in enumerate(text.tags[i + ngram_size + window_left - 1: i + ngram_size + window_right]):
                            if wl_matching.check_context(
                                i, tokens,
                                context_settings = settings['context_settings'],
                                search_terms_inclusion = search_terms_inclusion,
                                search_terms_exclusion = search_terms_exclusion
                            ):
                                if (ngram, collocate) not in colligations_freqs_file:
                                    colligations_freqs_file[(ngram, collocate)] = [0] * window_size

                                colligations_freqs_file[(ngram, collocate)][j] += 1

                            colligations_freqs_file_all[ngram_size][(ngram, collocate)] += 1

            colligations_freqs_file = {(ngram, collocate): freqs
                                     for (ngram, collocate), freqs in colligations_freqs_file.items()
                                     if all(ngram) and collocate}

            # Filter search terms
            if settings['search_settings']['search_settings']:
                colligations_freqs_file_filtered = {}

                for search_term in search_terms:
                    len_search_term = len(search_term)

                    for (node, collocate), freqs in colligations_freqs_file.items():
                        for ngram in nltk.ngrams(node, len_search_term):
                            if ngram == search_term:
                                colligations_freqs_file_filtered[(node, collocate)] = freqs

                self.colligations_freqs_files.append(colligations_freqs_file_filtered)
            else:
                self.colligations_freqs_files.append(colligations_freqs_file)

            # Frequency (All)
            colligations_freqs_files_all.append(colligations_freqs_file_all)

            # Nodes Text
            if settings['token_settings']['use_tags']:
                for (node, collocate) in colligations_freqs_file:
                    self.nodes_text[node] = wl_word_detokenization.wl_word_detokenize(self.main, node, text.lang)
            else:
                for (node, collocate) in colligations_freqs_file:
                    self.nodes_text[node] = ' '.join(node)

            texts.append(text)

        # Total
        if len(files) > 1:
            colligations_freqs_total = {}
            colligations_freqs_total_all = {}

            # Frequency
            for colligations_freqs_file in self.colligations_freqs_files:
                for colligation, freqs in colligations_freqs_file.items():
                    if colligation not in colligations_freqs_total:
                        colligations_freqs_total[colligation] = freqs
                    else:
                        colligations_freqs_total[colligation] = list(map(operator.add, colligations_freqs_total[colligation], freqs))
            # Frequency (All)
            for colligations_freqs_file_all in colligations_freqs_files_all:
                for ngram_size, colligations_freqs in colligations_freqs_file_all.items():
                    if ngram_size not in colligations_freqs_total_all:
                        colligations_freqs_total_all[ngram_size] = collections.Counter()

                    colligations_freqs_total_all[ngram_size] += colligations_freqs

            self.colligations_freqs_files.append(colligations_freqs_total)
            colligations_freqs_files_all.append(colligations_freqs_total_all)

            texts.append(wl_text.Wl_Text_Blank())

        self.progress_updated.emit(self.tr('Processing data ...'))

        # Statistiscal Significance & Effect Size
        text_test_significance = settings['generation_settings']['test_significance']
        text_measure_effect_size = settings['generation_settings']['measure_effect_size']

        test_significance = self.main.settings_global['tests_significance']['collocation'][text_test_significance]['func']
        measure_effect_size = self.main.settings_global['measures_effect_size']['collocation'][text_measure_effect_size]['func']

        colligations_total = self.colligations_freqs_files[-1].keys()

        for text, colligations_freqs_file, colligations_freqs_file_all in zip(texts,
                                                                              self.colligations_freqs_files,
                                                                              colligations_freqs_files_all):
            colligations_stats_file = {}
            c1xs = collections.Counter()
            cx1s = collections.Counter()
            cxxs = {}

            # C1x & Cx1
            for ngram_size, colligations_freqs in colligations_freqs_file_all.items():
                for (node, collocate), freq in colligations_freqs.items():
                    c1xs[collocate] += freq
                    cx1s[node] += freq

            # Cxx
            for ngram_size, colligations_freqs in colligations_freqs_file_all.items():
                cxxs[ngram_size] = sum(colligations_freqs.values())

            for node, collocate in colligations_total:
                if (node, collocate) in colligations_freqs_file:
                    c11 = sum(colligations_freqs_file[(node, collocate)])
                else:
                    c11 = 0

                c12 = c1xs[collocate] - c11
                c21 = cx1s[node] - c11
                c22 = cxxs[len(node)] - c11 - c12 - c21

                # Berry-Rogghe's z-score
                if test_significance == wl_measures_statistical_significance.berry_rogghes_z_score:
                    span = (abs(window_left) + abs(window_right)) / 2

                    colligations_stats_file[(node, collocate)] = test_significance(self.main, c11, c12, c21, c22, span)
                else:
                    colligations_stats_file[(node, collocate)] = test_significance(self.main, c11, c12, c21, c22)

                colligations_stats_file[(node, collocate)].append(measure_effect_size(self.main, c11, c12, c21, c22))

            self.colligations_stats_files.append(colligations_stats_file)

        if len(files) == 1:
            self.colligations_freqs_files *= 2
            self.colligations_stats_files *= 2

class Wl_Worker_Colligation_Table(Wl_Worker_Colligation):
    def run(self):
        super().run()

        self.progress_updated.emit(self.tr('Rendering table ...'))

        time.sleep(0.1)

        self.worker_done.emit(wl_misc.merge_dicts(self.colligations_freqs_files),
                              wl_misc.merge_dicts(self.colligations_stats_files),
                              self.nodes_text)

class Wl_Worker_Colligation_Fig(Wl_Worker_Colligation):
    def run(self):
        super().run()

        self.progress_updated.emit(self.tr('Rendering figure ...'))

        time.sleep(0.1)

        self.worker_done.emit(wl_misc.merge_dicts(self.colligations_freqs_files),
                              wl_misc.merge_dicts(self.colligations_stats_files),
                              self.nodes_text)

@wl_misc.log_timing
def generate_table(main, table):
    def update_gui(colligations_freqs_files, colligations_stats_files, nodes_text):
        if colligations_freqs_files:
            table.clear_table()

            table.settings = main.settings_custom

            text_test_significance = settings['generation_settings']['test_significance']
            text_measure_effect_size = settings['generation_settings']['measure_effect_size']

            (text_test_stat,
             text_p_value,
             text_bayes_factor) = main.settings_global['tests_significance']['collocation'][text_test_significance]['cols']
            text_effect_size =  main.settings_global['measures_effect_size']['collocation'][text_measure_effect_size]['col']

            # Insert columns (files)
            for i, file in enumerate(files):
                for i in range(settings['generation_settings']['window_left'],
                               settings['generation_settings']['window_right'] + 1):
                    if i < 0:
                        table.insert_col(table.columnCount() - 2,
                                         main.tr(f'[{file["name"]}]\nL{-i}'),
                                         is_int = True, is_cumulative = True, is_breakdown = True)
                        table.insert_col(table.columnCount() - 2,
                                         main.tr(f'[{file["name"]}]\nL{-i} %'),
                                         is_pct = True, is_cumulative = True, is_breakdown = True)
                    elif i > 0:
                        table.insert_col(table.columnCount() - 2,
                                         main.tr(f'[{file["name"]}]\nR{i}'),
                                         is_int = True, is_cumulative = True, is_breakdown = True)
                        table.insert_col(table.columnCount() - 2,
                                         main.tr(f'[{file["name"]}]\nR{i} %'),
                                         is_pct = True, is_cumulative = True, is_breakdown = True)

                    # Show breakdown by span position
                    table.cols_breakdown_position.add(table.columnCount() - 3)
                    table.cols_breakdown_position.add(table.columnCount() - 4)

                table.insert_col(table.columnCount() - 2,
                                 main.tr(f'[{file["name"]}]\nFrequency'),
                                 is_int = True, is_cumulative = True, is_breakdown = True)
                table.insert_col(table.columnCount() - 2,
                                 main.tr(f'[{file["name"]}]\nFrequency %'),
                                 is_pct = True, is_cumulative = True, is_breakdown = True)

                if text_test_stat:
                    table.insert_col(table.columnCount() - 2,
                                     main.tr(f'[{file["name"]}]\n{text_test_stat}'),
                                     is_float = True, is_breakdown = True)

                table.insert_col(table.columnCount() - 2,
                                 main.tr(f'[{file["name"]}]\n{text_p_value}'),
                                 is_float = True, is_breakdown = True)

                if text_bayes_factor:
                    table.insert_col(table.columnCount() - 2,
                                     main.tr(f'[{file["name"]}]\n{text_bayes_factor}'),
                                     is_float = True, is_breakdown = True)

                table.insert_col(table.columnCount() - 2,
                                 main.tr(f'[{file["name"]}]\n{text_effect_size}'),
                                 is_float = True, is_breakdown = True)

            # Insert columns (total)
            for i in range(settings['generation_settings']['window_left'],
                           settings['generation_settings']['window_right'] + 1):
                if i < 0:
                    table.insert_col(table.columnCount() - 2,
                                     main.tr(f'Total\nL{-i}'),
                                     is_int = True, is_cumulative = True)
                    table.insert_col(table.columnCount() - 2,
                                     main.tr(f'Total\nL{-i} %'),
                                     is_pct = True, is_cumulative = True)
                elif i > 0:
                    table.insert_col(table.columnCount() - 2,
                                     main.tr(f'Total\nR{i}'),
                                     is_int = True, is_cumulative = True)
                    table.insert_col(table.columnCount() - 2,
                                     main.tr(f'Total\nR{i} %'),
                                     is_pct = True, is_cumulative = True)

                # Show breakdown by span position
                table.cols_breakdown_position.add(table.columnCount() - 3)
                table.cols_breakdown_position.add(table.columnCount() - 4)

            table.insert_col(table.columnCount() - 2,
                             main.tr('Total\nFrequency'),
                             is_int = True, is_cumulative = True)
            table.insert_col(table.columnCount() - 2,
                             main.tr('Total\nFrequency %'),
                             is_pct = True, is_cumulative = True)

            if text_test_stat:
                table.insert_col(table.columnCount() - 2,
                                 main.tr(f'Total\n{text_test_stat}'),
                                 is_float = True)

            table.insert_col(table.columnCount() - 2,
                             main.tr(f'Total\n{text_p_value}'),
                             is_float = True)

            if text_bayes_factor:
                table.insert_col(table.columnCount() - 2,
                                 main.tr(f'Total\n{text_bayes_factor}'),
                                 is_float = True)

            table.insert_col(table.columnCount() - 2,
                             main.tr(f'Total\n{text_effect_size}'),
                             is_float = True)

            # Sort by p-value of the first file
            table.horizontalHeader().setSortIndicator(
                table.find_col(main.tr(f'[{files[0]["name"]}]\n{text_p_value}')),
                Qt.AscendingOrder
            )

            table.blockSignals(True)
            table.setSortingEnabled(False)
            table.setUpdatesEnabled(False)

            if settings['generation_settings']['window_left'] < 0:  
                cols_freqs_start = [table.find_col(f'[{file["name"]}]\nL{-settings["generation_settings"]["window_left"]}')
                                    for file in files]
                cols_freqs_start.append(table.find_col(f'Total\nL{-settings["generation_settings"]["window_left"]}'))
            else:
                cols_freqs_start = [table.find_col(f'[{file["name"]}]\nR{settings["generation_settings"]["window_left"]}')
                                    for file in files]
                cols_freqs_start.append(table.find_col(f'Total\nR{settings["generation_settings"]["window_left"]}'))

            cols_freq = table.find_cols(main.tr('\nFrequency'))
            cols_freq_pct = table.find_cols(main.tr('\nFrequency %'))

            for col in cols_freq_pct:
                cols_freq.remove(col)

            if text_test_stat:
                cols_test_stat = table.find_cols(main.tr(f'\n{text_test_stat}'))

            cols_p_value = table.find_cols(main.tr('\np-value'))

            if text_bayes_factor:
                cols_bayes_factor = table.find_cols(main.tr('\nBayes Factor'))

            cols_effect_size = table.find_cols(f'\n{text_effect_size}')
            col_files_found = table.find_col(main.tr('Number of\nFiles Found'))
            col_files_found_pct = table.find_col(main.tr('Number of\nFiles Found %'))

            freqs_totals = numpy.array(list(colligations_freqs_files.values())).sum(axis = 0)
            freq_totals = numpy.array(list(colligations_freqs_files.values())).sum(axis = 2).sum(axis = 0)
            len_files = len(files)

            table.setRowCount(len(colligations_freqs_files))

            for i, ((node, collocate), stats_files) in enumerate(wl_sorting.sorted_collocations_stats_files(colligations_stats_files)):
                freqs_files = colligations_freqs_files[(node, collocate)]

                # Rank
                table.set_item_num(i, 0, -1)

                # Node
                table.setItem(i, 1, wl_table.Wl_Table_Item(nodes_text[node]))
                # Collocate
                table.setItem(i, 2, wl_table.Wl_Table_Item(collocate))

                # Frequency
                for j, freqs_file in enumerate(freqs_files):
                    for k, freq in enumerate(freqs_file):
                        table.set_item_num(i, cols_freqs_start[j] + k * 2, freq)

                        if freqs_totals[j][k]:
                            table.set_item_num(i, cols_freqs_start[j] + k * 2 + 1, freq / freqs_totals[j][k])
                        else:
                            table.set_item_num(i, cols_freqs_start[j] + k * 2 + 1, 0)

                    table.set_item_num(i, cols_freq[j], sum(freqs_file))

                    if freq_totals[j]:
                        table.set_item_num(i, cols_freq_pct[j], sum(freqs_file) / freq_totals[j])
                    else:
                        table.set_item_num(i, cols_freq_pct[j], 0)

                for j, (test_stat, p_value, bayes_factor, effect_size) in enumerate(stats_files):
                    # Test Statistic
                    if text_test_stat:
                        table.set_item_num(i, cols_test_stat[j], test_stat)

                    # p-value
                    table.set_item_num(i, cols_p_value[j], p_value)

                    # Bayes Factor
                    if text_bayes_factor:
                        table.set_item_num(i, cols_bayes_factor[j], bayes_factor)

                    # Effect Size
                    table.set_item_num(i, cols_effect_size[j], effect_size)

                # Number of Files Found
                num_files_found = len([freqs_file for freqs_file in freqs_files[:-1] if sum(freqs_file)])

                table.set_item_num(i, col_files_found, num_files_found)
                table.set_item_num(i, col_files_found_pct, num_files_found / len_files)

            table.setSortingEnabled(True)
            table.setUpdatesEnabled(True)
            table.blockSignals(False)

            table.toggle_pct()
            table.toggle_cumulative()
            table.toggle_breakdown()
            table.update_ranks()

            table.itemChanged.emit(table.item(0, 0))

            wl_msg.wl_msg_generate_table_success(main)
        else:
            wl_msg_box.wl_msg_box_no_results(main)

            wl_msg.wl_msg_generate_table_error(main)

    settings = main.settings_custom['colligation']
    files = main.wl_files.get_selected_files()

    if wl_checking_file.check_files_on_loading_colligation(main, files):
        for file in files:
            if re.search(r'\.xml$', file['path'], flags = re.IGNORECASE):
                if file['tokenized'] == 'No' or file['tagged'] == 'No':
                    wl_msg_box.wl_msg_box_invalid_xml_file(main)

                    return
        
        if (not settings['search_settings']['search_settings'] or
            not settings['search_settings']['multi_search_mode'] and settings['search_settings']['search_term'] or
            settings['search_settings']['multi_search_mode'] and settings['search_settings']['search_terms']):
            dialog_progress = wl_dialog_misc.Wl_Dialog_Progress_Process_Data(main)

            worker_colligation_table = Wl_Worker_Colligation_Table(
                main,
                dialog_progress = dialog_progress,
                update_gui = update_gui
            )

            thread_colligation_table = wl_threading.Wl_Thread(worker_colligation_table)
            thread_colligation_table.start_worker()
        else:
            wl_msg_box.wl_msg_box_missing_search_term_optional(main)

            wl_msg.wl_msg_generate_table_error(main)
    else:
        wl_msg.wl_msg_generate_table_error(main)

@wl_misc.log_timing
def generate_fig(main):
    def update_gui(colligations_freqs_file, colligations_stats_files, nodes_text):
        if colligations_freqs_file:
            text_test_significance = settings['generation_settings']['test_significance']
            text_measure_effect_size = settings['generation_settings']['measure_effect_size']

            (text_test_stat,
             text_p_value,
             text_bayes_factor) = main.settings_global['tests_significance']['collocation'][text_test_significance]['cols']
            text_effect_size =  main.settings_global['measures_effect_size']['collocation'][text_measure_effect_size]['col']

            if re.search(r'^[LR][0-9]+$', settings['fig_settings']['use_data']):
                span_positions = (list(range(settings['generation_settings']['window_left'], 0)) +
                                  list(range(1, settings['generation_settings']['window_right'] + 1)))

                if 'L' in settings['fig_settings']['use_data']:
                    span_position = span_positions.index(-int(settings['fig_settings']['use_data'][1:]))
                else:
                    span_position = span_positions.index(int(settings['fig_settings']['use_data'][1:]))

                # Network Graph
                if settings['fig_settings']['graph_type'] == main.tr('Network Graph'):
                    collocates_freq_files = {
                        (nodes_text[node], collocate): numpy.array(freqs)[:, span_position]
                        for (node, collocate), freqs in colligations_freqs_file.items()
                    }
                # Line Chart & Word Cloud
                else:
                    collocates_freq_files = {
                        ', '.join([nodes_text[node], collocate]): numpy.array(freqs)[:, span_position]
                        for (node, collocate), freqs in colligations_freqs_file.items()
                    }

                wl_fig_freq.wl_fig_freq(
                    main, collocates_freq_files,
                    settings = settings['fig_settings'],
                    label_x = main.tr('Colligation')
                )
            elif settings['fig_settings']['use_data'] == main.tr('Frequency'):
                # Network Graph
                if settings['fig_settings']['graph_type'] == main.tr('Network Graph'):
                    collocates_freq_files = {
                        (nodes_text[node], collocate): numpy.array(freqs).sum(axis = 1)
                        for (node, collocate), freqs in colligations_freqs_file.items()
                    }
                # Line Chart & Word Cloud
                else:
                    collocates_freq_files = {
                        ', '.join([nodes_text[node], collocate]): numpy.array(freqs).sum(axis = 1)
                        for (node, collocate), freqs in colligations_freqs_file.items()
                    }

                wl_fig_freq.wl_fig_freq(
                    main, collocates_freq_files,
                    settings = settings['fig_settings'],
                    label_x = main.tr('Colligation')
                )
            else:
                # Network Graph
                if settings['fig_settings']['graph_type'] == main.tr('Network Graph'):
                    colligations_stats_files = {
                        (nodes_text[node], collocate): freqs
                        for (node, collocate), freqs in colligations_stats_files.items()
                    }
                # Line Chart & Word Cloud
                else:
                    colligations_stats_files = {
                        ', '.join([nodes_text[node], collocate]): freqs
                        for (node, collocate), freqs in colligations_stats_files.items()
                    }

                if settings['fig_settings']['use_data'] == text_test_stat:
                    collocates_stat_files = {
                        collocate: numpy.array(stats_files)[:, 0]
                        for collocate, stats_files in colligations_stats_files.items()
                    }

                    label_y = text_test_stat
                elif settings['fig_settings']['use_data'] == text_p_value:
                    collocates_stat_files = {
                        collocate: numpy.array(stats_files)[:, 1]
                        for collocate, stats_files in colligations_stats_files.items()
                    }

                    label_y = text_p_value
                elif settings['fig_settings']['use_data'] == text_bayes_factor:
                    collocates_stat_files = {
                        collocate: numpy.array(stats_files)[:, 2]
                        for collocate, stats_files in colligations_stats_files.items()
                    }

                    label_y = text_bayes_factor
                elif settings['fig_settings']['use_data'] == text_effect_size:
                    collocates_stat_files = {
                        collocate: numpy.array(stats_files)[:, 3]
                        for collocate, stats_files in colligations_stats_files.items()
                    }

                    label_y = text_effect_size

                wl_fig_stat.wl_fig_stat(
                    main, collocates_stat_files,
                    settings = settings['fig_settings'],
                    label_x = main.tr('Colligation'),
                    label_y = label_y
                )

            wl_msg.wl_msg_generate_fig_success(main)
        else:
            wl_msg_box.wl_msg_box_no_results(main)

            wl_msg.wl_msg_generate_fig_error(main)

        dialog_progress.accept()

        if colligations_freqs_file:
            wl_fig.show_fig()

    settings = main.settings_custom['colligation']
    files = main.wl_files.get_selected_files()

    if wl_checking_file.check_files_on_loading_colligation(main, files):
        for file in files:
            if re.search(r'\.xml$', file['path'], flags = re.IGNORECASE):
                if file['tokenized'] == 'No' or file['tagged'] == 'No':
                    wl_msg_box.wl_msg_box_invalid_xml_file(main)

                    return
        
        if (not settings['search_settings']['search_settings'] or
            not settings['search_settings']['multi_search_mode'] and settings['search_settings']['search_term'] or
            settings['search_settings']['multi_search_mode'] and settings['search_settings']['search_terms']):
            dialog_progress = wl_dialog_misc.Wl_Dialog_Progress_Process_Data(main)

            worker_colligation_fig = Wl_Worker_Colligation_Fig(
                main,
                dialog_progress = dialog_progress,
                update_gui = update_gui
            )

            thread_colligation_fig = wl_threading.Wl_Thread(worker_colligation_fig)
            thread_colligation_fig.start_worker()
        else:
            wl_msg_box.wl_msg_box_missing_search_term_optional(main)

            wl_msg.wl_msg_generate_fig_error(main)
    else:
        wl_msg.wl_msg_generate_fig_error(main)
