# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest CERN as a publisher
# FS 2019-03-01

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'CERN'
jnlid = sys.argv[1]
volid = sys.argv[2]

jnlfilename = 'cern%s.%s' % (jnlid, volid)


cnum = False
if len(sys.argv) > 3: 
    cnum = sys.argv[3]
    jnlfilename += '_' + cnum


if jnlid == 'cycrp':
    tc = 'C'
    jnl = 'CERN Yellow Rep.Conf.Proc.'
elif jnlid == 'cp':
    tc = 'C'
    jnl = 'CERN Conf.Proc.'
elif jnlid == 'cyrsp':
    tc = 'CL'
    jnl = 'CERN Yellow Rep.School Proc.'
elif jnlid == 'cyrcp':
    tc = 'C'
    jnl = 'CERN Yellow Rep.Conf.Proc.'
elif jnlid == 'cyrm':
    tc = 'S'
    jnl = 'CERN Yellow Rep.Monogr.'
else:
    print 'does not know journal ID "%s"' % (jnlid)
    sys.exit(0)

urltrunk = 'https://e-publishing.cern.ch/index.php/%s' % (jnlid.upper())
tocurl = '%s/issue/view/%s/showToc' % (urltrunk, volid)
try:
    print tocurl
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))


recs = []
#for table in tocpage.body.find_all('table', attrs = {'class' : 'tocArticle'}):
for table in tocpage.body.find_all('div', attrs = {'class' : 'obj_article_summary'}):
    rec = {'jnl' : jnl, 'tc' : tc, 'keyw' : [], 'autaff' : []}
#    for div in table.find_all('div', attrs = {'class' : 'tocTitle'}):
    for div in table.find_all('div', attrs = {'class' : 'title'}):
        rec['tit'] = re.sub('[\n\t]', '', div.text.strip())
        for a in div.find_all('a'):
            rec['artlink'] = a['href']
            recs.append(rec)

    
i = 0
for rec in recs:
    i += 1
    print '---{ %i/ %i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if cnum:
            rec['cnum'] = cnum
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'DC.Date.created':
                rec['date'] = meta['content'] 
            #abstract
            elif meta['name'] == 'DC.Description':
                rec['abs'] = meta['content'] 
            #pages
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content'] 
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content'] 
            #volume
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content'] 
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content'] 
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #PDF
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content'] 
            #authors
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            #affiliations
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
    #license
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['license'] = {'url' : a['href']}
    print '  ', rec.keys()

        
                                       
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
 
