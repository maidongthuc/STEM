import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag
import paho.mqtt.client as mqtt

broker = "broker.hivemq.com"
port = 1883
topic = "Livingroom/device_1"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(topic)

def on_message(client, userdata, msg):
    print(f"Message received: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port, 60)
client.loop_start()

class DraggableLabel(QLabel):
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        self.text = text

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startPos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton:
            return

        drag = QDrag(self)
        mimeData = QMimeData()
        
        # Set the text of the label as the mime data
        mimeData.setText(self.text)

        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())
        dropAction = drag.exec_(Qt.MoveAction)

class EditableLabel(QFrame):
    def __init__(self, text, parent):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        if 'Up' in text or 'Down' in text:
            parts = text.split(' ')
            self.prefix = QLabel(parts[0] + ' ', self)
            self.edit = QLineEdit(parts[1], self)
            self.suffix = QLabel(' ' + parts[2], self)
        elif 'Turn right' in text or 'Turn left' in text:
            parts = text.split(' ')
            self.prefix = QLabel(parts[0] + ' ' + parts[1] + ' ', self)
            self.edit = QLineEdit(parts[2], self)
            self.suffix = QLabel(' ' + parts[3], self)
        
        layout.addWidget(self.prefix)
        layout.addWidget(self.edit)
        layout.addWidget(self.suffix)
        self.edit.returnPressed.connect(self.convertToDraggableLabel)

    def convertToDraggableLabel(self):
        text = self.prefix.text() + self.edit.text() + self.suffix.text()
        draggable_label = DraggableLabel(text, self.parent())
        layout = self.parent().layout()
        index = layout.indexOf(self)
        layout.insertWidget(index, draggable_label)
        self.deleteLater()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startPos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton:
            return

        drag = QDrag(self)
        mimeData = QMimeData()
        
        # Set the text of the label as the mime data
        mimeData.setText(self.prefix.text() + self.edit.text() + self.suffix.text())

        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())
        dropAction = drag.exec_(Qt.MoveAction)

    def get_text(self):
        return self.prefix.text() + self.edit.text() + self.suffix.text()

    def get_value(self):
        return self.edit.text()

class DropArea(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setLineWidth(2)
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            source = event.source()
            
            if source.parent() == self:
                # Rearrange within DropArea
                source.setParent(None)
                self.layout.removeWidget(source)
                self.layout.insertWidget(self.getDropPosition(event.pos()), source)
            else:
                # Add new editable label from blocks
                if 'Up' in text or 'Down' in text or 'Turn right' in text or 'Turn left' in text:
                    widget = EditableLabel(text, self)
                else:
                    widget = DraggableLabel(text, self)
                self.layout.insertWidget(self.getDropPosition(event.pos()), widget)

            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def getDropPosition(self, pos):
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item.spacerItem():
                continue
            widget = item.widget()
            if widget and pos.y() < widget.y() + widget.height() // 2:
                return i
        return self.layout.count() - 1

    def get_all_steps_and_degrees(self):
        commands = []
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, EditableLabel):
                    text = widget.get_text()
                    if 'Up' in text:
                        commands.append(f"u{widget.get_value()}")
                    elif 'Down' in text:
                        commands.append(f"d{widget.get_value()}")
                    elif 'Turn right' in text:
                        commands.append(f"r{widget.get_value()}")
                    elif 'Turn left' in text:
                        commands.append(f"l{widget.get_value()}")
        return commands

    def clear(self):
        while self.layout.count() > 1:  # Keep the spacer
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

class DragAndDropApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        hbox = QHBoxLayout()

        self.blocks = QVBoxLayout()
        self.blocks.addWidget(DraggableLabel('Start', self))
        self.blocks.addWidget(DraggableLabel('Up 10 Steps', self))
        self.blocks.addWidget(DraggableLabel('Down 15 Steps', self))
        self.blocks.addWidget(DraggableLabel('Turn right 15 Degrees', self))
        self.blocks.addWidget(DraggableLabel('Turn left 20 Degrees', self))

        self.workspace = DropArea()

        hbox.addLayout(self.blocks)
        hbox.addWidget(self.workspace)

        main_layout = QVBoxLayout()
        main_layout.addLayout(hbox)

        # Create button layout
        button_layout = QHBoxLayout()
        self.clear_button = QPushButton('Clear', self)
        self.clear_button.clicked.connect(self.on_clear_click)
        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.on_ok_click)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.ok_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('Drag & Drop App')
        self.show()

    def on_ok_click(self):
        commands = self.workspace.get_all_steps_and_degrees()
        for command in commands:
            client.publish(topic, command)
            print(f"Published: {command}")

    def on_clear_click(self):
        self.workspace.clear()

def main():
    app = QApplication(sys.argv)
    ex = DragAndDropApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
