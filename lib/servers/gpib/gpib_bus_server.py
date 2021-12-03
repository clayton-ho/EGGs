# CHANGELOG
#
# 2011 December 10 - Peter O'Malley & Jim Wenner
#
# Fixed bug where doesn't add devices if no SOCKETS connected.
#
# 2011 December 5 - Jim Wenner
#
# Added ability to read TCPIP (Ethernet) devices if configured to use
# sockets (i.e., fixed port address). To do this, added getSocketsList
# function and changed refresh_devices.
#
# 2011 December 3 - Jim Wenner
#
# Added ability to read TCPIP (Ethernet) devices. Must be configured
# using VXI-11 or LXI so that address ends in INSTR. Does not accept if
# configured to use sockets. To do this, changed refresh_devices.
#
# To be clear, the gpib system already supported ethernet devices just fine
# as long as they weren't using raw socket protocol. The changes that
# were made here and in the next few revisions are hacks to make socket
# connections work, and should be improved.
#
# 2021 October 17 - Clayton Ho
# Added back automatic device polling
# 2021 November 25 - Clayton Ho
# Added configurable device polling


from labrad.server import LabradServer, setting
from labrad.errors import DeviceNotSelectedError
import labrad.units as units

from twisted.internet.defer import inlineCallbacks
from twisted.internet.reactor import callLater
from twisted.internet.task import LoopingCall

import pyvisa as visa

"""
### BEGIN NODE INFO
[info]
name = GPIB Bus
version = 1.5.1
description = Gives access to GPIB devices via pyvisa.
instancename = %LABRADNODE% GPIB Bus

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 100
### END NODE INFO
"""


KNOWN_DEVICE_TYPES = ('GPIB', 'TCPIP', 'USB')


class GPIBBusServer(LabradServer):
    """Provides direct access to GPIB-enabled devices."""
    name = '%LABRADNODE% GPIB Bus'

    defaultTimeout = 1.0 * units.s

    def initServer(self):
        self.devices = {}
        self.refresher = LoopingCall(self.refreshDevices)
        # start refreshing only after we have started serving to ensure
        # we have a cxn before we send messages
        callLater(2, self.refresher.start, 10)

    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()

    def refreshDevices(self):
        """
        Refresh the list of known devices on this bus.
        Currently supported are GPIB devices and GPIB over USB.
        """
        try:
            rm = visa.ResourceManager()
            addresses = [str(x) for x in rm.list_resources()]
            additions = set(addresses) - set(self.devices.keys())
            deletions = set(self.devices.keys()) - set(addresses)
            for addr in additions:
                try:
                    if not addr.startswith(KNOWN_DEVICE_TYPES):
                        continue
                    instr = rm.open_resource(addr)
                    instr.write_termination = ''
                    instr.clear()
                    if addr.endswith('SOCKET'):
                        instr.write_termination = '\n'
                    self.devices[addr] = instr
                    self.sendDeviceMessage('GPIB Device Connect', addr)
                except Exception as e:
                    print('Failed to add ' + addr + ':' + str(e))
            for addr in deletions:
                del self.devices[addr]
                self.sendDeviceMessage('GPIB Device Disconnect', addr)
        except Exception as e:
            print('Problem while refreshing devices:', str(e))

    def sendDeviceMessage(self, msg, addr):
        print(msg + ': ' + addr)
        self.client.manager.send_named_message(msg, (self.name, addr))

    def initContext(self, c):
        c['timeout'] = self.defaultTimeout

    def getDevice(self, c):
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected")
        if c['addr'] not in self.devices:
            raise Exception('Could not find device ' + c['addr'])
        instr = self.devices[c['addr']]
        return instr

    @setting(0, addr='s', returns='s')
    def address(self, c, addr=None):
        """Get or set the GPIB address for this context.

        To get the addresses of available devices,
        use the list_devices function.
        """
        if addr is not None:
            c['addr'] = addr
        return c['addr']

    @setting(2, time='v[s]', returns='v[s]')
    def timeout(self, c, time=None):
        """Get or set the GPIB timeout."""
        if time is not None:
            c['timeout'] = time
        return c['timeout']

    @setting(3, data='s', returns='')
    def write(self, c, data):
        """Write a string to the GPIB bus."""
        self.getDevice(c).write(data)

    @setting(8, data='y', returns='')
    def write_raw(self, c, data):
        """Write a string to the GPIB bus."""
        self.getDevice(c).write_raw(data)

    @setting(4, n_bytes='w', returns='s')
    def read(self, c, n_bytes=None):
        """Read from the GPIB bus.

        Termination characters, if any, will be stripped.
        This includes any bytes corresponding to termination in
        binary data. If specified, reads only the given number
        of bytes. Otherwise, reads until the device stops sending.
        """
        instr = self.getDevice(c)
        if n_bytes is None:
            ans = instr.read_raw()
        else:
            ans = instr.read_raw(n_bytes)
        #convert from bytes to string for python 3
        ans = ans.strip().decode()
        return ans

    @setting(5, data='s', returns='s')
    def query(self, c, data):
        """Make a GPIB query, a write followed by a read.

        This query is atomic.  No other communication to the
        device will occur while the query is in progress.
        """
        instr = self.getDevice(c)
        instr.write(data)
        ans = instr.read_raw()
        # convert from bytes to string for python 3
        ans = ans.strip().decode()
        return ans

    @setting(7, n_bytes='w', returns='y')
    def read_raw(self, c, n_bytes=None):
        """Read raw bytes from the GPIB bus.

        Termination characters, if any, will not be stripped.
        If n_bytes is specified, reads only that many bytes.
        Otherwise, reads until the device stops sending.
        """
        instr = self.getDevice(c)
        if n_bytes is None:
            ans = instr.read_raw()
        else:
            ans = instr.read_raw(n_bytes)
        return bytes(ans)

    @setting(20, returns='*s')
    def list_devices(self, c):
        """Get a list of devices on this bus."""
        return sorted(self.devices.keys())

    @setting(21)
    def refresh_devices(self, c):
        """ manually refresh devices """
        self.refreshDevices()

    @setting(31, status='b', interval='v', returns='(bv)')
    def set_polling(self, c, status, interval):
        """
        Configure polling of serial ports.
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


__server__ = GPIBBusServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
