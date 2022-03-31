import pandas as pd
import numpy as np
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import ngrams
from collections import Counter
import requests
import json
import sys
import spacy
from normalize_test import driver


def get_categories(descriptions=None, n_words=1 ,return_type="list", n_results=3):
    """
        Input - descriptions: a dictionary of which the key
            is the query and value is an array of product descriptions

              - n_words [1, 2, 3]: representing single words, word pairs, or trigrams

              - return_type [df, list]: output in the form of a dataframe or list

              - n_results: number of counts to return

        Use Case - Performs a bag of words analysis of the list of descriptions
            for a given query. Bag of words is a representation of of text as the
            frequency for which each word appears.

        Output - The n_results most frequent words, word pairs, or trigrams as either a
        dataframe or array. 
    
    """
    descriptions = descriptions[list(descriptions.keys())[0]]
    descriptions = [item for sublist in descriptions for item in sublist]
    
    sentence = " ".join(descriptions)
    # creates tokens, creates lower class, removes numbers and lemmatizes the words
    new_tokens = word_tokenize(sentence)
    new_tokens = [t.lower() for t in new_tokens]
    new_tokens = [t for t in new_tokens if t not in stopwords.words('english')]
    new_tokens = [t for t in new_tokens if t.isalpha()]
    lemmatizer = WordNetLemmatizer()
    new_tokens = [lemmatizer.lemmatize(t) for t in new_tokens]
    #counts the words, pairs and trigrams
    counted = Counter(new_tokens)
    counted_2 = Counter(ngrams(new_tokens, 2))
    counted_3 = Counter(ngrams(new_tokens, 3))

    #creates 3 data frames and returns thems
    word_freq = pd.DataFrame(counted.items(), columns=[
                             'word', 'frequency']).sort_values(by='frequency', ascending=False)
    word_pairs = pd.DataFrame(counted_2.items(), columns=[
                              'pairs', 'frequency']).sort_values(by='frequency', ascending=False)
    trigrams = pd.DataFrame(counted_3.items(), columns=[
                            'trigrams', 'frequency']).sort_values(by='frequency', ascending=False)

    if return_type == "df":
        if n_words == 1:
            return word_freq.iloc[:n_results]
        if n_words == 2:
            return word_pairs.iloc[:n_results]
        if n_words == 3:
            return trigrams.iloc[:n_results]
    else:
        if n_words == 1:
            return word_freq.values.tolist()[:n_results]
        if n_words == 2:
            return word_pairs.values.tolist()[:n_results]
        if n_words == 3:
            return trigrams.values.tolist()[:n_results]


if __name__ == '__main__':
    # product description dictionary using Joey's module
    products = driver("description")

    # bag of words results as either word, word pair, or trigram counts
    results = get_categories(products, 1, "df")
    results2 = get_categories(products, 3, "list", 5)
    
    print("\n\n------top 3 word frequencies as DF------\n")
    print(results)

    print("\n\n------ top 5 trigrams as list------\n")
    print(results2)




# get_categories()
