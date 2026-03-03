from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QSizeGrip,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea
from osdagbridge.desktop.ui.dialogs.custom_titlebar import CustomTitleBar


class NoScrollTable(QTableWidget):
    """Passes wheel events to parent scroll area — table never scrolls."""
    def wheelEvent(self, event):
        event.ignore()


class DeckDesign(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DeckDesign")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Deck Design")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)

    def init_ui(self):
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(2)



        # ── SCROLL AREA ───────────────────────────────────────────────────────
        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        container_layout.addWidget(self._build_properties_section())
        container_layout.addWidget(self._build_reinforcement_section())
        container_layout.addWidget(self._build_design_check_section())
        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ── HELPERS — same as steel_design_details.py ─────────────────────────────

    def _create_card_frame(self):
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet(
            "QFrame#girderCard { background-color: white; border: 1px solid #cfcfcf; border-radius: 10px; }"
        )
        return frame

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 12px; color: #2f2f2f; font-weight: 600; background: transparent;"
        )
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 10px; color: #5a5a5a; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _readonly_field(self):
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedWidth(150)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _make_grid(self):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 180)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        return grid

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(self._create_small_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                         row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    # ── SECTIONS ──────────────────────────────────────────────────────────────

    def _build_properties_section(self):
        card = self._create_card_frame()
        card.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Deck Properties:"))

        grid = self._make_grid()
        self.grade_field     = self._readonly_field()
        self.thickness_field = self._readonly_field()

        r = 0
        r = self._add_row(grid, r, "Grade of Material:", self.grade_field)
        r = self._add_row(grid, r, "Thickness (mm):",    self.thickness_field)

        card_layout.addLayout(grid)
        return card

    def _build_reinforcement_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Reinforcement Details:"))

        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #b0b0b0;
                border-radius: 0px;
                background: white;
            }
        """)
        table_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        table_frame_layout = QVBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(0, 0, 0, 0)
        table_frame_layout.setSpacing(0)

        self.rebar_table = NoScrollTable()
        self.rebar_table.setRowCount(2)
        self.rebar_table.setColumnCount(6)
        self.rebar_table.setHorizontalHeaderLabels([
            "Position",
            "Material Yield\nStrength (MPa)",
            "Diameter (mm)",
            "Spacing (mm)",
            "Clear Cover from\nTop (mm)",
            "Area (mm\u00b2)",
        ])

        for row, name in enumerate(["Top Layer", "Bottom Layer"]):
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemIsEnabled)
            self.rebar_table.setItem(row, 0, item)
            for col in range(1, 6):
                empty = QTableWidgetItem("")
                empty.setFlags(Qt.ItemIsEnabled)
                self.rebar_table.setItem(row, col, empty)

        self.rebar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rebar_table.verticalHeader().setVisible(False)
        self.rebar_table.verticalHeader().setDefaultSectionSize(30)
        self.rebar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rebar_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rebar_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rebar_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.rebar_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #cfcfcf;
                color: black;
                font-size: 10px;
                border: none;
            }
            QHeaderView::section {
                background-color: #EAEAEA;
                color: black;
                font-weight: bold;
                border: none;
                border-right: 1px solid #cfcfcf;
                border-bottom: 1px solid #cfcfcf;
                padding: 3px;
                font-size: 10px;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QTableWidget::item {
                color: black;
            }
        """)

        self.rebar_table.setViewportMargins(0, 0, -1, 0)

        table_frame_layout.addWidget(self.rebar_table)
        self.rebar_table.resizeRowsToContents()
        def _fit_table():
            h = (self.rebar_table.horizontalHeader().height()
                 + sum(self.rebar_table.rowHeight(r) for r in range(self.rebar_table.rowCount()))
                 + 2)
            self.rebar_table.setFixedHeight(h)
            table_frame.setFixedHeight(h)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, _fit_table)

        card_layout.addWidget(table_frame)
        return card

    def _build_design_check_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Design Check:"))

        self.design_check_text = QTextEdit()
        self.design_check_text.setReadOnly(True)
        self.design_check_text.setMinimumHeight(200)
        self.design_check_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.design_check_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-size: 10px;
                color: #222;
            }
        """)
        card_layout.addWidget(self.design_check_text)
        return card

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def load_data(self, cad_state: dict):
        if not cad_state:
            return

        self.grade_field.setText(str(cad_state.get("deck_grade", "")))
        self.thickness_field.setText(str(cad_state.get("deck_thickness", "")))

        rebar_map = {0: "top", 1: "bottom"}
        for row, prefix in rebar_map.items():
            self.rebar_table.setItem(row, 1, QTableWidgetItem(str(cad_state.get(f"rebar_{prefix}_yield",   ""))))
            self.rebar_table.setItem(row, 2, QTableWidgetItem(str(cad_state.get(f"rebar_{prefix}_dia",     ""))))
            self.rebar_table.setItem(row, 3, QTableWidgetItem(str(cad_state.get(f"rebar_{prefix}_spacing", ""))))
            self.rebar_table.setItem(row, 4, QTableWidgetItem(str(cad_state.get(f"rebar_{prefix}_cover",   ""))))
            self.rebar_table.setItem(row, 5, QTableWidgetItem(str(cad_state.get(f"rebar_{prefix}_area",    ""))))

        self.design_check_text.setPlainText(str(cad_state.get("deck_design_check", "")))