# -*- coding: utf-8 -*-
#harvest Florida State University theses
#FS: 2020-04-24


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
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Florida State U., Tallahassee (main)'

typecode = 'T'

jnlfilename = 'THESES-FLORIDASTATE-%s' % (stampoftoday)

tocurls = ['https://diginole.lib.fsu.edu/islandora/search/%2A%3A%2A?collection=fsu%3Aresearch_repository&f%5B0%5D=RELS_EXT_hasModel_uri_ms%3A%22info%3Afedora/ir%3AthesisCModel%22&f%5B1%5D=RELS_EXT_isMemberOfCollection_uri_ms%3A%22info%3Afedora/fsu%3Aetds%22&f%5B2%5D=mods_subject_topic_ms%3A%22Physics%22&islandora_solr_search_navigation=0&sort=date_sort_dt%20desc', 'https://diginole.lib.fsu.edu/islandora/search/%2A%3A%2A?collection=fsu%3Aresearch_repository&f%5B0%5D=RELS_EXT_hasModel_uri_ms%3A%22info%3Afedora/ir%3AthesisCModel%22&f%5B1%5D=RELS_EXT_isMemberOfCollection_uri_ms%3A%22info%3Afedora/fsu%3Aetds%22&f%5B2%5D=mods_subject_topic_ms%3A%22Mathematics%22&islandora_solr_search_navigation=0&sort=date_sort_dt%20desc']
#tocurls = ['https://diginole.lib.fsu.edu/islandora/search/%2A%3A%2A?page=1&collection=fsu%3Aresearch_repository&f%5B0%5D=RELS_EXT_hasModel_uri_ms%3A%22info%3Afedora/ir%3AthesisCModel%22&f%5B1%5D=RELS_EXT_isMemberOfCollection_uri_ms%3A%22info%3Afedora/fsu%3Aetds%22&f%5B2%5D=mods_subject_topic_ms%3A%22Mathematics%22&islandora_solr_search_navigation=0&sort=date_sort_dt%20desc', 'https://diginole.lib.fsu.edu/islandora/search/%2A%3A%2A?page=2&collection=fsu%3Aresearch_repository&f%5B0%5D=RELS_EXT_hasModel_uri_ms%3A%22info%3Afedora/ir%3AthesisCModel%22&f%5B1%5D=RELS_EXT_isMemberOfCollection_uri_ms%3A%22info%3Afedora/fsu%3Aetds%22&f%5B2%5D=mods_subject_topic_ms%3A%22Mathematics%22&islandora_solr_search_navigation=0&sort=date_sort_dt%20desc', 'https://diginole.lib.fsu.edu/islandora/search/%2A%3A%2A?page=1&collection=fsu%3Aresearch_repository&f%5B0%5D=RELS_EXT_hasModel_uri_ms%3A%22info%3Afedora/ir%3AthesisCModel%22&f%5B1%5D=RELS_EXT_isMemberOfCollection_uri_ms%3A%22info%3Afedora/fsu%3Aetds%22&f%5B2%5D=mods_subject_topic_ms%3A%22Physics%22&islandora_solr_search_navigation=0&sort=date_sort_dt%20desc', 'https://diginole.lib.fsu.edu/islandora/search/%2A%3A%2A?page=2&collection=fsu%3Aresearch_repository&f%5B0%5D=RELS_EXT_hasModel_uri_ms%3A%22info%3Afedora/ir%3AthesisCModel%22&f%5B1%5D=RELS_EXT_isMemberOfCollection_uri_ms%3A%22info%3Afedora/fsu%3Aetds%22&f%5B2%5D=mods_subject_topic_ms%3A%22Physics%22&islandora_solr_search_navigation=0&sort=date_sort_dt%20desc']


#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}


prerecs = []
recs = []
for tocurl in tocurls:
    print '[]', tocurl
    try:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(5)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")

    for div in tocpage.body.find_all('div', attrs = {'class' : 'islandora-solr-search-result-inner'}):
        for dl in div.find_all('dl', attrs = {'class' : 'solr-thumb'}):
            for a in dl.find_all('a'):
                rec = {'jnl' : 'BOOK', 'tc' : 'T', 'supervisor' : [], 'keyw' : []}
                rec['artlink'] = 'https://diginole.lib.fsu.edu' + a['href']
                prerecs.append(rec)

i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(prerecs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_publication_date':                
                rec['date'] = meta['content']
                rec['year'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ re.sub('\(.*\)', '', meta['content']), publisher ]]
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'islandora-definition-row'}):
        for th in tr.find_all('th'):
            tht = th.text.strip()
            for td in tr.find_all('td'):
                #supervisor
                if tht == 'Name(s):':
                    for br in td.find_all('br'): br.replace_with('XXX')
                    for tdt in re.split('XXX', td.text.strip()):
                        if re.search(', Professor Directing Dissertation', tdt, re.IGNORECASE):
                            rec['supervisor'].append([re.sub(', [12]\d.*', '', re.sub(', .rofessor.*', '', tdt))])
                #pages
                elif tht == 'Extent:':
                    if re.search('\d pages', td.text):
                        rec['pages'] = re.sub('.*?(\d+) pages.*', r'\1', td.text.strip())
                #abstract
                elif re.search('Abstract', tht, re.IGNORECASE):
                    rec['abs'] = td.text.strip()
                #keyword
                elif re.search('Subject', tht, re.IGNORECASE):
                    for a in td.find_all('a'):
                        rec['keyw'].append(a.text.strip())
                #link
                elif re.search('Persistent Link', tht, re.IGNORECASE):
                    for a in td.find_all('a'):
                        rec['link'] = a['href']
                        rec['doi'] = '20.2000/FSU/' + re.sub('.*\/', '', a['href'])
    if not rec['keyw']: del rec['keyw']
    if not rec['supervisor']: del rec['supervisor']
    if 'doi' in rec.keys():
        recs.append(rec)
        print '  ', rec.keys()
    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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
