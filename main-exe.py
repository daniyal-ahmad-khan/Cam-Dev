import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt
from main_window import MainWindow
import logging

def apply_dark_theme(app):
    app.setStyle('Fusion')
    dark_palette = QPalette()

    # Set the palette colors for a dark theme
    dark_palette.setColor(QPalette.Window, QColor(45, 45, 48))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 48))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(0, 122, 204))
    dark_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)

    # Apply custom fonts
    font = QFont("Roboto", 10)
    app.setFont(font)

def excepthook(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
    QMessageBox.critical(None, "Critical Error",
                         f"An un-expected error occurred:\n{exc_value}\n\nSee 'video_stitcher.log' for more details.")
    sys.exit(1)

def get_qss_file_path():
    """Helper function to get the correct path for dark_theme.qss."""
    if hasattr(sys, '_MEIPASS'):
        # If the program is running from a PyInstaller bundle, use _MEIPASS
        return os.path.join(sys._MEIPASS, 'dark_theme.qss')
    else:
        # If running in a normal environment, use the current directory
        return os.path.join(os.path.dirname(__file__), 'dark_theme.qss')

def main():
    # Set the global exception handler
    sys.excepthook = excepthook

    app = QApplication(sys.argv)

    # Apply the dark theme
    apply_dark_theme(app)

    # Apply a global style sheet
    qss_file_path = get_qss_file_path()
    try:
        with open(qss_file_path, 'r') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        logging.critical(f"Could not find the QSS file at {qss_file_path}", exc_info=True)
        QMessageBox.critical(None, "File Not Found", "The required theme file 'dark_theme.qss' was not found.")

    main_window = MainWindow()
    main_window.show()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical("Exception in QApplication exec_", exc_info=True)
        QMessageBox.critical(None, "Critical Error",
                             f"An unexpected error occurred:\n{str(e)}\n\nSee 'video_stitcher.log' for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
