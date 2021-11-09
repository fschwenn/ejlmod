# -*- coding: utf-8 -*-
#harvest theses from Rice University
#JH+FS: 2021-11-04

from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import ejlmod2
import os
import datetime
import codecs
import getopt
import sys
import re

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
pages = 10

publisher = 'Rice U.'
jnlfilename = 'THESES-RICE-%s' % (stampoftoday)

# Initilize Webdriver
driver = webdriver.PhantomJS()

# In this variable all the data is saved
recs = []

# The variables for later saving the data
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

# The function that opens the subsite
def get_subsite(link, title):
	driver.get(link)
	soup = BeautifulSoup(driver.page_source, 'lxml')

	rec = {'keyw' : [], 'jnl' : 'BOOK', 'tc' : 'T'}
	
	# Check if it is a Master Thesis
        for degree_div in soup.find_all('div', attrs={'class': 'simple-item-view-degree'}):
		if re.search('Master', degree_div.text):
			print "["+ link  +"] is not a PhD thesis! --> Skipping this thesis"
			return None

	print "["+ link  +"] is a PhD thesis! --> Pursue harvesting"

	# Get the title
	title_section = soup.find_all('h2', attrs={'class': 'page-header'})
	if len(title_section) == 1:
		rec['tit'] = title_section[0].text

	# Get the author name
	author_div = soup.find_all('div', attrs={'class': 'simple-item-view-anthors'})
	authors = author_div[0].select('div')[0].text.split(';')
	rec['autaff'] = []
	for author in authors:
		name, surname = author.split(', ')
		rec['autaff'].append([author, publisher])

	# Ge the advisor name
	advisor_div = soup.find_all('div', attrs={'class': 'simple-item-view-advisor'})
	if len(advisor_div) == 1:
		rec['supervisor'] = []
		advisors = advisor_div[0].text.split('\n')[2].split(';')
		for advisor in advisors:
	                rec['supervisor'].append([advisor])

	# Get the public date
	date_section = soup.find_all('div', attrs={'class', 'simple-item-view-date'})
	if len(date_section) == 1:
		rec['date'] = date_section[0].text.replace('\n', '')[len('Date'):]

	# Get the abstract
	abstract_outer_section = soup.find_all('div', attrs={'class', 'simple-item-view-description'})
	if len(abstract_outer_section) == 1:
		abstract_section = abstract_outer_section[0].find_all('div')
		if len(abstract_section) == 1:
			rec['abs'] = abstract_section[0].text

	# Get Keywords
	#keywords_outer_section = soup.find_all('div', attrs={'class': 'simple-item-view-keyword'})
	#if len(keywords_outer_section) == 1:
	#	keywords_section = keywords_outer_section[0].find_all('div')
	#	if len(keywords_section) == 1:
	#		keywords = keywords_section[0].text
	#		rec['keyw'] = keywords[0:len(keywords)-len(' Less...')-2].replace('\n', '').split('; ')
        for meta in soup.find_all('meta', attrs={'name' : 'DC.subject'}):
                if re.search(', .*, ', meta['content']):
                        rec['keyw'] += re.split(', ', meta['content'])
                else:
                        rec['keyw'].append(meta['content'])
	# Get the handle
	handle_outer_section = soup.find_all('div', attrs={'class': 'simple-item-view-citation'})
	if len(handle_outer_section) == 1:
		handle_section = handle_outer_section[0].find_all('dim')
		if len(handle_section) == 1:
			citation_parts = handle_section[0].text
			handle_link_start = citation_parts.find('https://hdl.handle.net')
			handle_link_splitted = citation_parts[handle_link_start:len(citation_parts)-1].split('/')
			rec['hdl'] = handle_link_splitted[-2] + "/" + handle_link_splitted[-1]
	
	# Get the pdf Link
	#pdf_section = soup.find_all('img', attrs={'alt': 'Thumbnail'})
	#if len(pdf_section) == 1:
	#	pdf_link_list = "https://scholarship.rice.edu" + pdf_section[0].get('src')
	#	if len(pdf_link_list) == 1:
	#		rec['hidden'] = pdf_link_list[0]
        for meta in soup.find_all('meta', attrs={'name' : 'citation_pdf_url'}):
                rec['hidden'] = meta['content']
	# Get the link
	rec['link'] = link
	recs.append(rec)
        return



for page in range(pages):
        # Get Index Page
        url = "https://scholarship.rice.edu/handle/1911/8299/recent-submissions?offset=" + str(20*page)
        print '---{ %i/%i }---{ %s }---' % (page+1, pages, url)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        # Get all the articles
        articles = soup.find_all('div', attrs={'class': 'artifact-description'})
	for article in articles:
		link = article.select('a')[0].get('href')
		title = article.select('a')[0].text	
		get_subsite('https://scholarship.rice.edu' + link, title)
		sleep(10)
	sleep(10)

 
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'),'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
