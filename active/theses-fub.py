# Program to harvest "Freie Universitaet Berlin"
#!/usr/bin/python
# -*- coding: utf-8 -*-
# JH 2022-03-03

from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import os
import ejlmod2
import codecs
import codecs
import datetime
import re

driver = webdriver.PhantomJS()

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

jnlfilename = "THESES-FUB-%s" % (stampoftoday)

publisher = 'Freie U., Berlin'
recs = []
rpp = 40
numofpages = 1
boring = []

def get_sub_site(url):
	print "["+url+"] --> Harvesting Data"
	
	rec = {'jnl': 'BOOK', 'tc': 'T', 'note' : []}

	free_access = False

	driver.get(url)
	soup = BeautifulSoup(driver.page_source, 'lxml')
	if len(soup.find_all('div', attrs={'class': 'box box-search-list list-group'})) == 2:
		table = soup.find_all('div', attrs={'class': 'box box-search-list list-group'})[0]
		for row in table.find_all('div', attrs={'class': 'list-group-item'}):
			columns = row.find_all('div')
			
			if len(columns) == 0:
				continue

			first_column = columns[0]
			if first_column.text.find('author') != -1:
				rec['autaff'] = [[columns[1].text]]
			
			elif first_column.text.find('identifier') != -1:
				# Check if it is a DOI
				if columns[1].text.find('doi') != -1:
					doi_parted = columns[1].text.split('/')
					rec['doi'] = doi_parted[-2] + "/" + doi_parted[-1]
				elif first_column.text.find('urn') != -1:
					rec['urn'] = columns[1].text
				else:
					rec['url'] = columns[1].text

			elif first_column.text.find('rights') != -1:
				if columns[1].text in ['free', 'open access', 'accept']:
					free_access = True
					continue
				elif columns[1].text.find('public-domain') != -1:
					rec['license'] = {
						"url": columns[1].text,
						"statement": "CC0"
					}
					free_access = True
				elif columns[1].text == "http://www.fu-berlin.de/sites/refubium/rechtliches/Nutzungsbedingungen":
					#rec['license'] = {
					#	"url": columns[1].text,
					#	"statement": ""
					#}
					free_access = False
				else:
					unformated_license = columns[1].text.split('/licenses/')[1]
                	                formated_license = unformated_license[0:len(unformated_license)-1].replace('/', '-').upper()
					rec['license'] = {
						"url": columns[1].text,
						"statement": formated_license
					}
                                        if re.search('creativecommons.org', columns[1].text):
					        free_access = True
                                                

			elif first_column.text.find('abstract') != -1:
                                if len(columns) > 2:
                                        if  columns[2].text.strip() == 'de':
                                                rec['absde'] = columns[1].text
                                        else:
                                                rec['abs'] = columns[1].text
                                else:
				        rec['abs'] = columns[1].text

			elif re.search('format.*extent', first_column.text):
				pages = columns[1].text
                                if re.search('\d\d+', pages):
				        rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', pages)

			elif first_column.text.find('language') != -1:
                                language = columns[1].text
                                if language == 'ger':
				        rec['language'] = 'German'

			elif first_column.text.find('subject') != -1 and first_column.text.find('ddc') == -1:
				if "keyw" not in rec.keys():
					rec['keyw'] = []
				rec['keyw'].append(columns[1].text)

			elif first_column.text.find('title') != -1:
                                if first_column.text.find('translated') != -1:
				        rec['transtit'] = columns[1].text
                                else:
				        rec['tit'] = columns[1].text

			elif first_column.text.find('type') != -1:
                                disstype = columns[1].text
				if disstype.find('Dissertation') == -1:
                                        if disstype in boring:
                                                return None
                                        else:
                                                rec['note'].append(disstype)

			elif first_column.text.find('contributor') != -1 and first_column.text.find('gender') == -1:
                                if not re.search('contact', first_column.text):
				        if "supervisor" not in rec.keys():
					        rec['supervisor'] = []
                                        sv = re.sub('(Prof\.|Dr\.|Priv\.\-Doz\.) *', '', columns[1].text)
				        rec['supervisor'].append([sv])

			elif first_column.text.find('issued') != -1:
				rec['date'] = columns[1].text
        #german fallback
        if not 'abs' in rec.keys() and 'absde' in rec.keys():
                rec['abs'] = rec['absde']
                

	# Get link
	#rec['link'] = url

	# Get The pdf link
	links = soup.find_all('a', attrs={'class': 'btn btn-default'})
	for link in links:
		if link.get('title') is not None and link.get('href') is not None:
			if link.text.find('ffnen') != -1:
				if free_access:
					rec['FFT'] = "https://refubium.fu-berlin.de" + link.get('href')
				else:
					rec['hidden'] = "https://refubium.fu-berlin.de" + link.get('href')

	recs.append(rec)
        print '  ', rec.keys()


v = 0
for (fc, dep) in [('m', 'Mathematik+und+Informatik'), ('', 'Physik')]:
	for page in range(numofpages):
		tocurl = 'https://refubium.fu-berlin.de/handle/fub188/14/browse?rpp=' + str(rpp) + '&offset=' + str(page*rpp) + '&etal=-1&sort_by=2&type=affiliation&value=' + dep + '&order=DESC'
		print '>', tocurl
		driver.get(tocurl)
		for link in BeautifulSoup(driver.page_source, 'lxml').find_all('a', attrs={'class': 'box-search-list-title'}):
			get_sub_site('https://refubium.fu-berlin.de' + link.get('href') + "?show=full")
			sleep(3)
			v += 1
		sleep(10)
	sleep(10)


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
