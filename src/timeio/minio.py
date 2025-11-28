import json
import logging
import subprocess
import tempfile

from minio import Minio
from minio.commonconfig import GOVERNANCE, Tags
from minio.objectlockconfig import ObjectLockConfig, YEARS


class MinIoClientError(Exception):
    pass


class MinioClientNotFoundError(Exception):
    pass


class Mc:
    ALIAS = "my_minio"
    CONFIG_TEMPLATE = {
        "version": "10",
        "aliases": {
            ALIAS: {
                "url": "",
                "accessKey": "",
                "secretKey": "",
                "api": "s3v4",
                "path": "auto",
            }
        },
    }

    def __init__(self, url: str, access_key: str, secret_key: str, secure=True):

        self.url = url
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure

        self.alias = Mc.ALIAS
        self.config = Mc.CONFIG_TEMPLATE.copy()
        self.proto = "https://"

        self.config_dir = tempfile.TemporaryDirectory()
        self.config_file = open(
            "{}/config.json".format(self.config_dir.name), mode="w+"
        )

        self._init_config()

        # Python SDK minio client
        self.minio = Minio(
            self.url,
            secure=self.secure,
            access_key=self.access_key,
            secret_key=self.secret_key,
        )

        self.logger = logging.getLogger("minio-cli-wrapper")

        self._check_setup()

    def _check_setup(self):
        """
        Self check of client installation and credentials
        :return:
        """
        try:
            self._command(["admin", "info", self.alias])
        except FileNotFoundError as e:
            raise MinioClientNotFoundError(
                "Unable to find minio cli client. Install it from "
                "<https://docs.min.io/docs/minio-client-quickstart-guide.html#GNU/Linux>. "
            ) from e

    def _init_config(self):
        self.proto = "https://" if self.secure else "http://"
        self.config["aliases"][self.alias]["url"] = "{proto}{url}".format(
            proto=self.proto, url=self.url
        )
        self.config["aliases"][self.alias]["accessKey"] = self.access_key
        self.config["aliases"][self.alias]["secretKey"] = self.secret_key
        json.dump(self.config, self.config_file, indent=4)
        self.config_file.flush()

    def _command(self, command: list, confidential=False):
        ret = subprocess.run(
            ["mc", "-C", self.config_dir.name] + command + ["--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        if ret.returncode != 0:

            err_from_stdout = (
                ret.stdout if json.loads(ret.stdout).get("status") == "error" else ""
            )
            msg = (
                ret.stderr
                or err_from_stdout
                or '"Unspecified error: Empty response from minio ' 'client" '
            )
            self.logger.error(msg)
            raise MinIoClientError(json.dumps(json.loads(msg), indent=4))

        if not confidential:
            self.logger.info(ret.stdout)

        # Workaround for multiline json returned by mc
        val = self.parse_mc_output(ret)

        return val

    def parse_mc_output(self, ret):
        val = {}
        if len(ret.stdout.splitlines()) > 1:
            val["multiline"] = []
            for line in ret.stdout.splitlines():
                try:
                    val["multiline"].append(json.loads(line or "null"))
                except json.JSONDecodeError:
                    val["multiline"].append(line)
        else:
            val = json.loads(ret.stdout or "null")
        return val

    def user_add(self, access_key: str, secret_key: str):
        ret = self._command(
            ["admin", "user", "add", self.alias, access_key, secret_key],
            confidential=True,
        )
        # manually remove confidential parts before logging
        ret["secretKey"] = "*****"

        self.logger.info(ret)

    def policy_add(self, policy_name: str, policy: dict):
        policy_file = tempfile.NamedTemporaryFile(mode="w+")
        json.dump(policy, policy_file, indent=4)
        policy_file.flush()

        self._command(
            ["admin", "policy", "create", self.alias, policy_name, policy_file.name]
        )

    def policy_set_user(self, policy_name: str, username: str):

        if self.policy_user_mapping_exists(policy_name, username):
            self.logger.info(
                f'Policy mapping from user "{username}" to policy "{policy_name}" already set'
            )
            return

        self._command(
            ["admin", "policy", "attach", self.alias, policy_name, "--user", username]
        )

    def policy_unset_user(self, policy_name: str, username: str):

        if not self.policy_user_mapping_exists(policy_name, username):
            self.logger.info(
                f'Policy mapping from user "{username}" to policy "{policy_name}" not set'
            )
            return

        self._command(
            ["admin", "policy", "detach", self.alias, policy_name, "--user", username]
        )

    def get_policy_entities(self, username: str):
        return self._command(
            ["admin", "policy", "entities", self.alias, "--user", username]
        )

    def policy_user_mapping_exists(self, policy_name: str, username: str):
        user_mappings_result = self.get_policy_entities(username)

        for mapping in user_mappings_result["result"].get("userMappings", []):
            for policy in mapping.get("policies", []):
                if policy == policy_name:
                    return True

        return False

    def create_service_account(self, username: str):
        ret = self._command(
            ["admin", "user", "svcacct", "add", self.alias, username], confidential=True
        )
        # filter the relevant keys from the returned output
        return {"accessKey": ret["accessKey"], "secretKey": ret["secretKey"]}

    def bucket_exists(self, bucket_name):
        return self.minio.bucket_exists(bucket_name)

    def make_locked_bucket(self, bucket_name):
        return self.minio.make_bucket(bucket_name, object_lock=True)

    def set_bucket_100y_retention(self, bucket_name):
        lock_config = ObjectLockConfig(GOVERNANCE, 100, YEARS)
        self.minio.set_object_lock_config(bucket_name, lock_config)

    def enable_bucket_notification(self, bucket_name, event=["put"]):
        # Find notification targets
        info = self._command(["admin", "info", self.alias])
        targets = info.get("info").get("sqsARN")

        # add event listener
        for target in targets:
            if not self.bucket_notification_exists(bucket_name, target):
                self._command(
                    [
                        "event",
                        "add",
                        "{}/{}".format(self.alias, bucket_name),
                        target,
                        "--event",
                        ",".join(event),
                    ]
                )

    def bucket_notification_exists(self, bucket_name, target, prefix="", suffix=""):
        event_list = self._command(
            ["event", "list", "{}/{}".format(self.alias, bucket_name)]
        )

        if event_list is None:
            return False

        events = []

        # Sometimes it is a list, sometimes a single line :(
        if event_list.get("multiline"):
            events = event_list.get("multiline")
        else:
            events.append(event_list)

        for event in events:
            if (
                event.get("arn") == target
                and event.get("prefix") == prefix
                and event.get("suffix") == suffix
            ):
                return True

        return False

    def set_bucket_tags(self, bucket_name: str, plain_tags: dict):
        bucket_tags = Tags.new_bucket_tags()

        for k, v in plain_tags.items():
            bucket_tags[k] = v

        self.minio.set_bucket_tags(bucket_name, bucket_tags)

    def policy_set_ldap_user(self, policy_name: str, ldap_dn: str):
        ret = self._command(
            [
                "idp",
                "ldap",
                "policy",
                "attach",
                self.alias,
                policy_name,
                "--user",
                ldap_dn,
            ]
        )

        self.logger.info(ret)
        return ret

    def policy_unset_ldap_user(self, policy_name: str, ldap_dn: str):
        ret = self._command(
            [
                "idp",
                "ldap",
                "policy",
                "detach",
                self.alias,
                policy_name,
                "--user",
                ldap_dn,
            ]
        )

        self.logger.info(ret)
        return ret

    def set_bucket_quota(self, bucket_name: str, bucket_quota: str):
        ret = self._command(
            [
                "quota",
                "set",
                "{}/{}".format(self.alias, bucket_name),
                "--size",
                bucket_quota,
            ]
        )

        self.logger.info(ret)
        return ret
