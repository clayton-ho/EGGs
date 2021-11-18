"""
### BEGIN NODE INFO
[info]
name = Serial Server
version = 1.4.2
description = Gives access to serial devices via pyserial.
instancename = %LABRADNODE% Serial Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import collections, time, os
import os.path
from time import sleep

from labrad import types as T
from labrad.errors import Error
from labrad.server import LabradServer, setting
from twisted.internet import reactor, threads
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import deferLater, LoopingCall

from serial import Serial
from serial.serialutil import SerialException
import serial.tools.list_ports


#Errors
class NoPortSelectedError(Error):
    """Please open a port first."""
    code = 1

class NoPortsAvailableError(Error):
    """No serial ports are available."""
    code = 3


SerialDevice = collections.namedtuple('SerialDevice', ['name', 'devicepath'])


class SerialServer(LabradServer):
    """Provides access to a computer's serial (COM) ports."""
    name = '%LABRADNODE% Serial Server'
    refreshInterval = 10

    def initServer(self):
        self.enumerate_serial_pyserial()
        #start looping call to periodically update
        #serial devices
        reactor.callLater(1, self.startRefreshing)

    def startRefreshing(self):
        self.refresher = LoopingCall(self.enumerate_serial_pyserial)
        self.refresherDone = self.refresher.start(self.refreshInterval)

    @inlineCallbacks
    def stopServer(self):
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            #yield self.refresherDone

    def enumerate_serial_windows(self):
        """Manually Enumerate the first 20 COM ports.

        pyserial includes a function to enumerate device names, but it
        possibly doesn't work right on windows for COM ports above 4.
        http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
        """
        self.SerialPorts = []
        print('Searching for COM ports:')
        for a in range(1, 40):
            COMexists = True
            dev_name = 'COM{}'.format(a)
            dev_path = r'\\.\{}'.format(dev_name)
            try:
                ser = Serial(dev_name)
                ser.close()
            except SerialException as e:
                if e.message.find('cannot find') >= 0:
                    COMexists = False
            if COMexists:
                self.SerialPorts.append(SerialDevice(dev_name, dev_path))
                print("  ", dev_name)
        if not len(self.SerialPorts):
            print('  none')

    def enumerate_serial_pyserial(self):
        """This uses the pyserial built-in device enumeration.

        We ignore the pyserial "human readable" device name
        because that appears to make no sense.  For instance, a
        particular FTDI USB-Serial adapter shows up as 'Microsoft
        Corp. Optical Mouse 200'.

        Following the example from the above windows version, we try to open
        each port and ignore it if we can't.
        """
        self.SerialPorts = []
        dev_list = serial.tools.list_ports.comports()
        for d in dev_list:
            dev_path = d[0]
            try:
                ser = Serial(dev_path)
                ser.close()
            except SerialException as e:
                pass
            else:
                _, _, dev_name = dev_path.rpartition(os.sep)
                self.SerialPorts.append(SerialDevice(dev_name, dev_path))

    def expireContext(self, c):
        if 'PortObject' in c:
            c['PortObject'].close()

    def getPort(self, c):
        try:
            return c['PortObject']
        except:
            raise NoPortSelectedError()

    @setting(1, 'List Serial Ports', returns=['*s: List of serial ports'])
    def list_serial_ports(self, c):
        """Retrieves a list of all serial ports.

        NOTES:
        This list contains all ports installed on the computer,
        including ones that are already in use by other programs."""
        print(self.SerialPorts)
        port_list = [x.name for x in self.SerialPorts]

        return port_list

    @setting(10, 'Open', port=[': Open the first available port', 's: Port to open, e.g. COM4'],
             returns=['s: Opened port'])
    def open(self, c, port=''):
        """Opens a serial port in the current context.

        args:
        port   device name as returned by list_serial_ports.

        On windows, the device name will generally be of the form
        COM1 or COM42 (i.e., without the device prefix \\\\.\\).  On
        linux, it will be the device node name (ttyUSB0) without the
        /dev/ prefix.  This is case insensitive on windows, case sensitive
        on Linux.  For compatibility, always use the same case.
        """
        c['Timeout'] = 0
        if 'PortObject' in c:
            c['PortObject'].close()
            del c['PortObject']
        if not port:
            for i in range(len(self.SerialPorts)):
                try:
                    c['PortObject'] = Serial(self.SerialPorts[i].devicepath,
                                             timeout=0)
                    break
                except SerialException:
                    pass
            if 'PortObject' not in c:
                raise NoPortsAvailableError()
        else:
            for x in self.SerialPorts:
                if os.path.normcase(x.name) == os.path.normcase(port):
                    try:
                        c['PortObject'] = Serial(x.devicepath, timeout=0)
                        return x.name
                    except SerialException as e:
                        if e.message.find('cannot find') >= 0:
                            raise Error(code=1, msg=e.message)
                        else:
                            raise Error(code=2, msg=e.message)
        raise Error(code=1, msg='Unknown port %s' % (port,))

    @setting(11, 'Close', returns=[''])
    def close(self, c):
        """Closes the current serial port."""
        if 'PortObject' in c:
            c['PortObject'].close()
            del c['PortObject']

    @setting(20, 'Baudrate', data=[': List baudrates', 'w: Set baudrate (0: query current)'],
             returns=['w: Selected baudrate', '*w: Available baudrates'])
    def baudrate(self, c, data=None):
        """Sets the baudrate."""
        ser = self.getPort(c)
        baudrates = ser.BAUDRATES
        if data is None:
            return baudrates
        else:
            if data in baudrates:
                ser.baudrate = data
            return int(ser.baudrate)

    @setting(21, 'Bytesize', data=[': List bytesizes', 'w: Set bytesize (0: query current)'], returns=['*w: Available bytesizes', 'w: Selected bytesize'])
    def bytesize(self, c, data=None):
        """Sets the bytesize."""
        ser = self.getPort(c)
        bytesizes = ser.BYTESIZES
        if data is None:
            return bytesizes
        else:
            if data in bytesizes:
                ser.bytesize = data
            return int(ser.bytesize)

    @setting(22, 'Parity', data=[': List parities', 's: Set parity (empty: query current)'], returns=['*s: Available parities', 's: Selected parity'])
    def parity(self, c, data=None):
        """Sets the parity."""
        ser = self.getPort(c)
        parities = ser.PARITIES
        if data is None:
            return parities
        else:
            data = data.upper()
            if data in parities:
                ser.parity = data
            return ser.parity

    @setting(23, 'Stopbits', data=[': List stopbits', 'w: Set stopbits (0: query current)'],
             returns=['*w: Available stopbits', 'w: Selected stopbits'])
    def stopbits(self, c, data=None):
        """Sets the number of stop bits."""
        ser = self.getPort(c)
        stopbits = ser.STOPBITS
        if data is None:
            return stopbits
        else:
            if data in stopbits:
                ser.stopbits = data
            return int(ser.stopbits)

    @setting(25, 'Timeout', data=[': Return immediately', 'v[s]: Timeout to use (max: 5min)'],
             returns=['v[s]: Timeout being used (0 for immediate return)'])
    def timeout(self, c, data=T.Value(0, 's')):
        """Sets a timeout for read operations."""
        c['Timeout'] = min(data['s'], 300)
        return T.Value(c['Timeout'], 's')

    @setting(30, 'RTS', data=['b'], returns=['b'])
    def RTS(self, c, data):
        """Sets the state of the RTS line."""
        ser = self.getPort(c)
        ser.rts = int(data)
        return data

    @setting(31, 'DTR', data=['b'], returns=['b'])
    def DTR(self, c, data):
        """Sets the state of the DTR line."""
        ser = self.getPort(c)
        ser.dtr = int(data)
        return data

    @setting(40, 'Write', data=['s: Data to send', '*w: Byte-data to send'],
             returns=['w: Bytes sent'])
    def write(self, c, data):
        """Sends data over the port."""
        ser = self.getPort(c)
        if type(data) == str:
            data = data.encode()
        ser.write(data)
        return int(len(data))

    @setting(41, 'Write Line', data=['s: Data to send'],
             returns=['w: Bytes sent'])
    def write_line(self, c, data):
        """Sends data over the port appending CR LF."""
        ser = self.getPort(c)
        if type(data) == str:
            data = data.encode()
        ser.write(data + b'\r\n')
        return int(len(data) + 2)

    @setting(42, 'Pause', duration='v[s]: Time to pause', returns=[])
    def pause(self, c, duration):
        _ = yield deferLater(reactor, duration['s'], lambda: None)
        return

    @inlineCallbacks
    def deferredRead(self, ser, timeout, count=1):
        killit = False

        def doRead(count):
            d = b''
            while not killit:
                d = ser.read(count)
                if d:
                    break
                sleep(0.010)
            return d

        data = threads.deferToThread(doRead, count)
        timeout_object = []
        start_time = time.time()
        r = yield util.maybeTimeout(data, min(timeout, 300), timeout_object)
        killit = True

        if r == timeout_object:
            elapsed = time.time() - start_time
            print("deferredRead timed out after {} seconds".format(elapsed))
            r = b''
        if r == b'':
            r = ser.read(count)

        returnValue(r)

    @inlineCallbacks
    def readSome(self, c, count=0):
        ser = self.getPort(c)
        if count == 0:
            returnValue(ser.read(10000))

        timeout = c['Timeout']
        if timeout == 0:
            returnValue(ser.read(count))

        recd = b''
        while len(recd) < count:
            r = ser.read(count - len(recd))
            if r == b'':
                r = yield self.deferredRead(ser, timeout, count - len(recd))
                if r == b'':
                    ser.close()
                    ser.open()
                    break
            recd += r
        returnValue(recd)

    @setting(50, 'Read', count=[': Read all bytes in buffer', 'w: Read this many bytes'],
             returns=['s: Received data'])
    def read(self, c, count=0):
        """Read data from the port.

        Args:
            count:   bytes to read.

        If count=0, reads the contents of the buffer (non-blocking).  Otherwise
        reads for up to <count> characters or the timeout, whichever is first
        """
        return self.readSome(c, count)

    @setting(51, 'Read as Words', data=[': Read all bytes in buffer', 'w: Read this many bytes'],
             returns=['*w: Received data'])
    def read_as_words(self, c, data=0):
        """Read data from the port."""
        ans = yield self.readSome(c, data)
        returnValue([int(ord(x)) for x in ans])

    @setting(52, 'Read Line', data=[': Read until LF, ignoring CRs', 's: Other delimiter to use'],
             returns=['s: Received data'])
    def read_line(self, c, data=''):
        """Read data from the port, up to but not including the specified delimiter."""
        ser = self.getPort(c)
        timeout = c['Timeout']
        #set default end character if not specified
        if data:
            #ensure end chararcter is of type byte
            if type(data) != bytes:
                data = bytes(data, encoding='utf-8')
            delim, skip = data, b''
        else:
            delim, skip = b'\n', b'\r'

        recd = b''
        while True:
            r = ser.read(1)
            # only try a deferred read if there is a timeout
            if r == b'' and timeout > 0:
                r = yield self.deferredRead(ser, timeout)
            if r in (b'', delim):
                break
            elif r != skip:
                recd += r
        returnValue(recd)

    @setting(61, 'Flush Input', returns='')
    def flush_input(self, c):
        """Flush the input buffer"""
        ser = self.getPort(c)
        yield ser.reset_input_buffer()

    @setting(62, 'Flush Output', returns='')
    def flush_output(self, c):
        """Flush the output buffer"""
        ser = self.getPort(c)
        yield ser.reset_output_buffer()


__server__ = SerialServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
