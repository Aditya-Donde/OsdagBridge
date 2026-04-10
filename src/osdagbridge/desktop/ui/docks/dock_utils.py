from PySide6.QtWidgets import QComboBox, QLineEdit, QSizePolicy

def apply_field_style(widget):
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    widget.setMinimumHeight(28)

    if isinstance(widget, QComboBox):
        widget.setStyleSheet("""
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
            QComboBox QAbstractItemView{
                background-color: white;
                border: 1px solid black;
                color: black;
            }
            QComboBox:disabled{
                padding: 1px 7px;
                border: 1px solid #666;
                border-radius: 5px;
                background-color: #f1f1f1;
                color: #666;
            }
        """)
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet("""
            QLineEdit {
                padding: 1px 7px;
                border: 1px solid #070707;
                border-radius: 6px;
                background-color: white;
                color: #000000;
            }
            QLineEdit[error='true'] {
                padding: 1px 7px;
                border: 1px solid #FF0000;
                border-radius: 6px;
                background-color: white;
                color: #000000;
            }
            QLineEdit:disabled {
                padding: 1px 7px;
                border: 1px solid #070707;
                border-radius: 6px;
                background-color: #f1f1f1;
                color: #666;
            }
            QLineEdit[error='true']:disabled {
                padding: 1px 7px;
                border: 1px solid #FF0000;
                border-radius: 6px;
                background-color: #f1f1f1;
                color: #666;
            }
        """)
