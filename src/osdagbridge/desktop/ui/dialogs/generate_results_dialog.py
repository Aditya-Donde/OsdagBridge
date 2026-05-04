from PySide6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QComboBox, QSizeGrip,
    QFrame, QSizePolicy, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont
from osdagbridge.desktop.ui.utils.generate_results_schema import GENERATE_RESULTS_SCHEMA
from osdagbridge.desktop.ui.utils.generate_results_default import GENERATE_RESULTS_DEFAULTS
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.export_table_dialog import ExportTableDialog
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType


#CHECKBOX DELEGATE
class CheckboxDelegate(QStyledItemDelegate):
    """Custom delegate to paint checkmarks in checkboxes."""

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        tree = self.parent()
        if not isinstance(tree, QTreeWidget):
            return

        item = tree.itemFromIndex(index)
        if not item:
            return

        check_state = item.checkState(0)

        if check_state == Qt.Checked:
            symbol = "✓"
        elif check_state == Qt.PartiallyChecked:
            symbol = "−"
        else:
            return
        

        checkbox_rect = QRect(
            option.rect.left() + 4,
            option.rect.top(),
            20,
            option.rect.height()
        )

        painter.setPen(QColor("#90AF13"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(checkbox_rect, Qt.AlignCenter, symbol)


#NO-SCROLL COMBO BOX
class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


#FIELD STYLE HELPER
def apply_field_style(widget):
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    widget.setMinimumHeight(30)

    if isinstance(widget, QComboBox):
        widget.setStyleSheet("""
            QComboBox {
                padding: 1px 8px;
                border: 1px solid black;
                border-radius: 6px;
                background: white;
                color: black;
            }
            QComboBox::drop-down {
                border: none;
                width: 26px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #d0d0d0;
                outline: 0px;
                selection-background-color: rgba(144,175,19,45);
                selection-color: black;
                color: black;
            }
            QComboBox QAbstractItemView::item {
                padding: 5px;
                margin: 0px;
                border-bottom: 1px solid #ebebeb;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(144,175,19,45);
                border-bottom: 1px solid #ebebeb;
                outline: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background: rgba(144,175,19,65);
                border-bottom: 1px solid #ebebeb;
                outline: none;
            }
        """)


#MAIN DIALOG
class GenerateResultsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumWidth(920)
        self.setMinimumHeight(650)
        self.setObjectName("generate_results_dialog")

        self.setStyleSheet("""
            QDialog#generate_results_dialog {
                background: white;
                border: 1px solid #90AF13;
            }
        """)

        self.setup_ui()

    #WRAPPER
    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Generate Results Table")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch()
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

        main_layout.addLayout(overlay)

    #MAIN UI
    def setup_ui(self):
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(18, 18, 18, 14)
        main_layout.setSpacing(12)

        body = QHBoxLayout()
        body.setSpacing(14)

        #LEFT CARD
        left_card = QFrame()
        left_card.setObjectName("leftCard")
        left_card.setStyleSheet("""
            QFrame#leftCard {
                background: white;
                border: 1px solid #90af13;
                border-radius: 10px;
            }
        """)

        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(12)

        #TOP BAR
        top_bar = QHBoxLayout()

        title = QLabel("Select Tables")
        title.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 700;
                color: #2d2d2d;
            }
        """)
        top_bar.addWidget(title)

        top_bar.addStretch()

        action_btn_style = """
            QPushButton {
                background: white;
                color: #3a3a3a;
                border: 1px solid #90af13;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #90AF13;
                border-color: #90AF13;
                color: white;
            }
            QPushButton:pressed {
                background: #7a9a10;
                border-color: #7a9a10;
                color: white;
            }
        """

        self.select_btn = QPushButton("Select All")
        self.select_btn.setStyleSheet(action_btn_style)
        self.select_btn.clicked.connect(self.select_all_items)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet(action_btn_style)
        self.clear_btn.clicked.connect(self.clear_all_items)

        top_bar.addWidget(self.select_btn)
        top_bar.addWidget(self.clear_btn)

        left_layout.addLayout(top_bar)

        #TREE WIDGET
        self.tree = QTreeWidget()
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: white;
                border: none;
                color: black;
                font-size: 12px;
                outline: 0;
                show-decoration-selected: 0;
            }
            QTreeWidget::item {
                height: 24px;
                border: none;
                padding: 2px 4px;
            }
            QTreeWidget::item:hover {
                background: rgba(144,175,19,45);
                border: none;
                color: black;
            }
            QTreeWidget::indicator {
                width: 14px;
                height: 14px;
            }
            QTreeWidget::indicator:unchecked {
                background-color: white;
                border: 1px solid #90af13;
                border-radius: 3px;
            }
            QTreeWidget::indicator:checked {
                background-color: white;
                border: 1px solid #90af13;
                border-radius: 3px;
            }
            QTreeWidget::indicator:indeterminate {
                background-color: white;
                border: 1px solid #90af13;
                border-radius: 3px;
            }
            QTreeWidget::item:selected {
                background: rgba(144,175,19,55);
                border: none;
                color: black;
            }
            QTreeWidget::branch:selected {
                background: transparent;
            }
            QTreeView::branch {
                background: transparent;
                border: none;
                image: none;
            }
            QTreeView::branch:selected {
                background: transparent;
            }
            QTreeView::branch:has-siblings:!adjoins-item,
            QTreeView::branch:has-siblings:adjoins-item,
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:has-children:!has-siblings:open,
            QTreeView::branch:closed:has-children,
            QTreeView::branch:open:has-children {
                border-image: none;
                image: none;
            }
                        QScrollBar:vertical {
                width: 2px;
                background: transparent;
                border-radius: 6px;
            }

            QScrollBar:horizontal {
                height: 2px;
                background: transparent;
                border-radius: 6px;
            }

            QScrollBar::handle {
                background: transparent;
                border-radius: 3px;
            }

            QScrollBar::handle:hover,
            QScrollBar::handle:pressed {
                background: #90AF13;
            }

            QScrollBar::add-line,
            QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }

            QScrollBar::add-page,
            QScrollBar::sub-page {
                background: transparent;
            }
        """)
        self.tree.setItemDelegate(CheckboxDelegate(self.tree))
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setAllColumnsShowFocus(False)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(18)
        self.tree.setHeaderHidden(True)
        self.tree.itemChanged.connect(self.handle_item_changed)

        left_layout.addWidget(self.tree, 1)

        body.addWidget(left_card, 2)

        #RIGHT CARD
        right_card = QFrame()
        right_card.setObjectName("rightCard")
        right_card.setStyleSheet("""
            QFrame#rightCard {
                background: white;
                border: 1px solid #90AF13;
                border-radius: 10px;
            }
        """)

        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        lc_label = QLabel("Load Case")
        lc_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 700;
                color: #2d2d2d;
            }
        """)
        right_layout.addWidget(lc_label)

        self.load_case_combo = NoScrollComboBox()
        self.load_case_combo.addItems([
            "DL", "DW", "SIDL", "LL",
            "Wind", "Seismic", "Temperature",
            "ULS Combo", "SLS Combo"
        ])
        apply_field_style(self.load_case_combo)
        right_layout.addWidget(self.load_case_combo)

        member_label = QLabel("Member Case")
        member_label.setStyleSheet(lc_label.styleSheet())
        right_layout.addWidget(member_label)

        self.member_combo = NoScrollComboBox()
        self.member_combo.addItems([
            "All Girders",
            "Girder 1",
            "Girder 2",
            "Girder 3",
            "Girder 4"
        ])
        apply_field_style(self.member_combo)
        right_layout.addWidget(self.member_combo)

        right_layout.addStretch()

        body.addWidget(right_card, 1)

        main_layout.addLayout(body)

        #FOOTER
        footer = QHBoxLayout()
        footer.addStretch()

        btn_style = """
            QPushButton {
                background: white;
                color: black;
                border: 1px solid #c0c0c0;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                min-width: 110px;
            }
            QPushButton:hover {
                background: #90AF13;
                border-color: #90AF13;
                color: white;
            }
        """

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(btn_style)
        cancel_btn.clicked.connect(self.reject)

        self.show_btn = QPushButton("Show Selections")
        self.show_btn.setStyleSheet(btn_style)
        self.show_btn.clicked.connect(self.show_selections)

        footer.addWidget(cancel_btn)
        footer.addWidget(self.show_btn)

        main_layout.addLayout(footer)

        self.build_tree()

    #TREE BUILD
    def build_tree(self):
        self.tree.blockSignals(True)

        for main_group, sub_groups in GENERATE_RESULTS_SCHEMA.items():

            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, main_group)
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.Unchecked)

            for sub_group, tables in sub_groups.items():

                child = QTreeWidgetItem(parent)
                child.setText(0, sub_group)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)

                for table in tables:
                    leaf = QTreeWidgetItem(child)
                    leaf.setText(0, table)
                    leaf.setFlags(leaf.flags() | Qt.ItemIsUserCheckable)
                    leaf.setCheckState(0, Qt.Unchecked)

        self.tree.expandToDepth(1)
        self.tree.blockSignals(False)

    #CHECKBOX LOGIC
    def handle_item_changed(self, item, column):
        state = item.checkState(0)

        self.tree.blockSignals(True)

        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self.update_children(child, state)

        self.update_parents(item)

        self.tree.blockSignals(False)

    def update_children(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self.update_children(child, state)

    def update_parents(self, item):
        parent = item.parent()

        while parent:
            checked = 0
            unchecked = 0

            for i in range(parent.childCount()):
                st = parent.child(i).checkState(0)

                if st == Qt.Checked:
                    checked += 1
                elif st == Qt.Unchecked:
                    unchecked += 1

            if checked == parent.childCount():
                parent.setCheckState(0, Qt.Checked)
            elif unchecked == parent.childCount():
                parent.setCheckState(0, Qt.Unchecked)
            else:
                parent.setCheckState(0, Qt.PartiallyChecked)

            parent = parent.parent()

    #SELECT / CLEAR ALL
    def select_all_items(self):
        self.tree.blockSignals(True)

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setCheckState(0, Qt.Checked)
            self.update_children(item, Qt.Checked)

        self.tree.blockSignals(False)

    def clear_all_items(self):
        self.tree.blockSignals(True)

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setCheckState(0, Qt.Unchecked)
            self.update_children(item, Qt.Unchecked)

        self.tree.blockSignals(False)


    #SELECTION
    def get_selected_tables(self):
        selected = []

        root = self.tree.invisibleRootItem()

        for i in range(root.childCount()):
            main_item = root.child(i)

            for j in range(main_item.childCount()):
                group = main_item.child(j)

                for k in range(group.childCount()):
                    leaf = group.child(k)

                    if leaf.checkState(0) == Qt.Checked:
                        selected.append(leaf.text(0))

        return selected

    def show_selections(self):
        selected_names = self.get_selected_tables()

        if not selected_names:
            CustomMessageBox(
                title="No Table Selected",
                text="Please select at least one table to continue.",
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        export_data = {}

        for main_key, groups in GENERATE_RESULTS_DEFAULTS.items():
            main_bucket = {}

            for group_key, tables in groups.items():
                group_bucket = {}

                for table_key, table_data in tables.items():

                    if table_data["label"] in selected_names:
                        group_bucket[table_data["label"]] = table_data

                if group_bucket:
                    main_bucket[group_key.replace("_", " ").title()] = group_bucket

            if main_bucket:
                export_data[main_key.replace("_", " ").title()] = main_bucket

        dlg = ExportTableDialog(export_data)
        dlg.exec()

    #TREE CLICK TOGGLE
    def on_tree_item_clicked(self, item, column):
        pos = self.tree.viewport().mapFromGlobal(
            self.tree.viewport().cursor().pos()
        )
        index = self.tree.indexAt(pos)
        checkbox_rect = self.tree.visualRect(index)
        checkbox_rect.setWidth(20)

        if checkbox_rect.contains(pos):
            return

        current = item.checkState(0)
        if current == Qt.Checked:
            item.setCheckState(0, Qt.Unchecked)
        else:
            item.setCheckState(0, Qt.Checked)