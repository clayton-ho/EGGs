from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QFrame, QSizePolicy, QWidget, QLabel,\
    QGridLayout, QDoubleSpinBox, QComboBox, QHBoxLayout, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox

_SHELL_FONT = 'MS Shell Dlg 2'


class SLS_gui(QFrame):

    def __init__(self, channelinfo=None):
        super().__init__()
        self.setWindowTitle('SLS Client')
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(680, 410)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.makeWidgets()
        self.makeLayout()
        for widget in (self.autolock_lockswitch, self.off_lockswitch, self.PDH_lockswitch, self.servo_lockswitch):
            widget.setChecked(False)

    def makeWidgets(self):
        # AUTOLOCK
        self.autolock_widget = QWidget(self)
        autolock_layout = QVBoxLayout(self.autolock_widget)

        autolock_param_label = QLabel("Sweep Parameter")
        autolock_time_label = QLabel("Lock Time (d:h:m)")
        autolock_toggle_label = QLabel("Autolock")
        autolock_attempts_label = QLabel("Lock Attempts")

        self.autolock_time = QLabel("Time")
        self.autolock_time.setAlignment(Qt.AlignCenter)
        self.autolock_time.setFont(QFont(_SHELL_FONT, pointSize=18))
        self.autolock_time.setStyleSheet('color: blue')
        self.autolock_param = QComboBox(self.autolock_widget)

        for item_text in ("Off", "PZT", "Current"):
            self.autolock_param.addItem(item_text)

        self.autolock_attempts = QLabel("NULL", self.autolock_widget)
        self.autolock_attempts.setAlignment(Qt.AlignCenter)
        self.autolock_attempts.setFont(QFont(_SHELL_FONT, pointSize=18))
        self.autolock_attempts.setStyleSheet('color: blue')
        self.autolock_toggle = TextChangingButton(('On', 'Off'), self.autolock_widget)

        self.autolock_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.autolock_lockswitch.toggled.connect(lambda status, widget=self.autolock_widget: self._lock(status, widget))

        for widget in (autolock_time_label, self.autolock_time, autolock_attempts_label, self.autolock_attempts,
                       autolock_toggle_label, self.autolock_toggle, autolock_param_label, self.autolock_param):
            autolock_layout.addWidget(widget)

        # OFFSET LOCK
        self.off_widget = QWidget(self)
        off_layout = QVBoxLayout(self.off_widget)

        off_lockpoint_label = QLabel("Lockpoint")
        off_freq_label = QLabel("Offset Frequency (MHz)")

        self.off_freq = QDoubleSpinBox(self.off_widget)
        self.off_freq.setRange(10.0, 35.0)
        self.off_freq.setSingleStep(0.1)
        self.off_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.off_lockswitch.toggled.connect(lambda status, widget=self.off_widget: self._lock(status, widget))
        self.off_lockpoint = QComboBox(self.off_widget)

        for item_text in ("J(+2)", "J(+1)", "Resonance", "J(-1)", "J(-2)"):
            self.off_lockpoint.addItem(item_text)

        for widget in (off_freq_label, self.off_freq, off_lockpoint_label, self.off_lockpoint):
            off_layout.addWidget(widget)

        # PDH
        self.PDH_widget = QWidget(self)
        self.PDH_layout = QVBoxLayout(self.PDH_widget)

        PDH_filter_label = QLabel("Filter Index")
        PDH_phasemodulation_label = QLabel("Phase modulation (rad)")
        PDH_phaseoffset_label = QLabel("Reference phase (deg)")
        PDH_freq_label = QLabel("Frequency (MHz)")

        self.PDH_freq = QDoubleSpinBox(self.PDH_widget)
        self.PDH_freq.setRange(10.0, 35.0)
        self.PDH_freq.setSingleStep(0.1)
        self.PDH_filter = QComboBox(self.PDH_widget)
        self.PDH_filter.addItem("None")
        for i in range(1, 16):
            self.PDH_filter.addItem(str(i))

        self.PDH_phaseoffset = QDoubleSpinBox(self.PDH_widget)
        self.PDH_phaseoffset.setMaximum(360.0)
        self.PDH_phaseoffset.setSingleStep(0.1)
        self.PDH_phasemodulation = QDoubleSpinBox(self.PDH_widget)
        self.PDH_phasemodulation.setMaximum(3.0)
        self.PDH_phasemodulation.setSingleStep(0.1)

        self.PDH_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.PDH_lockswitch.toggled.connect(lambda status, widget=self.PDH_widget: self._lock(status, widget))

        for widget in (PDH_freq_label, self.PDH_freq, PDH_phasemodulation_label, self.PDH_phasemodulation,
                       PDH_phaseoffset_label, self.PDH_phaseoffset, PDH_filter_label, self.PDH_filter):
            self.PDH_layout.addWidget(widget)

        # PID
        self.servo_widget = QWidget(self)
        servo_layout = QVBoxLayout(self.servo_widget)

        servo_param_label = QLabel("Parameter")
        servo_set_label = QLabel("Setpoint")
        servo_p_label = QLabel("Proportional")
        servo_i_label = QLabel("Integral")
        servo_d_label = QLabel("Differential")
        servo_filter_label = QLabel("Filter Index")

        self.servo_filter = QComboBox()
        self.servo_filter.addItem("None")
        for i in range(1, 16):
            self.servo_filter.addItem(str(i))

        self.servo_set = QDoubleSpinBox()
        self.servo_set.setRange(-1000000.0, 1000000.0)
        self.servo_p = QDoubleSpinBox()
        self.servo_p.setMaximum(1000.0)
        self.servo_i = QDoubleSpinBox()
        self.servo_i.setMaximum(1.0)
        self.servo_i.setSingleStep(0.01)
        self.servo_d = QDoubleSpinBox()
        self.servo_d.setMaximum(10000.0)
        self.servo_param = QComboBox()
        for item_text in ("Current", "PZT", "TX"):
            self.servo_param.addItem(item_text)

        self.servo_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.servo_lockswitch.toggled.connect(lambda status, widget=self.servo_widget: self._lock(status, widget))

        for widget in (servo_param_label, self.servo_param, servo_set_label, self.servo_set, servo_p_label, self.servo_p,
                       servo_i_label, self.servo_i, servo_d_label, self.servo_d, servo_filter_label, self.servo_filter):
            servo_layout.addWidget(widget)

    def makeLayout(self):
        autolock_widget_wrapped = QCustomGroupBox(self.autolock_widget, "Autolock")
        off_widget_wrapped = QCustomGroupBox(self.off_widget, "Offset Lock")
        PDH_widget_wrapped = QCustomGroupBox(self.PDH_widget, "PDH")
        servo_widget_wrapped = QCustomGroupBox(self.servo_widget, "PID")
        for widget in (autolock_widget_wrapped, off_widget_wrapped, PDH_widget_wrapped, servo_widget_wrapped):
            widget.setFixedWidth(161)

        # title
        sls_label = QLabel("SLS Client", self)
        sls_label.setFont(QFont(_SHELL_FONT, pointSize=20))
        sls_label.setAlignment(Qt.AlignCenter)
        # lay out
        layout = QGridLayout(self)
        layout.addWidget(sls_label,                         0, 0, 1, 4)
        layout.addWidget(self.autolock_lockswitch,          1, 0, 1, 1)
        layout.addWidget(autolock_widget_wrapped,           2, 0, 7, 1)
        layout.addWidget(self.off_lockswitch,               1, 1, 1, 1)
        layout.addWidget(off_widget_wrapped,                2, 1, 4, 1)
        layout.addWidget(self.PDH_lockswitch,               1, 2, 1, 1)
        layout.addWidget(PDH_widget_wrapped,                2, 2, 6, 1)
        layout.addWidget(self.servo_lockswitch,             1, 3, 1, 1)
        layout.addWidget(servo_widget_wrapped,              2, 3, 10, 1)

    def _lock(self, status, widget):
        widget.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SLS_gui)
