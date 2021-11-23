"""
### BEGIN NODE INFO
[info]
name = ARTIQ Server
version = 1.0
description = Pulser using the ARTIQ box. Backwards compatible with old pulse sequences and experiments.
instancename = ARTIQ Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

#labrad imports
from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread

#artiq imports
from artiq_api import ARTIQ_api
from artiq.experiment import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager
from sipyco.pc_rpc import Client
from sipyco.sync_struct import Subscriber

#function imports
import numpy as np

class ARTIQ_Server(LabradServer):
    """ARTIQ box server."""
    name = 'ARTIQ Server'
    regKey = 'ARTIQ_Server'

    def __init__(self):
        self.api = ARTIQ_api()
        self.ddb_filepath = 'C:\\Users\\EGGS1\\Documents\\ARTIQ\\artiq-master\\device_db.py'
        self.devices = DeviceDB(self.ddb_filepath)
        self.device_manager = DeviceManager(self.devices)
        LabradServer.__init__(self)

    @inlineCallbacks
    def initServer(self):
        self.listeners = set()
        yield self._setClients()
        yield self._setVariables()
        yield self._setDevices()

    def _setClients(self):
        """
        Create clients to ARTIQ master.
        Used to get datasets and submit experiments.
        """
        self.scheduler = Client('::1', 3251, 'master_schedule')
        self.datasets = Client('::1', 3251, 'master_dataset_db')

    def _setVariables(self):
        """
        Sets ARTIQ-related variables.
        """
        #used to ensure atomicity
        self.inCommunication = DeferredLock()
        #pulse sequencer variables
        self.ps_filename = 'C:\\Users\\EGGS1\\Documents\\Code\\EGGS_labrad\\lib\\servers\\pulser\\run_ps.py'
        self.ps_rid = None
        #conversions
            #dds
        dds_tmp = list(self.api.dds_list.values())[0]
        self.seconds_to_mu = self.api.core.seconds_to_mu
        self.amplitude_to_asf = dds_tmp.amplitude_to_asf
        self.frequency_to_ftw = dds_tmp.frequency_to_ftw
        self.turns_to_pow = dds_tmp.turns_to_pow
        self.dbm_to_fampl = lambda dbm: 10**(float(dbm/10))
            #dac
        from artiq.coredevice.ad53xx import voltage_to_mu
        self.voltage_to_mu = voltage_to_mu

    def _setDevices(self):
        """
        Get the list of devices in the ARTIQ box.
        """
        self.ttlout_list = list(self.api.ttlout_list.keys())
        self.dds_list = list(self.api.dds_list.keys())

    # Core
    @setting(21, "Get Devices", returns='')
    def getDevices(self):
        """
        Returns the ARTIQ device database.
        """
        return self.devices.get_device_db()

    #Pulse sequencing
    @setting(111, "Run Experiment", path='s', maxruns = 'i', returns='')
    def runExperiment(self, c, path, maxruns = 1):
        """
        Run the experiment a given number of times.
        Argument:
            path    (string): the filepath to the ARTIQ experiment.
            maxruns (int)   : the number of times to run the experiment
        """
        #set pipeline, priority, and expid
        ps_pipeline = 'PS'
        ps_priority = 1
        ps_expid = {'log_level': 30,
                    'file': path,
                    'class_name': None,
                    'arguments': {'maxRuns': maxruns,
                                  'linetrigger_enabled': self.linetrigger_enabled,
                                  'linetrigger_delay_us': self.linetrigger_delay,
                                  'linetrigger_ttl_name': self.linetrigger_ttl}}

        #run sequence then wait for experiment to submit
        yield self.inCommunication.acquire()
        self.ps_rid = yield deferToThread(self.scheduler.submit, pipeline_name = ps_pipeline, expid = ps_expid, priority = ps_priority)
        self.inCommunication.release()

    @setting(112, "Stop Experiment", returns='')
    def stopSequence(self, c):
        """
        Stops any currently running sequence.
        """
        #check that an experiment is currently running
        if self.ps_rid not in self.scheduler.get_status().keys(): raise Exception('No experiment currently running')
        yield self.inCommunication.acquire()
        yield deferToThread(self.scheduler.delete, self.ps_rid)
        self.ps_rid = None
        #todo: make resetting of ps_rid contingent on defertothread completion
        self.inCommunication.release()

    @setting(113, "Runs Completed", returns='i')
    def runsCompleted(self, c):
        """
        Check how many iterations of the experiment have been completed.
        """
        completed_runs = yield self.datasets.get('numRuns')
        returnValue(completed_runs)


    #TTLs
    @setting(211, 'TTL Get', returns='*s')
    def getTTL(self, c):
        """
        Returns all available TTL channels
        """
        return self.ttlout_list

    @setting(221, "TTL Set", ttl_name='s', state='b', returns='')
    def setTTL(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state.
        Arguments:
            ttl_name (str)  : name of the ttl
            state   (bool)  : ttl power state
        """
        if ttl_name not in self.ttlout_list:
            raise Exception('Error: device does not exist.')
        yield self.api.setTTL(ttl_name, state)


    #DDS functions
    @setting(311, "DDS Get", returns='*s')
    def getDDS(self, c):
        """get the list of available channels"""
        dds_list = yield self.api.dds_list.keys()
        returnValue(list(dds_list))

    @setting(321, "DDS Initialize", dds_name='s', returns='')
    def initializeDDS(self, c, dds_name):
        """
        Resets/initializes the DDSs.
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        yield self.api.initializeDDS(dds_name)

    @setting(322, "DDS Toggle", dds_name='s', state='b', returns='')
    def toggleDDS(self, c, dds_name, state):
        """
        Manually toggle a DDS via the RF switch
        Arguments:
            dds_name    (str)   : the name of the dds
            state       (bool)  : power state
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        yield self.api.toggleDDS(dds_name, state)

    @setting(323, "DDS Waveform", dds_name='s', param='s', param_val='v', returns='')
    def setDDSWav(self, c, dds_name, param, param_val):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            dds_name     (str)  : the name of the dds
            param       (str)   : the parameter to set
            param_val   (float) : the value of the parameter
        """
        #todo: check input
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        if param.lower() in ('frequency', 'f'):
            ftw = yield self.frequency_to_ftw(param_val)
            yield self.api.setDDS(dds_name, 0, ftw)
        elif param.lower() in ('amplitude', 'a'):
            asf = yield self.amplitude_to_asf(param_val)
            yield self.api.setDDS(dds_name, 1, asf)
        elif param.lower() in ('phase', 'p'):
            if param_val >= 1 or pow < 0:
                raise Exception('Error: phase outside bounds of [0,1]')
            pow = yield self.turns_to_pow(param_val)
            yield self.api.setDDS(dds_name, 2, pow)

    @setting(326, "DDS Attenuation", dds_name='s', att='v', profile='i', returns='')
    def setDDSAtt(self, c, dds_name, att, profile=None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            dds_name (str)  : the name of the dds
            att     (float) : attenuation (in dBm)
            profile (int)   : the DDS profile to set & change to
        """
        #todo: check input
        att_mu = att
        yield self.api.setDDSAtt(dds_name, att_mu)


    #DAC
    @setting(421, "DAC Initialize", returns='')
    def initializeDAC(self, c):
        """
        Manually initialize the DAC.
        """
        yield self.api.initializeDAC()

    @setting(411, "DAC Set", dac_num='i', voltage='v', returns='')
    def setDAC(self, c, dac_num, voltage):
        """
        Manually set the voltage of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            voltage (float) : the DAC register voltage (not the same as
                                output voltage due to offset registers)
        """
        #only 32 channels per DAC
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        #todo: check voltage
        voltage_mu = yield self.voltage_to_mu(voltage)
        yield self.api.setDAC(dac_num, voltage_mu)

    @setting(412, "DAC Gain", dac_num='i', gain='v', returns='')
    def setDACGain(self, c, dac_num, gain):
        """
        Manually set the gain of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            gain (float)    : the DAC channel gain
        """
        # only 32 channels per DAC
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        #check that gain is valid
        if gain > 1 or gain < 0:
            raise Exception('Error: gain outside bounds of [0,1]')
        #gain is a 16 bit register, 0xffff is full
        gain_mu = int(gain * 0xffff) - 1
        yield self.api.setDACGain(dac_num, gain_mu)

    @setting(413, "DAC Offset", dac_num='i', voltage='v', returns='')
    def setDACOffset(self, c, dac_num, voltage):
        """
        Manually set the offset voltage of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            voltage (float) : the DAC offset register voltage
        """
        #only 32 channels per DAC
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        #todo: check voltage
        voltage_mu = yield self.voltage_to_mu(voltage)
        yield self.api.setDACOffset(dac_num, voltage_mu)


    #Sampler


    #Signal/Context functions
    def notifyOtherListeners(self, context, message, f):
        """
        Notifies all listeners except the one in the given context, executing function f
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

if __name__ == '__main__':
    from labrad import util
    util.runServer(ARTIQ_Server())