import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap
import time
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QPlainTextEdit


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'micrOS devToolKit GUI dashboard'
        self.left = 10
        self.top = 10
        self.width = 700
        self.height = 400
        self.buttons_list = []
        self.pbar = None
        self.pbar_status = 0
        self.dropdown_objects_list = {}
        self.console = MyConsole(self)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("background-color: grey")
        self.progressbar()

    def buttons(self):
        height = 40
        width = 200
        yoffset = 10
        buttons = {'Deploy over USB': ['This is an example button',
                                       20, 100, width, height, self.on_click_usb_deploy, 'darkCyan'],
                   'OTA-OverTheAir update': ['This is an example button',
                                       20, 100+height+yoffset, width, height, self.on_click_ota_update, 'darkCyan'],
                   'Update over USB': ['This is an example button',
                                       20, 100+(height+yoffset)*2, width, height, self.on_click_usb_update, 'darkCyan']}

        for key, data_struct in buttons.items():
            tool_tip = data_struct[0]
            x = data_struct[1]
            y = data_struct[2]
            w = data_struct[3]
            h = data_struct[4]
            event_cbf = data_struct[5]
            bg = data_struct[6]

            button = QPushButton(key, self)
            button.setToolTip(tool_tip)
            button.setGeometry(x, y, w, h)
            button.setStyleSheet("QPushButton"
                                 "{"
                                 "background-color : darkCyan;"
                                 "}"
                                 "QPushButton::pressed"
                                 "{"
                                 "background-color : darkGreen;"
                                 "}")


            #"background-color: {}; border: 2px solid black;".format(bg))
            button.clicked.connect(event_cbf)

    @pyqtSlot()
    def on_click_usb_deploy(self):
        print('on_click_usb_deploy')
        self.console.append_output('on_click_usb_deploy')
        self.progressbar_update()

    @pyqtSlot()
    def on_click_ota_update(self):
        print('on_click_ota_update')
        self.console.append_output('on_click_ota_update')
        self.progressbar_update()

    @pyqtSlot()
    def on_click_usb_update(self):
        print('on_click_usb_update')
        self.console.append_output('on_click_usb_update')
        self.progressbar_update()

    def draw_logo(self):
        label = QLabel(self)
        label.setGeometry(20, 10, 80, 80)
        label.setScaledContents(True)
        pixmap = QPixmap('/Users/bnm/Documents/NodeMcu/MicrOs/media/logo_mini.png')
        label.setPixmap(pixmap)

    def progressbar(self):
        # creating progress bar
        self.pbar = QProgressBar(self)

        # setting its geometry
        self.pbar.setGeometry(10, self.height-40, self.width-20, 25)

    def progressbar_update(self, value=None, reset=False):
        if reset:
            self.pbar_status = 0
        if value is not None and 0 <= value <= 100:
            self.pbar_status = value
        self.pbar_status = self.pbar_status + 1 if self.pbar_status < 100 else 0
        self.pbar.setValue(self.pbar_status)
        print(self.pbar_status)

    def draw(self):
        self.show()

    def dropdown_board(self):
        dropdown_label = QLabel(self)
        dropdown_label.setText("Select board".upper())
        dropdown_label.setGeometry(250, 84, 170, 30)

        # creating a combo box widget
        combo_box = QComboBox(self)

        # setting geometry of combo box
        combo_box.setGeometry(250, 110, 170, 30)

        # geek list
        geek_list = ["esp8266", "esp32"]

        # making it editable
        combo_box.setEditable(False)

        # adding list of items to combo box
        combo_box.addItems(geek_list)

        combo_box.setStyleSheet("QComboBox"
                                     "{"
                                     "border : 3px solid purple;"
                                     "}"
                                     "QComboBox::on"
                                     "{"
                                     "border : 4px solid;"
                                     "border-color : orange orange orange orange;"
                                
                                     "}")

        # getting view part of combo box
        view = combo_box.view()

        # making view box hidden
        view.setHidden(False)

        self.dropdown_objects_list['board'] = combo_box
        combo_box.activated.connect(self.get_dropdown_values)

    def dropdown_micropythonbin(self):
        dropdown_label = QLabel(self)
        dropdown_label.setText("Select micropython".upper())
        dropdown_label.setGeometry(450, 84, 170, 30)

        # creating a combo box widget
        combo_box = QComboBox(self)

        # setting geometry of combo box
        combo_box.setGeometry(450, 110, 170, 30)

        # geek list
        geek_list = ["micropython_1.11.bin", "micropython_1.12.bin"]

        # making it editable
        combo_box.setEditable(False)

        # adding list of items to combo box
        combo_box.addItems(geek_list)

        combo_box.setStyleSheet("QComboBox"
                                "{"
                                "border : 3px solid green;"
                                "}"
                                "QComboBox::on"
                                "{"
                                "border : 4px solid;"
                                "border-color : orange orange orange orange;"

                                "}")

        # getting view part of combo box
        view = combo_box.view()

        # making view box hidden
        view.setHidden(False)

        self.dropdown_objects_list['micropython'] = combo_box
        combo_box.activated.connect(self.get_dropdown_values)

    def dropdown_device(self):
        dropdown_label = QLabel(self)
        dropdown_label.setText("Select device".upper())
        dropdown_label.setGeometry(250, 140, 170, 20)

        # creating a combo box widget
        combo_box = QComboBox(self)

        # setting geometry of combo box
        combo_box.setGeometry(250, 160, 170, 30)

        # geek list
        geek_list = ["BedLamp", "airquality", "mazsola"]

        # making it editable
        combo_box.setEditable(False)

        # adding list of items to combo box
        combo_box.addItems(geek_list)

        combo_box.setStyleSheet("QComboBox"
                                "{"
                                "border : 3px solid blue;"
                                "}"
                                "QComboBox::on"
                                "{"
                                "border : 4px solid;"
                                "border-color : orange orange orange orange;"

                                "}")

        # getting view part of combo box
        view = combo_box.view()

        # making view box hidden
        view.setHidden(False)

        self.dropdown_objects_list['device'] = combo_box
        combo_box.activated.connect(self.get_dropdown_values)

    def get_dropdown_values(self, index):
        board = "BOARD: {}".format(self.dropdown_objects_list['board'].itemText(index))
        micropython = "MICROPYTHON: {}".format(self.dropdown_objects_list['micropython'].itemText(index))
        device = "DEVICE: {}".format(self.dropdown_objects_list['device'].itemText(index))
        self.console.append_output(board)
        self.console.append_output(micropython)
        self.console.append_output(device)
        print(board)
        print(micropython)
        print(device)


class MyConsole(QPlainTextEdit):
    #https://gist.github.com/blubberdiblub/007bb92991d01ad29877931f75260b39

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setReadOnly(True)
        self.setMaximumBlockCount(20000)  # limit console to 20000 lines

        self._cursor_output = self.textCursor()
        self.setGeometry(250, 210, 400, 150)

    @pyqtSlot(str)
    def append_output(self, text, end='\n'):
        self._cursor_output.insertText("{}{}".format(text, end))
        self.scroll_to_last_line()

    def scroll_to_last_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.Up if cursor.atBlockStart() else
                            QTextCursor.StartOfLine)
        self.setTextCursor(cursor)


def main():
    app = QApplication(sys.argv)
    ex = App()

    ex.draw_logo()
    ex.buttons()
    ex.dropdown_board()
    ex.dropdown_micropythonbin()
    ex.dropdown_device()

    ex.draw()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()