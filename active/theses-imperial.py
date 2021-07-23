# -*- coding: utf-8 -*-
#harvest theses from Imperial Coll., London
#FS: 2019-09-26


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

publisher = 'Imperial Coll., London'

typecode = 'T'

jnlfilename = 'THESES-IMPERIAL-%s' % (stampoftoday)
startyear = str(now.year-1)
pages = 1
rpp = 20

hdr = {'User-Agent' : 'Magic Browser'}


recs = []
for page in range(pages):
    tocurl = 'https://spiral.imperial.ac.uk/handle/10044/1/1240/simple-search?location=10044%2F1%2F1240&query=&filter_field_1=dateIssued&filter_type_1=equals&filter_value_1=%5B' + startyear + '+TO+2040%5D&rpp=' + str(rpp) + '&sort_by=dc.date.issued_dt&order=DESC&etal=5&submit_search=Update&start=' + str(rpp*page)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr'):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : []}
        for a in tr.find_all('a'):
            rec['artlink'] = 'https://spiral.imperial.ac.uk' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            recs.append(rec)
    time.sleep(5)

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
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Imperial Coll., London')
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org\/10', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    #license
    for a in artpage.body.find_all('a'):
        if re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' :  a['href']}
    #supervisor
    for tr in artpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
            if re.search('Supervisor:', td.text):
                for br in tr.find_all('br'):
                    br.replace_with('BRBRBR')
                for td2 in tr.find_all('td', attrs = {'class' : 'metadataFieldValue'}):
                    for supervisor in re.split(' *BRBRBR *', td2.text.strip()):
                        rec['supervisor'].append([ supervisor,  'Imperial Coll., London'])
    print '    ', rec.keys()



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
