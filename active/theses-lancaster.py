# -*- coding: utf-8 -*-
#harvest theses from Lancaster University
#FS: 2020-08-10


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time
import json

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Lancaster U. (main)'

hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-LANCASTER-%s' % (stampoftoday)
recs = []

startyear = now.year-1
stopyear = now.year+1
rpp = 20
pages = 1


recs = []
for section in ['Physics&organisations=5227', 'Mathematics+and+Statistics&organisations=5198']:
    for page in range(pages):
        tocurl = 'http://www.research.lancs.ac.uk/portal/en/publications/search.html?search=&uri=&advanced=true&organisationName=' + section + '&type=%2Fdk%2Fatira%2Fpure%2Fresearchoutput%2Fresearchoutputtypes%2Fthesis%2Fdoc&language=+&publicationYearsFrom=' + str(startyear) + '&publicationYearsTo=' + str(stopyear) + '2020&publicationstatus=published&publicationcategory=&documents=+&peerreview=&pageSize=' + str(rpp) + 'page=' + str(page+1)

        tocurl = 'http://www.research.lancs.ac.uk/portal/en/publications/search.html?publicationYearsFrom=' + str(startyear) + '&publicationstatus=published&advanced=true&documents=%20&pageSize=' + str(rpp) + '&language=%20&publicationYearsTo=' + str(stopyear) + '&type=%2Fdk%2Fatira%2Fpure%2Fresearchoutput%2Fresearchoutputtypes%2Fthesis%2Fdoc&uri=&search=&organisationName=' + section + '&publicationcategory=&peerreview=&page=' + str(page+1)


        
        print '==={ %s }==={ %i/%i }==={ %s }===' % (re.sub('\&.*', '', section), page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for li in tocpage.body.find_all('li', attrs = {'class' : 'portal_list_item'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'autaff' : [], 'supervisor' : [], 'note' : []}
            for h2 in li.find_all('h2'):
                for a in h2.find_all('a'):
                    rec['artlink'] = a['href']
                    rec['tit'] = a.text.strip()
            recs.append(rec)
            
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for table in artpage.body.find_all('table', attrs = {'class' : 'properties'}):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                #date (web page has different date formats -> take only year)
                if tht == 'Publication date':
                    rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', td.text.strip())
                    rec['date'] = rec['year']
                #pages
                elif tht == 'Number of pages':
                    rec['pages'] = td.text.strip()
                #supervisor
                if tht == 'Supervisors/Advisors':
                    for strong in td.find_all('strong'):
                        rec['supervisor'].append([re.sub(', [A-Z][a-z]+visor', '', strong.text.strip())])
    #author
    for ul in  artpage.body.find_all('ul', attrs = {'class' : 'relations persons'}):
        for li in ul.find_all('li'):
            rec['autaff'].append([li.text.strip(), publisher])
    #abstract
    for div in  artpage.body.find_all('div', attrs = {'class' : 'rendering_abstractportal'}):
        rec['abs'] = div.text.strip()
    #DOI
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('doi.org\/10', a['href']):
            rec['doi'] = re.sub('.*oi.org\/', '', a['href'])
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/LANCASTER/' + re.sub('\W', '', rec['artlink'][40:])
        rec['link'] = rec['artlink']
    #license
    for p in artpage.body.find_all('p', attrs = {'class' : 'license'}):
        for span in p.find_all('span'):
            span.decompose()
        pt = p.text.strip()
        statement = re.sub(' ', '-', re.sub(':.*', '', pt))
        if re.search('\d\.0', pt):
            version = re.sub('.*(\d\.0).*', r'-\1', pt)
        else:
            version = ''
        rec['license'] = {'statement' : statement+version}
    #fulltext 
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('\.pdf$', a['href']):
            if 'license' in rec.keys():
                rec['FFT'] =  'http://www.research.lancs.ac.uk' + a['href']
            else:
                rec['hidden'] =  'http://www.research.lancs.ac.uk' + a['href']
    #organization
    for a in artpage.body.find_all('a', attrs = {'rel' : 'Organisation'}):
        org = a.text.strip()
        if org != 'Lancaster University':
            rec['note'].append(org)
    print rec.keys()
                        
    


#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
