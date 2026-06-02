"""
Field Type for Custom-Load-Combinations in Additional Inputs dialog. Shows a table of combinations with Add/Modify/Delete buttons.
Part of UI-Builder
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QSizePolicy,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.common import *
class LoadCombinationWidget(QWidget):
    """
    Self-contained widget — table + Add/Modify/Delete buttons.
    Populated from a list of dicts:
        [{"name": str, "included": bool, "items": [{"case": str, "factor": str}]}]
    """

    def __init__(self, field_id: str, on_click: str, owner, ai, parent=None):
        super().__init__(parent)
        self._field_id = field_id
        self._is_irc6_widget = (
            self._field_id == "irc6_default_combinations"
        )

        self._on_click = on_click
        self._owner    = owner
        self._ai       = ai
        self._data: list = []

        try:
            self._irc6_data = IRC6_2017.uls_load_combinations()
        except Exception as e:
            print("Error loading IRC6 ULS combinations:", e)
            self._irc6_data = []

        try:
            self._irc6_sls_data = IRC6_2017.sls_load_combinations()
        except Exception as e:
            print("Error loading IRC6 SLS combinations:", e)
            self._irc6_sls_data = []    

        self.setObjectName(field_id)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Button row ─────────────────────────────────────────────────────
        if not self._is_irc6_widget:
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)

            btn_style = (
                "QPushButton { background:#ffffff; border:1px solid #a0a0a0;"
                " border-radius:3px; padding:4px 10px; font-size:11px; color:#2a2a2a; }"
                "QPushButton:hover { background:#f0f0f0; }"
                "QPushButton:pressed { background:#e0e0e0; }"
            )

            self.add_btn    = QPushButton("Add Custom Combination")
            self.modify_btn = QPushButton("Modify")
            self.delete_btn = QPushButton("Delete")

            self.modify_btn.setVisible(False)
            self.delete_btn.setVisible(False)

            for btn in (self.add_btn, self.modify_btn, self.delete_btn):
                btn.setStyleSheet(btn_style)
                btn_row.addWidget(btn)

            btn_row.addStretch()
            layout.addLayout(btn_row)

        # ── Table ─────────────────────────────────────────────────────────
        self.table = QTableWidget(0, 2)
        self.table.setObjectName(self._field_id + "_table")
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 1200)
        self.table.setColumnWidth(1, 80)

        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.table.setStyleSheet("""
            QTableWidget { background-color: transparent; border: none; }
            QTableWidget::item { padding: 6px; color: #000000; font-size: 11px; border: none; }
            QTableWidget::item:selected { background-color: transparent; color: #000000; }
        """)
        layout.addWidget(self.table)

        # ── Signals ────────────────────────────────────────────────────────
        if not self._is_irc6_widget:
            self.add_btn.clicked.connect(self._on_add)
            self.modify_btn.clicked.connect(self._on_modify)
            self.delete_btn.clicked.connect(self._on_delete)
            self.table.itemSelectionChanged.connect(self._on_selection_changed)
        else:
            self._populate_default_combinations()

    # ── Public ─────────────────────────────────────────────────────────────

    def update(self, data: list):
        """Refresh table from list of combination dicts."""
        self._data = list(data)
        self.table.setRowCount(0)

        if not data:
            self.table.setVisible(False)
            return

        self.table.setVisible(True)

        for idx, combo in enumerate(data):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            name = QTableWidgetItem(combo.get("name", ""))
            name.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name.setFlags(name.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, name)

            cb_container = QWidget()
            cb_container.setStyleSheet("background: transparent;")
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb = QCheckBox()
            cb.setChecked(combo.get("included", True))
            cb.setStyleSheet("QCheckBox { spacing:0; background:transparent; }")
            cb.stateChanged.connect(
                lambda state, i=idx: self._on_included_changed(i, bool(state))
            )
            cb_layout.addWidget(cb)
            self.table.setCellWidget(row_idx, 1, cb_container)

        self._adjust_table_height()

    def collect(self) -> list:
        """Read current table state back into list of dicts."""
        if self._ai and hasattr(self._ai, "working_input_dict"):
            return self._ai.working_input_dict.get(self._field_id, [])
        return []
    
    def _on_included_changed(self, idx: int, checked: bool):
        if idx < len(self._data):
            self._data[idx]["included"] = checked
            if self._ai:
                self._ai._on_field_edited(self._field_id, self._data)

    # ── Private ────────────────────────────────────────────────────────────

    def _adjust_table_height(self):
        rows        = self.table.rowCount()
        row_height  = self.table.verticalHeader().defaultSectionSize()
        hdr_height  = self.table.horizontalHeader().height()
        new_height  = hdr_height + rows * row_height + 8
        new_height  = max(80, new_height)
        self.table.setFixedHeight(new_height)

    def _on_selection_changed(self):
        has = bool(self.table.selectedItems())
        self.modify_btn.setVisible(has)
        self.delete_btn.setVisible(has)

    def _current_data(self) -> list:
        return list(self._data)

    def _save_data(self, data: list):
        self._data = list(data)
        if self._ai:
            self._ai._on_field_edited(self._field_id, data)
        self.update(data)

    def _on_add(self):
        if self._on_click and hasattr(self._owner, self._on_click):
            getattr(self._owner, self._on_click)(widget=self)

    def _on_modify(self):
        row = self.table.currentRow()
        if row < 0:
            return
        data = self._current_data()
        if row < len(data):
            if self._on_click and hasattr(self._owner, self._on_click):
                getattr(self._owner, self._on_click)(existing=data[row], widget=self)

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        data = self._current_data()
        if row < len(data):
            data.pop(row)
            self._save_data(data)  

    # ── Load abbreviation map ───────────────────────────────────────────────
    _ABBREV = {
        'dead_load':          'DL',
        'surfacing':          'DW',
        'live_load':          'LL',
        'wind_load':          'WL',
        'thermal_load':       'TL',
        'seismic':            'EL',
        'vehicle_collision':  'VC',
        'barge_impact':       'BI',
        'floating_bodies':    'FB',
    }

    # ── Key map: (combination_type, leading_or_condition, accidental_load, direction)
    #            → KEY string
    _ULS_CASE_KEYS = {
        ('basic',       'live_load',  None,                'adding'):    'loading.load_combination.basic.ll_leading.adding',
        ('basic',       'wind_load',  None,                'adding'):    'loading.load_combination.basic.wl_leading.adding',
        ('basic',       'thermal_load', None,              'adding'):    'loading.load_combination.basic.tl_leading.adding',
        ('basic',       'live_load',  None,                'relieving'): 'loading.load_combination.basic.ll_leading.relieving',
        ('basic',       'wind_load',  None,                'relieving'): 'loading.load_combination.basic.wl_leading.relieving',
        ('basic',       'thermal_load', None,              'relieving'): 'loading.load_combination.basic.tl_leading.relieving',
        ('accidental',  'live_load',  'vehicle_collision', 'adding'):    'loading.load_combination.accidental.vc.ll_leading.adding',
        ('accidental',  'live_load',  'barge_impact',      'adding'):    'loading.load_combination.accidental.bi.ll_leading.adding',
        ('accidental',  'live_load',  'floating_bodies',   'adding'):    'loading.load_combination.accidental.fb.ll_leading.adding',
        ('accidental',  'live_load',  'vehicle_collision', 'relieving'): 'loading.load_combination.accidental.vc.ll_leading.relieving',
        ('accidental',  'live_load',  'barge_impact',      'relieving'): 'loading.load_combination.accidental.bi.ll_leading.relieving',
        ('accidental',  'live_load',  'floating_bodies',   'relieving'): 'loading.load_combination.accidental.fb.ll_leading.relieving',
        ('seismic',     'service',    None,                'adding'):    'loading.load_combination.seismic.service.adding',
        ('seismic',     'construction', None,              'adding'):    'loading.load_combination.seismic.construction.adding',
        ('seismic',     'service',    None,                'relieving'): 'loading.load_combination.seismic.service.relieving',
        ('seismic',     'construction', None,              'relieving'): 'loading.load_combination.seismic.construction.relieving',
    }

    _SLS_CASE_KEYS = {
        ('rare',            'live_load',    'adding'):    'loading.load_combination.sls.rare.ll_leading.adding',
        ('rare',            'wind_load',    'adding'):    'loading.load_combination.sls.rare.wl_leading.adding',
        ('rare',            'thermal_load', 'adding'):    'loading.load_combination.sls.rare.tl_leading.adding',
        ('rare',            'live_load',    'relieving'): 'loading.load_combination.sls.rare.ll_leading.relieving',
        ('rare',            'wind_load',    'relieving'): 'loading.load_combination.sls.rare.wl_leading.relieving',
        ('rare',            'thermal_load', 'relieving'): 'loading.load_combination.sls.rare.tl_leading.relieving',
        ('frequent',        'live_load',    'adding'):    'loading.load_combination.sls.frequent.ll_leading.adding',
        ('frequent',        'wind_load',    'adding'):    'loading.load_combination.sls.frequent.wl_leading.adding',
        ('frequent',        'thermal_load', 'adding'):    'loading.load_combination.sls.frequent.tl_leading.adding',
        ('frequent',        'live_load',    'relieving'): 'loading.load_combination.sls.frequent.ll_leading.relieving',
        ('frequent',        'wind_load',    'relieving'): 'loading.load_combination.sls.frequent.wl_leading.relieving',
        ('frequent',        'thermal_load', 'relieving'): 'loading.load_combination.sls.frequent.tl_leading.relieving',
        ('quasi_permanent', None,           'adding'):    'loading.load_combination.sls.quasi_permanent.adding',
        ('quasi_permanent', None,           'relieving'): 'loading.load_combination.sls.quasi_permanent.relieving',
    }

    def _populate_default_combinations(self):
        """
        Expand each IRC6 ULS combination into adding/relieving cases,
        collapse to single case when adding == relieving for all permanent loads.
        """
        self.table.setRowCount(0)
        self._data = []

        basic_count = 1
        accidental_count = 1
        seismic_count = 1

        #ULS Combination------------------------------------
        for combo in self._irc6_data:
            ctype   = combo['combination_type']
            factors = combo['factors']
            name    = combo['name']

            dl  = factors.get('dead_load',  {})
            dw  = factors.get('surfacing',  {})

            dl_add = dl.get('adding',   dl) if isinstance(dl, dict) else dl
            dl_rel = dl.get('relieving', dl) if isinstance(dl, dict) else dl
            dw_add = dw.get('adding',   dw) if isinstance(dw, dict) else dw
            dw_rel = dw.get('relieving', dw) if isinstance(dw, dict) else dw

            same_permanent = (dl_add == dl_rel and dw_add == dw_rel)

            # Determine leading load / condition for key lookup
            if ctype == 'basic':
                # name format: "Basic — live_load leading"
                leading = name.split('—')[1].strip().replace(' leading', '')
                acc_load = None
            elif ctype == 'accidental':
                # name format: "Accidental (vehicle_collision) — live_load leading"
                import re
                acc_load = re.search(r'\((.+?)\)', name).group(1)
                leading  = name.split('—')[1].strip().replace(' leading', '')
            else:  # seismic
                # name format: "Seismic (service) — all variable loads accompanying"
                import re
                leading  = re.search(r'\((.+?)\)', name).group(1)
                acc_load = None

            directions = ['adding'] if same_permanent else ['adding', 'relieving']

            for direction in directions:
                dl_f = dl_add if direction == 'adding' else dl_rel
                dw_f = dw_add if direction == 'adding' else dw_rel

                # Build expression string
                parts = [f"{dl_f}DL", f"{dw_f}DW"]
                for load in ['live_load', 'wind_load', 'thermal_load',
                            'seismic', 'vehicle_collision', 'barge_impact', 'floating_bodies']:
                    val = factors.get(load)
                    if val is not None:
                        parts.append(f"{val}{self._ABBREV.get(load, load)}")

                expr = ' + '.join(parts)

                if ctype == "basic":
                    combo_name = f"basic_{basic_count}"
                    basic_count += 1

                elif ctype == "accidental":
                    combo_name = f"accidental_{accidental_count}"
                    accidental_count += 1

                elif ctype == "seismic":
                    combo_name = f"seismic_{seismic_count}"
                    seismic_count += 1

                display = f"{combo_name} : {expr}"

                # Look up key
                key = self._ULS_CASE_KEYS.get((ctype, leading, acc_load, direction), '')

                entry = {
                    'name':     display,
                    'included': True,
                    'key':      key,
                    'expr':     expr,
                }
                self._data.append(entry)

                row = self.table.rowCount()
                self.table.insertRow(row)

                name_item = QTableWidgetItem(display)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 0, name_item)

                cb_container = QWidget()
                cb_layout = QHBoxLayout(cb_container)
                cb_layout.setContentsMargins(0, 0, 0, 0)
                cb_layout.setAlignment(Qt.AlignCenter)
                cb = QCheckBox()
                cb.setChecked(True)
                cb.stateChanged.connect(
                    lambda state, i=row: self._on_included_changed(i, bool(state))
                )
                cb_layout.addWidget(cb)
                self.table.setCellWidget(row, 1, cb_container)

        rare_count = 1
        frequent_count = 1
        qp_count = 1

        # ── SLS combinations ───────────────────────────────────────────────
        for combo in self._irc6_sls_data:
            ctype   = combo['combination_type']
            factors = combo['factors']
            name    = combo['name']

            dl  = factors.get('dead_load', 1.0)
            dw  = factors.get('surfacing', {})

            dl_f   = dl if not isinstance(dl, dict) else dl.get('adding', 1.0)
            dw_add = dw.get('adding',    dw) if isinstance(dw, dict) else dw
            dw_rel = dw.get('relieving', dw) if isinstance(dw, dict) else dw

            same_surf = (dw_add == dw_rel)

            # Determine leading load for key lookup
            if ctype == 'quasi_permanent':
                leading  = None
                directions = ['adding'] if same_surf else ['adding', 'relieving']
            else:
                # name format: "SLS Rare — live_load leading"
                leading = name.split('—')[1].strip().replace(' leading', '')
                directions = ['adding'] if same_surf else ['adding', 'relieving']

            for direction in directions:
                dw_f = dw_add if direction == 'adding' else dw_rel

                parts = [f"{dl_f}DL", f"{dw_f}DW"]
                for load in ['live_load', 'wind_load', 'thermal_load']:
                    val = factors.get(load)
                    if val is not None and val != 0:
                        parts.append(f"{val}{self._ABBREV.get(load, load)}")

                expr = ' + '.join(parts)

                if ctype == "rare":
                    combo_name = f"rare_{rare_count}"
                    rare_count += 1

                elif ctype == "frequent":
                    combo_name = f"frequent_{frequent_count}"
                    frequent_count += 1

                elif ctype == "quasi_permanent":
                    combo_name = f"quasi_permanent_{qp_count}"
                    qp_count += 1

                display = f"{combo_name} : {expr}"

                key = self._SLS_CASE_KEYS.get((ctype, leading, direction), '')

                entry = {
                    'name':     display,
                    'included': True,
                    'key':      key,
                    'expr':     expr,
                }
                self._data.append(entry)

                row = self.table.rowCount()
                self.table.insertRow(row)

                name_item = QTableWidgetItem(display)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 0, name_item)

                cb_container = QWidget()
                cb_layout = QHBoxLayout(cb_container)
                cb_layout.setContentsMargins(0, 0, 0, 0)
                cb_layout.setAlignment(Qt.AlignCenter)
                cb = QCheckBox()
                cb.setChecked(True)
                cb.stateChanged.connect(
                    lambda state, i=row: self._on_included_changed(i, bool(state))
                )
                cb_layout.addWidget(cb)
                self.table.setCellWidget(row, 1, cb_container)

        self.table.setVisible(True)
        self._adjust_table_height()   

        if self._ai:
            self._ai._on_field_edited(self._field_id, self._data)