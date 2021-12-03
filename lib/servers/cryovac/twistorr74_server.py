"""
### BEGIN NODE INFO
[info]
name = TwisTorr74 Server
version = 1.0
description = Talks to the TwisTorr 74 Turbopump
instancename = TwisTorr74 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 5

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
import time
import numpy as np

from labrad.types import Value
from labrad.server import setting, Signal
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

class TwisTorr74Server(SerialDeviceServer):
    """
    Talks to the TwisTorr 74 Turbopump.
    """

    name = 'TwisTorr74 Server'
    regKey = 'TwisTorr74Server'
    serNode = 'mongkok'
    port = 'COM56'

    timeout = Value(5.0, 's')
    baudrate = 9600

    STX_msg = b'\x02'
    ADDR_msg = b'\x80'
    READ_msg = b'\x30'
    WRITE_msg = b'\x31'
    ETX_msg = b'\x03'

    ERRORS_msg = {
        b'\x15': "Execution failed",
        b'\x32': "Unknown window",
        b'\x33': "Data type error",
        b'\x34': "Value out of range",
        b'\x35': "Window disabled",
    }

    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', 'v')

    # STARTUP
    def initServer(self):
        super().initServer()
        self.refresher = LoopingCall(self.poll)
        from twisted.internet.reactor import callLater
        callLater(1, self.refresher.start, 2)

    def stopServer(self):
        if hasattr(self, 'refresher'):
            self.refresher.stop()
        super().stopServer()

    def setUnits(self):
        pass


    # TOGGLE
    @setting(111, 'toggle', onoff='b', returns='b')
    def toggle(self, c, onoff=None):
        """
        Start or stop the pump
        Args:
            onoff   (bool)  : desired pump state
        Returns:
                    (bool)  : pump state
        """
        #create and send message to device
        message = None
        if onoff is True:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=self.WRITE_msg, DATA_msg=b'1')
        elif onoff is False:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=self.WRITE_msg, DATA_msg=b'0')
        elif onoff is None:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=self.READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read(10)
        resp = yield self._parse(resp)
        if resp == '1':
            resp = True
        elif resp == '2':
            resp = False
        returnValue(resp)

    # READ PRESSURE
    @setting(211, 'Read Pressure', returns='v')
    def pressure_read(self, c):
        """
        Get pump pressure
        Returns:
            (float): pump pressure in mbar
        """
        #create and send message to device
        message = yield self._create_message(CMD_msg=b'224', DIR_msg=self.READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read(19)
        resp = yield self._parse(resp)
        resp = float(resp)
        #send signal and return value
        self.pressure_update(resp)
        returnValue(resp)


    # POLLING
    @setting(911, 'Set Polling', status='b', interval='v', returns='(bv)')
    def set_polling(self, c, status, interval):
        """
        Configure polling of device for values.
        """
        #ensure interval is valid
        if (interval < 1) or (interval > 60):
            raise Exception('Invalid polling interval.')
        #only start/stop polling if we are not already started/stopped
        if status and (not self.refresher.running):
            self.refresher.start(interval)
        elif status and self.refresher.running:
            self.refresher.interval = interval
        elif (not status) and (self.refresher.running):
            self.refresher.stop()
        return (self.refresher.running, self.refresher.interval)

    @setting(912, 'Get Polling', returns='(bv)')
    def get_polling(self, c):
        """
        Get polling parameters.
        """
        return (self.refresher.running, self.refresher.interval)

    @inlineCallbacks
    def poll(self):
        """
        Polls the device for pressure readout.
        """
        yield self.ser.write(b'\x02\x802240\x0387')
        resp = yield self.ser.read(19)
        resp = yield self._parse(resp)
        resp = float(resp)
        self.pressure_update(resp)


    # Helper functions
    def _create_message(self, CMD_msg, DIR_msg, DATA_msg=b''):
        """
        Creates a message according to the Twistorr74 serial protocol
        """
        #create message as bytearray
        msg = self.STX_msg + self.ADDR_msg + CMD_msg + DIR_msg + DATA_msg + self.ETX_msg
        msg = bytearray(msg)
        #calculate checksum
        CRC_msg = 0x00
        for byte in msg[1:]:
            CRC_msg ^= byte
        #convert checksum to hex value and add to end
        CRC_msg = hex(CRC_msg)[2:]
        msg.extend(bytearray(CRC_msg, encoding='utf-8'))
        return bytes(msg)

    def _parse(self, ans):
        if ans == b'':
            raise Exception('No response from device')
        # remove STX, ADDR, and CRC
        ans = ans[2:-3]
        #check if we have CMD and DIR and remove them if so
        if len(ans) > 1:
            ans = ans[4:]
            ans = ans.decode()
        elif ans in self.ERRORS_msg:
            raise Exception(self.ERRORS_msg[ans])
        elif ans == b'\x06':
            ans = 'Acknowledged'
        #if none of these cases, we just return it anyways
        return ans


if __name__ == '__main__':
    from labrad import util
    util.runServer(TwisTorr74Server())