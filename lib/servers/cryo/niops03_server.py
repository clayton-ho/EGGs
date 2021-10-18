"""
### BEGIN NODE INFO
[info]
name = NIOPS03 Server
version = 1.0.0
description = Controls NIOPS-03 Power Supply which controls ion pumps
instancename = NIOPS03 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.server import setting
from labrad.support import getNodeName

import numpy as np

TIMEOUT = 3.0
BAUDRATE = 115200
TERMINATOR = '\r\n'
QUERY_msg = b'\x05'

class NIOPS03Server(SerialDeviceServer):
    name = 'NIOPS03 Server'
    regKey = 'NIOPS03Server'
    serNode = getNodeName()

    @inlineCallbacks
    def initServer( self ):
        # if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        # port = yield self.getPortFromReg( self.regKey )
        port = 'COM3'
        self.port = port
        self.timeout = TIMEOUT
        try:
            serStr = yield self.findSerial( self.serNode )
            print(serStr)
            self.initSerial( serStr, port, baudrate = BAUDRATE)
        except SerialConnectionError as e:
            self.ser = None
            if e.code == 0:
                print('Could not find serial server for node: %s' % self.serNode)
                print('Please start correct serial server')
            elif e.code == 1:
                print('Error opening serial connection')
                print('Check set up and restart serial server')
            else:
                raise Exception('Unknown connection error')

    #STATUS
    @setting(11,'Status', returns = 's')
    def get_status(self, c):
        """
        Get controller status
        Returns:
            (str): which switches and alarms are on/off
        """
        yield self.ser.write('TS' + TERMINATOR)
        resp = yield self.ser.read()
        return resp

    # ON/OFF
    @setting(111,'Toggle IP', power = 'b', returns = 's')
    def toggle_ip(self, c, power = None):
        """
        Set or query whether ion pump is off or on
        Args:
            (bool): whether pump is to be on or off
        Returns:
            (float): pump power status
        """
        if power == True:
            yield self.ser.write('G' + TERMINATOR)
        elif power == False:
            yield self.ser.write('B' + TERMINATOR)
        resp = yield self.ser.read()
        return resp

    @setting(112,'Toggle NP', power = 'b')
    def toggle_np(self, c, power = None):
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
        resp = yield self.ser.read()
        return resp

    #PARAMETERS
    @setting(211,'Get Pressure', returns = 'v')
    def get_pressure(self, c):
        """
        Get ion pump pressure
        Returns:
            (float): ion pump pressure
        """
        yield self.ser.write('Tb' + TERMINATOR)
        resp = yield self.ser.read()
        return float(resp)

    @setting(221,'Get IP Voltage', returns = 'v')
    def get_voltage_ip(self, c):
        """
        Get ion pump voltage
        Returns:
            (float): ion pump voltage
        """
        yield self.ser.write('Tb' + TERMINATOR)
        resp = yield self.ser.read()
        return float(resp)

    @setting(222,'Get NP Voltage', returns = 'v')
    def get_voltage_np(self, c):
        """
        Get getter voltage
        Returns:
            (float): getter voltage
        """
        yield self.ser.write('u' + TERMINATOR)
        resp = yield self.ser.read()
        return float(resp)
        #todo: need to convert from hex to decimal, 4 integer values

    @setting(231,'Get Working Time', returns = 'str')
    def get_time_working(self, c):
        """
        Get getter voltage
        Returns:
            (float): getter voltage
        """
        yield self.ser.write('u' + TERMINATOR)
        resp = yield self.ser.read()
        return float(resp)
        #todo: write correctly


if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())