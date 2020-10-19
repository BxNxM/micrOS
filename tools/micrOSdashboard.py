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
        self.data_set = {'force': False}
        self.console = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setFixedWidth(self.width)
        self.setFixedHeight(self.height)
        self.setStyleSheet("background-color: grey")
        self.venv_indicator()

    def create_console(self):
        dropdown_label = QLabel(self)
        dropdown_label.setText("Console".upper())
        dropdown_label.setStyleSheet("background-color : darkGray;")
        dropdown_label.setGeometry(250, 117, 420, 15)
        self.console = MyConsole(self)

    def venv_indicator(self):
        state = False
        if hasattr(sys, 'real_prefix'):
            state = True

        if state:
            label = QLabel(' [devEnv] virtualenv active', self)
            label.setGeometry(20, 5, self.width-50, 20)
            label.setStyleSheet("background-color : green;")
        else:
            label = QLabel(' [devEnv] virtualenv inactive', self)
            label.setGeometry(20, 5, self.width-50, 20)
            label.setStyleSheet("background-color : yellow;")

    def buttons(self):
        height = 35
        width = 200
        yoffset = 3
        buttons = {'Deploy (USB)': ['Install "empty" device, deploy micropython and micrOS Framework',
                                       20, 115, width, height, self.__on_click_usb_deploy, 'darkCyan'],
                   'Update (OTA)': ['OTA - Over The Air (wifi) update, upload micrOS resources over webrepl',
                                  20, 115 + height + yoffset, width, height, self.__on_click_ota_update, 'darkCyan'],
                   'Update (USB)': ['Update micrOS (with redeploy micropython) over USB',
                                       20, 115 + (height+yoffset) * 2, width, height, self.__on_click_usb_update, 'darkCyan'],
                   'Search device': ['Search online micrOS devices on local network (wifi)',
                                      20, 115 + (height + yoffset) * 3, width, height, self.__on_click_serach_devices, 'darkCyan'],
                   'Simulator': ['Start micrOS on host with micropython dummy (module) interfaces',
                                      20, 115 + (height + yoffset) * 4, width, height, self.__on_click_simulator, 'darkCyan']
                   }

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
    def __on_click_usb_deploy(self):
        print('__on_click_usb_deploy')
        self.console.append_output('__on_click_usb_deploy')
        self.progressbar_update()

    @pyqtSlot()
    def __on_click_ota_update(self):
        print('__on_click_ota_update')
        self.console.append_output('__on_click_ota_update')
        self.progressbar_update()

    @pyqtSlot()
    def __on_click_usb_update(self):
        print('__on_click_usb_update')
        self.console.append_output('__on_click_usb_update')
        self.progressbar_update()

    @pyqtSlot()
    def __on_click_serach_devices(self):
        print('__on_click_serach_devices')
        self.console.append_output('__on_click_serach_devices')
        self.progressbar_update()

    @pyqtSlot()
    def __on_click_simulator(self):
        print('__on_click_simulator')
        self.console.append_output('__on_click_simulator')
        self.progressbar_update()

    def draw_logo(self):
        label = QLabel(self)
        label.setGeometry(20, 30, 80, 80)
        label.setScaledContents(True)
        pixmap = QPixmap('/Users/bnm/Documents/NodeMcu/MicrOs/media/logo_mini.png')
        label.setPixmap(pixmap)

    def progressbar(self):
        # creating progress bar
        self.pbar = QProgressBar(self)

        # setting its geometry
        self.pbar.setGeometry(20, self.height-40, self.width-70, 30)

    def progressbar_update(self, value=None, reset=False):
        if reset:
            self.pbar_status = 0
        if value is not None and 0 <= value <= 100:
            self.pbar_status = value
        self.pbar_status = self.pbar_status + 1 if self.pbar_status < 100 else 0
        self.pbar.setValue(self.pbar_status)
        print(self.pbar_status)

    def draw(self):
        self.progressbar()
        self.create_console()
        self.draw_logo()
        self.buttons()
        self.dropdown_board()
        self.dropdown_micropythonbin()
        self.dropdown_device()
        self.force_mode_radiobutton()
        self.show()

    def dropdown_board(self):
        dropdown_label = QLabel(self)
        dropdown_label.setText("Select board".upper())
        dropdown_label.setGeometry(120, 30, 170, 30)

        # creating a combo box widget
        combo_box = QComboBox(self)

        # setting geometry of combo box
        combo_box.setGeometry(120, 60, 170, 30)

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
        combo_box.activated.connect(self.get_widget_values)

    def dropdown_micropythonbin(self):
        dropdown_label = QLabel(self)
        dropdown_label.setText("Select micropython".upper())
        dropdown_label.setGeometry(310, 30, 170, 30)

        # creating a combo box widget
        combo_box = QComboBox(self)

        # setting geometry of combo box
        combo_box.setGeometry(310, 60, 170, 30)

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
        combo_box.activated.connect(self.get_widget_values)

    def dropdown_device(self):
        dropdown_label = QLabel(self)
        dropdown_label.setText("Select device".upper())
        dropdown_label.setGeometry(500, 35, 170, 20)

        # creating a combo box widget
        combo_box = QComboBox(self)

        # setting geometry of combo box
        combo_box.setGeometry(500, 60, 170, 30)

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
        combo_box.activated.connect(self.get_widget_values)

    def get_widget_values(self, index):
        self.data_set['board'] = self.dropdown_objects_list['board'].itemText(index)
        self.data_set['micropython'] = self.dropdown_objects_list['micropython'].itemText(index)
        self.data_set['device'] = self.dropdown_objects_list['device'].itemText(index)
        self.__show_gui_state_on_console()
        return self.data_set

    def __show_gui_state_on_console(self):
        self.console.append_output("micrOS GUI Info")
        for key, value in self.data_set.items():
            self.console.append_output("  {}: {}".format(key, value))

    def force_mode_radiobutton(self):
        #label = QLabel('Force mode for version override')
        rbtn1 = QRadioButton('Force mode', self)
        rbtn1.move(20, self.height-60)
        rbtn1.toggled.connect(self.__on_click_force_mode)

        #layout = QVBoxLayout()
        #layout.setGeometry(0, 0, 100, 20)
        #layout.addWidget(label)
        #layout.addWidget(rbtn1)
        #self.setLayout(layout)

    def __on_click_force_mode(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.data_set['force'] = True
        else:
            self.data_set['force'] = False
        self.__show_gui_state_on_console()


class MyConsole(QPlainTextEdit):
    console = None

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(20000)  # limit console to 20000 lines
        self._cursor_output = self.textCursor()
        self.setGeometry(250, 132, 420, 175)
        MyConsole.console = self

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
    ex.draw()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
