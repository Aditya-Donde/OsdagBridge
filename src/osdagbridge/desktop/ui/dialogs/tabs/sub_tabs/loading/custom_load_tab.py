from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class CustomLoadTab(QWidget):
    """Custom load input editor."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.custom_load_items = getattr(owner, "custom_load_items", [])
        owner.custom_load_items = self.custom_load_items
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f0f0f0;")
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(8, 8, 8, 8)
        page_layout.setSpacing(8)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(12)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"
        heading_style = "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        field_width = 105

        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(8)

        diagram = QFrame()
        diagram.setMinimumSize(QSize(380, 130))
        diagram.setMaximumHeight(130)
        diagram.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #d0d0d0; }"
        )
        diagram_layout = QVBoxLayout(diagram)
        diagram_layout.setContentsMargins(8, 8, 8, 8)
        diagram_label = QLabel("Bridge Geometry\nDiagram")
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #2a2a2a; background: transparent; border: none;"
        )
        diagram_layout.addWidget(diagram_label, 1)
        left_column.addWidget(diagram)

        input_card = owner._create_card()
        input_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)

        title = QLabel("Custom Load Input Add/Edit:")
        title.setStyleSheet(heading_style)
        input_layout.addWidget(title)

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(8)
        form_grid.setColumnMinimumWidth(0, 120)
        form_grid.setColumnStretch(0, 0)
        form_grid.setColumnStretch(1, 0)
        form_grid.setColumnStretch(2, 0)

        lbl = QLabel("Load Case:")
        lbl.setStyleSheet(label_style)
        owner.custom_load_case_combo = QComboBox()
        owner.custom_load_case_combo.addItems(["", "LL", "DL", "Custom"])
        owner.custom_load_case_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_case_combo)
        form_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        form_grid.addWidget(owner.custom_load_case_combo, 0, 1, Qt.AlignLeft)

        owner.custom_load_case_button = QPushButton("Custom")
        owner.custom_load_case_button.setFixedWidth(field_width)
        owner.custom_load_case_button.setStyleSheet(
            "QPushButton { background: #e8e8e8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #f0f0f0; }"
            "QPushButton:pressed { background: #d8d8d8; }"
        )
        form_grid.addWidget(owner.custom_load_case_button, 0, 2, Qt.AlignLeft)

        lbl = QLabel("Load Type:")
        lbl.setStyleSheet(label_style)
        owner.custom_load_type_combo = QComboBox()
        owner.custom_load_type_combo.addItems(["Point", "Line/Area"])
        owner.custom_load_type_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_type_combo)
        form_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        form_grid.addWidget(owner.custom_load_type_combo, 1, 1, Qt.AlignLeft)

        self.custom_load_stack = QStackedWidget()
        self.custom_load_stack.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.custom_load_stack.setFixedWidth(360)
        self.custom_load_stack.setStyleSheet(
            "QStackedWidget { border: none; background: transparent; }"
            "QWidget#customPointWidget, QWidget#customLineWidget { background: transparent; }"
        )

        point_widget = QWidget()
        point_widget.setObjectName("customPointWidget")
        point_grid = QGridLayout(point_widget)
        point_grid.setContentsMargins(0, 0, 0, 0)
        point_grid.setHorizontalSpacing(8)
        point_grid.setVerticalSpacing(8)
        point_grid.setColumnMinimumWidth(0, 240)
        point_grid.setColumnStretch(0, 0)
        point_grid.setColumnStretch(1, 0)

        lbl = QLabel("Distance from Left Edge of Bridge Cross\nSection (m):")
        lbl.setStyleSheet(label_style)
        owner.custom_point_left_input = QLineEdit()
        owner.custom_point_left_input.setFixedWidth(105)
        apply_field_style(owner.custom_point_left_input)
        point_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        point_grid.addWidget(owner.custom_point_left_input, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Distance from Center Line of Bearing\n(m):")
        lbl.setStyleSheet(label_style)
        owner.custom_point_bearing_input = QLineEdit()
        owner.custom_point_bearing_input.setFixedWidth(105)
        apply_field_style(owner.custom_point_bearing_input)
        point_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        point_grid.addWidget(owner.custom_point_bearing_input, 1, 1, Qt.AlignLeft)

        self.custom_load_stack.addWidget(point_widget)

        line_widget = QWidget()
        line_widget.setObjectName("customLineWidget")
        line_grid = QGridLayout(line_widget)
        line_grid.setContentsMargins(0, 0, 0, 0)
        line_grid.setHorizontalSpacing(8)
        line_grid.setVerticalSpacing(4)
        line_grid.setColumnMinimumWidth(0, 240)

        def _start_end_row(label_text, start_attr, end_attr, row_idx):
            row_label = QLabel(label_text)
            row_label.setStyleSheet(label_style)
            start_field = QLineEdit()
            end_field = QLineEdit()
            start_field.setFixedWidth(52)
            end_field.setFixedWidth(52)
            apply_field_style(start_field)
            apply_field_style(end_field)

            line_grid.addWidget(row_label, row_idx * 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
            line_grid.addWidget(start_field, row_idx * 2, 1, Qt.AlignLeft)
            line_grid.addWidget(end_field, row_idx * 2, 2, Qt.AlignLeft)

            start_lbl = QLabel("Start")
            start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
            end_lbl = QLabel("End")
            end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
            line_grid.addWidget(start_lbl, row_idx * 2 + 1, 1, Qt.AlignHCenter | Qt.AlignTop)
            line_grid.addWidget(end_lbl, row_idx * 2 + 1, 2, Qt.AlignHCenter | Qt.AlignTop)

            setattr(owner, start_attr, start_field)
            setattr(owner, end_attr, end_field)

        _start_end_row(
            "Distance from Left Edge of Bridge Cross\nSection (m):",
            "custom_line_left_start",
            "custom_line_left_end",
            0,
        )
        _start_end_row(
            "Distance from Center Line of Bearing\n(m):",
            "custom_line_bearing_start",
            "custom_line_bearing_end",
            1,
        )

        self.custom_load_stack.addWidget(line_widget)

        form_grid.addWidget(self.custom_load_stack, 2, 0, 1, 3)

        input_layout.addLayout(form_grid)

        save_btn = QPushButton("Save")
        save_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        save_btn.setStyleSheet(
            "QPushButton { background: #c8c8c8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 5px 16px; font-weight: 600; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #d8d8d8; }"
            "QPushButton:pressed { background: #b8b8b8; }"
        )
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 4, 0, 0)
        save_row.addWidget(save_btn)
        input_layout.addLayout(save_row)

        left_column.addWidget(input_card)

        list_card = owner._create_card()
        list_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        list_card.setMinimumHeight(120)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(8)

        list_title = QLabel("Custom Load Name")
        list_title.setStyleSheet(heading_style)
        list_layout.addWidget(list_title)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        owner.custom_add_btn = QPushButton("Add")
        owner.custom_edit_btn = QPushButton("Edit")
        owner.custom_delete_btn = QPushButton("Delete")
        for btn in (owner.custom_add_btn, owner.custom_edit_btn, owner.custom_delete_btn):
            btn.setFixedWidth(55)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        list_layout.addLayout(controls_row)

        owner.custom_load_list_container = QWidget()
        self.custom_load_list_layout = QVBoxLayout(owner.custom_load_list_container)
        self.custom_load_list_layout.setContentsMargins(2, 2, 2, 2)
        self.custom_load_list_layout.setSpacing(4)
        self.custom_load_list_layout.addStretch()
        list_layout.addWidget(owner.custom_load_list_container)

        left_column.addWidget(list_card)
        left_column.addStretch()

        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #d8d8d8; }"
        )
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(480)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        )
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addLayout(left_column, 3)
        content_row.addWidget(right_card, 2)
        page_layout.addLayout(content_row)

        owner.custom_load_type_combo.currentTextChanged.connect(self._on_custom_load_type_changed)
        self._on_custom_load_type_changed(owner.custom_load_type_combo.currentText())

        owner.custom_add_btn.clicked.connect(self._on_add_custom_load)
        owner.custom_delete_btn.clicked.connect(self._on_delete_custom_load)
        owner.custom_edit_btn.clicked.connect(
            lambda: QMessageBox.information(self, "Edit", "Edit functionality will be added in a future update.")
        )

        self._refresh_custom_load_list()

    def _on_custom_load_type_changed(self, text):
        if text.lower().startswith("point"):
            self.custom_load_stack.setCurrentIndex(0)
        else:
            self.custom_load_stack.setCurrentIndex(1)

    def _refresh_custom_load_list(self):
        if not hasattr(self, "custom_load_list_layout"):
            return
        while self.custom_load_list_layout.count():
            item = self.custom_load_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.custom_load_checkboxes = []
        for name in self.custom_load_items:
            row = QHBoxLayout()
            row.setContentsMargins(2, 0, 2, 0)
            row.setSpacing(4)
            label = QLabel(name)
            label.setStyleSheet(
                "font-size: 11px; font-style: italic; color: #3a3a3a; background: transparent; border: none;"
            )
            checkbox = QCheckBox()
            row.addWidget(label)
            row.addStretch()
            row.addWidget(checkbox)
            container = QWidget()
            container.setLayout(row)
            self.custom_load_list_layout.addWidget(container)
            self.custom_load_checkboxes.append((name, checkbox))
        self.custom_load_list_layout.addStretch()

    def _on_add_custom_load(self):
        next_index = len(self.custom_load_items) + 1
        new_name = f"Custom Load {next_index}"
        self.custom_load_items.append(new_name)
        self._refresh_custom_load_list()

    def _on_delete_custom_load(self):
        if not getattr(self, "custom_load_checkboxes", None):
            return
        remaining = [name for name, cb in self.custom_load_checkboxes if not cb.isChecked()]
        if len(remaining) == len(self.custom_load_checkboxes):
            QMessageBox.information(self, "Delete", "Select at least one custom load to delete.")
            return
        self.custom_load_items[:] = remaining
        self._refresh_custom_load_list()
