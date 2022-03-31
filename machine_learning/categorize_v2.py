import spacy
import descriptions as descriptions
from spacy.matcher import PhraseMatcher
import requests
import json
from uuid import uuid4 # only needed for demo purposes. Dynamo should have this all
import pymysql.cursors
import random 

aws_api_url = "https://5e7hnb1vb3.execute-api.us-west-2.amazonaws.com/dev/"

"""
init() returns the required data structures needed for ML product categorization.
Input:  query -> a string representing our dynamoDB sort key
        category -> a string representing our dynamoDB partition key
Output: nlp -> Spacy's natural language processing data structure
        products -> a dictionary of products returned from dynamoDB. These products
                    are found using the query and category arguments.
        matcher -> Spacy's phrase matcher used to help derive potential categories.
"""


def init(query, category):
    # necessary pipeline
    nlp = spacy.load("en_core_web_lg")
    matcher = PhraseMatcher(nlp.vocab)
    # load products from db
    products = descriptions.driver('description', query, category)
    return nlp, products, matcher


"""
create_docs() generates an array of NLP documents using spacy's data structures returned from
init(), and the products within dynamoDB.
Input:  nlp -> see init()
        products -> see init()
        query -> see init()
Output: doc_array -> an array containing tokenized strings of products.
"""


def create_docs(nlp, products, query):
    doc_array = {'docs': [], 'uuids': []}
    for product_array in products[query]:  # [query]:
        for store in product_array:
            for index in range(len(product_array[store]['products'])):
                doc_array['docs'].append(nlp(product_array[store]['products'][index].lower()))
                doc_array['uuids'].append(product_array[store]['uuids'][index])
    return doc_array


"""
Determines if any product within the products data structure matches
to a category within the categories array. If so, this product
is added to a matched_products data structure and returned.

Input:  products -> a dictionary containing the query key. The value of this
        key is an array of dictionaries. Each dictionary contains a key representing
        the store the data was sourced from, and an array value containing a list of
        strings representing the product.

        categories -> an array of dictionaries, each containing a category sourced from RDS.
        Each dictionary contains an int key'id' and a string key 'name'.
Output: a dictionary containing a key of a category 'id' and a product key.

"""


def match_products_to_categories(nlp, products, categories):
    matched_products = {}
    query = list(products.keys())[0]  # should only contain one key
    for store in products[query]:
        for products in list(store.values()):
            for index in range(len(products['products'])):
                sim_score = [
                    {'product': str(products['products'][index]),
                     'similarity': nlp(str(products['products'][index])).similarity(nlp(category['name'])),
                     'category': category,
                     'uuid': products['uuids'][index]} for category in categories]
                # sort array of similarities
                sorted_sim_score = sorted(
                    sim_score, key=lambda entry: entry['similarity'], reverse=True)
                #if sorted_sim_score[0]['similarity'] > 0.70:
                #matched_products.append(sorted_sim_score[0])
                if sorted_sim_score[0]['category']['name'] not in matched_products:
                    matched_products[sorted_sim_score[0]['category']['name']] = {
                            'id': sorted_sim_score[0]['category']['id'], 'products': []}
                    matched_products[sorted_sim_score[0]['category']
                                     ['name']]['products'].append(sorted_sim_score[0])
    # print(unsorted_matches)
    return matched_products


def generate_categories(nlp, matcher, products, query, category):
    # terms -> home of potential categories
    terms = []
    # categories -> dictionary that will contain our products mapped to a category
    categories = {}
    # generate documents
    doc_array = create_docs(nlp, products, query)
    # generate categories
    for doc in doc_array['docs']:
        new_category = ""
        add = True
        for token in doc:
            if token.similarity(nlp(query)) >= 0.60 and (token.text != query and token.text != category):
                new_category += "{} ".format(token.text)
        for word in new_category.split():
            if word in terms:
                add = False
        if add and len(new_category.strip()) > 0:
            terms.append(new_category.strip())

    # add categories to pattern matcher
    category_array = [nlp(category) for category in terms]
    matcher.add('{}_PATTERN'.format(query), category_array)

    # begin categorizing products further
    for index in range(len(doc_array['docs'])):
        doc = doc_array['docs'][index]
        matches = matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            if f"{query},{span.text}" not in categories:
                categories[f"{query},{span.text}"] = []
            categories[f"{query},{span.text}"].append({'product': doc.text, 'uuid': doc_array['uuids'][index]})

    # This should contain a unique code for each generated category, as well as products mapped to the category.

    return categories

"""
Retrieves all headings within our RDS database as an array of dictionaries.
The dictionary contains an 'id' field required for the subcategory table if
a new subcategory needs to be created. 

Output: headings -> an array of dictionaries containing a 'name' and 'id' key.
                    The array is empty if no content is found, or the API returns
                    a non-200 status code.
"""


def get_headings_from_rds():
    route = "headings"
    # grab all headings from rds using appropriate query string
    query_strings = "?class=all"
    raw_response = requests.get(aws_api_url + route + query_strings)
    headings = []
    if raw_response.status_code == 200:
        json_response = json.loads(raw_response.content)
        json_body = json.loads(json_response['body'])
        headings = [heading for heading in json_body['headings']]
    else:
        print("Could not query API.")
        print(raw_response.status_code)
    return headings


"""
Retrieves all subcategories within our RDS database as an array of dictionaries.
The dictionary contains an 'id' field required for the subcategory table if
a new subcategory needs to be created. 

Output: headings -> an array of dictionaries containing a 'name' and 'id' key.
                    The array is empty if no content is found, or the API returns
                    a non-200 status code.
"""


def get_subcategories_from_rds():
    route = "subcategories"
    # grab all headings from rds using appropriate query string
    raw_response = requests.get(aws_api_url + route)
    subcategories = []
    if raw_response.status_code == 200:
        json_response = json.loads(raw_response.content)
        json_body = json.loads(json_response['body'])
        subcategories = [
            subcategory for subcategory in json_body['subcategories']]
    else:
        print("Could not query API.")
        print(raw_response.status_code)
    return subcategories


# returns the parent code of the closest matching subcategories. 
def get_generated_category_parent_code(nlp, query, rds_categories):
    test = []
    FOUND = False
    for category in rds_categories:
        if query in category['name'].lower():
            FOUND = True
            #print(category['heading'], category['name'])
            return category['heading']
        sim = nlp(category['name']).similarity(nlp(query))
        test.append({'product': category['name'], 'similarity': sim})
    if not FOUND:
        return sorted(test, key=lambda entry: entry['similarity'], reverse=True)[0]['heading']


def insert_products_into_database(matched_products, generated_categories, generated_ids):
    insert_stmt = """INSERT INTO `items_details`.products (Parent_Id, Code) VALUES"""
    stmt_array = []
    counter = 0
    # matched products contain categories from RDS and products that should be mapped to them.
    # Since they are already in RDS, we should have the unique code for each subcategory already.
 #print(matched_products)
    for subcategory in matched_products:
        for product in matched_products[subcategory]['products']:
            stmt_array.append(insert_stmt + """ ({}, "{}");""".format(matched_products[subcategory]['id'], product['uuid']))
    # at this point, stmt_array is ready for inserting. But we need to do generated categories.
    for subcategory in generated_categories:
        for product in generated_categories[subcategory]:
            stmt_array.append(insert_stmt + """ ({}, "{}");""".format(generated_ids[counter], product['uuid']))
        counter += 1
    return stmt_array


def insert_subcategories_into_database(generated_categories, parent_code):
    insert_stmt = """INSERT INTO `items_details`.subcategories (Name, Parent_Id) VALUES"""
    stmt_array = []
    inserted_ids = []
    connection = pymysql.connect(host='',
                             user='',
                             password='',
                             database='',
                             cursorclass=pymysql.cursors.DictCursor)
    # generate our insert statements
    for subcategory in generated_categories:
        stmt_array.append(insert_stmt + """ ("{}", {})""".format(subcategory,parent_code))
        #inserted_ids.append(random.randint(100,200))
    with connection:
        with connection.cursor() as cursor:
            # Read a single record
            for stmt in stmt_array:
                cursor.execute(stmt)
                result = cursor.lastrowid
                inserted_ids.append(result)
        connection.commit()
    # at this point we need to insert these subcategories and return their id to insert 
    # products underneath them.
    return inserted_ids



if __name__ == "__main__":
    query = 'vegetables'
    category = 'meat'
    nlp, products, matcher = init(query, category)
    rds_categories = get_subcategories_from_rds()
    #generate_categories(nlp, matcher, products, query, category)
    matched_products = match_products_to_categories(
        nlp, products, rds_categories)
    parent_code = get_generated_category_parent_code(nlp, query, rds_categories)
    generated_categories = generate_categories(nlp, matcher, products, query, category)
    generated_ids = insert_subcategories_into_database(generated_categories, parent_code)
    #[insert_statements.append(stmt) for stmt in insert_products_into_database(matched_products, generated_categories)]
    insert_statements = insert_products_into_database(matched_products, generated_categories, generated_ids)
    for stmt in insert_statements:
        print(stmt)
