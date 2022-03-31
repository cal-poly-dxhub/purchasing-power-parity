import spacy
from spacy.matcher import Matcher

# import md package -- its larger than small for similarity comparing
nlp = spacy.load("en_core_web_lg")

# strings we will be using for our examples
product_string_example = "All Natural 93/7 Ground Beef - 1lb - Good &#38; Gather&#8482;"
product_string_example5 = "All Natural 93/7 Ground Beef - 2lbs - Good &#38; Gather&#8482;"
product_string_example6 = "All Natural* 80% Lean/20% Fat Ground Beef Chuck Tray, 2.25 lb"
product_string_example2 = "USDA Choice Angus Beef Steak Strips - 14oz - Good &#38; Gather&#8482;"
product_string_example3 = "Earth&#39;s Best Baked Mini Beef Meatballs - Frozen - 26oz"
product_string_example4 = "USDA Choice Angus Beef Skirt Steak - 0.75-1.6 lbs - price per lb - Good &#38; Gather&#8482;"

# spacy uses documents to tokenize
doc2 = nlp(product_string_example)
doc3 = nlp(product_string_example2)
doc4 = nlp(product_string_example3)
doc5 = nlp(product_string_example4)
doc6 = nlp(product_string_example5)
doc7 = nlp(product_string_example6)


def print_tokens_for_doc(doc):
    for token in doc:
        print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
              token.shape_, token.is_alpha, token.is_stop)


def example1(match_string):
    # Say we are given a query of `ground beef 1lb`.
    # find the average similarity of each token in a sentence.
    doc1 = nlp(match_string)
    print("{} <- similarity -> {}: {}".format(match_string,
          product_string_example, doc1.similarity(doc2)))
    print("{} <- similarity -> {}: {}".format(match_string,
          product_string_example2, doc1.similarity(doc3)))
    print("{} <- similarity -> {}: {}".format(match_string,
          product_string_example3, doc1.similarity(doc4)))
    print("{} <- similarity -> {}: {}".format(match_string,
          product_string_example4, doc1.similarity(doc5)))
    print("{} <- similarity -> {}: {}".format(match_string,
          product_string_example5, doc1.similarity(doc6)))


def example2(match_string, provided_doc):
    # tokenize the words and match independently
    doc1 = nlp(match_string)
    for token in provided_doc:
        print("{} <- similarity -> {}: {}".format(match_string,
              token.text, token.similarity(doc1)))


def example3(match_string, provided_doc):
    # pull out the high matching items
    new_string = ""
    # arbitary matching percentage
    match_percent = 0.8
    doc1 = nlp(match_string)
    # doc 1/2 example
    for token in doc1:
        for token2 in provided_doc:
            if token.similarity(token2) >= match_percent:
                new_string += " {} ".format(token2)
    # create new doc for highly matched string
    doc_local = nlp(new_string)
    # print("new string: {}".format(new_string))
    print("{} <- similarity -> {}: {}".format(match_string,
                                              provided_doc.text, doc1.similarity(doc_local)))


query = "Organic"
# query = "gallon milk"
query = "ground beef 2lbs USDA Prime"
#query = "milk"

"""
print("--- Example 1 ---")
example1(query)
print("\n")
"""

"""

"""
print("--- Example 3 ---")
example3(query, doc2)
example3(query, doc3)
example3(query, doc4)
example3(query, doc5)
example3(query, doc6)
example3(query, doc7)

"""
example3("1lb", doc2)
example2("1lb ", doc6)
"""
# example api call? category={meat}&product={ground beef}&weight={1lb}
