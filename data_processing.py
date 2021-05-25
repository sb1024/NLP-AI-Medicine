#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 22 12:21:02 2021

@author: Sope
"""
import csv
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from collections import Counter
import statistics
import pickle


def get_terms():
    ai_terms = [
        "Artificial Intelligence",
        "Machine Learning",
        "Deep Learning",
        "Natural Language Processing",
        "Random Forest",
        "Logistic Regression",
        "LSTM",
        "RNN",
        "CNN",
        "Federated Learning",
        "Decision Tree",
        "Support Vector Machine",
        "Bayesian Learning",
        "Gradient Boosting",
        "Computational Intelligence",
        "Naive Bayes",
        "Computer Vision",]
    
    purpose_terms = [
        "Diagnosis",
        "Early Detection",
        "Decision Support",
        "Screening"
        ]
    
    search_string = ""
    term_lists = [ai_terms, purpose_terms]
    for term_list in term_lists:
        for term in term_list:
            if term == term_list[0]:
                search_string += '("' + term + '" or '
            elif term == term_list[-1]:
                search_string += ('"' + term + '") and ')
            else:
                search_string += ('"' + term + '" or ')
    print(search_string)

def mk_int(s):
    s = s.strip()
    return int(s) if s else 0

def text_process(text):
    '''
    Takes in a string of text, then performs the following:
    1. Remove all punctuation
    2. Remove all stopwords
    3. Return the cleaned text as a list of words
    4. Remove words
    '''
    stemmer = WordNetLemmatizer()
    nopunc = [char for char in text if char not in string.punctuation]
    nopunc = ''.join([i for i in nopunc if not i.isdigit()])
    nopunc =  [word.lower() for word in nopunc.split()]
    nopunc = [word for word in nopunc if word not in stopwords.words('english')]
    return [stemmer.lemmatize(word) for word in nopunc]

def find_K(K, X_transformed, tfidfconvert, sosd):
    K = range(1,K+1)
    Sum_of_squared_distances = sosd
    for k in K:
        print(k)
        km = KMeans(n_clusters=k)
        km = km.fit(X_transformed)
        Sum_of_squared_distances.append(km.inertia_)
        
        order_centroids = km.cluster_centers_.argsort()[:, ::-1]
        terms = tfidfconvert.get_feature_names()
        centroid_file = open("/Users/Sope/Documents/GitHub/NLP-AI-Diagnosis/centroids/{}".format(str(k)), "w")
        for i in range(k):
            centroid_file.write("Cluster %d:" % i)
            for ind in order_centroids[i, :10]:
                centroid_file.write(" %s" % terms[ind])
            centroid_file.write("\n")
        centroid_file.close()
        
    plt.plot(K, Sum_of_squared_distances, 'bx-')
    plt.xlabel('k')
    plt.ylabel('Sum_of_squared_distances')
    plt.title('Elbow Method For Optimal k')
    plt.show()
    
    return Sum_of_squared_distances

def process_data(data_file, funding_file):
    funding_data = {}
    with open(funding_file, newline='') as csvfile:
        raw_data = list(csv.reader(csvfile))
        for i in range(1,len(raw_data)):
            org = raw_data[i][0]
            funding = int(raw_data[i][5])
            funding_data[org] = funding
    
    data = []
    with open(data_file, newline='') as csvfile:
        raw_data = list(csv.reader(csvfile))
        ids = []
        print(len(raw_data))
        for i in range(1,len(raw_data)):
            if (raw_data[i][7] in ids) or (raw_data[i][11][0] == 'Z'):
                continue
            else:
                ids.append(raw_data[i][6])
            abstract = raw_data[i][1].replace('\n',' ')
            relevance = raw_data[i][4].replace('\n',' ')
            funding = funding_data.get(raw_data[i][31], 0)
            data.append({
                "title": raw_data[i][3],
                "id": raw_data[i][6],
                "terms": raw_data[i][2].split(";"),
                "abstract": abstract,
                "relevance": relevance,
                "administration": raw_data[i][5],
                "organization": raw_data[i][31],
                "year": raw_data[i][42],
                "cost": mk_int(raw_data[i][43]) + mk_int(raw_data[i][44]),
                })
    
    test_data = []
    for item in data:
        if item["cost"] == 0:
            data.remove(item)
        elif item["year"] == "2021":
            data.remove(item)
            test_data.append(item)

    # Get TFIDF data
    X_train = [key["abstract"] for key in data]
    test = [key["abstract"] for key in test_data]
    tfidfconvert = TfidfVectorizer(analyzer=text_process, max_df=0.5).fit(X_train)
    
    # Transform
    tfidfconvert = TfidfVectorizer(analyzer=text_process, max_df=0.5).fit(X_train)
    X_transformed = tfidfconvert.transform(X_train)
    test_transformed = tfidfconvert.transform(test)
    
    with open("data.pkl", 'wb') as handle:
        pickle.dump(data, handle)
        
    with open("transformed.pkl", 'wb') as handle:
        pickle.dump(X_transformed, handle)
        
    with open("transformed_test.pkl", 'wb') as handle:
        pickle.dump(test_transformed, handle)
    
    print(len(data))
    return data, X_transformed, test_data

def get_clusters(k, data_file, X_transformed_file):
    # Load data as dictionary
    data = pickle.load(open(data_file,"rb"))
    
    # Transformed data
    X_transformed = pickle.load(open(X_transformed_file,"rb"))
    
    # Perform k means
    km = KMeans(n_clusters=k)
    clusters = km.fit_predict(X_transformed)
    print(clusters)
    
    # Output data
    costs = []
    yoy = []
    size = []
    
    for i in range(0,k):
        print(i)
        
        # indices of cluster k
        cluster = [idx for idx, element in enumerate(clusters) if element == i]
        print(cluster)
        
        # get points
        cluster_data = [data[ind] for ind in cluster]
        
        # calculate average cost and std
        try:
            average_cost = sum([item["cost"] for item in cluster_data])/len(cluster_data)
            #std = statistics.pstdev([item["cost"] for item in cluster_data])
        except:
            average_cost = 0
            #std = 0
        costs.append(average_cost)
        
        cost_trend = []
        for year in years:
            year_data = [data[ind]["cost"] for ind in cluster if data[ind]["year"] == year]
            if len(year_data) == 0:
                cost_trend.append(0)
            else:
                year_cost = sum(year_data)/len(year_data)
                cost_trend.append(year_cost)
        
        yoy.append(cost_trend)
        
        size.append(len(cluster))
        
    return costs, yoy, size
        
        

file = '/Users/Sope/Documents/GitHub/NLP-AI-Diagnosis/raw data.csv'
funding_file = '/Users/Sope/Documents/GitHub/NLP-AI-Diagnosis/institution-funding.csv'
years = ["2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020"]
data, X_transformed, test_data = process_data(file, funding_file)
# X_train = [key["abstract"] for key in data]
# costs = [key["cost"] for key in data]
# terms = [key["terms"] for key in data]

# try:
#     tfidfconvert = pickle.load(open("data.pkl","rb"))
#     X_transformed = tfidfconvert.transform(X_train)
#     sosd = pickle.load(open("sum_K_distance.pkl","rb"))
#     Sum_of_squared_distances = find_K(100, X_transformed, sosd)
# except:
#     tfidfconvert = TfidfVectorizer(analyzer=text_process, max_df=0.5).fit(X_train)
#     X_transformed = tfidfconvert.transform(X_train)
#     Sum_of_squared_distances = find_K(100, X_transformed, tfidfconvert, [])
#     with open("sosd.pkl", 'wb') as handle:
#         pickle.dump(Sum_of_squared_distances, handle)

# costs, cost_trend, size = get_clusters(10, "data.pkl", "transformed.pkl")
# plt.xlabel("Year")
# plt.ylabel("Funding")
# plt.title("Funding by cluster")
# for i in range(len(cost_trend)):
#     plt.plot(years, cost_trend[i], label=str(i))
# plt.legend()
# plt.show()
# print("Number of features = {}".format(str(len(tfidfconvert.get_feature_names()))))

# k = 10
# km = KMeans(n_clusters=k)
# km = km.fit(X_transformed)

# averages = []
# terms_freq = []
# all_terms_list = []
# k_data = {}


        
        # list of terms in this cluster
        # for term_list in [terms[l] for l in cluster]:
         #   all_terms_list += term_list
    


# results = []
# for item in data:
#     input_data = tfidfconvert.transform([item["abstract"]])
#     results.append([item["id"], item["title"], km.predict(input_data)[0]])
    
# with open('clusters/clusters_{}.csv'.format(k), 'w', newline='') as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerows(results)
