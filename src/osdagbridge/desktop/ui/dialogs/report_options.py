import os
import re
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QWidget, QFileDialog, QLabel, QMessageBox,
    QGroupBox, QGridLayout,
)
from PySide6.QtCore import Qt
from osdagbridge.core.reports.report_generator import (
    ReportMetadata, ReportOptions, ReportRequest
)


from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor

class ReportOptionsDialog(QDialog):
    """Design Report options dialog — Page 1 collects project metadata
    organised into three visually distinct sections (QGroupBoxes),
    Page 2 lets the user customise report sections.
    """

    # ── styling constants ────────────────────────────────────────────
    _OSDAG_GREEN = "#90AF13"
    _OSDAG_GREEN_DARK = "#64850c"

    def __init__(self, parent=None):
        super().__init__(None)
        self._main_window = parent
        self.setObjectName("report_options_dialog")
        self.resize(520, 650)

        self.setStyleSheet(self._build_stylesheet())

        self.setupWrapper()

        # The rest of UI builds inside self.content_widget
        self.stacked_widget = QStackedWidget(self.content_widget)

        self.page1 = QWidget()
        self.setup_page1()
        self.stacked_widget.addWidget(self.page1)

        self.page2 = QWidget()
        self.setup_page2()
        self.stacked_widget.addWidget(self.page2)

        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(12)
        layout.addWidget(self.stacked_widget)

        self.request = None
        self.is_preview = False

    # ── stylesheet ───────────────────────────────────────────────────

    @classmethod
    def _build_stylesheet(cls) -> str:
        """Return the complete stylesheet for the dialog."""
        return f"""
            QDialog#report_options_dialog {{
                background-color: #ffffff;
                border: 1px solid {cls._OSDAG_GREEN};
            }}

            /* Labels */
            QLabel#headline {{ font-size: 15px; font-weight: 700; color: #2d2d2d; }}
            QLabel {{ color: #1f1f1f; }}

            /* Group-box sections */
            QGroupBox {{
                font-weight: 600;
                font-size: 12px;
                color: {cls._OSDAG_GREEN_DARK};
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 14px;
                padding: 14px 10px 10px 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                color: {cls._OSDAG_GREEN_DARK};
            }}

            /* Inputs */
            QLineEdit {{
                padding: 4px 8px;
                border: 1px solid #070707;
                border-radius: 6px;
                background-color: white;
                color: #000000;
                font-weight: normal;
            }}
            QTextEdit {{
                padding: 4px 8px;
                border: 1px solid #070707;
                border-radius: 6px;
                background-color: white;
                color: #000000;
                font-weight: normal;
            }}

            /* Buttons */
            QPushButton#primary {{
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid {cls._OSDAG_GREEN};
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton#primary:hover {{ background-color: {cls._OSDAG_GREEN}; color: white; }}
            QPushButton#primary:pressed {{ background-color: {cls._OSDAG_GREEN_DARK}; color: white; }}

            QPushButton#ghost {{
                background-color: #ffffff;
                color: #1d1d1d;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton#ghost:hover {{ background-color: #f0f0f0; }}
            QPushButton#ghost:pressed {{ background-color: #d9d9d9; }}
        """

    # ── wrapper (title-bar + size-grip) ──────────────────────────────

    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window)
        self.setAttribute(Qt.WA_StyledBackground, True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle("Design Report")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("contentWidget")
        main_layout.addWidget(self.content_widget, 1)

        from PySide6.QtWidgets import QSizeGrip
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(16, 16)

        grip_layout = QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 2, 2)
        grip_layout.addStretch(1)
        grip_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(grip_layout)

    # ── page 1 — project metadata (3 boxes) ─────────────────────────

    def setup_page1(self):
        layout = QVBoxLayout(self.page1)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Box 1: Project & Team Information ────────────────────────
        box1 = QGroupBox("Project && Team Information")
        form1 = QFormLayout()
        form1.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form1.setHorizontalSpacing(12)
        form1.setVerticalSpacing(8)

        self.project_name = QLineEdit()
        form1.addRow("Project Name :", self.project_name)

        self.designer = QLineEdit()
        form1.addRow("Designer :", self.designer)

        self.reviewer = QLineEdit()
        form1.addRow("Reviewer :", self.reviewer)

        # Use / Save Profile buttons
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(8)
        use_profile_btn = QPushButton("Use Profile")
        use_profile_btn.setObjectName("ghost")
        use_profile_btn.setCursor(pointing_hand_cursor())
        use_profile_btn.clicked.connect(self.load_profile)
        save_profile_btn = QPushButton("Save Profile")
        save_profile_btn.setObjectName("ghost")
        save_profile_btn.setCursor(pointing_hand_cursor())
        save_profile_btn.clicked.connect(self.save_profile)
        profile_layout.addWidget(use_profile_btn)
        profile_layout.addWidget(save_profile_btn)
        profile_layout.addStretch()
        form1.addRow("", profile_layout)

        self.group_name = QLineEdit()
        form1.addRow("Organisation / Design Team Name :", self.group_name)

        # Organisation Logo (with Browse)
        self.org_logo = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("ghost")
        browse_btn.setCursor(pointing_hand_cursor())
        browse_btn.clicked.connect(self.browse_logo)
        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)
        logo_layout.addWidget(self.org_logo, 1)
        logo_layout.addWidget(browse_btn)
        form1.addRow("Organisation Logo :", logo_layout)

        box1.setLayout(form1)
        layout.addWidget(box1)

        # ── Box 2: Client & Job Information ──────────────────────────
        box2 = QGroupBox("Client && Job Information")
        form2 = QFormLayout()
        form2.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form2.setHorizontalSpacing(12)
        form2.setVerticalSpacing(8)

        self.client = QLineEdit()
        form2.addRow("Client Name && Organisation :", self.client)

        self.job_number = QLineEdit()
        form2.addRow("Job Number :", self.job_number)

        self.report_version = QLineEdit()
        form2.addRow("Report Version :", self.report_version)

        box2.setLayout(form2)
        layout.addWidget(box2)

        # ── Box 3: Additional Comments ───────────────────────────────
        box3 = QGroupBox("Additional Comments")
        box3_layout = QVBoxLayout()
        box3_layout.setContentsMargins(10, 10, 10, 10)

        self.comments = QTextEdit()
        self.comments.setMinimumHeight(80)
        box3_layout.addWidget(self.comments)

        box3.setLayout(box3_layout)
        layout.addWidget(box3)

        # ── Navigation buttons ───────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()
        next_btn = QPushButton("Next")
        next_btn.setObjectName("primary")
        next_btn.setCursor(pointing_hand_cursor())
        next_btn.clicked.connect(self.go_next)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(pointing_hand_cursor())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(next_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ── page 2 — customise report sections ───────────────────────────

    def setup_page2(self):
        layout = QVBoxLayout(self.page2)

        title_lbl = QLabel("Customize Report Sections")
        title_lbl.setObjectName("headline")
        layout.addWidget(title_lbl)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)

        sections = [
            ("Input Parameters", []),
            ("Design Checks", [
                "Section Classification", "Moment Capacity", "Shear Capacity",
                "LTB Check", "Stiffener Checks", "Deflection Checks",
                "Shear Connectors", "Cross Bracing", "End Diaphragm", "Design Summary"
            ]),
            ("Views", []),
            ("Design Log", [])
        ]

        for parent_text, children in sections:
            parent_item = QTreeWidgetItem(self.tree, [parent_text])
            parent_item.setFlags(
                parent_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
            )
            parent_item.setCheckState(0, Qt.Checked)

            for child_text in children:
                child_item = QTreeWidgetItem(parent_item, [child_text])
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Checked)

        self.tree.expandAll()

        btn_layout = QHBoxLayout()
        preview_btn = QPushButton("Preview PDF")
        preview_btn.setObjectName("ghost")
        preview_btn.setCursor(pointing_hand_cursor())
        preview_btn.clicked.connect(self.preview_pdf)
        btn_layout.addWidget(preview_btn)
        btn_layout.addStretch()

        back_btn = QPushButton("Back")
        back_btn.setObjectName("ghost")
        back_btn.setCursor(pointing_hand_cursor())
        back_btn.clicked.connect(self.go_back)
        save_btn = QPushButton("Save PDF")
        save_btn.setObjectName("primary")
        save_btn.setCursor(pointing_hand_cursor())
        save_btn.clicked.connect(self.save_pdf)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(pointing_hand_cursor())
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ── actions ──────────────────────────────────────────────────────

    def browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.org_logo.setText(path)

    # ── profile keys (ordered) ────────────────────────────────────────
    _PROFILE_FIELDS = [
        ("ProjectName",       "Project Name"),
        ("Designer",          "Designer"),
        ("Reviewer",          "Reviewer"),
        ("OrganisationName",  "Organisation / Design Team Name"),
        ("OrganisationLogo",  "Organisation Logo Path"),
    ]

    # regex to parse a single \ProfileField{Key}{Value} line
    _PROFILE_RE = re.compile(
        r"\\ProfileField\{(?P<key>[^}]+)\}\{(?P<value>[^}]*)\}"
    )

    def _get_profile_data(self) -> dict:
        """Collect Box 1 field values into an ordered dict keyed by
        the canonical TeX profile-field names."""
        return {
            "ProjectName":      self.project_name.text().strip(),
            "Designer":         self.designer.text().strip(),
            "Reviewer":         self.reviewer.text().strip(),
            "OrganisationName": self.group_name.text().strip(),
            "OrganisationLogo": self.org_logo.text().strip(),
        }

    def save_profile(self):
        """Save Project & Team Information fields to a `.tex` profile
        file at a user-chosen location.

        • Validates that at least one field is non-empty.
        • Writes a human-readable, machine-parseable LaTeX file.
        """
        data = self._get_profile_data()

        # Guard: require at least one field to be filled
        if not any(data.values()):
            CustomMessageBox(
                title="Empty Profile",
                text="Please fill in at least one field before saving a profile.",
                buttons=["OK"],
                dialogType=MessageBoxType.Critical
            ).exec()
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Profile",
            os.path.expanduser("~/OsdagBridge_Profile.tex"),
            "TeX Profile Files (*.tex)",
        )
        if not path:
            return  # user cancelled

        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("%% OsdagBridge — Design Report Profile\n")
                fh.write(
                    f"%% Generated: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
                )
                fh.write("%%\n")
                fh.write(
                    "%% This file stores Project & Team Information for re-use.\n"
                )
                fh.write(
                    "%% Do not edit the \\ProfileField lines manually unless\n"
                )
                fh.write("%% you know what you are doing.\n\n")
                for key, label in self._PROFILE_FIELDS:
                    fh.write(
                        f"\\ProfileField{{{key}}}{{{data.get(key, '')}}}  "
                        f"% {label}\n"
                    )
            CustomMessageBox(
                title="Profile Saved",
                text=f"Profile saved successfully.\n\n{path}",
                buttons=["OK"],
                dialogType=MessageBoxType.Success
            ).exec()
        except OSError as exc:
            CustomMessageBox(
                title="Save Error",
                text=f"Could not write profile file:\n{exc}",
                buttons=["OK"],
                dialogType=MessageBoxType.Critical
            ).exec()

    def load_profile(self):
        """Browse for a previously saved `.tex` profile and auto-fill
        the Project & Team Information fields from it."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Profile",
            os.path.expanduser("~"),
            "TeX Profile Files (*.tex)",
        )
        if not path:
            return  # user cancelled

        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except OSError as exc:
            CustomMessageBox(
                title="Read Error",
                text=f"Could not read profile file:\n{exc}",
                buttons=["OK"],
                dialogType=MessageBoxType.Critical
            ).exec()
            return

        parsed: dict[str, str] = {}
        for match in self._PROFILE_RE.finditer(content):
            parsed[match.group("key")] = match.group("value")

        if not parsed:
            CustomMessageBox(
                title="Invalid Profile",
                text="The selected file does not contain any valid OsdagBridge profile data.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        # Populate Box 1 fields
        self.project_name.setText(parsed.get("ProjectName", ""))
        self.designer.setText(parsed.get("Designer", ""))
        self.reviewer.setText(parsed.get("Reviewer", ""))
        self.group_name.setText(parsed.get("OrganisationName", ""))
        self.org_logo.setText(parsed.get("OrganisationLogo", ""))

    def go_next(self):
        self.stacked_widget.setCurrentIndex(1)
        self.title_bar.setTitle("Customize Report")

    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)
        self.title_bar.setTitle("Design Report")

    def get_checked_leaf_sections(self):
        sections = []
        # Walk all top-level and child items
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent.checkState(0) in (Qt.Checked, Qt.PartiallyChecked):
                sections.append(parent.text(0))
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) in (Qt.Checked, Qt.PartiallyChecked):
                    sections.append(child.text(0))
        return sections

    # ── build report request ─────────────────────────────────────────

    def build_request(self, output_path: str) -> ReportRequest:
        output_path = os.path.abspath(output_path)
        output_dir = os.path.dirname(output_path)
        if not output_dir:
            output_dir = os.path.expanduser('~')
        file_stem = os.path.splitext(os.path.basename(output_path))[0]
        if not file_stem:
            file_stem = 'osdag_bridge_report'

        metadata = ReportMetadata(
            project_name=self.project_name.text(),
            project_location='',
            designer=self.designer.text(),
            reviewer=self.reviewer.text(),
            client=self.client.text(),
            company=self.group_name.text(),
            group_name=self.group_name.text(),
            subtitle=self.report_version.text(),
            job_number=self.job_number.text(),
            additional_comments=self.comments.toPlainText(),
            logo_path=self.org_logo.text() or None,
            report_date=datetime.date.today().isoformat()
        )

        checked_sections = self.get_checked_leaf_sections()
        include_figures = "Views" in checked_sections

        options = ReportOptions(
            sections=checked_sections,
            include_figures=include_figures,
            include_toc=True,
            include_pdf=True
        )

        return ReportRequest(
            metadata=metadata,
            options=options,
            output_dir=output_dir,
            file_stem=file_stem
        )

    def preview_pdf(self):
        import tempfile
        tmp_dir = tempfile.mkdtemp(prefix="osdag_preview_")
        path = os.path.join(tmp_dir, "preview_report.pdf")
        self.request = self.build_request(path)
        self.is_preview = True
        self.accept()

    def save_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self.request = self.build_request(path)
            self.is_preview = False
            self.accept()
