# -*- coding: utf-8 -*-
#harvest theses from OSTI
#FS: 2020-05-26


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'
numofpages = 1

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'OSTI'
startyear = now.year - 2
pages = 20
chunksize = 100

uninteresting = [re.compile('biolog'), re.compile('chemic'), re.compile('medic'),
                 re.compile('waste'), re.compile('wildlife'), re.compile('chemistry')]
jnlfilename = 'THESES-OSTI-%s' % (stampoftoday)

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

                 
hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://www.osti.gov/search/sort:publication_date%20desc/publish-date-start:01/01/' + str(startyear) + '/publish-date-end:31/12/2050/product-type:Thesis/Dissertation/page:' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    time.sleep(3)
    for h2 in tocpage.body.find_all('h2', attrs = {'class' : 'title'}):
        for a in h2.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'rn' : [], 'keyw' : []}
            rec['artlink'] = 'https://www.osti.gov' + a['href']
            prerecs.append(rec)
            
i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }------{ %i }---' % (i, len(prerecs), rec['artlink'], len(recs))
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for script in artpage.find_all('script', attrs = {'type' : 'text/javascript'}):
        script.decompose()
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_authors':
                author = meta['content']
                if re.search('ORCID:', author):
                    rec['autaff'] = [[re.sub(' .ORCID.*', '', author)]]
                    orcid = re.sub('.*ORCID:(.*[\dX]).*', r'\1', author)
                    if len(orcid) == 16:
                        rec['autaff'][-1].append('ORCID:%s-%s-%s-%s' % (orcid[0:4], orcid[4:8], orcid[8:12], orcid[12:16]))
                    else:
                        rec['note'].append('ORCID? '+orcid)
                else:
                    rec['autaff'] = [[author]]
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = re.sub('.*?([12]\d\d\d).*', r'\1', meta['content'])
            #report number
            elif meta['name'] == 'citation_technical_report_number':
                rec['rn'] += re.split('; ', meta['content'])
            #not affiliation but Lab
            #elif meta['name'] == 'citation_technical_report_institution':
            #    rec['autaff'][-1].append(meta['content'])
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split('; ', meta['content'])
    #affiliation
    for ol in artpage.find_all('ol', attrs = {'class' : 'affiliation_list'}):
        for li in ol.find_all('li'):
            rec['autaff'][-1].append(li.text.strip())
    for script in artpage.body.find_all('script', attrs = {'type' : 'application/ld+json'}):
        if script.contents:
            scriptt = re.sub('[\n\t]', '', script.contents[0].strip())
            metadata = json.loads(scriptt)
            #abstract
            if 'description' in metadata.keys():
                rec['abs'] = metadata['description']
            if 'datePublished' in metadata.keys():
                rec['date'] = metadata['datePublished']
    #OSTI-number
    for dl in artpage.body.find_all('dl'):
        for dt in dl.find_all('dt'):
            if re.search('OSTI Identifier:', dt.text):
                for dd in dl.find_all('dd'):
                    rec['rn'].append('OSTI-%s' % (dd.text.strip()))
                    #fake doi
                    if not 'doi' in rec.keys():
                        rec['doi'] = '20.2000/OSTI/' + dd.text.strip()
                        rec['link'] = rec['artlink']
    #abstract
    if not 'abs' in rec.keys():
        for p in artpage.body.find_all('p', attrs = {'id' : 'citation-abstract'}):
            rec['abs'] = p.text.strip()
    skipit = False
    for keyw in rec['keyw']:
        if not skipit:
            for unin in uninteresting:
                if unin.search(keyw):
                    skipit = True
                    print '  skip "%s"' % (keyw)
                    break
    if not skipit:
        recs.append(rec)
        print '  ', rec.keys()



for i in range(len(recs)/chunksize + 2):
    jnlfilename = 'THESES-OSTI-%s_%02i' % (stampoftoday, i)
    
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writenewXML(recs[i*chunksize:(i+1)*chunksize],xmlfile,publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
    





sys.exit(0)

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
    
