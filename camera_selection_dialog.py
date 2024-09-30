# camera_selection_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton

class CameraSelectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Number of Cameras")
        self.num_cameras = 3  # Default
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        label = QLabel("Select the number of cameras (3-6):")
        self.combo_box = QComboBox()
        self.combo_box.addItems([str(i) for i in range(3, 7)])
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addWidget(self.combo_box)
        layout.addWidget(ok_button)
        self.setLayout(layout)

    def get_num_cameras(self):
        return int(self.combo_box.currentText())
