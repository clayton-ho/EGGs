"""
### BEGIN NODE INFO
[info]
name = Toptica Server
version = 1.0
description = Talks to Toptica devices.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting
from EGGS_labrad.servers import PollingServer
from twisted.internet.defer import returnValue, inlineCallbacks, DeferredLock

from toptica.lasersdk.client import Client, NetworkConnection


class TopticaServer(LabradServer):
    """
    Talks to Toptica devices.
    """

    name = 'Toptica Server'
    regKey = 'Toptica Server'
    device = None

    def initServer(self):
        # get DLC pro addresses from registry
        reg = self.client.registry
        pass
        # try:
        #     tmp = yield reg.cd()
        #     yield reg.cd(['', 'Servers', regKey])
        #     # todo: iteratively get all ip addresses
        #     node = yield reg.get('default_node')
        #     yield reg.cd(tmp)
        # except Exception as e:
        #     yield reg.cd(tmp)

    def stopServer(self):
        # close all devices on completion
        if self.device is not None:
            self.device.close()


    # DEVICE CONNECTION
    @setting(11, 'Device Select', ip_address='s', returns='')
    def deviceSelect(self, c, ip_address):
        """
        Attempt to connect to a DLC Pro at the given IP address.
        Arguments:
            ip_address  (str)   : the DLC Pro IP address
        """
        if self.device is None:
            print('Attempting to connect at:', ip_address)
            try:
                self.device = Client(NetworkConnection(ip_address))
                self.device.open()
                print('Successfully connected to device.')
            except Exception as e:
                print(e)
                print('Error: unable to connect to specified device.')
                self.device.close()
                self.device = None
        else:
            raise Exception('Error: another device is already connected.')

    @setting(12, 'Device Close', returns='')
    def deviceClose(self, c):
        """
        Closes the current serial device.
        """
        if self.device:
            self.device.close()
            self.device = None
            print('Device connection closed.')
        else:
            raise Exception('No device selected.')


    # DIRECT COMMUNICATION
    @setting(21, 'Direct Read', key='s', returns='s')
    def directRead(self, c, key):
        """
        Directly read the given parameter (verbatim).
        Arguments:
            key     (str)   : the parameter key to read from.
        """
        pass

    @setting(22, 'Direct Write', key='s', returns='s')
    def directWrite(self, c, key):
        """
        Directly write a value to a given parameter (verbatim).
        Arguments:
            key     (str)   : the parameter key to read from.
            value   (?)     : the value to set the parameter to
        """
        pass
#todo: errors

    # STATUS
    @setting(111, 'Device Info', returns='(ss)')
    def deviceInfo(self, c):
        """
        Returns the currently connected serial device's
        node and port.
        Returns:
            (str)   : the node
            (str)   : the port
        """
        if self.ser:
            return (self.serNode, self.port)
        else:
            raise Exception('No device selected.')


    # EMISSION
    @setting(211, 'Emission Interlock', status='b', returns='v')
    def emissionInterlock(self, c, status=None):
        """
        Get/set the status of the emission interlock.
        Arguments:
            status      (bool)  : the emission status of the laser head.
        Returns:
                        (bool)  : the emission status of the laser head.
        """
        pass


    # CURRENT
    @setting(311, 'Current Actual', returns='v')
    def currentActual(self, c):
        """
        Returns the actual current of the selected laser head.
        Returns:
            (float) : the current (in mA).
        """
        resp = yield self.device.get('laser1:dl:cc:current-act')
        returnValue(float(resp))

    @setting(312, 'Current Target', curr='v', returns='v')
    def currentSet(self, c, curr=None):
        """
        Get/set the target current of the selected laser head.
        Arguments:
            curr    (float) : the target current (in mA).
        Returns:
                    (float) : the target current (in mA).
        """
        if curr is not None:
            if (curr <= 0) or (curr >= 200):
                yield self.device.set('laser1:dl:cc:current-set', curr)
            else:
                raise Exception('Error: maximum current is set too high. Must be less than 200mA.')
        resp = yield self.device.get('laser1:dl:cc:current-set')
        returnValue(float(resp))

    @setting(313, 'Current Max', curr='v', returns='v')
    def currentMax(self, c, curr=None):
        """
        Get/set the maximum current of the selected laser head.
        Arguments:
            curr    (float) : the maximum current (in mA).
        Returns:
                    (float) : the maximum current (in mA).
        """
        if curr is not None:
            if (curr <= 0) or (curr >= 200):
                yield self.device.set('laser1:dl:cc:current-clip', curr)
            else:
                raise Exception('Error: maximum current is set too high. Must be less than 200mA.')
        resp = yield self.device.get('laser1:dl:cc:current-act')
        returnValue(float(resp))


    # TEMPERATURE
    @setting(321, 'Temperature Actual', returns='v')
    def tempActual(self, c):
        """
        Returns the actual temperature of the selected laser head.
        Returns:
            (float) : the temperature (in K).
        """
        pass

    @setting(322, 'Temperature Target', temp='v', returns='v')
    def tempSet(self, c, temp=None):
        """
        Get/set the target temperature of the selected laser head.
        Arguments:
            temp    (float) : the target temperature (in K).
        Returns:
                    (float) : the target temperature (in K).
        """
        pass

    @setting(323, 'Temperature Max', temp='v', returns='v')
    def tempMax(self, c, temp=None):
        """
        Get/set the maximum temperature of the selected laser head.
        Arguments:
            temp    (float) : the maximum temperature (in K).
        Returns:
                    (float) : the maximum temperature (in K).
        """
        pass


    # PIEZO
    @setting(411, 'th1', temp='v', returns='v')
    def th1(self, c, temp=None):
        """
        Get/set the maximum temperature of the selected laser head.
        Arguments:
            temp    (float) : the maximum temperature (in K).
        Returns:
                    (float) : the maximum temperature (in K).
        """
        pass


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls #.
        """
        pass
        # yield self.temperature_read(None, None)



if __name__ == '__main__':
    from labrad import util
    util.runServer(TopticaServer())
