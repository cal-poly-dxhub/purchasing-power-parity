from aws_cdk import core as cdk
from aws_cdk import aws_lambda as lam
import aws_cdk.aws_dynamodb as dynamodpib
from aws_cdk.aws_dynamodb import (
    Table,
    Attribute,
    AttributeType,
    StreamViewType,
    BillingMode
)

from aws_cdk.aws_iam import (
    Role,
    ServicePrincipal,
    ManagedPolicy
)
# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.


class DynamodbStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        table = Table(self, "Table",
        partition_key=Attribute(name="query", type=AttributeType.STRING),
        sort_key=Attribute(name="category", type=AttributeType.STRING),
        billing_mode=BillingMode.PAY_PER_REQUEST,
        removal_policy=cdk.RemovalPolicy.DESTROY,
        table_name='product-data')

        # product_data_role = Role(
        #     self, 'Prodcut-DataDynamoDBRole',
        #     assumed_by=ServicePrincipal('appsync.amazonaws.com')
        # )


        dynamodbDump = lam.Function.from_function_arn(self, id="dynamoDBDump",
        function_arn="arn:aws:lambda:us-west-2:234177478365:function:dynamoDBDump")

        print(dynamodbDump.function_name)
        table.grant_read_write_data(dynamodbDump)
        
        # product_data_role.add_managed_policy(
        #     ManagedPolicy.from_aws_managed_policy_name(
        #         'AmazonDynamoDBFullAccess'
        #     )
        # )

