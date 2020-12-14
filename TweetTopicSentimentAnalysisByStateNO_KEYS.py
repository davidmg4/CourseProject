# TweetTopicSentimentAnalysisByState.py
import collections
import csv
import fileinput
import itertools
import os
import re
import sys
from tabulate import tabulate
import warnings
import networkx
import nltk
import pandas as pd
import tweepy
from nltk.corpus import stopwords
from requests_oauthlib import OAuth1Session
from textblob import TextBlob


def tweetPuller(filename):

    #tweetPuller.py
    # This portion of the code performs the scraping of Tweet data in a format that is easily written to a simple CSV file searching by
    # topic and state name. This requires a Twitter developer account and the Tweepy API.



    # Twitter API credentials 
    consumer_key = ''
    consumer_secret = ''
    access_token = '-'
    access_token_secret = ''

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)




    # Use CSV Writer
    # Open/Create a file to tweet data and write with topic and state information, stripping URLs in the process 


    csvFile = open(filename + '.csv', 'a')
    csvWriter = csv.writer(csvFile)
    csvWriter.writerow(['date', 'text', 'state', 'topic'])

    for topic in topics:
        for state in geography:        
            combo = topic + " " + state + " -filter:retweets"
            for tweet in tweepy.Cursor(api.search,q=combo,
                                    lang="en",
                                    tweet_mode="extended").items():
                result = re.sub(r"http\S+", "", str(tweet.full_text.encode('utf-8')))
                csvWriter.writerow([tweet.created_at, result, state, topic])

    csvFile.close()

# Remove emojis and other non-text data for improved readability 
# Source: Abdul-Razak Adam @ StackOverflow 

def demoji(text):
	emoji_pattern = re.compile("["
		u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U00010000-\U0010ffff"
	                           "]+", flags=re.UNICODE)
	return (emoji_pattern.sub(r' ', text))

# Remove numbers 

def alphaOnly(tExt):
    regex = re.compile('[^a-zA-Z]')
    return regex.sub(' ', tExt)

# Returns sentiment polarity score only

def sentimentScore(x):
    return TextBlob(x).sentiment.polarity


# Adds ID tag for improved formatting in dataViewer.html
# Source: 's02', 'eyquem' @ StackOverflow 
def  modify_file(file_name,pattern,value=""):  
    fh=fileinput.input(file_name,inplace=True)  
    for line in fh:  
        replacement=value  
        line=re.sub(pattern,replacement,line)  
        sys.stdout.write(line)  
    fh.close()  


def sentimentAnalysis(filename):
    #sentimentAnalysis.py
    # This portion of the code performs the sentiment analysis by first importing the tweet data as a Pandas Dataframe, scrubbing irrelevant 
    # non-textual data and adding TextBlob sentiment scores to each tweet.
    # 
    # It is then aggregated as simple arithmetic mean for each state and topic combination to feed into the dataViewer webpage HTML file. 


    # Read each aggregated Tweet Database by topic from CSV file 
    
    dataFileName = filename + ".csv"
    dataFile = pd.read_csv(dataFileName)
    df = pd.DataFrame(dataFile)

    # Convert tweets to lowercase string and eliminate special characters/URLs if not already. 
    # Leading symbols inherent in Tweepy scraping also removed. 

    df['text'] = df['text'].astype(str)
    df['text'] = df['text'].str.slice(start=2)

    # Apply datacleanup functions (including newline characters)
    df['text'] = df['text'].apply(demoji)
    df['text'] = df['text'].str.replace('\n\n', '')
    df['text'] = df['text'].str.replace('\n', '')
    df['text'] = df['text'].apply(alphaOnly)
    df['text'] = df['text'].str.lower()




    # Remove stop-words

    stop = stopwords.words('english')
    df['text'] = df['text'].apply(lambda x: " ".join(x for x in x.split() if x not in stop))

    #apply sentiment scores into new column

    df['sentiment_score'] = df['text'].apply(sentimentScore)



    # write aggregated sentiment data to CSV by state for each topic 
    summaryDict = {}
    for state in geography:
        summaryDict[state] = {}
        summaryDict[state]['overall'] = 0
        for topic in topics:
            summaryDict[state][topic] = {}
            summaryDict[state][topic] = round(df.loc[(df['state']==state) & (df['topic']==topic) & (df['sentiment_score']!=0), 'sentiment_score'].mean()*100, 1)
            summaryDict[state]['overall'] += round(df.loc[(df['state']==state) & (df['topic']==topic) & (df['sentiment_score']!=0), 'sentiment_score'].mean()*100 / len(topics), 1)
    
    
    csvFile = open(filename + 'Summary.csv', 'a')
    csvWriter = csv.writer(csvFile)
    csvWriter.writerow(['State'] + [[topic] for topic in topics] + ['[\'Overall\']'])
    

    table_data = [[]]
    table_data_header = ['State'] + [topic for topic in topics] + ['Overall']
    table_data[0] = (table_data_header)



    for state in geography:
        csvWriter.writerow([state] + [summaryDict[state][topic] for topic in topics] + [summaryDict[state]['overall']])
        table_data.append([state] +  [summaryDict[state][topic] for topic in topics] + [str(round(summaryDict[state]['overall'],1))])
    csvFile.close()

    print(table_data)


    header = open("header.html", "r").read()

    footer = open("footer.html","r").read()

    webOutputData =tabulate(table_data, tablefmt='html')

    viewFile = filename + "Viewer.html"
    webOutput = open(viewFile,"w")
    webOutput.write(header)
    webOutput.write(webOutputData)
    webOutput.write(footer)
    webOutput.close()

    modify_file(viewFile,'<table>','<table id=\"table_data\" class=\"display\">')
    modify_file(viewFile,'<tbody>','<thead>')
    modify_file(viewFile,r'td>Overall</td></tr>', r'td>Overall</td></tr></thead>')


# Main Driver Function

if __name__ == '__main__':

    # Data Variables

    geography = [ "Alabama", "Alaska" , "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
                "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
                "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey" , "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", 
                "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
                "West Virginia", "Wisconsin", "Wyoming"] 
    topics = [
        "Government",
        "Weather",
        "Economy",
        "Nature",
        "Lifestyle"
    ]

    # Generate filename
    filename = '12132020'

    # Run Tweet Puller
    print( '-'*150 + "\n\nBeginning Twitter Pull...\n\n" + '-'*150)
    tweetPuller(filename)
    
    # Run Sentiment Analysis 
    print('-'*150 + "\n\nBeginning Analysis...\n\n" + '-'*150)
    sentimentAnalysis(filename)

    #Output file given for review
    print('-'*50 + " Complete! Please check the output files: "+ filename +"Summary.csv and " +filename + "Viewer.html" + '-'*50)

