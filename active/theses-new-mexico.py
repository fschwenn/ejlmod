# -*- coding: UTF-8 -*-
# Program to harvest New Mexico University
# JH 2021-12-20

from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import urllib2
from json import loads
import urlparse
import getopt
import sys
import os
import ejlmod2
import codecs
import datetime
import re
#import classifier
from base64 import b64encode

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'UNM, Albuquerque'
numoftheses = 25

jnlfilename = 'THESES-NEW-MEXICO-%s' % (stampoftoday)

recs = []


def http_request(url):
    hdr = {'User-Agent' : 'Magic Browser'}
    req = urllib2.Request(url, headers=hdr)
    soup = BeautifulSoup(urllib2.urlopen(req).read(), 'lxml')
    return soup

def get_sub_site(url, fc, aff):
    print "["+url+"] --> harvesting data"

    rec = {'link' : unicode(url), 'tc' : 'T', 'jnl' : 'BOOK', 'note': []}
    rec['doi'] = '20.2000/NewMexico/' + re.sub('\W', '', url[25:])
    if fc:
        rec['fc'] = fc

    soup = http_request(url)

    # Extract the title and pdf link
    title_section = soup.find_all('div', attrs={'id': 'title'})
    if len(title_section) == 1:
        title = title_section[0].find_all('a')

        if len(title) == 1:
            rec['hidden'] = title[0].get('href')
            rec['tit'] = unicode(title[0].text)

    # Extract author
    author_section = soup.find_all('p', attrs={'class': 'author'})
    if len(author_section) == 1:
        author_link = author_section[0].a
        author_query = urlparse.parse_qsl(urlparse.urlsplit(author_link.get('href')).query)
	if len(author_query) == 3:
	    first_name_raw, name_raw = author_query[0][1].split("\" ")
	    first_name = first_name_raw.split(':"')[1]
	    last_name = name_raw.split(':"')[1]

	    first_name = first_name[0:len(first_name)]
	    last_name = last_name[0:len(last_name)-1]
            rec['autaff'] = [[ unicode(last_name + ", " + first_name, 'utf-8'), aff ]]

    # Extract Publication date
    for date_section in soup.find_all('div', attrs={'id': 'publication_date'}):
        for p in date_section.find_all('p'):
            if re.search(' ', p.text):
                rec['date'] = re.sub('^\D*', '', p.text)
            else:
                rec['date'] = p.text


    # Extract the committee members and abstract
    committee_members = []
    div_elements = soup.find_all('div', attrs={'class', 'element'})
    for element in div_elements:
        if element.get('id') is None:
            continue
        if element.get('id') == 'abstract':
            abstract_paragraphs = element.find_all('p')
            abstract = ""
            for paragraph in abstract_paragraphs:
                abstract += paragraph.text
            rec['abs'] = unicode(abstract)

        if element.get('id').find('advisor') != -1:
            for p in element.find_all('p'):
                committee_members.append([p.text])

    rec['supervisor'] = committee_members
    # Extract Keywords
    keywords_section = soup.find_all('div', attrs={'id': 'keywords'})

    if len(keywords_section) == 1:
        keywords_subsection = keywords_section[0].find_all('p')

        if len(keywords_subsection) == 1:
            keywords = keywords_subsection[0].text.replace('\n', '').split(', ')
            rec['keyw'] = keywords

    recs.append(rec)
    print '  ', rec.keys()

for (fc, dep, aff) in [('', 'phyc', 'New Mexico U.'), ('m', 'math', 'UNM, Albuquerque')]:
    index_url = "https://digitalrepository.unm.edu/%s_etds/" % (dep)
    print "--- OPENING article list ---", dep
    v = 0
    for article in http_request(index_url).find_all('p', attrs={'class': 'article-listing'}):
        article_link = article.a
        get_sub_site(article_link.get('href'), fc, aff)
        sleep(10)
        if v >= numoftheses:
            break
        v += 1

xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
