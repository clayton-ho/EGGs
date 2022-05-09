@ECHO OFF && TITLE LabRAD Shell && CALL conda activate labart && python -ix "%~f0" %* & goto :eof

# get current module to set server variables
from sys import modules
current_module=modules[__name__]

# connect to labrad
import labrad
cxn = labrad.connect()

# connect to wavemeter labrad
cxn_wm = labrad.connect('10.97.111.8',password='lab')
wm = cxn_wm.multiplexerserver

# list of servers we want and their shorthand names
server_dict = {
        'ss': 'script_scanner', 'pv': 'parameter_vault', 'dv': 'data_vault',
        'ni': 'niops03_server', 'tt': 'twistorr74_server', 'ls': 'lakeshore336_server',
        'rga': 'rga_server', 'rf': 'rf_server', 'sls': 'sls_server', 'aq': 'artiq_server',
        'pmt': 'pmt_server', 'dc': 'dc_server', 'fma': 'fma1700a_server', 'to': 'toptica_server',
        'os': 'oscilloscope_server', 'fg': 'function_generator_server', 'sa': 'spectrum_analyzer_server',
        'gpib': 'gpib_device_manager', 'mk_gpib': 'mongkok_gpib_bus', 'hf_gpib': 'hengfachuen_gpib_bus',
        'mk': 'node_mongkok', 'cw': 'node_causewaybay', 'hf': 'node_hengfachuen'
        }

for servers in server_dict.items():
    try:
        # set server as variable
        setattr(current_module, servers[0], cxn[servers[1]])
    except Exception as e:
        print("Server unavailable:", e)
