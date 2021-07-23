# -*- coding: utf-8 -*-
#harvest theses from Siegen U.
#FS: 2020-02-14


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Siegen U.'
jnlfilename = 'THESES-SIEGEN-%s' % (stampoftoday)

rpp = 50
pages = 1

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for i in range(pages):
    tocurl = 'https://dspace.ub.uni-siegen.de/handle/ubsi/8/browse?type=type&sort_by=2&order=DESC&rpp=' + str(rpp) + '&etal=-1&value=Doctoral+Thesis&offset=' + str(i*rpp)
    print '---{ %i/%i }---{ %s }---' % (i+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'headers' : 't2'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [], 'keyw_de' : []}
            for a in td.find_all('a'):
                rec['link'] = 'https://dspace.ub.uni-siegen.de' + a['href'] #+ '?show=full'
                prerecs.append(rec)
    time.sleep(15)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #urn
            elif meta['name'] == 'DC.identifier':
                if re.search('^urn', meta['content']):
                    rec['urn'] = meta['content']
            #thesis type
            elif meta['name'] == 'DC.type':
                rec['note'].append(meta['content'])
            #keywords
            elif meta['name'] == 'DC.subject':
                if meta.has_attr('scheme') and meta['scheme'] == 'DCTERMS.DDC':
                    rec['ddc'] = re.sub('^.*?(\d\d\d).*', r'\1', meta['content'])
                else:
                    if meta.has_attr('xml:lang'):
                        if meta['xml:lang'] == 'de':
                            rec['keyw_de'].append(meta['content'])
                        else:
                            rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta.has_attr('xml:lang'):
                    if meta['xml:lang'] == 'de':
                        rec['abs_de'] = meta['content']
                    else:
                        rec['abs'] = meta['content']
                else:
                    rec['abs'] = meta['content']                        
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    #german abstract?
    if not 'keyw' in rec.keys() and 'keyw_de' in rec.keys():
        rec['keyw'] = rec['keyw_de']
    #german kywords?
    if not 'abs' in rec.keys() and 'abs_de' in rec.keys():
        rec['abs'] = rec['abs_de']
    #pseudo DOI?
    if not 'urn' in rec.keys():
        rec['doi'] = '20.2000/' + re.sub('\W', '', rec['link'])
    if 'ddc' in rec.keys():
        if rec['ddc'][0] != '5':
            print '  skip ddc=%s' % (rec['ddc'])
            continue
    print ' ', rec.keys()
    recs.append(rec)



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

