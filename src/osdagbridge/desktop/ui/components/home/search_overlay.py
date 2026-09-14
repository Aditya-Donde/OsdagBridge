"""
Search overlay components for OsdagBridge GUI
Displays search results in a dropdown below the search bar
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QEvent
from PySide6.QtGui import QPainterPath, QRegion
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor
from osdagbridge.desktop.data.database.database_config import *
from osdagbridge.desktop.ui.components.home.recents_common import (
    HoverExpandFrame, ProjectActions, recents_pixmap,
)

class SearchResultItem(HoverExpandFrame):
    """Individual search result item with expandable action buttons"""
    openModule = Signal(str)
    openProject = Signal(dict)
    generateReport = Signal(dict)
    downloadOsi = Signal(dict)

    def __init__(self, item_data, item_type=KEY_SEARCH_PROJ, parent=None):
        super().__init__(collapsed_height=50, expanded_height=85, parent=parent)
        self.item_data = item_data
        self.setObjectName("search_result_item")
        self.item_type = item_type

        if item_type == KEY_SEARCH_MODULE:
            self.setCursor(pointing_hand_cursor())

        self.setupUI()

    def setupUI(self):
        self.setFixedHeight(self.original_height)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(0)

        # Main info layout
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)

        # Module icon
        icon_label = QLabel()
        icon_label.setObjectName("iconLabel")
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(recents_pixmap(self.item_data))
        info_layout.addWidget(icon_label)

        # Content layout
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        is_project = self.item_type == KEY_SEARCH_PROJ

        # Primary text (Project/Module name)
        primary_label = QLabel(self.item_data.get(
            PROJECT_NAME if is_project else RELATED_SUBMODULE))
        primary_label.setObjectName("primaryText")
        content_layout.addWidget(primary_label)

        # Secondary text (submodule or module name)
        secondary_text = self.item_data.get(
            RELATED_SUBMODULE if is_project else RELATED_MODULE)
        if secondary_text:
            secondary_label = QLabel(secondary_text)
            secondary_label.setObjectName("secondaryText")
            content_layout.addWidget(secondary_label)

        info_layout.addLayout(content_layout, 1)

        # Date
        date_text = self.item_data.get(LAST_EDITED, "")
        if date_text:
            date_label = QLabel(date_text)
            date_label.setObjectName("dateText")
            date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            info_layout.addWidget(date_label)

        main_layout.addLayout(info_layout)

        # Action buttons (only for projects)
        if is_project:
            actions = ProjectActions(
                self.item_data,
                button_object_name="search_result_proj_btn",
                report_label="Generate Report",
                margins=(28, 2, 10, 2),
            )
            actions.generateReport.connect(self.generateReport)
            actions.downloadOsi.connect(self.downloadOsi)
            actions.openProject.connect(self.openProject)
            main_layout.addWidget(actions)
            self.init_expansion(actions)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.item_type == KEY_SEARCH_MODULE:
            self.openModule.emit(self.item_data.get(MODULE_KEY))
        return super().mousePressEvent(event)


class SearchOverlay(QFrame):
    """Overlay widget that displays search results"""
    openModule = Signal(str)
    openProject = Signal(dict)
    generateReport = Signal(dict)
    downloadOsi = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Use ToolTip instead of Popup - it doesn't steal focus
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.border_radius = 12
        self.max_height = 400  # Maximum height for the overlay
        self.setObjectName("overlayFrame")
        self.search_widget = None  # Reference to the search bar widget
        self.setupUI()

        # Install event filter on application to detect clicks outside
        QApplication.instance().installEventFilter(self)

    def set_search_widget(self, widget):
        """Set the search bar widget reference"""
        self.search_widget = widget

    def setupUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for results
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("search_overlay_scrollarea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("search_overlay_scroll_content")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(3)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def eventFilter(self, obj, event):
        """Filter events to detect clicks outside the overlay and window focus changes"""
        if self.isVisible():
            # Handle mouse clicks outside overlay
            if event.type() == QEvent.Type.MouseButtonPress:
                # Get the global position of the click
                click_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()

                # Check if click is outside both overlay and search widget
                if not self.geometry().contains(self.mapFromGlobal(click_pos)):
                    # Also check if click is outside search widget
                    if self.search_widget:
                        search_rect = self.search_widget.rect()
                        search_local_pos = self.search_widget.mapFromGlobal(click_pos)
                        if not search_rect.contains(search_local_pos):
                            self.hide()
                    else:
                        self.hide()

            # Handle window deactivation (Alt+Tab, focus loss)
            elif event.type() == QEvent.Type.WindowDeactivate:
                self.hide()

            # Handle application state changes (minimize, focus loss)
            elif event.type() == QEvent.Type.ApplicationStateChange:
                self.hide()

        return super().eventFilter(obj, event)

    def showEvent(self, event):
        """Apply clipping mask when widget is shown"""
        super().showEvent(event)
        self.apply_rounded_mask()

    def resizeEvent(self, event):
        """Reapply mask when widget is resized"""
        super().resizeEvent(event)
        self.apply_rounded_mask()

    def apply_rounded_mask(self):
        """Apply a rounded rectangle mask to clip content at borders"""
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(),
                           self.border_radius, self.border_radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def adjust_size_to_content(self):
        """Adjust the overlay size to fit content, up to maximum"""
        # Get the content widget's size hint
        content_height = self.content_widget.sizeHint().height()

        # Add some padding for margins
        total_height = min(content_height + 6, self.max_height)

        # Set the height (width will be set by position_below_widget)
        if total_height > 0:
            self.setFixedHeight(total_height)
        else:
            self.setFixedHeight(80)  # Minimum height for "No results"

    def show_results(self, search_data):
        """Display search results"""
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        projects = search_data.get(KEY_SEARCH_PROJ)
        modules = search_data.get(KEY_SEARCH_MODULE)

        # Show no results message if empty
        if not projects and not modules:
            no_results = QLabel("No results found")
            no_results.setObjectName("noResults")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_results)
            # Adjust size after adding content
            QTimer.singleShot(0, self.adjust_size_to_content)
            return

        # Add Projects section
        if projects:
            projects_header = QLabel("Projects")
            projects_header.setObjectName("projectsHeader")
            self.content_layout.addWidget(projects_header)

            for proj in projects:
                result_item = SearchResultItem(proj, KEY_SEARCH_PROJ)
                result_item.openProject.connect(self._handle_open_project)
                result_item.generateReport.connect(self._handle_generate_report)
                result_item.downloadOsi.connect(self._handle_download_osi)
                self.content_layout.addWidget(result_item)

        # Add Modules section
        if modules:
            modules_header = QLabel("Modules")
            modules_header.setObjectName("modulesHeader")
            self.content_layout.addWidget(modules_header)

            for mod in modules:
                result_item = SearchResultItem(mod, KEY_SEARCH_MODULE)
                result_item.openModule.connect(self._handle_open_module)
                self.content_layout.addWidget(result_item)

        self.content_layout.addStretch()

        # Adjust size after adding all content
        QTimer.singleShot(0, self.adjust_size_to_content)

    def _handle_open_project(self, record):
        """Handle open project and close overlay"""
        self.openProject.emit(record)
        self.hide()

    def _handle_generate_report(self, record):
        """Handle generate report and close overlay"""
        self.generateReport.emit(record)
        self.hide()

    def _handle_download_osi(self, record):
        """Handle download OSI and close overlay"""
        self.downloadOsi.emit(record)
        self.hide()

    def _handle_open_module(self, module_key):
        """Handle open module and close overlay"""
        self.openModule.emit(module_key)
        self.hide()

    def position_below_widget(self, target_widget):
        """Position the overlay below the target widget"""
        global_pos = target_widget.mapToGlobal(QPoint(0, target_widget.height() + 4))
        self.move(global_pos)
        self.setFixedWidth(target_widget.width())

    def closeEvent(self, event):
        """Clean up event filter when closing"""
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)
