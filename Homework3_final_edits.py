
"""
Created on Thu Jul 20 12:53:11 2017

@author: mead
Adrian Mead, Natesh Prakash
atm4rf, np2hf
July 21, 2017
CS 5010
Homework 3 - Python Web Scraper

"""

# Used for the html output
from bs4 import BeautifulSoup
# Used to curl the webpage
from urllib.request import *
import numpy as np
# For reading in and out of dataframes
import pandas as pd
# For creating graphs
import networkx as nx
# For generating graph visualization
import matplotlib.pyplot as plt

# Introduction!
print("Welcome to the Star Wars Web Crawler!\n" \
      "This tool is designed for a user to enter a wiki page they would like to\n" \
      "visit and a number representing a desired degree(s) of separation. At \n" \
      "this point the script will scrape the seed page provided and follow \n" \
      "every wiki article link on that page, repeating this process for the \n" \
      "desired degrees of separation, at which point the process terminates and \n" \
      "a number of statistics are returned")
# Prompt the user(s) for input
wiki = 'wookiepedia'
#wiki = input("Enter the domain portion of a desired wikia (eg: wookiepedia, banjokazooie): ")
# User has the ability to pick a seed article. One that will process quickly is Unidentified_Echani_Senator
orig_article = input("Enter a desired wiki article (must be exact! eg: Unidentified_Echani_Senator, Luke_Skywalker, Yoda, Revan): ")
#orig_article = 'Unidentified_Echani_Senator'
#orig_article = 'Revan'
orig_article = ['/wiki/' + orig_article]
# dos = degree of separation
dos = 2
print("Using " + str(dos) + " degrees of separation")

count = 0
#def set_globalcount_to_one():
#    global global_count    # Needed to modify global copy of globvar
#    global_count = 1

# We need a function to perform the cleaning and scraping of the HTML from each webpage we visit
def pull_wiki_links(page):
    # Open a connection and grab the contents of some webpage
    global count
    print(count)
    html_page = urlopen('http://' + wiki + '.wikia.com/' + page)
    # Makes a BeautifulSoup object for the html contents, which are easier to manipulate
    soup = BeautifulSoup(html_page, 'lxml')
    all_links = []
    # Part of data cleaning -- only grab the hyperlinks
    for link in soup.findAll('a'):
        all_links.append(str(link.get('href')))
    # Further cleaning: only grab links that start '/wiki'
    wiki_links = list(filter(lambda x: x.find('/wiki', 0, min(5,len(x)-1))!=-1, all_links))
    # Final portion of cleaning; only grab the links without colons (:) or question marks (?), and a few other things
    # Each name is fairly self-explanatory. Just removing some non-interesting entries
    wiki_links_no_colon = list(filter(lambda x: x.find(':')==-1, wiki_links))
    wiki_links_no_question_mark = list(filter(lambda x: x.find('?')==-1, wiki_links_no_colon))
    wiki_links_no_art_noms = list(filter(lambda x: x.find('Article_nominations')==-1, wiki_links_no_question_mark))
    wiki_links_no_main_page = list(filter(lambda x: x.find('Main_Page')==-1, wiki_links_no_art_noms))
    wiki_links_no_sitemap = list(filter(lambda x: x.find('Sitemap')==-1, wiki_links_no_main_page))
    wiki_links_no_other_languages = list(filter(lambda x: x.find('other_languages')==-1, wiki_links_no_sitemap))
   # Also want to pull out unique variables
    wiki_links_unique = np.unique(wiki_links_no_other_languages)
    wiki_links_list = wiki_links_unique.tolist()
    count += 1
    return(wiki_links_list)

# Initialize empty graph
G=nx.Graph()

# This article var will store all of the paths of articles that we've visited
article = orig_article
# Add starting node
G.add_nodes_from(orig_article)
# Copying list to dataframe
df = pd.DataFrame([('0',article[0])], columns=['degree', 'Links'])


# This for-loops will exist to go through each degree of separation
for num in range(dos):
    # This for-loop is here to go through every link in the article
    old_article = article
    dummy = list(map(pull_wiki_links, article))
    # reduce from a list of lists to a list of strings
    article = sum(dummy,[])
    # Appending to dataframe -- better for data manipulation later
    to_append = list((num+1, link) for link in article)
    df = df.append(pd.DataFrame(to_append, columns=['degree', 'Links']),ignore_index=True)
    
    #Appending to graph nodes
    if(num == 0):
        G.add_nodes_from(article)
        #Appending to graph edges
        for node in old_article:
            for neighbor in article:
                G.add_edge(node, neighbor)
        # Help the user understand how long it will likely take to run the code
        print("ETA: " + str(len(article)) + "loops.")

# Keeping track of how many of the second-degree pages link back to the seed page
count_loops = len(list(filter(lambda x: x == orig_article[0], article)))

# Printing df to csv
df.to_csv('articlelist.csv', index = None)
# Reading in csv
dfread = pd.read_csv('articlelist.csv')
# Printing csv to console

# Counting how many of each Link we have using the Panda
dfLink_grpd = dfread.groupby(['Links']).size().to_frame('size')
dfLink_grpd.sort_values('size', ascending = False, inplace = True)
# Want to know what the count is corresponding to some of the most linked-to pages (5th highest entry is the bar)
# Note that the extra logic is included because some hyperlinks are automatically included on every page based on being a recent update
most_popular = dfLink_grpd[(dfLink_grpd['size'] >= dfLink_grpd.iloc[15,0]) & 
                           (dfLink_grpd['size'] != dfLink_grpd.iloc[1,0])]

# Output
# Want to print out how many of the linked-to articles immediately link back to the seed article
# Also printing out what we think the most similar pages are
print("In summary, we found " + str(len(dfread.groupby('degree').get_group(1))) + " links from the seed page.")
print("There were " + str(len(dfread.groupby('degree').get_group(2))) + " different paths our webcrawler \n" \
      "found across all " + str(dos) + " degrees of separation.")
print("We found that exactly " + str(count_loops) + " of these first-degree links return(s) to \n" \
      "the seed article after " + str(dos) + " degree(s) of separation.")
print("So this seed article is " + str(round(count_loops / len(dfread.groupby('degree').get_group(1)) * 100,2)) + "% well-connected \n" \
      "with " + str(dos) + " degree(s) of separation.")
print("In addition, we have estimated that the page(s) most closely related to the seed article, " + orig_article[0] + " , are: ")
print(most_popular)
print("We're also going to show a nodes-edges plot of the first degree of separation: ")

# Exporting graph visualization using inbuilt function
pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos=pos, nodelist = G.nodes())
nx.draw_networkx_edges(G, pos=pos, edgelist = G.edges())
nx.draw_networkx_labels(G, pos=pos)
# Saves output
plt.savefig("Graph.png", format="PNG")

