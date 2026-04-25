import os

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QApplication = pytest.importorskip("PySide6.QtWidgets").QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _cleanup_widgets(qapp):
    yield
    qapp.processEvents()
    for widget in list(qapp.topLevelWidgets()):
        try:
            widget.close()
        except Exception:
            pass
    qapp.processEvents()
