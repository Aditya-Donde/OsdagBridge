"""Core UIBuilder class — composes the mixins and exposes the two
public entry points (``build_tab`` and ``build``).

All field/section/CAD/wiring methods live in the mixin modules; this
file just stitches them together and handles the top-level layout
dispatch (description? cards? sections? legacy? rows?).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.builder.cad import CADMixin
from osdagbridge.desktop.ui.dialogs.tabs.builder.constants import (
    _DEFAULT_FIELD_WIDTH,
    _DEFAULT_LABEL_WIDTH,
)
from osdagbridge.desktop.ui.dialogs.tabs.builder.fields import FieldBuildersMixin
from osdagbridge.desktop.ui.dialogs.tabs.builder.layouts import LayoutBuildersMixin
from osdagbridge.desktop.ui.dialogs.tabs.builder.special_sections import SpecialSectionsMixin
from osdagbridge.desktop.ui.dialogs.tabs.builder.wiring import WiringMixin


class UIBuilder(
    FieldBuildersMixin,
    LayoutBuildersMixin,
    SpecialSectionsMixin,
    CADMixin,
    WiringMixin,
):
    """Renders a complete tab UI from a schema dict.

    Parameters
    ----------
    owner:
        QWidget that receives bound widget attributes.  When a schema field
        declares ``"bind": "my_combo"``, the builder does
        ``setattr(owner, "my_combo", widget)``.
    schema:
        Schema dict (from the schemas/ directory).
    tab_class_resolver:
        Optional callable ``(class_name: str) -> Type`` used by the
        ``tab_container`` section to look up sub-tab classes. Defaults to the
        plate-girder Additional Inputs registry. Pass a different resolver to
        plug in another bridge type's tab catalogue without touching the
        builder.
    """

    def __init__(self, owner: QWidget, schema: dict, tab_class_resolver=None) -> None:
        self.owner  = owner
        self.schema = schema
        self.tab_class_resolver = tab_class_resolver

    def build_tab(self, tab_widget: QWidget) -> None:
        """Build the full tab UI into *tab_widget*.

        Handles scroll area, card framing, section boxes and field rows.
        After calling this the tab class only needs to add custom widgets
        (e.g. CAD drawings) to ``tab_widget``'s layout.
        """
        tab_widget.setStyleSheet("background-color: #f5f5f5;")

        schema = self.schema
        margins = schema.get("margins", [12, 12, 12, 12])
        if not isinstance(margins, (list, tuple)) or len(margins) != 4:
            margins = [12, 12, 12, 12]
        spacing = int(schema.get("spacing", 12))
        add_stretch = bool(schema.get("add_stretch", True))
        scrollable = bool(schema.get("scrollable", True))

        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        if scrollable:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")

            scroll_content = QWidget()
            scroll_content.setStyleSheet("background-color: #f5f5f5;")

            page_layout = QVBoxLayout(scroll_content)
            page_layout.setContentsMargins(*[int(v) for v in margins])
            page_layout.setSpacing(spacing)
            self.page_layout = page_layout

            self._build_schema_content(page_layout)
            if add_stretch:
                page_layout.addStretch()

            scroll.setWidget(scroll_content)
            main_layout.addWidget(scroll)
        else:
            main_layout.setContentsMargins(*[int(v) for v in margins])
            main_layout.setSpacing(spacing)
            self.page_layout = main_layout

            self._build_schema_content(main_layout)
            if add_stretch:
                main_layout.addStretch()

        self._wire_conditions()
        self._wire_deferred_cad_bindings()

    def _build_schema_content(self, page_layout: QLayout) -> None:
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))
        has_layout = "layout" in schema
        has_description = "description" in schema
        has_cards       = "cards" in schema
        has_sections    = "sections" in schema
        has_legacy_groups = self._has_legacy_groups(schema)

        if has_layout:
            self._build_layout_node(page_layout, schema["layout"], label_width, field_width)
        elif has_description and self._description_has_content(schema.get("description")):
            self._build_two_panel(page_layout)
        elif has_cards:
            self._build_cards_column(page_layout, schema["cards"])
        elif has_sections:
            self._build_section_cards(page_layout, schema["sections"])
        elif has_legacy_groups:
            self._build_legacy_groups(page_layout)
        else:
            self.build(page_layout)

    def build(self, parent_layout: QLayout) -> None:
        """Populate *parent_layout* from the schema's top-level structure."""
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))

        if "cards" in schema:
            self._build_cards_column(parent_layout, schema["cards"])
        elif "sections" in schema:
            self._build_sections(parent_layout, schema["sections"], label_width, field_width)
        elif self._has_legacy_groups(schema):
            self._build_legacy_groups(parent_layout)
        elif "rows" in schema:
            self._build_rows(parent_layout, schema["rows"], label_width, field_width)
        elif "columns" in schema:
            self._build_columns(parent_layout, schema["columns"], label_width, field_width)
