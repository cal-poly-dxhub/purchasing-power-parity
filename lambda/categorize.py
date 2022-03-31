import descriptions
import spacy


nlp = spacy.load("en_core_web_lg")
products = descriptions.driver(['description'])
categories = {}


def create_docs(products, column):
    doc_array = []
    for product in products[column]:
        # for product in product_array:
        doc_array.append(nlp(product.lower()))
    return doc_array


def parse_parts_of_speech(doc_array, query):
    product_dependency_array = []
    for doc in doc_array:
        stripped_doc = ""
        for token in doc:
            if len(token.text) > 2 and token.is_alpha:
                stripped_doc += "{} ".format(token.text)
            # print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
                # token.shape_, token.is_alpha, token.is_stop)
        new_doc = nlp(stripped_doc)

        print("\n")
        # strings representing various token dependencies
        root = compound = pobj = nmod = npadvmod = other = ""
        # our nlp data structure for comparison
        doc_category = nlp(query)
        # begin processing word dependencies
        for token in new_doc:
            # grab the nouns/proper nouns
            if (token.pos_ == "NOUN" or token.pos_ == "PROPN") and token.is_alpha:
                # the below dependencies are common parts of speech to help grab categories
                # as of now, a list of english dependencies are here:
                # https://github.com/clir/clearnlp-guidelines/blob/master/md/specifications/dependency_labels.md
                if token.dep_ == "compound":
                    compound += "{} ".format(token.text)
                elif token.dep_ == "pobj":
                    pobj += "{} ".format(token.text)
                elif token.dep_ == "ROOT":
                    root += "{} ".format(token.text)
                elif token.dep_ == "npadvmod":
                    npadvmod += "{} ".format(token.text)
                elif token.dep_ == "nmod":
                    nmod += "{} ".format(token.text)
                else:
                    if token.similarity(doc_category) > 0.70:
                        compound += "{} ".format(token.text)
                    else:
                        other += "{} ".format(token.text)

        dep_similarity = [
            {
                'phrase': compound, 'similarity': nlp(compound).similarity(doc_category)
            },
            {
                'phrase': pobj, 'similarity': nlp(pobj).similarity(doc_category)
            },
            {
                'phrase': root, 'similarity': nlp(root).similarity(doc_category)
            },
            {
                'phrase': npadvmod, 'similarity': nlp(npadvmod).similarity(doc_category)
            },
            {
                'phrase': nmod, 'similarity': nlp(nmod).similarity(doc_category)
            },
            {
                'phrase': other, 'similarity': nlp(other).similarity(doc_category)
            }
        ]

        product_dependency_array.append({
            'product': doc.text,
            'phrases': sorted(dep_similarity,
                              key=lambda k: k['similarity'], reverse=True)
        })
    return product_dependency_array


def predict_category(product):
    # print(product)
    global categories
    keys = list(categories.keys())
    phrase_list = product['phrases']
    potential_category = ""
    for phrase in phrase_list:
        if len(categories) > 0:
            for key in keys.copy():
                if key in phrase['phrase']:
                    print(
                        'category matched -> {} with {}'.format(key, product['product']))
                    # categories[phrase['phrase']].append(product['product'])
                    break
                else:
                    if phrase['similarity'] > 0.70 and phrase['phrase'] != 'beef ':
                        categories[phrase['phrase']] = []
                        # categories[phrase['phrase']].append(product['product'])
                        break
        else:
            if phrase['similarity'] > 0.70 and phrase['phrase'] != 'beef ':
                categories[phrase['phrase']] = []
                # categories[phrase['phrase']].append(product['product'])
                print('Creating category -> {}'.format(phrase['phrase']))
                break


# changed now that products is DF with description col
doc_array = create_docs(products, "description")
dep_array = parse_parts_of_speech(doc_array, 'beef')
print(dep_array)
for product in dep_array:
    # predict_category(product)
    print("Product: {}".format(product['product']))
    for phrase in product['phrases']:
        print("Potentially Useful phrase: {}".format(phrase))
    predict_category(product)

    print("\n")


for item in categories:
    print(item)
