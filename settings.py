from PyQt5.QtWidgets import QLineEdit, QVBoxLayout, QDialog, QPushButton

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Connection Settings')
        self.layout = QVBoxLayout(self)

        self.entry1 = QLineEdit(self)
        self.entry1.setPlaceholderText('Enter setting 1')
        self.layout.addWidget(self.entry1)

        self.entry2 = QLineEdit(self)
        self.entry2.setPlaceholderText('Enter setting 2')
        self.layout.addWidget(self.entry2)

        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

    def save_settings(self):
        # Placeholder: save settings logic
        setting1 = self.entry1.text()
        setting2 = self.entry2.text()
        print(f'Settings saved: {setting1}, {setting2}')
        self.accept()