import spacy
import descriptions
from spacy.matcher import PhraseMatcher


# necessary pipeline
nlp = spacy.load("en_core_web_lg")
matcher = PhraseMatcher(nlp.vocab)

query = 'beef'  # 'vegetables'
db_category = 'meat'  # 'vegetables'


# load products from db
products = descriptions.driver('description', query, db_category)
# terms -> home of potential categories
terms = []
# categories -> dictionary containing our products mapped to a category
categories = {}


def create_docs(products, query):
    doc_array = []
    for product_array in products[query]:
        for product in product_array:
            doc_array.append(nlp(product.lower()))
    return doc_array


# generate documents
doc_array = create_docs(products, query)

# generate categories
for doc in doc_array:
    new_category = ""
    add = True
    for token in doc:
        if token.similarity(nlp(query)) >= 0.60 and (token.text != query and token.text != db_category):
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
for doc in doc_array:
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        if span.text not in categories:
            categories[span.text] = []
        categories[span.text].append(doc.text)


for key in categories:
    print("\nPrinting products matching {}".format(key))
    for product in categories[key]:
        print("   {}".format(product))
