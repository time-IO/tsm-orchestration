import ingestExternalApiDwdController from "src/services/ingest_external_api_dwd"
import ingestExternalApiNeutronMonitorController from "src/services/ingest_external_api_neutron_monitor"
import ingestExternalApiUbaController from "src/services/ingest_external_api_uba"

import permissionGroupController from "src/services/permission_group"
import userController from "src/services/user"
import neutronMonitorStationController from "src/services/neutron_monitor_stations"
import mqttParserController from "src/services/mqtt_parser"

export const API = {
  ingestExternalApiDwd:ingestExternalApiDwdController,
  ingestExternalApiUba: ingestExternalApiUbaController,
  ingestExternalApiNeutronMonitor: ingestExternalApiNeutronMonitorController,
  permissionGroup: permissionGroupController,
  user: userController,
  neutronMonitorStation: neutronMonitorStationController,
  mqttParser: mqttParserController,
};
