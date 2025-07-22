"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3

# Create an AWS resource (S3 Bucket)
bucket = s3.BucketV2('my-bucket')

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)
# Bucket ...

# Turn the bucket into a website:
website = s3.BucketWebsiteConfigurationV2("website",
    bucket=bucket.id,
    index_document={
        "suffix": "index.html",
    })

# Permit access control configuration:
ownership_controls = s3.BucketOwnershipControls(
    'ownership-controls',
    bucket=bucket.id,
    rule={
        "object_ownership": 'ObjectWriter',
    },
)

# Enable public access to the website:
public_access_block = s3.BucketPublicAccessBlock(
    'public-access-block', bucket=bucket.id, block_public_acls=False
)