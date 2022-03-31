import json
import sys

import requests
import spacy
from pandas import json_normalize

try:
    nlp = spacy.load("en_core_web_lg")
except:
    print("Please install en_core_web_lg")
    sys.exit(-1)

"""

returns a dictionary containing data from DynamoDB. The function requires a
query string, as well as a category. Ideally these should be an index and sort
key for our database.

Example queries: milk, beef, margarine (partition key)
Example categories: dairy, meat, oils_fats (sort key)

"""


def get_data(query, category):
    # required api call variables
    api_key = '' # NOTE: must provide own api key
    awsURL = "https://5e7hnb1vb3.execute-api.us-west-2.amazonaws.com/dev/dynamo?"
    # what I am querying
    query_qs = 'query={}'.format(query)
    category_qs = 'category={}'.format(category)
    headers = {'x-api-key': api_key}
    awsURL += query_qs + "&" + category_qs

    # grab data then load as json
    response = requests.get(awsURL, headers=headers)
    return json.loads(response.text)


"""

A basic normalization of JSON product data.
It may need to be fine-tuned to grab deeper-nested data for some attributes.

Data input should already be loaded by json.loads(), or returned from the
get_data() function.

Returns an array of dictionaries, or an empty array if an error occurs.
Each dictionary item contains a 'store' key and a 'frame' key,
which store is the location data was taken from and frame is a pandas data frame.

"""


def normalize_data(data):
    normalized_dataframes = []
    try:
        for key in data['stores']:
            store_name = key  # save for later
            nested_data = data['stores'][key]
            # we need to try and get as deep down as we can to product data.
            # if nested_data length is 1, it implies we aren't yet to product data.
            while (len(nested_data) == 1):
                for new_key in nested_data:
                    nested_data = nested_data[new_key]
            normalized_dataframes.append(
                {'store': store_name, 'frame': json_normalize(nested_data)})
        return normalized_dataframes
    except Exception as e:
        print(e)
        return []


"""
This function requires a dictionary input variable returned from normalize_data().
keyword input is for matching. this will either be 'description' or 'images'.

This function processes a pandas dataframe and creates a dictionary. The dictionary contain
the store's name as the index, and contains an array value sorted by the percentage in similarity
(high to low) between column attributes and product description.

Example response:
    {'vendor1' : [{'column_name' : '<info product description>'}, ... ]}

Returns an array of json objects containing a store, column, and match percent
key.
"""


def process_frames(frames, keyword):
    try:
        data_array = {}
        for frame in frames:
            # grab panda frame headers
            columns = frame['frame'].columns.values
            # split values that are json nested, remove special chars
            parsed_columns = list(map(
                lambda column_name: "".join(column_name.replace(".", " ")), columns))
            matched_columns = []
            for column in parsed_columns:
                matched_columns.append(match_description(column, keyword))
                data_array[frame['store']] = sorted(
                    matched_columns, key=lambda k: k['similarity'], reverse=True)
        return data_array
    except Exception as e:
        print(e)
        return []


"""
This function takes a string and calculates the similarity between it and
all strings in the matching_strings array. It then returns a dictionary with
the following keys:
    'column_name': the name of the column
    'similarity': the average similarity between the provided string and strings
                  in the matching_strings array.

An example may be as follows:
    column_name = info primary_brand name
    column_name = info product_description title

Ideally, the second column name string would return a better overall match than
the first one because it contains the actual product description.

The issue with the first string is that Spacy would calculate the similarity rating
with `info primary_brand name` as 99% because it contains the word `info`. To combat this,
an average is taken of all strings in the matching_strings array to produce a reliable result.
This would allow the `product_description` tag to increase the similarity results for more 
accuracy.

As we see more attributes from various venders, we can add to the matching_strings array to 
provide reliable results over time.
"""


def match_description(column_name, keyword):
    column_copy = column_name
    # array of strings to try and find similiarity with product description/images
    matching_strings = ["image", "product image", "image url"]
    if (keyword == "description"):
        matching_strings = ["description",
                            "product description", "product info"]
    elif keyword == "price":
        matching_strings = ["price", "product price",
                            "pricing", "display price"]
    elif keyword == "brand":
        matching_strings = ["brand", "product brand", "vendor", "name"]
    # matching_strings = ["price", "product price", "pricing", "display price"]
    # matching_strings = ["brand", "product brand", "vendor", "name"]
    # matching_strings = ["image", "product image", "image url"]

    percentage_array = []
    try:
        column_name = column_name.replace("_", " ")
        doc_column = nlp(column_name)
        for token in doc_column:
            percentages = (list(map(lambda e: token.similarity(nlp(e)),
                                [x for x in matching_strings])))
            percentage_array.append((sum(percentages) / len(percentages)))
        return {
            "column_name": column_copy,
            "similarity": (sum(percentage_array) / len(percentage_array))}
    except Exception as e:
        print(e)
        print("match_description error")
        return {}

    # sorted(percentage_array, key=lambda k: k['similarity'], reverse=True)[0]


"""
Returns a dictionary containing:
    '<store name>' : [{product description}, ...],
    where store name is Vendor1, Vendor2, etc...
    and product description is a pandas dataframe
"""


def grab_product_descriptions(frames, headers):
    descriptions = {}
    for frame in frames:
        store = frame['store']
        # the first index is the most similar to description
        column_to_print = headers[store][0]['column_name']
        # reserve json format we stripped in other function
        values = frame['frame'][column_to_print.replace(" ", ".")]
        descriptions[store] = values
    return descriptions


"""
returns a dictionary containing a key of <query>, and
an array value of all product descriptions or images for <query>
"""


def driver(keyword, query, category):
    # see get_data function description on choosing a valid query/category :)
    #query = 'beef'
    #category = 'meat'
    # query API
    data = get_data(query, category)
    # normalize our API data
    frames = normalize_data(data)
    # grab columns from databse matching `keyword`
    headers = process_frames(frames, keyword)
    # get product data
    descriptions = grab_product_descriptions(frames, headers)
    if len(descriptions) > 0:
        # format for printing
        formatted_descriptions = {query: []}
        for key in descriptions:
            print(key)
            formatted_descriptions[query].append(
                {key: descriptions[key].values})
        return formatted_descriptions
    return []


if __name__ == "__main__":
    # Jaron -> replace `description` with 'images'
    products = driver('description', 'beef', 'meat')
    # use the products dictionary as you see fit :)
    print(products)
