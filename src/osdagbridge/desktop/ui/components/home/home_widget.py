"""
Home widget for OsdagBridge GUI.
Displays recent projects, modules, and search bar.
"""
import sys, shutil
import os, subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit, QFileDialog,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QKeySequence, QColor, QShortcut, QFontMetrics, QCursor
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor
from PySide6.QtSvgWidgets import QSvgWidget

import osdagbridge.desktop.resources.mainPageIcons_rc
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.components.home.search_overlay import SearchOverlay
from osdagbridge.desktop.data.database.database_config import *
from osdagbridge.desktop.ui.components.home.recents_common import (
    HoverExpandFrame, ProjectActions, recents_pixmap,
)

# --- Enhanced Search Bar Widget ---
class SearchBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ensures automatic deletion when closed
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setupUI()

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_container = QWidget()
        self.search_container.setObjectName("searchContainer")
        container_layout = QHBoxLayout(self.search_container)
        container_layout.setContentsMargins(15, 0, 15, 0)
        container_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search modules or projects...")
        self.search_input.setFixedHeight(48)
        self.search_input.setObjectName("searchInput")
        container_layout.addWidget(self.search_input)

        shortcut_layout = QHBoxLayout()
        shortcut_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_layout.setSpacing(0)

        self.shortcut_hint = QLabel("Ctrl")
        self.shortcut_hint.setObjectName("shortcutKey")
        self.shortcut_hint.setFixedSize(36, 20)
        self.shortcut_hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        shortcut_layout.addWidget(self.shortcut_hint)

        self.plus_label = QLabel("+")
        self.plus_label.setObjectName("plusLabel")
        self.plus_label.setFixedSize(20, 20)
        self.plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_layout.addWidget(self.plus_label)

        self.l_key = QLabel("L")
        self.l_key.setObjectName("lKey")
        self.l_key.setFixedSize(20, 20)
        self.l_key.setAlignment(Qt.AlignmentFlag.AlignLeft)
        shortcut_layout.addWidget(self.l_key)

        container_layout.addLayout(shortcut_layout)

        self.search_icon = QSvgWidget(":/vectors/search_icon.svg")
        self.search_icon.setObjectName("searchIcon")
        self.search_icon.setFixedSize(20, 20)
        container_layout.addWidget(self.search_icon)

        layout.addWidget(self.search_container)

        self.search_input.focusInEvent = self._focus_in_event
        self.search_input.focusOutEvent = self._focus_out_event

    def _focus_in_event(self, event):
        self.search_container.setProperty("focused", True)
        self.search_container.style().unpolish(self.search_container)
        self.search_container.style().polish(self.search_container)
        QLineEdit.focusInEvent(self.search_input, event)

    def _focus_out_event(self, event):
        self.search_container.setProperty("focused", False)
        self.search_container.style().unpolish(self.search_container)
        self.search_container.style().polish(self.search_container)
        QLineEdit.focusOutEvent(self.search_input, event)

    @property
    def textChanged(self):
        return self.search_input.textChanged

    def setFocus(self):
        self.search_input.setFocus()

    def selectAll(self):
        self.search_input.selectAll()

# --- Project Item Widget ---
class ProjectItem(HoverExpandFrame):
    openProject = Signal(dict)
    generateReport = Signal(dict)
    downloadOsi = Signal(dict)

    def __init__(self, project_data):
        super().__init__(collapsed_height=55, expanded_height=95)
        self.project_data = project_data
        self.setupUI()

    def mousePressEvent(self, event):
        self.set_selected(True)
        # Optionally notify parent to deselect others

    def set_selected(self, selected):
        if selected:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(155, 197, 61, 90))
            self.setGraphicsEffect(shadow)
        else:
            self.setGraphicsEffect(None)

    def _set_hovered(self, hovered):
        self.setProperty("hovered", hovered)
        self.style().unpolish(self)
        self.style().polish(self)

    def setupUI(self):
        self.setObjectName("projectItem")
        self.setFixedHeight(self.original_height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 5, 2, 5)
        layout.setSpacing(0)

        # Project info layout
        info_layout = QHBoxLayout()
        info_layout.setSpacing(0)

        # Module icon
        number_label = QLabel()
        number_label.setObjectName("record_icon_label")
        number_label.setFixedSize(24, 24)
        number_label.setAlignment(Qt.AlignCenter)
        number_label.setPixmap(recents_pixmap(self.project_data))
        info_layout.addWidget(number_label)

        # Project details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(1)

        # Truncate long project names
        project_name = self.project_data[PROJECT_NAME]
        short_project_name = project_name
        if len(project_name) > 30:
            short_project_name = short_project_name[:30] + "..."

        project_name_label = QLabel(short_project_name)
        project_name_label.setObjectName("projectName")
        if len(project_name) > 30:
            project_name_label.setToolTip(project_name)
        project_name_label.setWordWrap(True)
        project_name_label.setContentsMargins(2, 2, 2, 2)
        project_name_label.setMinimumHeight(18)
        details_layout.addWidget(project_name_label)

        sub_detail_layout = QHBoxLayout()
        sub_detail_layout.setSpacing(0)
        sub_detail_layout.setContentsMargins(2, 0, 20, 0)

        # Truncate long submodule names
        submodule = self.project_data[RELATED_SUBMODULE]
        if len(submodule) > 24:
            submodule = submodule[:24] + "..."

        submodule_label = QLabel(submodule)
        submodule_label.setObjectName("submoduleName")
        submodule_label.setContentsMargins(1, 1, 1, 1)
        submodule_label.setMinimumHeight(18)
        sub_detail_layout.addWidget(submodule_label)

        # Date label
        date_label = QLabel(self.project_data[LAST_EDITED])
        date_label.setObjectName("dateLabel")
        date_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        sub_detail_layout.addWidget(date_label)

        details_layout.addLayout(sub_detail_layout)
        info_layout.addLayout(details_layout)

        layout.addLayout(info_layout)

        actions = ProjectActions(
            self.project_data,
            button_object_name="recent_proj_btn",
            report_label="Download Report",
            margins=(2, 5, 2, 5),
        )
        actions.generateReport.connect(self.generateReport)
        actions.downloadOsi.connect(self.downloadOsi)
        actions.openProject.connect(self.openProject)
        layout.addWidget(actions)
        self.init_expansion(actions)


class ModuleItem(QFrame):
    openModule = Signal(str) # Module Key
    def __init__(self, module_data):
        super().__init__()
        self.module_data = module_data
        self.setupUI()
        self.selected = False

    def enterEvent(self, event):
        self.setCursor(pointing_hand_cursor())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().leaveEvent(event)

    def set_selected(self, selected):
        self.selected = selected
        self.update_style()

    def update_style(self):
        if self.selected:
            self.setProperty("selected", True)
        else:
            self.setProperty("selected", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def setupUI(self):
        self.setObjectName("moduleItem")
        self.setFixedHeight(55)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # Icon with proper SVG handling
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setObjectName("moduleIcon")
        self.icon_label.setPixmap(recents_pixmap(self.module_data))

        layout.addWidget(self.icon_label)

        # Module details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(2)

        module_name_label = EllipsisLabel(self.module_data[RELATED_SUBMODULE])
        module_name_label.setObjectName("moduleName")
        details_layout.addWidget(module_name_label)

        sub_detail_layout = QHBoxLayout()
        sub_detail_layout.setSpacing(0)
        sub_detail_layout.setContentsMargins(0, 0, 0, 0)

        sub_module_label = EllipsisLabel(self.module_data[RELATED_MODULE])
        sub_module_label.setObjectName("subModuleLabel")
        sub_detail_layout.addWidget(sub_module_label)

        # Date label
        date_label = QLabel(self.module_data[LAST_OPENED])
        date_label.setObjectName("dateLabel")
        date_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        sub_detail_layout.addWidget(date_label)

        details_layout.addLayout(sub_detail_layout)
        layout.addLayout(details_layout)

    # Mouse Press Event
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.openModule.emit(self.module_data.get(MODULE_KEY))
        return super().mousePressEvent(event)

class SectionWidget(QFrame):
    openProject = Signal(dict)
    openModule = Signal(str)
    generateReport = Signal(dict)
    downloadOsi = Signal(dict)

    def __init__(self, title, items, is_project=True):
        super().__init__()
        self.items = items
        self.is_project = is_project
        self.title = title
        self.setObjectName("sectionFrame")
        self.setFixedSize(370, 320)
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Heading to match the image style
        heading = QLabel(self.title)
        heading.setAlignment(Qt.AlignCenter)
        heading.setObjectName("sectionHeading")
        heading.setFixedHeight(48)
        layout.addWidget(heading)

        # Scroll area
        scroll = QScrollArea()
        scroll.setObjectName("recents_scroll_area")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFixedHeight(275)

        container = QWidget()
        if len(self.items) == 0:
            container.setObjectName("scrollContainer_empty")
        else:
            container.setObjectName("scrollContainer")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(8, 5, 8, 5)
        vbox.setSpacing(2)

        # Add items
        for item in self.items:
            if self.is_project:
                item_widget = ProjectItem(item)
                item_widget.openProject.connect(self.openProject)
                item_widget.downloadOsi.connect(self.downloadOsi)
                item_widget.generateReport.connect(self.generateReport)
            else:
                item_widget = ModuleItem(item)
                item_widget.openModule.connect(self.openModule)
            vbox.addWidget(item_widget)

        if len(self.items) == 0:
            vbox.addStretch()
            path = ''
            if self.is_project:
                path = ":/vectors/no_projects_light.svg"
            else:
                path = ":/vectors/no_modules_light.svg"
            self.empty_label = QSvgWidget(path)
            hlayout = QHBoxLayout()
            hlayout.addStretch()
            hlayout.addWidget(self.empty_label)
            hlayout.addStretch()
            vbox.addLayout(hlayout)

        vbox.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

class EllipsisLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text
        self.setText(text)

    def setText(self, text):
        self._text = text
        self.updateText()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateText()

    def updateText(self):
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._text, Qt.ElideRight, self.width())
        super().setText(elided)

class HomeWidget(QWidget):
    openProject = Signal(dict)
    openModule = Signal(str)
    def __init__(self):
        super().__init__()
        # Ensures automatic deletion when closed
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.search_overlay = None

        self.setupUI()
        self.setupShortcuts()
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Hide overlay when clicking outside"""
        if self.search_overlay and self.search_overlay.isVisible():
            if event.type() == event.Type.MouseButtonPress:
                if not self.search_bar.geometry().contains(event.pos()) and \
                not self.search_overlay.geometry().contains(event.globalPos()):
                    self.search_overlay.hide()
        return super().eventFilter(obj, event)

    def setupShortcuts(self):
        search_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        search_shortcut.activated.connect(self.focus_search_bar)

    def focus_search_bar(self):
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def setupUI(self):
        content_area_layout = QVBoxLayout(self)
        content_area_layout.setContentsMargins(0, 0, 0, 0)
        content_area_layout.setSpacing(0)
        content_area_layout.addStretch()

        search_layout = QHBoxLayout()
        search_layout.addStretch()
        self.search_bar = SearchBarWidget()
        self.search_bar.setFixedWidth(500)

        self.search_bar.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_bar)
        search_layout.addStretch()

        content_area_layout.addLayout(search_layout)
        content_area_layout.addStretch()

        sections_layout = QHBoxLayout()
        sections_layout.setSpacing(30)

        # Fetch recents data from database
        projects = fetch_all_recent_projects()
        modules = fetch_all_recent_modules()

        self.recent_projects = SectionWidget("Recent Projects", projects, is_project=True)
        self.recent_projects.openProject.connect(self.openProject)
        self.recent_projects.downloadOsi.connect(self.handle_download_osi)
        self.recent_projects.generateReport.connect(self.recents_generate_report)

        self.recent_modules = SectionWidget("Recently Used Modules", modules, is_project=False)
        self.recent_modules.openModule.connect(self.openModule)

        sections_layout.addStretch(1)
        sections_layout.addWidget(self.recent_projects, alignment=Qt.AlignCenter)
        sections_layout.addWidget(self.recent_modules, alignment=Qt.AlignCenter)
        sections_layout.addStretch(1)
        content_area_layout.addLayout(sections_layout)
        content_area_layout.addStretch()

    def on_search_text_changed(self, text):
        """Handle search text changes - called on every keystroke"""
        keyword = text.strip()

        if not keyword:
            # If search is empty, hide overlay and reload original data
            if self.search_overlay:
                self.search_overlay.hide()
        else:
            # Call the search function
            search_results = search_projects_and_modules(keyword)

            # Show overlay with results
            self.show_search_overlay(search_results)

    def show_search_overlay(self, search_data):
        """Display the search overlay below the search bar"""
        # Create overlay if it doesn't exist
        if not self.search_overlay:
            self.search_overlay = SearchOverlay(self)
            self.search_overlay.openProject.connect(self.openProject)
            self.search_overlay.downloadOsi.connect(self.handle_download_osi)
            self.search_overlay.generateReport.connect(self.recents_generate_report)
            self.search_overlay.openModule.connect(self.openModule)
            self.search_overlay.set_search_widget(self.search_bar)

        # Update and show overlay
        self.search_overlay.show_results(search_data)
        self.search_overlay.position_below_widget(self.search_bar)
        self.search_overlay.show()

    def handle_download_osi(self, record: dict):
        # Ask user for save location
        src_path = record.get(PROJECT_PATH)
        if not src_path or not os.path.exists(src_path):
            CustomMessageBox(
                title="Error",
                text="Project file not found.",
                dialogType=MessageBoxType.Critical
            ).exec()
            return

        # Suggest a default filename
        default_name = os.path.basename(src_path) if src_path else "project.osi"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save OSI File",
            default_name,
            "OsdagBridge Project Files (*.osi);;All Files (*)"
        )
        if save_path:
            try:
                shutil.copy2(src_path, save_path)
                CustomMessageBox(
                    title="Success",
                    text=f"Project saved to:\n{save_path}",
                    dialogType=MessageBoxType.Success
                ).exec()

                # Open the directory containing the saved file
                folder = os.path.dirname(save_path)
                if folder and os.path.exists(folder):
                    try:
                        if sys.platform == 'win32':
                            os.startfile(folder)
                        elif sys.platform == 'darwin':
                            import subprocess
                            subprocess.run(['open', folder])
                        else:
                            import subprocess
                            subprocess.run(['xdg-open', folder])
                    except Exception as e:
                        print(f"[ERROR] Failed to open folder: {e}")

            except Exception as e:
                CustomMessageBox(
                    title="Error",
                    text=f"Failed to save file:\n{e}",
                    dialogType=MessageBoxType.Critical
                ).exec()

    #-------------Functions-to-generate-report-of-recent-project-START---------------------------

    class ReportWorker(QThread):
        success = Signal(str)   # emits PDF path
        error = Signal(str)     # emits error message

        def __init__(self, record, target_pdf, parent=None):
            super().__init__(parent)
            self.record = record
            self.target_pdf = target_pdf

        @staticmethod
        def _latex_compiler():
            """Return the bundled pdflatex if osdag_latex_env provides one."""
            try:
                import importlib
                module = importlib.import_module('osdag_latex_env.__main__')
                latex_env = getattr(module, 'OsdagLatexEnv')()
                if latex_env.pdflatex:
                    if latex_env.bin_dir:
                        os.environ['PATH'] = str(latex_env.bin_dir) + os.pathsep + os.environ.get('PATH', '')
                    return str(latex_env.pdflatex)
            except Exception as e:
                print(f"[INFO] osdag_latex_env not found or failed to load. ({e})")
            return 'pdflatex'

        def run(self):
            try:
                # The design page records where it wrote the report for this project.
                source = self.record.get(REPORT_FILE_PATH) or ""

                if not source or not os.path.exists(source):
                    self.error.emit(
                        "No design report has been generated for this project yet.\n"
                        "Open the project and use Create Design Report first."
                    )
                    return

                # An already-built PDF just needs copying.
                if source.lower().endswith(".pdf"):
                    shutil.copy2(source, self.target_pdf)
                    self.success.emit(self.target_pdf)
                    return

                if not source.lower().endswith(".tex"):
                    self.error.emit(f"Unsupported report source for this project:\n{source}")
                    return

                # Otherwise rebuild the PDF from the stored .tex source.
                result = subprocess.run(
                    [self._latex_compiler(), "-interaction=nonstopmode", os.path.basename(source)],
                    cwd=os.path.dirname(source),
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                generated_pdf = os.path.splitext(source)[0] + ".pdf"
                if os.path.isfile(generated_pdf):
                    shutil.copy2(generated_pdf, self.target_pdf)
                    self.success.emit(self.target_pdf)
                else:
                    self.error.emit(
                        "PDF generation failed; pdflatex produced no output.\n"
                        f"{(result.stderr or result.stdout or '')[:400]}"
                    )

            except subprocess.TimeoutExpired:
                self.error.emit("pdflatex timed out.")
            except Exception as e:
                self.error.emit(str(e))

    def recents_generate_report(self, record: dict):
        # QFileDialog must stay in the main thread
        target_pdf, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report As",
            record[PROJECT_NAME],
            "PDF (*.pdf)"
        )
        if not target_pdf:
            return

        if not target_pdf.lower().endswith(".pdf"):
            target_pdf += ".pdf"

        # Run heavy stuff in worker thread
        self.worker = self.ReportWorker(record, target_pdf, parent=self)
        self.worker.success.connect(lambda path: CustomMessageBox(
            title="Success",
            text=f"PDF Report Saved Successfully.",
            dialogType=MessageBoxType.Success
        ).exec())
        self.worker.error.connect(lambda msg: CustomMessageBox(
            title="Error",
            text=msg,
            dialogType=MessageBoxType.Critical
        ).exec())
        self.worker.start()

    #-------------Functions-to-generate-report-of-recent-project-END---------------------------
