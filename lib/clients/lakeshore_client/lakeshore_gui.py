from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
import sys

from common.lib.clients.qtui.q_custom_text_changing_button import TextChangingButton as _TextChangingButton

class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)

class lakeshore_gui(QtWidgets.QFrame):
    def __init__(self, parent=None):
        window = QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Lakeshore 336 Temperature Controller")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'

        #temperature readout
        self.tempAll_label = QtWidgets.QLabel('Temperature Readout')
        self.tempAll_label.setFont(QFont(shell_font, pointSize= 20))
        self.tempAll_label.setAlignment(QtCore.Qt.AlignCenter)
            #diode 1
        self.temp1_label = QtWidgets.QLabel('Diode 1')
        self.temp1 = QtWidgets.QLabel('Diode 1')
        self.temp1.setFont(QFont(shell_font, pointSize=25))
        self.temp1.setAlignment(QtCore.Qt.AlignCenter)
        self.temp1.setStyleSheet('color: blue')
            #diode 2
        self.temp2_label = QtWidgets.QLabel('Diode 2')
        self.temp2 = QtWidgets.QLabel('Diode 2')
        self.temp2.setFont(QFont(shell_font, pointSize=25))
        self.temp2.setAlignment(QtCore.Qt.AlignCenter)
        self.temp2.setStyleSheet('color: blue')
            #diode 3
        self.temp3_label = QtWidgets.QLabel('Diode 3')
        self.temp3 = QtWidgets.QLabel('Diode 3')
        self.temp3.setFont(QFont(shell_font, pointSize=25))
        self.temp3.setAlignment(QtCore.Qt.AlignCenter)
        self.temp3.setStyleSheet('color: blue')
            #diode 4
        self.temp4_label = QtWidgets.QLabel('Diode 4')
        self.temp4 = QtWidgets.QLabel('Diode 4')
        self.temp4.setFont(QFont(shell_font, pointSize=25))
        self.temp4.setAlignment(QtCore.Qt.AlignCenter)
        self.temp4.setStyleSheet('color: blue')
            #record button
        self.record = TextChangingButton(('Start Recording', 'Stop Recording'))

        #heaters
        self.heatAll_label = QtWidgets.QLabel('Heater Configuration')
        self.heatAll_label.setFont(QFont(shell_font, pointSize= 20))
        self.heatAll_label.setAlignment(QtCore.Qt.AlignCenter)
        self.lockswitch = TextChangingButton(('Locked', 'Unlocked'))
            #heater output
        self.heat1_label = QtWidgets.QLabel('Heater 1')
        self.heat1 = QtWidgets.QLabel('Current 1')
        self.heat1.setFont(QFont(shell_font, pointSize=25))
        self.heat1.setAlignment(QtCore.Qt.AlignCenter)
        self.heat1.setStyleSheet('color: red')
        self.heat1_update = QtWidgets.QPushButton('Update')

        self.heat2_label = QtWidgets.QLabel('Heater 2')
        self.heat2 = QtWidgets.QLabel('Current 2')
        self.heat2.setFont(QFont(shell_font, pointSize=25))
        self.heat2.setAlignment(QtCore.Qt.AlignCenter)
        self.heat2.setStyleSheet('color: red')
        self.heat2_update = QtWidgets.QPushButton('Update')
            #mode function
        self.heat1_mode_label = QtWidgets.QLabel('Mode')
        self.heat1_mode = QtWidgets.QComboBox()
        self.heat1_mode.addItem('Off')
        self.heat1_mode.addItem('PID')
        self.heat1_mode.addItem('Zone')
        self.heat1_mode.addItem('Manual')

        self.heat2_mode_label = QtWidgets.QLabel('Mode')
        self.heat2_mode = QtWidgets.QComboBox()
        self.heat2_mode.addItem('Off')
        self.heat2_mode.addItem('PID')
        self.heat2_mode.addItem('Zone')
        self.heat2_mode.addItem('Manual')
                #input control
        self.heat1_in_label = QtWidgets.QLabel('Input')
        self.heat1_in = QtWidgets.QComboBox()
        self.heat1_in.addItem('1')
        self.heat1_in.addItem('2')
        self.heat1_in.addItem('3')
        self.heat1_in.addItem('4')

        self.heat2_in_label = QtWidgets.QLabel('Input')
        self.heat2_in = QtWidgets.QComboBox()
        self.heat2_in.addItem('1')
        self.heat2_in.addItem('2')
        self.heat2_in.addItem('3')
        self.heat2_in.addItem('4')
                #resistance
        self.heat1_res_label = QtWidgets.QLabel('Resistance (Ohms)')
        self.heat1_res = QtWidgets.QComboBox()
        self.heat1_res.addItem('25')
        self.heat1_res.addItem('50')

        self.heat2_res_label = QtWidgets.QLabel('Resistance (Ohms)')
        self.heat2_res = QtWidgets.QComboBox()
        self.heat2_res.addItem('25')
        self.heat2_res.addItem('50')
                #max current
        self.heat1_curr_label = QtWidgets.QLabel('Max. Current (A)')
        self.heat1_curr = QtWidgets.QDoubleSpinBox()
        self.heat1_curr.setFont(QFont(shell_font, pointSize=16))
        self.heat1_curr.setDecimals(3)
        self.heat1_curr.setSingleStep(1e-3)
        self.heat1_curr.setRange(0, 2)
        self.heat1_curr.setKeyboardTracking(False)

        self.heat2_curr_label = QtWidgets.QLabel('Max. Current (A)')
        self.heat2_curr = QtWidgets.QDoubleSpinBox()
        self.heat2_curr.setFont(QFont(shell_font, pointSize=16))
        self.heat2_curr.setDecimals(3)
        self.heat2_curr.setSingleStep(1e-3)
        self.heat2_curr.setRange(0, 2)
        self.heat2_curr.setKeyboardTracking(False)
                #setpoint
        self.heat1_set_label = QtWidgets.QLabel('Set Point (K)')
        self.heat1_set = QtWidgets.QDoubleSpinBox()
        self.heat1_set.setFont(QFont(shell_font, pointSize=16))
        self.heat1_set.setDecimals(3)
        self.heat1_set.setSingleStep(1e-3)
        self.heat1_set.setRange(0, 2)
        self.heat1_set.setKeyboardTracking(False)

        self.heat2_set_label = QtWidgets.QLabel('Set Point (K)')
        self.heat2_set = QtWidgets.QDoubleSpinBox()
        self.heat2_set.setFont(QFont(shell_font, pointSize=16))
        self.heat2_set.setDecimals(3)
        self.heat2_set.setSingleStep(1e-3)
        self.heat2_set.setRange(0, 2)
        self.heat2_set.setKeyboardTracking(False)
                #control 1
        self.heat1_p1_label = QtWidgets.QLabel('Parameter 1')
        self.heat1_p1 = QtWidgets.QDoubleSpinBox()
        self.heat1_p1.setFont(QFont(shell_font, pointSize=16))
        self.heat1_p1.setDecimals(3)
        self.heat1_p1.setSingleStep(1e-3)
        #self.heat1_p1.setRange(0, 2)
        self.heat1_p1.setKeyboardTracking(False)

        self.heat2_p1_label = QtWidgets.QLabel('Parameter 1')
        self.heat2_p1 = QtWidgets.QDoubleSpinBox()
        self.heat2_p1.setFont(QFont(shell_font, pointSize=16))
        self.heat2_p1.setDecimals(3)
        self.heat2_p1.setSingleStep(1e-3)
        #self.heat2_p1.setRange(0, 2)
        self.heat2_p1.setKeyboardTracking(False)
                #control 2
        self.heat1_p2_label = QtWidgets.QLabel('Parameter 2')
        self.heat1_p2 = QtWidgets.QDoubleSpinBox()
        self.heat1_p2.setFont(QFont(shell_font, pointSize=16))
        self.heat1_p2.setDecimals(3)
        self.heat1_p2.setSingleStep(1e-3)
        #self.heat1_p2.setRange(0, 2)
        self.heat1_p2.setKeyboardTracking(False)

        self.heat2_p2_label = QtWidgets.QLabel('Parameter 2')
        self.heat2_p2 = QtWidgets.QDoubleSpinBox()
        self.heat2_p2.setFont(QFont(shell_font, pointSize=16))
        self.heat2_p2.setDecimals(3)
        self.heat2_p2.setSingleStep(1e-3)
        #self.heat2_p2.setRange(0, 2)
        self.heat2_p2.setKeyboardTracking(False)
                #control 3
        self.heat1_p3_label = QtWidgets.QLabel('Parameter 3')
        self.heat1_p3 = QtWidgets.QDoubleSpinBox()
        self.heat1_p3.setFont(QFont(shell_font, pointSize=16))
        self.heat1_p3.setDecimals(3)
        self.heat1_p3.setSingleStep(1e-3)
        #self.heat1_p3.setRange(0, 2)
        self.heat1_p3.setKeyboardTracking(False)

        self.heat2_p3_label = QtWidgets.QLabel('Parameter 3')
        self.heat2_p3 = QtWidgets.QDoubleSpinBox()
        self.heat2_p3.setFont(QFont(shell_font, pointSize=16))
        self.heat2_p3.setDecimals(3)
        self.heat2_p3.setSingleStep(1e-3)
        #self.heat2_p3.setRange(0, 2)
        self.heat2_p3.setKeyboardTracking(False)

    def makeLayout(self):
        layout = QtWidgets.QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        heatAll_col = 11

        heat1_label_col = 8
        heat1_box_col = 10

        heat2_label_col = 12
        heat2_box_col = 14

        heat_box_start = 5
        heat_box_step = 1

        layout.addWidget(self.tempAll_label, 1, 3)
        layout.addWidget(self.temp1, 3, 2, 3, 2)
        layout.addWidget(self.temp2, 8, 2, 3, 2)
        layout.addWidget(self.temp3, 13, 2, 3, 2)
        layout.addWidget(self.temp4, 18, 2, 3, 2)

        layout.addWidget(self.temp1_label, 2, 2)
        layout.addWidget(self.temp2_label, 7, 2)
        layout.addWidget(self.temp3_label, 12, 2)
        layout.addWidget(self.temp4_label, 17, 2)

        layout.addWidget(self.heatAll_label, 1, heatAll_col)
        layout.addWidget(self.lockswitch, 2, heatAll_col)

        layout.addWidget(self.heat1_label, 2, heat1_label_col)
        layout.addWidget(self.heat1, 3, heat1_box_col)
        layout.addWidget(self.heat1_mode_label, heat_box_start, heat1_label_col)
        layout.addWidget(self.heat1_mode, heat_box_start, heat1_box_col)
        layout.addWidget(self.heat1_in_label, heat_box_start + 1 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_in, heat_box_start + 1 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_res_label, heat_box_start + 2 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_res, heat_box_start + 2 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_curr_label, heat_box_start + 3 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_curr, heat_box_start + 3 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_set_label, heat_box_start + 4 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_set, heat_box_start + 4 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_p1_label, heat_box_start + 5 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_p1, heat_box_start + 5 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_p2_label, heat_box_start + 6 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_p2, heat_box_start + 6 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_p3_label, heat_box_start + 7 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_p3, heat_box_start + 7 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_update, heat_box_start + 8 * heat_box_step, 10)

        layout.addWidget(self.heat2_label, 2, heat2_label_col)
        layout.addWidget(self.heat2, 3, heat2_box_col)
        layout.addWidget(self.heat2_mode_label, 5, heat1_label_col)
        layout.addWidget(self.heat2_mode, 5, heat2_box_col)
        layout.addWidget(self.heat2_in_label, 7, heat1_label_col)
        layout.addWidget(self.heat2_in, 7, heat2_box_col)
        layout.addWidget(self.heat2_res_label, 8, heat1_label_col)
        layout.addWidget(self.heat2_res, 8, heat2_box_col)
        layout.addWidget(self.heat2_curr_label, 10, heat1_label_col)
        layout.addWidget(self.heat2_curr, 10, heat2_box_col)
        layout.addWidget(self.heat2_set_label, 12, heat1_label_col)
        layout.addWidget(self.heat2_set, 12, heat2_box_col)
        layout.addWidget(self.heat2_p1_label, 14, heat1_label_col)
        layout.addWidget(self.heat2_p1, 14, heat2_box_col)
        layout.addWidget(self.heat2_p2_label, 16, heat1_label_col)
        layout.addWidget(self.heat2_p2, 16, heat2_box_col)
        layout.addWidget(self.heat2_p3_label, 18, heat1_label_col)
        layout.addWidget(self.heat2_p3, 18, heat2_box_col)
        layout.addWidget(self.heat2_update, 20, heat2_box_col)

        layout.minimumSize()
        self.setLayout(layout)

    def lock(self):
        """
        fd
        """
        #todo: write


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = lakeshore_gui()
    icon.show()
    app.exec_()




