import ingestExternalApiBoschController from '@/services/ingest_external_api_bosch';
import ingestExternalApiDwdController from '@/services/ingest_external_api_dwd';
import ingestExternalApiNeutronMonitorController from '@/services/ingest_external_api_neutron_monitor';
import ingestExternalApiUbaController from '@/services/ingest_external_api_uba';
import ingestExternalApiTheThingsNetworkController from '@/services/ingest_external_api_the_things_network';
import ingestExternalApiTSystemsController from '@/services/ingest_external_api_tsystems';
import ingestExternalApiSensotoController from '@/services/ingest_external_api_sensoto';
import ingestMqttController from '@/services/ingest_mqtt';
import ingestJournalController from '@/services/ingest_journal';
import ingestSftpController from '@/services/ingest_sftp';
import ingestSftpStorageController from '@/services/ingest_sftp_storage';
import ingestExternalSftpController from '@/services/ingest_external_sftp';
import ingestExternalSftpStorageController from '@/services/ingest_external_sftp_storage';
import triggerExternalApiGenController from '@/services/trigger_external_api_generic';
import triggerExternalSftpController from '@/services/trigger_external_sftp';
import permissionGroupController from '@/services/permission_group';
import userController from '@/services/user';
import neutronMonitorStationController from '@/services/neutron_monitor_stations';
import mqttParserController from '@/services/parser_mqtt';
import csvParserController from '@/services/parser_csv';
import jsonParserController from '@/services/parser_json';
import soilcanParserController from '@/services/parser_soilcan';
import qualityControlSettingController from '@/services/quality_control_setting';
import staController from '@/services/sta';
import qualityControlSettingsTriggerController from '@/services/quality_control_settings_trigger';

import parserTimezoneController from '@/services/parser_timezone';
import parserEncodingController from '@/services/parser_encoding';

import ingestController from '@/services/ingest';
import parserDetailedController from '@/services/parser_detailed';
import ingestExternalApiController from '@/services/ingest_external_api';

import usageStatisticsController from '@/services/usage_statistics';

export const API = {
  ingestExternalApiBosch: ingestExternalApiBoschController,
  ingestExternalApiDwd: ingestExternalApiDwdController,
  ingestExternalApiNeutronMonitor: ingestExternalApiNeutronMonitorController,
  ingestExternalApiTSystems: ingestExternalApiTSystemsController,
  ingestExternalApiTheThingsNetwork: ingestExternalApiTheThingsNetworkController,
  ingestExternalApiUba: ingestExternalApiUbaController,
  ingestExternalApiSensoto: ingestExternalApiSensotoController,
  ingestMqtt: ingestMqttController,
  ingestJournal: ingestJournalController,
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
  triggerExternalSftp: triggerExternalSftpController,
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
