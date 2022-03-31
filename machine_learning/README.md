# Machine Learning Repository

This folder contains the machine learning code to help match products together. This code requires
the spacy library to function.

Note that similar files may exist in the `lambda/` directory. Please ignore and use these files instead.

## Categorize.py

This file contains the first revision of natural language processing to determine if a product description
can be parsed for information regarding the nature of the product. This is done using various parts of speech.

## Categorize_v2.py

This file contains a mosh of different functionality. This should be refactored out for the final product.

This python script can be used to source products from DynamoDB and determine a proper `home` for each
product. This is done by using Spacy's Okapi similarity for string vectors. If a product is deemed to be 
similar enough to a subcategory in RDS, the product is matched to that category. If no category is similar
enough for a product, the program attempts to auto generate a category.

This category is then placed into RDS, and the process repeats.

TODO:
This program can be greatly improved if auto-generated categories are then compared to existing categories. If an RDS category exists that extremely similar to a ML-generated category, these two can be merged together to prevent categorical overlap.


## Word_dependency.py

This was the initial test script used to show that products could be matched together using machine learning. Spacy is used to determine similarity between two product descriptions. A match is deemed if the similarity score is high enough. 

This is a rudimentary program, meaning it could be improved using vectorization of product attributes for similarity scores.

# get_descriptions.py

A script used to retrieve products from Dynamo. Spacy is used to determine which attribute best matches product description, brand, image, etc. Once this attribute is found, the product attribute in Dynamo is returned. 

For example, this code could be used to get the product descriptions of all product entries in DynamoDB, or brands.