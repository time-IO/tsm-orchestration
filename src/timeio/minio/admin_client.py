commit 8e958c6c3253367bc199cc49840f9dbb6e06d5a2
Author: Joost Hemmen <joost.hemmen@ufz.de>
Date:   Fri Dec 12 22:32:29 2025 +0100

    worker-thing-setup, wip

diff --git a/src/timeio/minio/admin_client.py b/src/timeio/minio/admin_client.py
index 5a23e22..a481999 100644
--- a/src/timeio/minio/admin_client.py
+++ b/src/timeio/minio/admin_client.py
@@ -71,14 +71,14 @@ class MinioAdminClient:
         r = self.minio_admin.policy_info(policy_name=policy_name)
         return self._parse(r)
 
-    def user_policy_set(self, policy_name: str, access_key: str) -> UserT:
-        self.minio_admin.policy_set(policy_name=policy_name, access_key=access_key)
-        r = self.minio_admin.user_info(access_key=access_key)
+    def user_policy_set(self, policy_name: str, user: str) -> UserT:
+        self.minio_admin.policy_set(policy_name=policy_name, user=user)
+        r = self.minio_admin.user_info(access_key=user)
         return self._parse(r)
 
-    def user_policy_unset(self, policy_name: str, access_key: str) -> UserT:
-        self.minio_admin.policy_unset(policy_name=policy_name, access_key=access_key)
-        r = self.minio_admin.user_info(access_key=access_key)
+    def user_policy_unset(self, policy_name: str, user: str) -> UserT:
+        self.minio_admin.policy_unset(policy_name=policy_name, user=user)
+        r = self.minio_admin.user_info(access_key=user)
         return self._parse(r)
 
     def get_policy_entities(
