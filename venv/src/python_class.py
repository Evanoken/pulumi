class resource:
    def __init__(self, name, resource_type):
        self.name = name
        self.resource_type = resource_type
        
    def describe(self):
        return f"resource: {self.name}, type: {self.resource_type}"
    
#creating an object instance

my_resource = resource("my-bucket", "AWS S3 Bucket")
print(my_resource.describe())


# Connecting to Pulumi
import pulumi_aws as aws

class S3Bucket:
    def __init__(self, bucket_name, is_public=False):
        self.bucket_name = bucket_name
        self.bucket = aws.s3.Bucket(
            bucket_name,
            acl="public-read" if is_public else "private"
        )

    def get_bucket_arn(self):
        return self.bucket.arn

# Usage in Pulumi
my_bucket = S3Bucket("my-app-bucket", is_public=True)
pulumi.export("bucket_arn", my_bucket.get_bucket_arn())


# Intermediate Concepts
class CloudResource:
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

class S3Bucket(CloudResource):  # Inherits from CloudResource
    def __init__(self, name, is_public=False):
        super().__init__(name)  # Call parent class's __init__
        self.bucket = aws.s3.Bucket(
            name,
            acl="public-read" if is_public else "private"
        )

# Usage
bucket = S3Bucket("my-app-bucket")
print(bucket.get_name())  # Output: my-app-bucket


# Encapsulation
class S3Bucket:
    def __init__(self, name):
        self.__name = name  # Private attribute
        self.bucket = aws.s3.Bucket(name)

    def get_name(self):
        return self.__name

bucket = S3Bucket("my-bucket")
print(bucket.get_name())  # Output: my-bucket
# print(bucket.__name)  # Error: AttributeError (cannot access private attribute)

# 3. Class vs. Instance Attributes
# Instance Attributes: Defined in __init__ and unique to each object.
# Class Attributes: Shared across all instances of the class.

class Resource:
    provider = "AWS"  # Class attribute

    def __init__(self, name):
        self.name = name  # Instance attribute

res1 = Resource("bucket1")
res2 = Resource("bucket2")
print(res1.provider, res1.name)  # Output: AWS bucket1
print(res2.provider, res2.name)  # Output: AWS bucket2

#new