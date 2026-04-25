"""CAD widget integration — instantiate CAD widgets from the registry,
bind them, wire reactivity to schema-declared source widgets, and lay
out CAD rows / legends.
"""

import logging

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.builder.constants import (
    _CARD_STYLE,
    _DEFAULT_FIELD_WIDTH,
    _DEFAULT_LABEL_WIDTH,
)

_log = logging.getLogger(__name__)


class CADMixin:
    """Builders for ``cad``, ``cad_row``, and ``legend`` schema sections."""

    _SIZE_POLICY_MAP = {
        "expanding": QSizePolicy.Expanding,
        "preferred": QSizePolicy.Preferred,
        "fixed":     QSizePolicy.Fixed,
        "minimum":   QSizePolicy.Minimum,
    }

    def _build_cad_section(self, parent_layout: QLayout, section: dict) -> QWidget | None:
        """Instantiate a CAD widget from the registry, bind, and wire reactivity.

        Schema shape::

            {
                "type": "cad",
                "widget": "SupportDetailCADWidget",
                "bind": "right_cad",
                "min_size": [150, 200],
                "size_policy": "expanding",
                "update_method": "update_params",
                "params_map": {
                    "bearing_length": {"widget": "bearing_length_input",
                                        "cast": "float", "default": 400}
                },
                "reactive_sources": [
                    {"widget": "bearing_length_input", "signal": "textChanged"}
                ],
            }
        """
        widget_name = section.get("widget")
        if not widget_name:
            return None

        try:
            from osdagbridge.desktop.ui.dialogs.tabs.cad_registry import CAD_WIDGETS
        except ImportError:
            _log.warning("UIBuilder[%s]: cad_registry not importable — CAD widget %r skipped", type(self.owner).__name__, widget_name)
            return None

        widget_cls = CAD_WIDGETS.get(str(widget_name))
        if widget_cls is None:
            _log.warning("UIBuilder[%s]: CAD widget %r not in cad_registry.CAD_WIDGETS", type(self.owner).__name__, widget_name)
            return None

        cad_widget = widget_cls()

        for prop, val in (section.get("properties") or {}).items():
            try:
                setattr(cad_widget, prop, val)
            except Exception as e:
                _log.warning("UIBuilder[%s]: Failed to set property %r=%r on %s: %s",
                             type(self.owner).__name__, prop, val, type(cad_widget).__name__, e)

        self._apply_cad_sizing(cad_widget, section)

        bind = section.get("bind")
        if bind:
            setattr(self.owner, str(bind), cad_widget)
            cad_widget.setObjectName(str(bind))

        update_method_name = str(section.get("update_method", "update_params"))
        params_map = section.get("params_map") or {}
        reactive_sources = section.get("reactive_sources") or []

        should_wire_cad_update = bool(params_map or reactive_sources or section.get("update_method"))
        if should_wire_cad_update and not hasattr(cad_widget, update_method_name):
            _log.warning(
                "UIBuilder[%s]: CAD widget %s has no method %r",
                type(self.owner).__name__, type(cad_widget).__name__, update_method_name,
            )

        def refresh(*_args) -> None:
            method = getattr(cad_widget, update_method_name, None)
            if not callable(method):
                return
            params: dict = {}
            for param_name, entry in params_map.items():
                if isinstance(entry, str):
                    source_name, cast, default = entry, None, None
                else:
                    source_name = entry.get("widget")
                    cast = entry.get("cast")
                    default = entry.get("default")
                source = getattr(self.owner, str(source_name), None) if source_name else None
                raw = self._read_widget_value(source)
                params[param_name] = self._cast_value(raw, cast, default)
            method(params)

        for src in reactive_sources:
            source_name = src.get("widget") if isinstance(src, dict) else src
            if not source_name:
                continue
            signal_name = src.get("signal", "textChanged") if isinstance(src, dict) else "textChanged"
            source = getattr(self.owner, str(source_name), None)
            if source is None:
                _log.debug(
                    "UIBuilder[%s]: reactive source %r not on owner (bind it before CAD section)",
                    type(self.owner).__name__, source_name,
                )
                continue
            signal = getattr(source, str(signal_name), None)
            if signal is None:
                continue
            signal.connect(refresh)

        if reactive_sources or params_map:
            refresh()

        display_widget = cad_widget
        if section.get("scrollable"):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
            scroll.setWidget(cad_widget)
            display_widget = scroll
            min_h = section.get("min_height")
            if min_h:
                display_widget.setMinimumHeight(int(min_h))

        stretch = int(section.get("stretch", 0))
        if isinstance(parent_layout, QHBoxLayout) and stretch > 0:
            parent_layout.addWidget(display_widget, stretch)
        else:
            parent_layout.addWidget(display_widget)
        return cad_widget

    def _build_cad_row_section(self, parent_layout: QLayout, section: dict) -> None:
        """Horizontal row wrapper for multiple widgets (CAD, Legend, etc.)."""
        wrap = QFrame()
        wrap.setStyleSheet(_CARD_STYLE)
        self._apply_cad_sizing(wrap, section)

        row = QHBoxLayout(wrap)
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(int(section.get("spacing", 12)))

        items = section.get("widgets") or section.get("cads") or []
        for item in items:
            itype = str(item.get("type", "cad")).lower()
            stretch = int(item.get("stretch", 0))
            if itype == "cad":
                self._build_cad_section(row, item)
            elif itype == "legend":
                legend = self._build_legend_widget(item)
                if stretch > 0:
                    row.addWidget(legend, stretch)
                else:
                    row.addWidget(legend)
            else:
                self._dispatch_section(row, item, _DEFAULT_LABEL_WIDTH, _DEFAULT_FIELD_WIDTH)

        parent_layout.addWidget(wrap)

    def _build_legend_widget(self, section: dict) -> QWidget:
        """Build a small color-coded legend box."""
        legend = QFrame()
        legend.setStyleSheet(
            "QFrame { border: 1px solid #d8d8d8; border-radius: 8px; background-color: #ffffff; }"
        )
        self._apply_cad_sizing(legend, section)

        layout = QVBoxLayout(legend)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title_text = section.get("title", "Legend")
        if title_text:
            title = QLabel(title_text)
            title.setStyleSheet("font-size: 11px; font-weight: 700; color: #333333; border: none;")
            layout.addWidget(title)

        for item in section.get("items", []):
            row = QHBoxLayout()
            row.setSpacing(6)

            color_box = QFrame()
            color_box.setFixedSize(12, 12)
            color = item.get("color", "#000000")
            color_box.setStyleSheet(
                f"background-color: {color}; border: 1px solid #999999; border-radius: 2px;"
            )
            row.addWidget(color_box)

            label = QLabel(item.get("label", ""))
            label.setStyleSheet("font-size: 11px; color: #444444; border: none;")
            row.addWidget(label)
            row.addStretch(1)
            layout.addLayout(row)

        layout.addStretch(1)
        return legend

    def _apply_cad_sizing(self, widget: QWidget, section: dict) -> None:
        min_size = section.get("min_size")
        if min_size:
            widget.setMinimumSize(int(min_size[0]), int(min_size[1]))
        max_size = section.get("max_size")
        if max_size:
            widget.setMaximumSize(int(max_size[0]), int(max_size[1]))
        policy_name = str(section.get("size_policy", "expanding")).lower()
        policy = self._SIZE_POLICY_MAP.get(policy_name, QSizePolicy.Expanding)
        widget.setSizePolicy(policy, policy)
