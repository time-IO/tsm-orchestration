import ingestExternalApiDwdController from "src/services/ingest_external_api_uba"
import permissionGroupController from "src/services/permission_group"
import userController from "src/services/user"

export const API = {
  ingestExternalApiDwd: ingestExternalApiDwdController,
  permissionGroup: permissionGroupController,
  user: userController
}
