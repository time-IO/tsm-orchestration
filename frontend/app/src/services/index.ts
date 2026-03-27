import ingestExternalApiBoschController from "src/services/ingest_external_api_bosch"
import ingestExternalApiDwdController from "src/services/ingest_external_api_dwd"
import ingestExternalApiNeutronMonitorController from "src/services/ingest_external_api_neutron_monitor"
import ingestExternalApiUbaController from "src/services/ingest_external_api_uba"
import ingestExternalApiTheThingsNetworkController from 'src/services/ingest_external_api_the_things_network';
import ingestExternalApiTSystemsController from 'src/services/ingest_external_api_tsystems';
import ingestMqttController from 'src/services/ingest_mqtt';
import ingestSftpController from 'src/services/ingest_sftp';
import ingestExternalSftpController from 'src/services/ingest_external_sftp';
import triggerExternalApiGenController from 'src/services/trigger_external_api_generic';

import permissionGroupController from "src/services/permission_group"
import userController from "src/services/user"
import neutronMonitorStationController from "src/services/neutron_monitor_stations"
import mqttParserController from "src/services/mqtt_parser"
import csvParserController from "src/services/parser_csv"

export const API = {
  ingestExternalApiBosch: ingestExternalApiBoschController,
  ingestExternalApiDwd: ingestExternalApiDwdController,
  ingestExternalApiNeutronMonitor: ingestExternalApiNeutronMonitorController,
  ingestExternalApiTSystems: ingestExternalApiTSystemsController,
  ingestExternalApiTheThingsNetwork: ingestExternalApiTheThingsNetworkController,
  ingestExternalApiUba: ingestExternalApiUbaController,
  ingestMqtt: ingestMqttController,
  ingestSftp: ingestSftpController,
  ingestExternalSftp: ingestExternalSftpController,
  permissionGroup: permissionGroupController,
  user: userController,
  neutronMonitorStation: neutronMonitorStationController,
  mqttParser: mqttParserController,
  csvParser: csvParserController,
  triggerExternalGenAPI:triggerExternalApiGenController
};
