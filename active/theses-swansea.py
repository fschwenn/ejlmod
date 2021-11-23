# -*- coding: utf-8 -*-
#harvest theses from Swansea
#JH: 2019-11-21

from bs4 import BeautifulSoup
from time import sleep
import urllib2
from json import loads
import urlparse
import ejlmod2
import codecs
import datetime
import getopt
import sys
import os
import re

recs = []


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Swansea U.'
jnlfilename = 'THESES-SWANSEA-%s' % (stampoftoday)
pages = 2

def http_request(url):
	hdr = {'User-Agent' : 'Magic Browser'}
	req = urllib2.Request(url, headers=hdr)
	soup = BeautifulSoup(urllib2.urlopen(req).read(), 'lxml')
	return soup


def get_subside(url):
	soap = http_request(url)
	print "["+ url + "] --> Harvesting data"
	rec = {}

	rec['tc'] = 'T'
	rec['jnl'] = 'BOOK'

	# Get the title
	title_section = soap.find_all('strong', attrs={'property': 'name'})
	if len(title_section) == 1:
		rec['tit'] = title_section[0].text

	# Get the author's name
	author_section = soap.find_all('span', attrs={'property': 'author'})
	if len(author_section) == 1:
		rec['autaff'] = [[author_section[0].text ]]
        if not 'autaff' in rec.keys():
                for meta in soap.find_all('meta', attrs={'name' : 'citation_author'}):
                        rec['autaff'] = [[ meta['content'] ]]
	rec['autaff'][-1].append(publisher)

	# Get DOI
	doi_section = soap.find_all('a', attrs={'class': 'online'})
	if len(doi_section) == 1:
		rec['doi'] = doi_section[0].text

	# Get the abstract
	table_section = soap.find_all('div', attrs={'class': 'description-tab'})
	if len(table_section) == 1:
		table_rows = table_section[0].find_all('tr')
		for tr in table_rows:
			table_header = tr.find_all('th')
			if len(table_header) > 0:
				if table_header[0].text.find('Abstract') != -1:
					abstract_raw = tr.find_all('td')
					if len(abstract_raw) == 1:
						rec['abs'] = abstract_raw[0].text.replace('\n', '').replace('                  ', '')

	details_section = soap.find_all('table', attrs={'summary': 'Bibliographic Details'})
	if len(details_section) == 1:
		for tr in details_section[0].find_all('tr'):
			th = tr.find_all('th')
			td = tr.find_all('td')

			if len(th) == 1 and len(td) == 1:
				# Get the URL
				if th[0].text.find('URI') != -1:
					rec['link'] = td[0].text

				# Get Publish Date
				if th[0].text.find('Published') != -1:
					rec['year'] = td[0].text.split('\n')[-3]
				# Get Supervisor
				if th[0].text.find('Supervisor') != -1:
					supervisors = td[0].text.split(';')
					rec['supervisor'] = []
					for i in supervisors:
						rec['supervisor'].append([i])
					#print rec['supervisor']

	# Get the pdf link
	pdf_section = soap.find_all('a', attrs={'class': 'file-download'})
	if len(pdf_section) == 1:
		pdf_link = pdf_section[0].get('href')
		rec['hidden'] = "https://cronfa.swan.ac.uk" + pdf_link
	
	# Get the Keywords
	description_table = soap.find_all('table', attrs={'summary': 'Description'})
	if len(description_table) == 1:
		rows = description_table[0].find_all('tr')
		for tr in rows:
			th = tr.find_all('th')
			if len(th) == 1:
				if th[0].text.find('Keywords') != -1:
					rec['keyw'] = tr.find_all('td')[0].text.replace('\n', '').replace('                  ', '').split(', ')

        #pseudoDOI
        if not 'doi' in rec.keys():
                rec['doi'] = '20.2000/Swansea/' + re.sub('\W', '', url[20:])

	recs.append(rec)
        print '  ', rec.keys()

# Get Index Pages

for page in range(1, pages+1):
	url = "https://cronfa.swan.ac.uk/Search/Results?type=AllFields&sort=year&filter%5B%5D=college_str%3A%22College+of+Science%22&filter%5B%5D=format%3A%22E-Thesis%22&page=" + str(page)
	print "--- Open page " + str(page) + " --- " + url

	for link in http_request(url).find_all('a', attrs={'class': 'title'}):
		get_subside("https://cronfa.swan.ac.uk" + link.get('href'))
		sleep(10)

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
