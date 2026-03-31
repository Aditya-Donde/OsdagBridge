from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QPushButton, QGroupBox, QCheckBox, QScrollArea, QFrame, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.core.utils.common import TYPE_TITLE

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Prevent changing selection on scroll

def apply_field_style(widget):
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    widget.setMinimumHeight(28)
    if isinstance(widget, QComboBox):
        style = """
            QComboBox{
                padding: 1px 7px;
                border: 1px solid black;
                border-radius: 5px;
                background-color: white;
                color: black;
            }
            QComboBox::drop-down{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border-left: 0px;
            }
            QComboBox::down-arrow{
                image: url(:/vectors/arrow_down_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox::down-arrow:on {
                image: url(:/vectors/arrow_up_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView{
                background-color: white;
                border: 1px solid black;
                outline: none;
            }
            QComboBox QAbstractItemView::item{
                color: black;
                background-color: white;
                border: none;
                border: 1px solid white;
                border-radius: 0;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item:hover{
                border: 1px solid #90AF13;
                background-color: #90AF13;
                color: black;
            }
            QComboBox QAbstractItemView::item:selected{
                background-color: #90AF13;
                color: black;
                border: 1px solid #90AF13;
            }
            QComboBox QAbstractItemView::item:selected:hover{
                background-color: #90AF13;
                color: black;
                border: 1px solid #94b816;
            } 
        """
        widget.setStyleSheet(style)
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet("""
            QLineEdit {
                padding: 1px 7px;
                border: 1px solid #070707;
                border-radius: 6px;
                background-color: white;
                color: #000000;
                font-weight: normal;
            }
        """)

class OutputDock(QWidget):
    """Output dock with collapsible design controls and scrollable layout."""

    def __init__(self, backend=None, parent=None):
        super().__init__()
        self.parent = parent
        self.backend = backend
        self.setStyleSheet("background: transparent;")
        configs = self._load_configs()
        self.analysis_config = configs.get("analysis")
        # Configurable button rows per section; populated from backend ui_fields
        self.section_configs = configs.get("design", [])
        self.init_ui()

    def toggle_output_dock(self):
        parent = self.parent
        if hasattr(parent, 'toggle_animate'):
            is_collapsing = self.width() > 0
            parent.toggle_animate(show=not is_collapsing, dock='output')
        
        self.toggle_btn.setText("❮" if is_collapsing else "❯")
        self.toggle_btn.setToolTip("Show panel" if is_collapsing else "Hide panel")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Checking hasattr is only meant to prevent errors
        if self.parent:
            if self.width() == 0:
                if hasattr(self.parent, 'update_docking_icons'):
                    self.parent.update_docking_icons(output_is_active=False)
            elif self.width() > 0:
                if hasattr(self.parent, 'update_docking_icons'):
                    self.parent.update_docking_icons(output_is_active=True)


    def init_ui(self):
        # Main horizontal layout to hold toggle strip and content
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Toggle strip on the left
        self.toggle_strip = QWidget()
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        self.toggle_strip.setFixedWidth(6)
        toggle_layout = QVBoxLayout(self.toggle_strip)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(0)
        toggle_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.toggle_btn = QPushButton("❯")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.setToolTip("Hide panel")
        self.toggle_btn.clicked.connect(self.toggle_output_dock)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #7a9a12;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                border: none;
            }
            QPushButton:hover {
                background-color: #6a8a10;
            }
        """)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_btn)
        toggle_layout.addStretch()
        self.main_layout.addWidget(self.toggle_strip)

        # Content container
        content_container = QWidget()
        content_container.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)

        # Top Bar with buttons
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        top_bar.setContentsMargins(0, 0, 0, 15)
        
        input_dock_btn = QPushButton("Output Dock")
        input_dock_btn.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 7px 20px;
                min-width: 80px;
            }
        """)
        input_dock_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.addWidget(input_dock_btn)
        top_bar.addStretch()
        content_layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: white; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)

        analysis_group = self._build_analysis_group()
        if analysis_group:
            scroll_layout.addWidget(analysis_group)

        design_group = QGroupBox("Design")
        design_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #333;
                border: 1px solid #90AF13;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 4px;
                background-color: white;
            }
            """
        )
        design_layout = QVBoxLayout(design_group)
        design_layout.setContentsMargins(10, 8, 10, 10)
        design_layout.setSpacing(8)

        # Dynamic design sections
        for section_cfg in self.section_configs:
            section_group = self._create_toggle_group(section_cfg)
            design_layout.addWidget(section_group)

        scroll_layout.addWidget(design_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        content_layout.addWidget(scroll)

        h_layout = QHBoxLayout()
        h_layout.setSpacing(5)
        h_layout.setContentsMargins(0, 0, 0, 0)

        results_btn = DockCustomButton("Generate Results Table", ":/vectors/design_report.svg")
        results_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout.addWidget(results_btn)

        report_btn = DockCustomButton("Generate Report", ":/vectors/design_report.svg")
        report_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        h_layout.addWidget(report_btn)
        content_layout.addLayout(h_layout)
        
        # Add content container to main layout
        self.main_layout.addWidget(content_container)

    def open_steel_design(self):
        """Open the Steel Design dialog."""
        from osdagbridge.desktop.ui.dialogs.steel_design import SteelDesign
        dlg = SteelDesign(parent=self.parent)
        dlg.exec()

    def open_deck_design(self):
        """Open the Deck Design dialog."""
        from osdagbridge.desktop.ui.dialogs.deck_design import DeckDesign
        dlg = DeckDesign(parent=self.parent)
        dlg.exec()

    def show_additional_inputs(self):
        """Handle showing additional geometry inputs."""
        # Implement your logic here
        print("Show additional inputs clicked")

    # --- Helpers for dynamic section/button rendering ---
    def _load_configs(self):
        if self.backend and hasattr(self.backend, "output_values"):
            try:
                cfg = self.backend.output_values(flag=None)
                if cfg is not None:
                    return self._normalize_section_configs(cfg)
            except Exception:
                pass
        return {"analysis": None, "design": []}

    def _normalize_section_configs(self, cfg):
        result = {"analysis": None, "design": []}
        if not cfg:
            return result

        # Already structured dict
        if isinstance(cfg, dict):
            result["analysis"] = cfg.get("analysis")
            if isinstance(cfg.get("design"), list):
                result["design"] = cfg.get("design")
            return result

        # Legacy dict list: treat as design-only
        if isinstance(cfg, list) and all(isinstance(item, dict) for item in cfg):
            result["design"] = cfg
            return result

        # Tuple-based definitions similar to input_values
        if isinstance(cfg, list) and all(isinstance(item, tuple) for item in cfg):
            for item in cfg:
                if len(item) < 7:
                    continue
                _, display_name, ui_type, _, is_visible, _, metadata = item
                if ui_type != TYPE_TITLE or not is_visible:
                    continue
                metadata = metadata or {}
                kind = metadata.get("kind", "design")
                if kind == "analysis":
                    result["analysis"] = {
                        "title": display_name,
                        "fields": metadata.get("fields", []),
                    }
                    continue
                rows = metadata.get("rows") or metadata.get("post_rows") or []
                if not isinstance(rows, list):
                    rows = []
                result["design"].append({"title": display_name, "rows": rows})
            return result

        return result

    def _default_analysis_config(self):
        return {
            "title": "Analysis Results",
            "fields": [
                {"type": "combobox", "label": "Member:", "values": ["All"]},
                {
                    "type": "combobox",
                    "label": "Load Combination:",
                    "values": ["Envelope"],
                },
                {
                    "type": "checkbox_grid",
                    "columns": [["Fx", "Mx", "Dx"], ["Fy", "My", "Dy"], ["Fz", "Mz", "Dz"]],
                },
                {
                    "type": "checkbox_row",
                    "label": "Display Options:",
                    "options": ["Max", "Min"],
                },
                {"type": "checkbox", "label": "Controlling Utilization Ratio"},
            ],
        }

    def _analysis_group_style(self):
        return (
            "QGroupBox {\n"
            "    font-weight: bold;\n"
            "    font-size: 11px;\n"
            "    color: #333;\n"
            "    border: 1px solid #90AF13;\n"
            "    border-radius: 4px;\n"
            "    margin-top: 8px;\n"
            "    padding-top: 12px;\n"
            "    background-color: white;\n"
            "}\n"
            "QGroupBox::title {\n"
            "    subcontrol-origin: margin;\n"
            "    subcontrol-position: top left;\n"
            "    left: 8px;\n"
            "    padding: 0 4px;\n"
            "    background-color: white;\n"
            "}"
        )

    def _build_analysis_group(self):
        cfg = self.analysis_config or self._default_analysis_config()
        if not cfg:
            return None

        group = QGroupBox(cfg.get("title", "Analysis Results"))
        group.setStyleSheet(self._analysis_group_style())
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        for field_cfg in cfg.get("fields", []):
            self._add_analysis_field(layout, field_cfg)

        return group

    def _normalize_field_cfg(self, field_cfg):
        if isinstance(field_cfg, dict):
            return field_cfg
        if isinstance(field_cfg, tuple) and len(field_cfg) >= 7:
            key, label, field_type, values, is_visible, _validator, metadata = field_cfg
            if not is_visible:
                return None
            meta = metadata or {}
            normalized = {
                "key": key,
                "label": label,
                "type": field_type,
                "values": values,
            }
            normalized.update(meta)
            return normalized
        return None

    def _add_analysis_field(self, layout, field_cfg):
        cfg = self._normalize_field_cfg(field_cfg)
        if not cfg:
            return
        field_type = cfg.get("type")
        if field_type == "combobox":
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)
            label = QLabel(cfg.get("label", ""))
            label.setStyleSheet("font-size: 10px; color: #333; font-weight: normal;")
            label.setMinimumWidth(cfg.get("label_min_width", 100))
            combo = NoScrollComboBox()
            values = cfg.get("values") or []
            combo.addItems(values)
            default = cfg.get("default")
            if default and default in values:
                combo.setCurrentText(default)
            apply_field_style(combo)
            row.addWidget(label)
            row.addWidget(combo)
            layout.addLayout(row)
        elif field_type == "checkbox_grid":
            columns = cfg.get("columns") or cfg.get("values") or []
            grid = QHBoxLayout()
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(8)
            for col_items in columns:
                col_layout = QVBoxLayout()
                col_layout.setContentsMargins(0, 0, 0, 0)
                col_layout.setSpacing(2)
                for text in col_items or []:
                    cb = QCheckBox(str(text))
                    col_layout.addWidget(cb)
                grid.addLayout(col_layout)
            if cfg.get("add_stretch", True):
                grid.addStretch()
            layout.addLayout(grid)
        elif field_type == "checkbox_row":
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(12)
            label = cfg.get("label")
            if label:
                lbl = QLabel(label)
                lbl.setStyleSheet("font-size: 10px; color: #333; font-weight: normal; margin-top: 4px;")
                row.addWidget(lbl)
            options = cfg.get("options") or cfg.get("values") or []
            for text in options:
                cb = QCheckBox(str(text))
                row.addWidget(cb)
            if cfg.get("add_stretch", True):
                row.addStretch()
            layout.addLayout(row)
        elif field_type == "checkbox":
            cb = QCheckBox(cfg.get("label", ""))
            layout.addWidget(cb)

    def _section_label_style(self):
        return (
            "QLabel {\n"
            "    color: #000000;\n"
            "    font-size: 12px;\n"
            "    background: transparent;\n"
            "}"
        )

    def _default_action_button_style(self):
        return (
            "QPushButton {\n"
            "    background-color: #90AF13;\n"
            "    color: white;\n"
            "    font-weight: bold;\n"
            "    border: none;\n"
            "    border-radius: 4px;\n"
            "    padding: 8px 20px;\n"
            "    font-size: 11px;\n"
            "    min-width: 80px;\n"
            "}\n"
            "QPushButton:hover {\n"
            "    background-color: #7a9a12;\n"
            "}\n"
        )

    def _create_action_button(self, cfg):
        btn = QPushButton(cfg.get("text", "Action"))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        style = cfg.get("style") or self._default_action_button_style()
        btn.setStyleSheet(style)
        if cfg.get("icon"):
            btn.setIcon(QIcon(cfg["icon"]))
            icon_size = cfg.get("icon_size")
            if isinstance(icon_size, (list, tuple)) and len(icon_size) == 2:
                btn.setIconSize(QSize(icon_size[0], icon_size[1]))
        cb_name = cfg.get("action")
        cb = getattr(self, cb_name, None) if cb_name else None
        if callable(cb):
            btn.clicked.connect(cb)
        else:
            btn.setEnabled(False)
        return btn

    def _add_button_row(self, parent_layout, row_cfg):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label_text = row_cfg.get("label")
        if label_text:
            label = QLabel(label_text)
            label.setStyleSheet(self._section_label_style())
            label.setMinimumWidth(row_cfg.get("label_min_width", 110))
            row.addWidget(label)

        buttons = row_cfg.get("buttons", [])
        for cfg in buttons:
            btn = self._create_action_button(cfg)
            row.addWidget(btn, cfg.get("stretch", 1 if len(buttons) == 1 else 0))

        if row_cfg.get("add_stretch", True):
            row.addStretch()

        parent_layout.addLayout(row)

    def _create_toggle_group(self, section_cfg):
        group = QGroupBox()
        group.setStyleSheet(
            "QGroupBox {\n"
            "    border: 1px solid #90AF13;\n"
            "    border-radius: 5px;\n"
            "    margin-top: 0px;\n"
            "    padding-top: 5px;\n"
            "    background-color: white;\n"
            "}"
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(section_cfg.get("title", ""))
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        header.addWidget(title)
        header.addStretch()

        toggle_btn = QPushButton()
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setIcon(QIcon(":/vectors/arrow_up_light.svg"))
        toggle_btn.setIconSize(QSize(20, 20))
        toggle_btn.setStyleSheet(
            "QPushButton {\n"
            "    background: transparent;\n"
            "    border: none;\n"
            "    padding: 2px;\n"
            "}\n"
            "QPushButton:hover {\n"
            "    background: transparent;\n"
            "}\n"
            "QPushButton:pressed {\n"
            "    background: transparent;\n"
            "}"
        )
        header.addWidget(toggle_btn)
        layout.addLayout(header)

        body = QFrame()
        body.setFrameShape(QFrame.NoFrame)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)
        body.setVisible(True)

        for row_cfg in section_cfg.get("rows", []):
            self._add_button_row(body_layout, row_cfg)

        layout.addWidget(body)

        def _toggle(checked):
            body.setVisible(checked)
            toggle_btn.setIcon(QIcon(":/vectors/arrow_up_light.svg" if checked else ":/vectors/arrow_down_light.svg"))

        toggle_btn.toggled.connect(_toggle)
        group.setLayout(layout)
        return group