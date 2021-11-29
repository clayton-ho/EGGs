"""
### BEGIN NODE INFO
[info]
name = SLS Server
version = 1.0
description =
instancename = SLS Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad import types as T
from twisted.internet.defer import returnValue
from labrad.support import getNodeName

from time import sleep

TERMINATOR = '\r\n'

class SLSServer(SerialDeviceServer):
    """Connects to the 729nm SLS Laser"""
    name = 'SLS Server'
    regKey = 'SLSServer'
    serNode = 'mongkok'
    port = 'COM44'

    baudrate = 115200
    timeout = T.Value(5.0, 's')

    #Autolock
    @setting(111, 'Autolock Toggle', enable='s', returns='s')
    def autolock_toggle(self, c, enable=None):
        '''
        Toggle autolock.
        '''
        chString = 'AutoLockEnable'
        resp = yield self._query(chString, enable)
        returnValue(resp)

    @setting(112, 'Autolock Status', returns='*s')
    def autolock_status(self, c):
        '''
        Get autolock status.
        Returns:
            [v, v, v]: the lock time, lock count, and lock state
        '''
        chString = ['LockTime', 'LockCount', 'AutoLockState']
        resp = []
        for string in chString:
            resp_tmp = yield self.ser.write('get ' + string + TERMINATOR)
            sleep(0.5)
            resp_tmp = yield self.ser.read()
            resp_tmp = yield self._parse(resp_tmp, False)
            resp.append(resp_tmp)
        returnValue(resp)

    @setting(113, 'Autolock Parameter', param='s', returns='s')
    def autolock_param(self, c, param=None):
        '''
        Choose parameter for autolock to sweep
        '''
        chString = 'SweepType'
        tgstring = {'OFF': '0', 'PZT': '1', 'CURRENT': '2'}
        param_tg = None
        if not param:
            try:
                param_tg = tgstring[param.upper()]
            except KeyError:
                print('Invalid parameter: parameter must be one of [\'OFF\', \'PZT\', \'CURRENT\']')
        resp = yield self._query(chString, param_tg)
        returnValue(resp)

    #PDH
    @setting(211, 'PDH', param_name='s', param_val='?', returns='s')
    def PDH(self, c, param_name, param_val=None):
        '''
        Adjust PDH settings
        Arguments:
            param_name      (string): the parameter to adjust, can be any of ['frequency', 'index', 'phase', 'filter']
            param_val       ()      : the value to set the parameter to
        Returns:
                                    : the value of param_name
        '''
        chstring = {'frequency': 'PDHFrequency', 'index': 'PDHPMIndex', 'phase': 'PDHPhaseOffset', 'filter': 'PDHDemodFilter'}
        try:
            string_tmp = chstring[param_name.lower()]
        except KeyError:
            print('Invalid parameter. Parameter must be one of [\'frequency\', \'index\', \'phase\', \'filter\']')
        if param_val:
            yield self.ser.write('set ' + string_tmp + ' ' + param_val + TERMINATOR)
            sleep(0.5)
            set_resp = yield self.ser.read()
            set_resp = yield self._parse(set_resp, True)
        yield self.ser.write('get ' + string_tmp + TERMINATOR)
        sleep(0.5)
        resp = yield self.ser.read()
        resp = yield self._parse(resp, False)
        returnValue(resp)

    #Offset lock
    @setting(311, 'Offset Frequency', freq='v', returns='v')
    def offset_frequency(self, c, freq=None):
        '''
        Set/get offset frequency.
        Arguments:
            freq    (float) : a frequency between [1e7, 8e8]
        Returns:
                            : the value of offset frequency
        '''
        chString = 'OffsetFrequency'
        resp = yield self._query(chString, freq)
        returnValue(float(resp))

    @setting(312, 'Offset Lockpoint', lockpoint='i', returns='i')
    def offset_lockpoint(self, c, lockpoint=None):
        '''
        Set offset lockpoint.
        Arguments:
            lockpoint   (float) : offset lockpoint between [0, 4]. 0
        Returns:
                                : the offset lockpoint
        '''
        chString = 'LockPoint'
        resp = yield self._query(chString, lockpoint)
        returnValue(int(resp))

    #Servo
    @setting(411, 'servo', servo_target='s', param_name='s', param_val='?', returns='s')
    def servo(self, c, servo_target, param_name, param_val=None):
        '''
        Adjust PID servo for given parameter
        Arguments:
            servo_target    (string): target of the PID lock
            param_name      (string): the parameter to change
            param_val       ()      : value to change
        '''
        tgstring = {'current': 'Current', 'pzt': 'PZT', 'tx': 'TX'}
        chstring = {'p': 'ServoPropGain', 'i': 'ServoIntGain', 'd': 'ServoDiffGain', 'set': 'ServoSetpoint', 'loop': 'ServoInvertLoop', 'filter': 'ServoOutputFilter'}
        try:
            string_tmp = tgstring[servo_target.lower()] + chstring[param_name.lower()]
        except KeyError:
            print('Invalid target or parameter. Target must be one of [\'current\',\'pzt\',\'tx\'].'
                  'Parameter must be one of [\'frequency\', \'index\', \'phase\', \'filter\']')
        resp = yield self._query(string_tmp, param_val)
        returnValue(resp)

    #Misc. settings

    #Helper functions
    def _parse(self, string, setter):
        """
        Strips echo from SLS and returns a dictionary with
        keys as parameter names and values as parameter value.
        """
        #result = {}
        if type(string) == bytes:
            string = string.decode('utf-8')
        #split by lines
        string = string.split('\r\n')
        #remove echo and end message
        string = string[1:-1]
        #setter responses only give ok or not ok
        if setter:
            return string
        #split parameters and values by '=' sign
        # for paramstring in string:
        #     params = paramstring.split('=')
        #     result[params[0]] = params[1]
        # print(string)
        params = string[0].split('=')
        return params[1]

    @inlineCallbacks
    def _query(self, chstring, param):
        """
        Writes parameter to SLS and verifies setting,
        then reads back same parameter
        """
        if param:
            #write data and read echo
            yield self.ser.write('set ' + chstring + ' ' + str(param) + TERMINATOR)
            sleep(0.5)
            set_resp = yield self.ser.read()
            #parse
            set_resp = yield self._parse(set_resp, True)
        # write data and read echo
        yield self.ser.write('get ' + chstring + TERMINATOR)
        sleep(0.5)
        resp = yield self.ser.read()
        # parse
        resp = yield self._parse(resp, False)
        returnValue(resp)


if __name__ == "__main__":
    from labrad import util
    util.runServer(SLSServer())
