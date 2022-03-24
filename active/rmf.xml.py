#program to harvest "Revista Mexicana de Fisica"
# -*- coding: UTF-8 -*-
## JH 2022-03-12

import os
import ejlmod2
import codecs
import re
import sys
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

if sys.argv[1] in ['E', 'S']:
        letter = sys.argv[1]
        volume = sys.argv[2]
        issue = sys.argv[3]
else:
        letter = ''
        volume = sys.argv[1]
        issue = sys.argv[2]
        

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Sociedad Mexicana de Fisica'
jnlfilename = 'rmf%s%s.%s' % (letter, volume, issue)

if letter == '':
        jnl = 'Rev.Mex.Fis.'
	tocurl = "https://rmf.smf.mx/ojs/index.php/rmf/issue/archive"
elif letter == 'E':
        jnl = 'Rev.Mex.Fis.E'
	tocurl = "https://rmf.smf.mx/ojs/index.php/rmf-e/issue/archive"
elif letter == 'S':
        jnl == 'Rev.Mex.Fis.Suppl.'
        tocurl = "https://rmf.smf.mx/ojs/index.php/rmf-s/issue/archive"

recs = []

redoi = re.compile('.*doi.org\/(10.\d+\/.*?)(, .*|\.$|$)')
def get_article(url, section):
	rec = {'jnl': jnl, 'tc': 'P', 'note' : [section], 'refs' : [],
               'vol' : volume, 'issue' : issue, 'keyw' : []}

	soup = BeautifulSoup(urllib2.urlopen(url), 'lxml')

	print "ARTICLE: ["+url+"] --> Harvesting data"

        for meta in soup.find_all('meta'):
                if meta.has_attr('name'):
                        #date
                        if meta['name'] == 'citation_date':
                                rec['date'] = meta['content']
                        #title
                        elif meta['name'] == 'citation_title':
                                rec['tit'] = meta['content']
                        #DOI
                        elif meta['name'] == 'DC.Identifier.DOI':
                                rec['doi'] = meta['content']
                        #license
                        elif meta['name'] == 'DC.Rights':
                                if re.search('creativecommons.org', meta['content']):
                                        rec['license'] = {'url' : meta['content']}
                        #abstract
                        elif meta['name'] == 'DC.Description':
                                rec['abs'] = meta['content']
                        #keywords
                        elif meta['name'] == 'citation_keywords':
                                rec['keyw'].append(meta['content'])
                        #fulltext
                        elif meta['name'] == 'citation_pdf_url':
                                if 'license' in rec.keys():
                                        rec['FFT'] = meta['content']
                                else:
                                        rec['hidden'] = meta['content']
                        #pages
                        elif meta['name'] == 'citation_firstpage':
                                p1 = meta['content']
                                rec['p1'] = re.sub(' .*', '', p1)
                        elif meta['name'] == 'citation_lastpage':
                                if re.search(' ', p1):                                        
                                        rec['pages'] = re.sub('.*\D', '', meta['content'])
                                else:
                                        rec['p2'] = meta['content']
                        #references
                        elif meta['name'] == 'citation_reference':
                                ref = [('x', meta['content'])]
                                if redoi.search(meta['content']):
                                        ref.append(('a', redoi.sub(r'doi:\1', meta['content'])))
                                rec['refs'].append(ref)
                        #language
                        elif meta['name'] == 'DC.Language"':
                                if meta['content'] == 'es':
                                        rec['language'] = 'Spanish'


	# Get the authors
	authors_section = soup.find_all('ul', attrs={'class': 'authors'})
	if len(authors_section) == 1:
		rec['autaff'] = []
		for author in authors_section[0].find_all('li'):
			for name in author.find_all('span', attrs={'class': 'name'}):
                                rec['autaff'].append([name.text.replace('\t','').replace('\n', '')])
                        for orcid in author.find_all('span', attrs={'class': 'orcid'}):
                                rec['autaff'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', orcid.text.replace('\t','').replace('\n', '')))
                        for aff in author.find_all('span', attrs={'class': 'affiliation'}):
                                rec['autaff'][-1].append(aff.text.replace('\t', '').replace('\n', ''))


	# Get the references
	references_section = soup.find_all('section', attrs={'class': 'item references'})
	if len(references_section) == 1:
		references_sub_section = references_section[0].find_all('div', attrs={'class': 'value'})
		if len(references_sub_section) == 1:
			references = references_sub_section[0].find_all('p')
			refs = []
			for reference in references:
				# Get the reference's DOI
				ref_doi = reference.find_all('a')
				if len(ref_doi) == 1:
					ref_doi = ref_doi[0].text.split('/')
					refs.append(ref_doi[-2] + "/" + ref_doi[-1])
                                        
	recs.append(rec)
        print '  ', rec.keys()




def get_issue(url):
	soup = BeautifulSoup(urllib2.urlopen(url), 'lxml')
	print "ISSUE: ["+url+"] --> Harversting data"
	# Get volume and issue number
	heading = soup.find_all('h1')
	if len(heading) == 1:
		vol_num = heading[0].text.split('):')[0].split(' (')[0]
		vol_num = vol_num.split(' ')
		vol = int(vol_num[1])
		issue = int(vol_num[3])
	for div in soup.find_all('div', attrs={'class': 'section'}):
                for h2 in div.find_all('h2'):
                        section = h2.text.strip()
	        articles = div.find_all('div', attrs={'class': 'obj_article_summary'})
	        for article in articles:
		        link = article.a
		        if link.get('href') is None:
			        continue
		        href = link.get('href')
		        get_article(href, section)
		        sleep(10)




jtocpage = BeautifulSoup(urllib2.urlopen(tocurl).read(), 'lxml')
#find issue link
for h2 in jtocpage.body.find_all('h2'):
        if re.search('.*Vol.? %s,? No.? %s .*' % (volume, issue), h2.text):
                for a in h2.find_all('a'):
                        tocurl = a['href']
                        print tocurl
get_issue(tocurl)

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
