# -*- coding: utf-8 -*-
#harvest theses from Salerno U.
#FS: 2020-08-25

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'THESES-SALERNO-%s' % (stampoftoday)

publisher = 'Salerno U.'

hdr = {'User-Agent' : 'Magic Browser'}

pages = 1
rpp = 50


unintersting = [re.compile('Chimica'), re.compile('Biologia'), re.compile('Politiche'),
                re.compile('Farmacia')]
recs = []
for page in range(pages):
    tocurl = 'http://elea.unisa.it:8080/xmlui/handle/10556/60/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        keepit = True
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        #check department
        for h4 in div.find_all('h4'):
            for span in h4.find_all('span'):
                if span.has_attr('title'):
                    rtfs = re.split('\&', span['title'])
                    department = re.sub('^.*?=', '', rtfs[-3])
                    rec['note'].append(department)
                    for unint in unintersting:
                        if unint.search(department):
                            print '    skip',  department
                            keepit = False
                            break
        #check year
        if keepit:
            for span in div.find_all('span', attrs = {'class' : 'date'}):
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                if int(rec['year']) < now.year - 2:
                    keepit = False
                    print '    skip',  rec['year']
        if keepit:
            for a in div.find_all('a'):
                if re.search('handle', a['href']):
                    rec['artlink'] = 'http://elea.unisa.it:8080' + a['href'] #+ '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
    print '  check %i of %i' % (len(recs), (page+1)*rpp)
    time.sleep(2)


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
                rec['autaff'][-1].append(publisher)
            #author
            #if meta['name'] == 'DC.contributor':
            #    rec['supervisor'].append([ meta['content'] ])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' the ',  meta['content']):
                    rec['abs'] = re.sub('ABSTRACT: ', '', meta['content'])
                else:
                    rec['absit'] = re.sub('RESUMEN: ', '', meta['content'])
            #ISBN
            elif meta['name'] == 'citation_isbn':
                rec['isbn'] = meta['content']
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split(' *; *', meta['content']):
                    if keyw != 'Doctoral Thesis':
                        rec['keyw'].append(keyw)
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] in ['it', 'ita']:
                    rec['language'] = 'italian'
    if not 'abs' in rec.keys():
        if 'absit' in rec.keys():
            rec['abs'] = rec['absit']
    print '   ', rec.keys()

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
