from sentry.autoload.pm_pdu_autoloader import PmPduAutoloader
from sentry.snmp_handler import SnmpHandler
from log_helper import LogHelper
from pysnmp.proto.rfc1902 import Integer
from pysnmp.smi.rfc1902 import ObjectIdentity
from time import sleep, strftime
from data_model import *

TIMEOUT = 1


class PmPduHandler:
    class Port:
        def __init__(self, port):
            self.address, port_details = port.split('/')
            self.port_number, self.pdu_number, self.outlet_number = port_details.split('.')

    def __init__(self, context, snmp_read, snmp_write):
        self.context = context
        self.snmp_read = snmp_write
        self.snmp_write = snmp_write
        self.logger = LogHelper.get_logger(self.context)
        self.snmp_handler = SnmpHandler(self.context, self.snmp_read, self.snmp_write)
        self.resource = Sentry4G2Pdu.create_from_context(context)
        self.address = context.resource.address

    def get_inventory(self):
        autoloader = PmPduAutoloader(self.context, self.snmp_read, self.snmp_write)

        return autoloader.autoload()

    def power_cycle(self, port_list, delay, d_list):
        self.logger.info("Power cycle called for ports %s" % port_list)
        for raw_port in port_list:
            self.logger.info("Power cycling port %s" % raw_port)
            port = self.Port(raw_port)
            self.logger.info("Powering off port %s" % raw_port)
            # self.snmp_handler.set(ObjectIdentity('Sentry4-MIB', 'st4OutletControlAction', port.port_number, port.pdu_number, port.outlet_number),
            #                       Integer(2))
            p_off_msg = self.power_off(port_list=port_list, d_list=d_list)
            self.logger.info("Sleeping %f second(s)" % delay)
            sleep(delay)
            self.logger.info("Powering on port %s" % raw_port)
            # self.snmp_handler.set(ObjectIdentity('Sentry4-MIB', 'st4OutletControlAction', port.port_number, port.pdu_number, port.outlet_number),
            #                       Integer(1))
            p_on_msg = self.power_on(port_list=port_list, d_list=d_list)

            return '{}\n{}\n\n{} Power Cycle Complete'.format(p_off_msg, p_on_msg, strftime('%Y-%m-%d %H:%M:%S'))

    def power_off(self, port_list, d_list):
        self.logger.info("Power off called for ports %s" % port_list)
        for raw_port in port_list:
            self.logger.info("Powering off port %s" % raw_port)
            port = self.Port(raw_port)
            self.snmp_handler.set(ObjectIdentity('Sentry4-MIB', 'st4OutletControlAction', port.port_number, port.pdu_number, port.outlet_number),
                                  Integer(2))
            sleep(TIMEOUT)
        # Custom messaging Dell:
        msg = '{} \n  Power Off called for {}\n  PDU: {} {} \n  Port(s) {}'.format(strftime('%Y-%m-%d %H:%M:%S'),
                                                                              d_list, self.resource.name,
                                                                              self.address, port_list)
        return msg

    def power_on(self, port_list, d_list):
        self.logger.info("Power on called for ports %s" % port_list)
        for raw_port in port_list:
            self.logger.info("Powering on port %s" % raw_port)
            port = self.Port(raw_port)
            self.snmp_handler.set(ObjectIdentity('Sentry4-MIB', 'st4OutletControlAction', port.port_number, port.pdu_number, port.outlet_number),
                                  Integer(1))
            sleep(TIMEOUT)
        # Custom messaging Dell:
        msg = '{} \n  Power On called for {}\n  PDU: {} {} \n  Port(s) {}'.format(strftime('%Y-%m-%d %H:%M:%S'),
                                                                                d_list, self.resource.name,
                                                                                self.address, port_list)
        return msg
