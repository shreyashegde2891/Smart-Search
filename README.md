# Smart-Search
Similar Issue finder Web-App from Issue and Project Tracking Software's

A web based tool to find similar issues from the corpus of existing issues. 
This model is built and tested on Jira, but can be used across any Issue and Project Tracking Software. 

This is a web tool built using Python flask, using ML concepts like tf-idf, Doc2Vec, TaggedDocument, Stemmers and Lemmatizers, pickle.

Similar issues are found out by scoring the terms occurring in the corpus, using tfidf vectorizers. Results are populated based on the cosine similarity between the input Jira defect, and the existing corpus.
The tool provides flexibility for the user to build his/her own model using the web page.

Usage: 
Python forms.py
