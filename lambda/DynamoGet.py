import boto3
import json
import sys

try:
    table = boto3.resource('dynamodb').Table('product-data')
except Exception as e:
    print(e)
    sys.exit(-1)


def lambda_handler(event, context):
    query = event.get(
        'queryStringParameters') and event['queryStringParameters'].get('query')
    if query is None:
        return generate_response(400, "Please provide a query to search for.")
    query_dynamo(query)


def query_dynamo(query):
    response = table.get_item(
        Key={
            'query': query
        },
        ProjectionExpression='stores'
    )
    if 'Item' in response:
        return generate_response(200, response['Item'])
    else:
        return generate_response(404, "Could not get from database: index does not exist.")


def generate_response(statusCode, message):
    return {
        'statusCode': statusCode,
        'headers': {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": """Content-Type, Date,
            X-Amzn-Trace-Id, x-amz-apigw-id, x-amzn-RequestId, Authorization""",
        },
        'body': json.dumps(message)
    }
