import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from desktop_app import MainWindow

def test_ui():
    app = QApplication.instance()
    print('Testing MainWindow...')
    print(f'Projects Button exists: {hasattr(mw, "projects_btn")}')
    if hasattr(mw, "projects_btn"):
        print(f'Projects Button text: {mw.projects_btn.text()}')
    app.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    QTimer.singleShot(1000, test_ui)
    app.exec()
