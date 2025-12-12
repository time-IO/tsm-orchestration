from admin_client import MinioAdminClient
from client import MinioClient
from minio.commonconfig import Tags

admin = MinioAdminClient()
minio = MinioClient()

# print(admin.info())

from uuid import uuid4


bucket_name = str(uuid4())


events = [
    "s3:ObjectCreated:CompleteMultipartUpload",
    "s3:ObjectCreated:Copy",  # not sure whether we want this one...
]

if not minio.bucket_exists(bucket_name):
    print("\tmaking bucket")
    print(minio.make_bucket(bucket_name))
    print("\tsetting retention")
    print(minio.set_bucket_retention(bucket_name, years=10))
print("\tgetting bucket")
print(minio.get_bucket(bucket_name))
print("\tsetting notification")
print(minio.set_bucket_notification(bucket_name=bucket_name))
tags = Tags.new_bucket_tags()
tags["key1"] = "value1"
tags["key2"] = "value2"
print("\tsetting tags")
print(minio.set_bucket_tags(bucket_name=bucket_name, tags=tags))
