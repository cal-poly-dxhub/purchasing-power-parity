import requests
import json
import sys 
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import datetime

#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-
    # Second "test" version of the lambda function to avoid adding unnceccesary 
    # code to the lambda
#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-----#-



# connect to dynamoDB
try:
    table = boto3.resource('dynamodb').Table('product-data')
except Exception as e:
    print(e)
    sys.exit(-1)

def lambda_handler(event=None, context=None):
    # Ideally we would get a query/store search parameter from event through api gateway
        # Ex: {'query' : 'apple', 'store' : 'vendor1'}
    query = event.get('queryStringParameters') and event['queryStringParameters'].get('query')
    store = event.get('queryStringParameters') and event['queryStringParameters'].get('store')
    category = event.get('queryStringParameters') and event['queryStringParameters'].get('category')
    #Default
    if query is None:
        query = "milk"

    if store is None:
        store = "vendor1"

    if category is None:
        category = 'milk_cheese_eggs'

    response = query_api(query, store, category)
    return response


def query_vendor1(query):
    headers = {'User-Agent': 'Mozilla/5.0', }
    response = None
    store_id = '5659'  # Arroyo Grande Vendor 1 Store ID

    # the below url only grabs 60 items for now...
    vendor = "" # NOTE: provide own vendor
    url = f'https://www.{vendor}.com/grocery/v4/api/products/search?count=60&offset=0&page=1&storeId={0}&query={1}'.format(
        store_id, query)
    response = requests.get(url, headers=headers)
    json_response = json.loads(response.text, parse_float=Decimal)
    products = json_response['products']
    return products

def query_vendor2(query):
    headers = {'User-Agent': 'Mozilla/5.0', }
    response = None
    store_id = '5659'

    provider = "" # NOTE: vendor has a provider
    vendor = "" # NOTE: provide own vendor
    key = "" # NOTE: requires an api key
    visitorId = "" # NOTE: requires a visitor id
    url = f"https://{provider}.{vendor}.com/{provider}_aggregations/v1/web/plp_search_v1?key={key}&channel=WEB&count=24&keyword={query}" \
    f"&page={query}&pricing_store_id=2759&store_ids=2759&visitor_id={visitorId}"

    response = requests.get(url, headers=headers)
    json_response = json.loads(response.text, parse_float=Decimal)
    products = json_response['data']['search']['products']
    return products

# For each store we want to get a few basic data points including
    # * product id / sku
    # * product image
    # * general info: name, sales quantity, dimensions/volume etc
    # * PRICE

def insert_vendor1_products(query, products, category):
    if len(products) == 0:
        print('No query results found')
        return None

    try:
        product_list = []
        stores = []
        store_info = {'name': 'vendor1'}
        product_metadata = {'product': query}

        for product in products:
            if 'sku' in product or 'USItemId':
                product_info = {
                    'sku': product['sku'] if 'sku' in product.keys() else product['USItemId'],
                    'info': product['basic'],  # vendor1 specific
                    'pricing': product['store']['price']
                }
                product_list.append(product_info)

        existing_record = table.query(KeyConditionExpression=Key('query').eq(query))
        
        stores = len(existing_record['Items']) > 0 and existing_record['Items'][0]['stores']         
        if stores is not False:
            stores['vendor1']  = product_list
            product_metadata['stores'] = stores
        else:
            product_metadata['stores'] = {'vendor1' : product_list} 

        product_metadata['category'] = category
        product_metadata['query'] = query # dynamo partition key
        response = table.put_item(Item=product_metadata)

        return response

    except Exception as e:
        print("Could not insert into db", e)
        return None


def insert_vendor2_products(query, products, category):
    if len(products) == 0:
        print('No query results found')
        return None

    try:
        product_list = []
        stores = []
        store_info = {'name': 'vendor2'}
        product_metadata = {'product': query}

        for product in products:
            if 'tcin' in product:
                product_info = {
                    'tcin' : product['tcin'],
                    'info' : product['item'],
                    'pricing' : product['price']
                }
            product_list.append(product_info)

        existing_record = table.query(KeyConditionExpression=Key('query').eq(query))
        
        stores = len(existing_record['Items']) > 0 and existing_record['Items'][0]['stores']         
        if stores is not False:
            stores['vendor2']  = product_list
            product_metadata['stores'] = stores
        else:
            product_metadata['stores'] = {'vendor2' : product_list} 

        product_metadata['category'] = category
        product_metadata['query'] = query # dynamo partition key
        product['date-collected'] = '2021-08-13'
        response = table.put_item(Item=product_metadata)

        return response

    except Exception as e:
        print("Could not insert into db", e)
        return None

def query_api(query, store, category):
    products = None
    response = None

    if store == 'vendor1':
        products = query_vendor1(query)
    elif store == 'vendor2':
        products = query_vendor2(query)
    else:
        raise ValueError('unsupported store')

    if store == 'vendor1':
        response = insert_vendor1_products(query, products, category)
    elif store == 'vendor2':
        response = insert_vendor2_products(query, products, category)

    return response and response['ResponseMetadata']['HTTPStatusCode']

# print(lambda_handler({'queryStringParameters' : {'query' : 'lamb', 'store' : 'vendor2'}}, None))
# print(lambda_handler({'queryStringParameters' : {'query' : 'mutton', 'store' : 'vendor1'}}, None))

foods = {
    # 'bread_cereal' : ['rice', 'cereal', 'bread', 'bakery', 'pasta', 'couscous'],
    # 'meat' : ['beef', 'veal', 'lamb', 'mutton', 'mutton', 'goat', 'chicken', 'poultry'],
    # 'fish_seafood' : ['fish', 'seafood', 'frozen-seafood', 'frozen-fish'],
    # 'milk_cheese_eggs' : ['milk', 'cheese', 'curd', 'eggs'],
    # 'oils_fats' : ['butter', 'margarine', 'oil'],
    # 'vegetables' : ['vegetables', 'potatoes', 'tuber-vegetables']
}

# stores = ['vendor2', 'vendor1']
# stores = ['vendor2']

# for store in stores: 
#     for category, food_list in foods.items():
#         for food in food_list:
#             print("{} {}".format(food, store))
#             response_code = lambda_handler({'queryStringParameters' : 
#                 {'query' : food, 'store' : store, 'category' : category}}, None)

#         if response_code != 200:
#             print('FAILED: {}       {}'.format(store, food))



