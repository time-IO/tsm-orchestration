commit 8e958c6c3253367bc199cc49840f9dbb6e06d5a2
Author: Joost Hemmen <joost.hemmen@ufz.de>
Date:   Fri Dec 12 22:32:29 2025 +0100

    worker-thing-setup, wip

diff --git a/src/setup_minio.py b/src/setup_minio.py
index dbb9c86..524b948 100755
--- a/src/setup_minio.py
+++ b/src/setup_minio.py
@@ -57,20 +57,20 @@ class CreateThingInMinioHandler(AbstractHandler):
         self.minio_admin.user_add(access_key=user, secret_key=passw)
 
         logger.debug(f"Creating MinIO policy {user} for bucket {bucket}")
-        policy = self.minio_admin.policy_build(bucket_name=bucket)
+        policy = self.minio_admin.build_bucket_policy(bucket_name=bucket)
         self.minio_admin.policy_add(
             policy_name=user,
             policy=policy,
         )
 
         logger.debug(f"Assigning policy {user} to user {user}")
-        self.minio_admin.user_policy_set(policy_name=user, access_key=user)
+        self.minio_admin.user_policy_set(policy_name=user, user=user)
 
-        if self.minio.bucket_exists(bucket_name=bucket, object_lock=True):
+        if self.minio.bucket_exists(bucket_name=bucket):
             logger.debug(f"Bucket {bucket} already exists")
         else:
             logger.debug(f"Creating bucket {bucket}")
-            self.minio.make_bucket(bucket_name=bucket)
+            self.minio.make_bucket(bucket_name=bucket, object_lock=True)
 
         if self.minio.get_bucket_retention(bucket_name=bucket):
             logger.debug(f"Bucket {bucket} already has retention set")
