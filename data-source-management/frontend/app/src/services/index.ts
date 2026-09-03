import ingestExternalApiBoschController from 'src/services/ingest_external_api_bosch';
import ingestExternalApiDwdController from 'src/services/ingest_external_api_dwd';
import ingestExternalApiNeutronMonitorController from 'src/services/ingest_external_api_neutron_monitor';
import ingestExternalApiUbaController from 'src/services/ingest_external_api_uba';
import ingestExternalApiTheThingsNetworkController from 'src/services/ingest_external_api_the_things_network';
import ingestExternalApiTSystemsController from 'src/services/ingest_external_api_tsystems';
import ingestExternalApiSensotoController from 'src/services/ingest_external_api_sensoto';
import ingestMqttController from 'src/services/ingest_mqtt';
import ingestSftpController from 'src/services/ingest_sftp';
import ingestHttpController from 'src/services/ingest_http';
import ingestSftpStorageController from 'src/services/ingest_sftp_storage';
import ingestExternalSftpController from 'src/services/ingest_external_sftp';
import ingestExternalSftpStorageController from 'src/services/ingest_external_sftp_storage';
import ingestExternalMqttController from 'src/services/ingest_external_mqtt';
import triggerExternalApiGenController from 'src/services/trigger_external_api_generic';
import permissionGroupController from 'src/services/permission_group';
import userController from 'src/services/user';
import neutronMonitorStationController from 'src/services/neutron_monitor_stations';
import mqttParserController from 'src/services/parser_mqtt';
import csvParserController from 'src/services/parser_csv';
import jsonParserController from 'src/services/parser_json';
import soilcanParserController from 'src/services/parser_soilcan';
import qualityControlSettingController from 'src/services/quality_control_setting';
import staController from 'src/services/sta';
import qualityControlSettingsTriggerController from 'src/services/quality_control_settings_trigger';

import parserTimezoneController from 'src/services/parser_timezone';
import parserEncodingController from 'src/services/parser_encoding';

import ingestController from 'src/services/ingest';
import parserDetailedController from 'src/services/parser_detailed';
import ingestExternalApiController from 'src/services/ingest_external_api';

import usageStatisticsController from 'src/services/usage_statistics';

export const API = {
  ingestExternalApiBosch: ingestExternalApiBoschController,
  ingestExternalApiDwd: ingestExternalApiDwdController,
  ingestExternalApiNeutronMonitor: ingestExternalApiNeutronMonitorController,
  ingestExternalApiTSystems: ingestExternalApiTSystemsController,
  ingestExternalApiTheThingsNetwork: ingestExternalApiTheThingsNetworkController,
  ingestExternalApiUba: ingestExternalApiUbaController,
  ingestExternalApiSensoto: ingestExternalApiSensotoController,
  ingestMqtt: ingestMqttController,
  ingestSftp: ingestSftpController,
  ingestSftpStorage: ingestSftpStorageController,
  ingestExternalSftp: ingestExternalSftpController,
  ingestExternalSftpStorage: ingestExternalSftpStorageController,
  permissionGroup: permissionGroupController,
  user: userController,
  neutronMonitorStation: neutronMonitorStationController,
  mqttParser: mqttParserController,
  csvParser: csvParserController,
  jsonParser: jsonParserController,
  soilcanParser: soilcanParserController,
  triggerExternalGenAPI: triggerExternalApiGenController,
  qualityControlSetting: qualityControlSettingController,
  sta: staController,
  triggerQCSetting: qualityControlSettingsTriggerController,
  parserTimezone: parserTimezoneController,
  parserEncoding: parserEncodingController,
  usageStatistics: usageStatisticsController,
  ingest: ingestController,
  parserDetailed: parserDetailedController,
  ingestExternalApi: ingestExternalApiController,
};
