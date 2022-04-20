from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QFrame

from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients.ARTIQ_client.AD9910_client import AD9910_channel


class DDS_client(QWidget):
    """
    Client for all DDS channels.
    """
    name = "ARTIQ DDS Client"
    row_length = 4

    def __init__(self, reactor, cxn=None, parent=None):
        super(DDS_client, self).__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.ad9910_clients = {}
        # start connections
        d = self.connect()
        d.addCallback(self.getDevices)
        d.addCallback(self.initializeGUI)

    @inlineCallbacks
    def connect(self):
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)
        return self.cxn

    @inlineCallbacks
    def getDevices(self, cxn):
        """
        Get devices from ARTIQ server and organize them.
        """
        # get artiq server and dds list
        try:
            self.artiq = yield self.cxn.artiq_server
            ad9910_list = yield self.artiq.dds_list()
        except Exception as e:
            print(e)
            raise

        # assign ad9910 channels to urukuls
        self.urukul_list = {}
        for device_name in ad9910_list:
            urukul_name = device_name.split('_')[0]
            if urukul_name not in self.urukul_list:
                self.urukul_list[urukul_name] = []
            self.urukul_list[urukul_name].append(device_name)
        return self.cxn

    def initializeGUI(self, cxn):
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, self.row_length)
        # layout widgets
        keys_tmp = list(self.urukul_list.keys())
        for i in range(len(keys_tmp)):
            urukul_name = keys_tmp[i]
            ad9910_list = self.urukul_list[urukul_name]
            urukul_group = self._makeUrukulGroup(urukul_name, ad9910_list)
            layout.addWidget(urukul_group, 2 + i, 0, 1, self.row_length)

    def _makeUrukulGroup(self, urukul_name, ad9910_list):
        """
        Creates a group of Urukul channels as a widget.
        """
        # create widget
        urukul_group = QFrame()
        urukul_group.setFrameStyle(0x0001 | 0x0010)
        urukul_group.setLineWidth(2)
        layout = QGridLayout(urukul_group)
        # set title
        title = QLabel(urukul_name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, self.row_length)
        # layout individual ad9910 channels
        for i in range(len(ad9910_list)):
            # initialize GUIs for each channel
            channel_name = ad9910_list[i]
            channel_gui = AD9910_channel(channel_name)
            # layout channel GUI
            row = int(i / self.row_length) + 2
            column = i % self.row_length
            # connect signals to slots
            channel_gui.freq.valueChanged.connect(lambda freq, chan=channel_name: self.artiq.dds_frequency(chan, freq))
            channel_gui.ampl.valueChanged.connect(lambda ampl, chan=channel_name: self.artiq.dds_amplitude(chan, ampl))
            channel_gui.att.valueChanged.connect(lambda att, chan=channel_name: self.artiq.dds_attenuation(chan, att, 'v'))
            channel_gui.rfswitch.toggled.connect(lambda status, chan=channel_name: self.artiq.dds_toggle(chan, status))
            # add widget to client list and layout
            self.ad9910_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
            # print(name + ' - row:' + str(row) + ', column: ' + str(column))
        return urukul_group

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    # run DDS Client
    from EGGS_labrad.clients import runClient
    runClient(DDS_client)
