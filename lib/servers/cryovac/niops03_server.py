"""
### BEGIN NODE INFO
[info]
name = NIOPS03 Server
version = 1.0.0
description = Controls NIOPS03 Power Supply which controls the ion pump and getter
instancename = NIOPS03 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import setting
from labrad.units import WithUnit

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

import time

TERMINATOR = '\r\n'
QUERY_msg = b'\x05'

class NIOPS03Server(SerialDeviceServer):
    """
    Controls NIOPS03 Power Supply which controls ion pumps.
    """
    name = 'NIOPS03 Server'
    regKey = 'NIOPS03Server'
    serNode = 'MongKok'
    port = 'COM55'

    timeout = WithUnit(3.0, 's')
    baudrate = 115200


    # STARTUP
    def initServer(self):
        super().initServer()
        self.tt = None
        self.refresher = LoopingCall(self.poll)
        from twisted.internet.reactor import callLater
        callLater(1, self.refresher.start, 2)

    def stopServer(self):
        super().stopServer()
        if hasattr(self, 'refresher'):
            self.refresher.stop()


    #STATUS
    @setting(11, 'Status', returns='s')
    def get_status(self, c):
        """
        Get controller status
        Returns:
            (str): power status of all alarms and devices
        """
        yield self.ser.write('TS' + TERMINATOR)
        resp = yield self.ser.read_line(TERMINATOR)
        returnValue(resp)

    # ON/OFF
    @setting(111, 'Toggle IP', power='b', returns='s')
    def toggle_ip(self, c, power):
        """
        Set or query whether ion pump is off or on
        Args:
            (bool): whether pump is to be on or off
        Returns:
            (float): pump power status
        """
        if power:
            yield self.ser.write('G' + TERMINATOR)
        else:
            yield self.ser.write('B' + TERMINATOR)
        resp = yield self.ser.read_line()
        resp = resp.strip()
        returnValue(resp)

    @setting(112, 'Toggle NP', power='b', returns='s')
    def toggle_np(self, c, power):
        """
        Set or query whether getter is off or on
        Args:
            (bool): whether getter is to be on or off
        Returns:
            (bool): getter power status
        """
        if power == True:
            yield self.ser.write('GN' + TERMINATOR)
        elif power == False:
            yield self.ser.write('BN' + TERMINATOR)
        resp = yield self.ser.read_line()
        returnValue(resp)

    #PARAMETERS
    @setting(211, 'IP Pressure', returns='v')
    def pressure_ip(self, c):
        """
        Get ion pump pressure in mbar
        Returns:
            (float): ion pump pressure
        """
        yield self.ser.write('Tb' + TERMINATOR)
        resp = yield self.ser.read_line()
        returnValue(float(resp))

    @setting(221, 'IP Voltage', voltage='v', returns='v')
    def voltage_ip(self, c, voltage=None):
        """
        Get/set ion pump voltage
        Arguments:
            voltage (float) : pump voltage in V
        Returns:
                    (float): ion pump voltage in V
        """
        if voltage:
            #convert voltage to hex
            voltage = hex(voltage)[2:]
            padleft = '0'*(4-len(voltage))
            yield self.ser.write('u' + padleft + voltage + TERMINATOR)
        yield self.ser.write('u' + TERMINATOR)
        resp = yield self.ser.read_line()
        #convert from hex to int
        resp = int(resp, 16)
        returnValue(resp)

    @setting(231, 'Working Time', returns='*2i')
    def working_time(self, c):
        """
        Gets working time of IP & NP
        Returns:
            [[int, int], [int, int]]: working time of ion pump and getter
        """
        #todo: ensure no problem here
        yield self.ser.write('TM' + TERMINATOR)
        ip_time = yield self.ser.read_line('\r')
        np_time = yield self.ser.read_line('\r')
        ip_time = ip_time[16:-8].split(' Hours ')
        np_time = np_time[16:-8].split(' Hours ')
        ip_time = [int(val) for val in ip_time]
        np_time = [int(val) for val in np_time]
        returnValue([ip_time, np_time])

    @setting(311, 'Interlock IP', status='b', press='v', returns='b')
    def interlock_ip(self, c, status, press):
        """
        Activates an interlock, switching off the ion pump
        if pressure exceeds a given value.
        Pressure is taken from the Twistorr74 turbo pump server.
        Arguments:
            press   (float) : the maximum pressure in mbar
        Returns:
                    (bool)  : activation state of the interlock
        """
        #create connection to turbopump as needed
        try:
            self.tt = yield self.client.twistorr74_server
        except KeyError:
            self.tt = None
            raise Exception('Twistorr74 server not available for interlock.')
        #set threshold pressure
        self.interlock_pressure = press
        #only start if stopped, and vice versa
        if status and not self.interlock_loop.running:
            self.interlock_loop.start(5)
        elif not status and self.interlock_loop.running:
            self.interlock_loop.stop()
        returnValue(self.interlock_loop.running)

    @inlineCallbacks
    def _interlock_poll(self):
        if interlock_active:
        press_tmp = yield self.tt.read_pressure()
        if press_tmp >= self.interlock_pressure:
            print('problem')
            # yield self.ser.write('B' + TERMINATOR)
            # yield self.ser.read_line()


if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())