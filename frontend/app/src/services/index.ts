import ingestExternalApiDwdController from "src/services/ingest_external_api_uba"
import permissionGroupController from "src/services/permission_group"
import userController from "src/services/user"
import neutronMonitorStationController from "src/services/neutron_monitor_stations"

export const API = {
  ingestExternalApiDwd: ingestExternalApiDwdController,
  permissionGroup: permissionGroupController,
  user: userController,
  neutronMonitorStation: neutronMonitorStationController
}
