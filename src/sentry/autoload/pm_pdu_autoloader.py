from sentry.snmp_handler import SnmpHandler
from cloudshell.shell.core.driver_context import AutoLoadResource, AutoLoadDetails, AutoLoadAttribute
from log_helper import LogHelper
from data_model import *


class PmPduAutoloader:
    def __init__(self, context, snmp_read, snmp_write):
        self.context = context
        self.logger = LogHelper.get_logger(self.context)
        self.snmp_handler = SnmpHandler(self.context, snmp_read, snmp_write).get_raw_handler('get')
        self.resource = Sentry4G2Pdu.create_from_context(context)

    def autoload(self):
        rv = AutoLoadDetails(resources=[], attributes=[])

        sysobject = self.snmp_handler.get_property('SNMPv2-MIB', 'sysObjectID', 0, return_type="str")
        if sysobject != 'Sentry4-MIB::sentry4':
            raise AssertionError("Device does not appear to be a Sentry4.")

        rv.attributes.append(self.makeattr('', 'CS_PDU.Location',
                                           self.snmp_handler.get_property('SNMPv2-MIB', 'sysLocation', 0)))
        # rv.attributes.append('', 'CS_PDU.Location', self.snmp_handler.get_property('Sentry4-MIB', 'st4SystemFirmwareVersion', 0)))
        # rv.attributes.append(self.makeattr('', 'Location', self.snmp_handler.get_property('SNMPv2-MIB', 'systemLocation', 0)))
        rv.attributes.append(self.makeattr('', 'CS_PDU.Model',
                                           self.snmp_handler.get_property('Sentry4-MIB', 'st4SystemProductName', 0)))
        rv.attributes.append(self.makeattr('', 'CS_PDU.Model Name',
                                           self.snmp_handler.get_property('Sentry4-MIB', 'st4UnitModel', 1)))
        rv.attributes.append(self.makeattr('', 'Sentry4G2Pdu.Serial Number',
                                           self.snmp_handler.get_property('Sentry4-MIB', 'st4UnitProductSN', 1)))
        rv.attributes.append(self.makeattr('', 'CS_PDU.Vendor', 'Sentry'))
        rv.attributes.append(self.makeattr('', 'Sentry4G2Pdu.Firmware Version',
                                           self.snmp_handler.get_property('Sentry4-MIB', 'st4SystemFirmwareVersion', 0)))
        rv.attributes.append(self.makeattr('', 'Sentry4G2Pdu.Hardware Details',
                                           self.snmp_handler.get_property('Sentry4-MIB', 'st4SystemNICHardwareInfo', 0)))

        pdu_name = self.snmp_handler.get_property('SNMPv2-MIB', 'sysName', 0)

        rv.attributes.append(self.makeattr('', 'CS_PDU.System Name', pdu_name))

        outlet_table = self.snmp_handler.get_table('Sentry4-MIB', 'st4OutletConfigTable')
        n = 1  # part of modification to Naming for DELL
        for index, attribute in outlet_table.iteritems():
            # name = '%s_%s' % (self.snmp_handler.get_property('Sentry4-MIB', 'st4OutletID', index),
            #                   self.snmp_handler.get_property('Sentry4-MIB', 'st4OutletName', index))

            # Modified naming per DELL request:
            i, j, k = index.split('.')
            name = 'Outlet_{num:02d}'.format(num=int(k) + ((int(i) - 1) * 30))  # assumes 30 outlets per unit max
            n += 1
            model_name = '%s_%s' % (self.snmp_handler.get_property('Sentry4-MIB', 'st4OutletID', index),
                                    self.snmp_handler.get_property('Sentry4-MIB', 'st4OutletName', index))
            # End Custom work ################

            relative_address = index
            unique_identifier = '%s.%s' % (pdu_name, index)

            rv.resources.append(self.makeres(name, 'Sentry4G2Pdu.PowerSocket', relative_address, unique_identifier))
            # rv.attributes.append(self.makeattr(relative_address, 'CS_PowerSocket.Model Name', attribute['st4OutletName']))
            rv.attributes.append(self.makeattr(relative_address, 'CS_PowerSocket.Model Name', model_name))  # custom

        return rv

    def makeattr(self, relative_address, attribute_name, attribute_value):
        return AutoLoadAttribute(relative_address=relative_address,
                                 attribute_name=attribute_name,
                                 attribute_value=attribute_value)

    def makeres(self, name, model, relative_address, unique_identifier):
        return AutoLoadResource(name=name, model=model,
                                relative_address=relative_address,
                                unique_identifier=unique_identifier)
