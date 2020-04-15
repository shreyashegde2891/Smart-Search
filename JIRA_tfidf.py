import pickle
from jira import JIRA
import re
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
import nltk
from hyperdash import monitor_cell
import warnings
import os
import pandas as pd


from nltk.corpus import stopwords
from collections import Counter
import pprint
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

stops = set(stopwords.words("english"))
stemmer = SnowballStemmer('english')

ignored_words_string = "load, paper, tray, auto, issue, Ressd, Simulator, labels, Setting, Settings, log, follow"
ignored_words_list = [x.strip() for x in ignored_words_string.split(',')]

def find_top_n_similar_documents(n,tfidf_test,tfidf_trainingset,cleaned_training_corpus):
    cosine_similarities = linear_kernel(tfidf_test, tfidf_trainingset).flatten()
    related_docs_indices = cosine_similarities.argsort()[:-n:-1]
    related_jira_ids = []
    for ticket in cleaned_training_corpus:
        if(ticket['index'] in related_docs_indices):
            related_jira_ids.append(ticket['jiraid'])
    return related_docs_indices,related_jira_ids

def remove_code_from_comments(comment_body):
    return re.sub(r'{code:.*}[\s\S]*?{code}','',str(comment_body))

def get_jira_issue_object(authed_jira, jira_name):
    return authed_jira.issue(jira_name)

def get_title(jira_issue_object):
    return jira_issue_object.fields.summary

def get_summary(jira_issue_object):
    return jira_issue_object.fields.description

def get_jira_id(jira_issue_object):
    return jira_issue_object.key

def get_status(jira_issue_object):
    return jira_issue_object.fields.status

def get_list_of_comments(jira_issue_object):
    return jira_issue_object.fields.comment.comments

def get_reqd_comments_data(list_of_comments):
    ticket_dict = {}
    ticket_dict['comments_data'] = [] 
    ticket_dict['comments_corpus'] = []
    for comment in list_of_comments:
        comment_data = {}
        comment_data['emailAddress'] = comment.author.emailAddress
        comment_data['body'] = comment.body
        comment_data['created'] = comment.created
        comment_data['updated'] = comment.updated
        ticket_dict['comments_data'].append(comment_data)
        comment_corpus_data = remove_code_from_comments(comment_data['body'])
        #print(comment_corpus_data)
        ticket_dict['comments_corpus'].append(comment_corpus_data)
    return ticket_dict['comments_data'],ticket_dict['comments_corpus']

def filter_crawler(authed_jira, jira_filter):
    print("Crawling the filter...")
    filter_tickets = authed_jira.search_issues(jira_filter, maxResults=maxResults)
    tickets_corpus = []
    for ticket in filter_tickets:
        ticket_dict = {}
        jira_id = get_jira_id(ticket)
        ticket_full_data = authed_jira.issue(jira_id)  
        ticket_dict['jiraid'] = jira_id
        ticket_dict['title'] = get_title(ticket_full_data) 
        ticket_dict['summary'] = get_summary(ticket_full_data)
        list_of_comments = get_list_of_comments(ticket_full_data)
        ticket_dict['comments_data'],ticket_dict['comments_corpus'] = get_reqd_comments_data(list_of_comments)
        tickets_corpus.append(ticket_dict)
    print("Crawling done.")
    return tickets_corpus

def clean_document(document_of_words):
    document_of_words = document_of_words.lower()
    document_of_words = re.sub('\\b\d+(?:\.\d+)?\s*', '', document_of_words)      # remove a number or decimal num followed by a space
    document_of_words = re.sub('[rc]*id\s*:*', '', document_of_words)              # remove rid, id fields
    #document_of_words = re.sub('([^\x00-\x7F])+', '', document_of_words)              # remove accent words
    document_of_words = re.split('\W+', document_of_words)                        # remove all non-words (make a list)
    document_of_words = [w for w in document_of_words if not w in stops]           # remove stop words
    #document_of_words = [w for w in document_of_words if not w in ignored_words_list]    # remove ignored words
    document_of_words = [w for w in document_of_words if not w in ignored_words_list]
    document_of_words = [w.replace("energy saver","powercut") for w in document_of_words]
    document_of_words = [w.replace("STR","powercut") for w in document_of_words]
    document_of_words = [w.replace("low power","powercut") for w in document_of_words]
    stemmed_words = [stemmer.stem(word) for word in document_of_words]       # stem each word
    return ' '.join(stemmed_words)
    

def extract_clean_documents_from_corpus(corpus):
    print("Extracting and Cleaning documents...")
    final_corpus = []
    list_of_docs = []
    i = 0
    for ticket_dict in corpus:
        #print("Processing ",ticket_dict['title'])
        doc_cleaned_text = ''
        #document_of_words = (str(ticket_dict['title'])+" "+str(ticket_dict['summary']))
        document_of_words = (str(ticket_dict['title']))
        doc_cleaned_text = clean_document(document_of_words)
        list_of_docs.append(doc_cleaned_text)
        final_corpus.append({'jiraid':ticket_dict['jiraid'], 'words':doc_cleaned_text, 'index':i})
        i+=1
    return list_of_docs,final_corpus

#def tf_idf(username,password,model,ticket):
def tf_idf(authed_jira,model,ticket):
	
	tfidf_model = TfidfVectorizer()
	path="C:\\JIRA-Similar-Issue-Finder-App-master\\Models\\"
	fnb_tickets_corpus=pickle.load(open(path + model,"rb"))
	list_of_docs,training_ticket_corpus = extract_clean_documents_from_corpus(fnb_tickets_corpus)
	tfidf_trainingset = tfidf_model.fit_transform(list_of_docs)
	test_issue = authed_jira.issue(ticket)
	title = get_title(test_issue)
	summary = get_summary(test_issue)
	document_test = str(title)+" "+str(summary)
	cleaned_document = clean_document(document_test)
	cleaned_document = [cleaned_document]
	tfidf_test = tfidf_model.transform(cleaned_document)
	related_indices, related_jiras = find_top_n_similar_documents(10,tfidf_test[0:1],tfidf_trainingset,training_ticket_corpus)
	#print("\n",ticket," >>>> ",related_jiras,"\n")
	return related_jiras
