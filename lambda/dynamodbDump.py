import requests
import json
import sys 
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import pandas as pd
import random
from bs4 import BeautifulSoup as bs

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
    store_id = '5659'  # Arroyo Grande vendor 1 Store ID
    proxies = { 'http': 'http://10.10.1.10:3128' }
    # the below url only grabs 60 items for now...
    vendor = ""
    url = f'https://www.{vendor}.com/grocery/v4/api/products/search?count=60&offset=0&page=1&storeId={store_id}&query={query}'
    response = requests.get(url, headers=headers, proxies=proxies)
    json_response = json.loads(response.text, parse_float=Decimal)
    products = json_response['products']
    return products

def query_vendor2(query):
    headers = {'User-Agent': 'Mozilla/5.0', }
    response = None
    store_id = '2759'

    provider = "" # NOTE: vendor has a provider
    vendor = "" # NOTE: provide own vendor
    key = "" # NOTE: requires an api key
    visitorId = "" # NOTE: requires a visitor id
    url = f"https://{provider}.{vendor}.com/{provider}_aggregations/v1/web/plp_search_v1?key={key}&channel=WEB&count=24&keyword={query}" \
    f"&page={query}&pricing_store_id={store_id}&store_ids={store_id}&visitor_id={visitorId}"

    response = requests.get(url, headers=headers)
    json_response = json.loads(response.text, parse_float=Decimal)
    products = json_response['data']['search']['products']
    return products


def query_vendor3(query):
    '''
    Queries vendor 3, an Online marketplace based in the _________.
    Offers prices for ___, ________-, and ____ for their respective currencies

    Currently: 
        Api only retreives offers from ___. Possible change in cookie values could retrieve other countries
        Limits high-rate requests, so the requests getting specific product specifications must be spread out
        If less specific data is ok, just the search result can be used. It contains the product name and price
    '''
    def vendor3_await_response():
        time.sleep(random.randint(27, 47)) # Scatters requests to not get 429 code. These numbers work consistently and were derived experimentally
    
    headers = {'User-Agent': 'Mozilla/5.0', }
    response = None
    #country_codes = ["___", "______", "______"]
    limit = 50  # default is 50, max is 150
    page = 1  # default is 1
    search_query = query.replace("-", " ")   # for better results
    vendor3 = ""
    search_url = f"https://www.{vendor3}.com/_svc/catalog/api/v2/u/search?limit={limit}&page={page}&q={search_query}"
    search_response = requests.get(search_url, headers=headers)
    if search_response.status_code != 200:
        raise Exception(f"Vendor 3 API Request Failed. Status Code {search_response.status_code}")
    vendor3_await_response()
    json_search_response = json.loads(search_response.text, parse_float=Decimal)
    results = json_search_response['hits']
    total_pages = json_search_response["nbPages"]  # not used, but can be for more results
    products = []
    for i, result in enumerate(results):
        product_url = f"https://www.{vendor3}.com/_svc/catalog/api/v2/u/{result['url']}/{result['sku']}/p?o={result['offer_code']}"
        product_response = requests.get(product_url, headers=headers)
        # print(f'{product_response.status_code} for vendor 3 product #{i+1}')
        if product_response.status_code != 200:
            print(f"Vendor 3 product #{i+1} for query, \"{query}\", returned reponse code {product_response.status_code}")
            if product_response.status_code == 429:
                for i in range(2):  # wait 2x the normal amount
                    vendor3_await_response()
            else:
                vendor3_await_response()
            break
        print(f'Vendor 3 product #{i+1} successfully retrieved')
        json_product_response = json.loads(product_response.text, parse_float=Decimal)
        products.append(json_product_response['product'])
        vendor3_await_response()
    return products

def query_vendor4(query):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument("--log-level=3")

    vendor4 = ""

    # load page
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get(f'https://www.{vendor4}.com.mx/en/search/?ref_p=ser_tp&q={query}&sort_by=relevance')
    # time.sleep(3)

    wait = WebDriverWait(driver, 10)
    # elements=wait.until(EC.element_to_be_selected(driver.find_elements_by_class_name("item")))
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item")))
    elements = driver.find_elements_by_class_name("item")
    product_list = []
    for item in elements:
        if len(product_list) >= 5:
            break
        # initial page of multiple items
        
        time.sleep(10)
        min_detail = item.find_elements_by_class_name("product-min-detail")[0]
        description = min_detail.find_element_by_tag_name("a").get_attribute('title')
        price = min_detail.find_element_by_class_name("product-price").text
        image = min_detail.parent.find_element_by_class_name('product-image') \
         .find_element_by_tag_name("a").find_element_by_tag_name("img").get_attribute('src')
        description = min_detail.find_element_by_tag_name("a").get_attribute('title')

        # specific item data
        url = min_detail.find_element_by_tag_name("a").get_attribute('href')
        # need new driver otherwise encounter stale element reference
        driver2 = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver2.get(url)
        time.sleep(10)

        # time.sleep(3)
        wait = WebDriverWait(driver, 10)
        # wait.until(EC.element_to_be_selected(driver2.find_element_by_id('product-attribute-specs-table'))).get_attribute('outerHTML')
        wait.until(EC.presence_of_element_located((By.ID, 'product-attribute-specs-table')))
        table = driver2.find_element_by_id('product-attribute-specs-table').get_attribute('outerHTML')
        
        driver2.quit()

        product_details = pd.read_html(table)[0]
        print(product_details)
        json = product_details.to_json(orient='index')
        record = {'description' : description, 'price' : price, 'image' : image, 'specifications' : json}
        product_list.append(record)
        
    raise Exception("goodnight")
    driver.quit()
    return product_list
# For each store we want to get a few basic data points including
#   * product id / sku
#   * product image
#   * general info: name, sales quantity, dimensions/volume etc
#   * PRICE
#   * Date

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
                    'info': product['basic'],  # vendor 1 specific
                    'pricing': product['store']['price']
                }
                product_list.append(product_info)

        existing_record = table.query(KeyConditionExpression=Key('query').eq(query))
        
        stores = len(existing_record['Items']) > 0 and existing_record['Items'][0]['stores']         
        if stores:
            stores['vendor1']  = product_list
            product_metadata['stores'] = stores
        else:
            product_metadata['stores'] = {'vendor1' : product_list} 

        # currencies = len(existing_record['Items']) > 0 and existing_record['Items'][0]['currencies']  
        # if currencies:
        #     product_metadata['currencies']['vendor1'] = 'USD'
        # else:
        #     product_metadata['currencies'] = {'vendor1' : 'USD'}

        product_metadata['category'] = category
        product_metadata['query'] = query # dynamo partition key
        product_metadata['date-collected'] = datetime.datetime.now().strftime("%Y-%m-%d")

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
        product_metadata = {'product': query,}

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
        if stores:
            stores['vendor2']  = product_list
            product_metadata['stores'] = stores
        else:
            product_metadata['stores'] = {'vendor2' : product_list, } 

        # currencies = len(existing_record['Items']) > 0 and existing_record['Items'][0]['currencies']  
        # if currencies:
        #     product_metadata['currencies']['vendor2'] = 'USD'
        # else:
        #     product_metadata['currencies'] = {'vendor2' : 'USD'}

        product_metadata['category'] = category     
        product_metadata['query'] = query # dynamo partition key
        product_metadata['date-collected'] = datetime.datetime.now().strftime("%Y-%m-%d")        
        response = table.put_item(Item=product_metadata)

        return response

    except Exception as e:
        print("Could not insert into db", e)
        return None

def insert_vendor3_products(query, products, category):
    # if len(products) == 0:
    #     print('No query results found')
    #     return None

    # try:
        product_list = []
        stores = []
        store_info = {'name': 'vendor3'}
        product_metadata = {'product': query}

        for product in products:
            if 'sku' in product:
                try:
                    product_info = {
                        'sku' : product['sku'],
                        'brand' : product['brand'],
                        'name' : product['product_title'],
                        'specifications' : product['specifications'],
                        'pricing' : {'price' : product['variants'][0]['offers'][0]['price'], 
                                    'sale_price' : product['variants'][0]['offers'][0]['sale_price']},
                        'images' : {'image_keys' : product['image_keys']},
                        'url' : product['variants'][0]['offers'][0]['url'] + "/" + product["sku"]
                    }
                except Exception as e:
                    print(f"vendor3: product {product['sku']} raised: {e}")
                    continue

            product_list.append(product_info)

        existing_record = table.query(KeyConditionExpression=Key('query').eq(query))
        
        stores = len(existing_record['Items']) > 0 and existing_record['Items'][0]['stores']         

        if stores:
            stores['vendor3']  = product_list
            product_metadata['stores'] = stores
        else:
            product_metadata['stores'] = {'vendor3' : product_list,} 

        # currencies = len(existing_record['Items']) > 0 and existing_record['Items'][0]['currencies']  
        # if currencies:
        #     product_metadata['currencies']['vendor3'] = 'USD'
        # else:
        #     product_metadata['currencies'] = {'vendor3' : 'USD'}

        product_metadata['category'] = category
        product_metadata['query'] = query # dynamo partition key
        product_metadata['date-collected'] = datetime.datetime.now().strftime("%Y-%m-%d")        
        response = table.put_item(Item=product_metadata)

        return response

    # except Exception as e:
    #     print("Could not insert into db", e)
    #     return None

def insert_vendor4_products(query, products, category):
    if len(products) == 0:
        print('No query results found')
        return None

    try:
        product_list = []
        stores = []
        store_info = {'name': 'vendor4'}
        product_metadata = {'product': query}

        for product in products:
            # record = {'description' : description, 'price' : price, 'image' : image, 'specifications' : json}
            product_info = {
                'description' : product['description'],
                'price' : product['price'],
                'image' : product['image'],
                'specifications' : product['specifications'],
            }
            product_list.append(product_info)

        existing_record = table.query(KeyConditionExpression=Key('query').eq(query))
        
        stores = len(existing_record['Items']) > 0 and existing_record['Items'][0]['stores']         
        if stores:
            stores['vendor4']  = product_list
            product_metadata['stores'] = stores
        else:
            product_metadata['stores'] = {'vendor4' : product_list,} 

        # currencies = len(existing_record['Items']) > 0 and existing_record['Items'][0]['currencies']  
        # if currencies:
        #     product_metadata['currencies']['vendor4'] = 'USD'
        # else:
        #     product_metadata['currencies'] = {'vendor4' : 'USD'}

        product_metadata['category'] = category
        product_metadata['query'] = query # dynamo partition key
        product_metadata['date-collected'] = datetime.datetime.now().strftime("%Y-%m-%d")        
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
        response = insert_vendor1_products(query, products, category)
    elif store == 'vendor2':
        products = query_vendor2(query)
        response = insert_vendor2_products(query, products, category)
    elif store == 'vendor3':
        products = query_vendor3(query)
        response = insert_vendor3_products(query, products, category)
    elif store == 'vendor4':
        products = query_vendor4(query)
        response = insert_vendor4_products(query, products, category)
    else:
        raise ValueError('unsupported store')


    return response and response['ResponseMetadata']['HTTPStatusCode']

# print(lambda_handler({"queryStringParameters" : {"query" : "toaster", "store" : "vendor2",
# 'category' : 'small_electric_household_appliances'}}, None))

# print(lambda_handler({"queryStringParameters" : {"query" : "milk", "store" : "vendor3",
# 'category' : 'milk_cheese_eggs'}}, None))
# # print(lambda_handler({'queryStringParameters' : {'query' : 'mutton', 'store' : 'vendor1'}}, None))

# just took out 'rice' as the first element of the list from 'bread_cereal'
'''
foods = {
    'bread_cereal' : ['rice', 'cereal', 'bread', 'bakery', 'pasta', 'couscous'],
    'meat' : ['beef', 'veal', 'lamb', 'goat', 'chicken', 'poultry'],
    'fish_seafood' : ['fish', 'seafood', 'frozen-seafood', 'frozen-fish'],
    'milk_cheese_eggs' : ['milk', 'cheese', 'curd', 'eggs'],
    'oils_fats' : ['butter', 'margarine', 'oil'],
    'vegetables' : ['vegetables', 'potatoes', 'tuber-vegetables']
}

household_appliances = {
    'small_electric_household_appliances' : ['coffee maker', 'food processor',
    'mixer', 'electric grill', 'microwave', 'fryer', 'rice cooker']
}
'''



household_appliances = {
    'small_electric_household_appliances' : ['microwave', 'fryer', 'rice cooker']
}

store = "vendor3"

# for category in foods:
#     for query in foods[category]:
#         print("Beginning -> " + store + ": " + category + ": " + query)
#         print(lambda_handler({"queryStringParameters" : {"query" : query, "store" : store,
#                                                          'category' : category}}, None))
#         print("Completed -> " + store + ": " + category + ": " + query)

for category in household_appliances:
    for query in household_appliances[category]:
        print("Beginning -> " + store + ": " + category + ": " + query)
        print(lambda_handler({"queryStringParameters" : {"query" : query, "store" : store,
                                                         'category' : category}}, None))
        print("Completed -> " + store + ": " + category + ": " + query)


# stores = ['vendor2', 'vendor3']

# for store in stores: 
#     for category, item_list in household_appliances.items():
#         for item in item_list:

#             if store != 'vendor4':
#                 time.sleep(random.randint(5,10))
#             try:
#                 response_code = lambda_handler({'queryStringParameters' : 
#                     {'query' : item, 'store' : store, 'category' : category}}, None)
#                 print("{} {}".format(item, store))

#             except Exception as e:
#                 print('FAILED: {}       {}\n Error: {}'.format(store, item, e))

#         if response_code != 200:
#             print('FAILED: {}       {}'.format(store, item))



