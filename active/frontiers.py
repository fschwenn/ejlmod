# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest articles from Frontiers-journal
# FS 2018-08-28

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
tmpdir = '/tmp'

timestamp = time.strftime("%03j-%H%M", time.localtime())
publisher = 'Frontiers'
typecode = 'P'
jnlfilename = 'frontiers.' + timestamp



urls = sys.argv[1:]
recs = []
i = 0
for artlink in urls:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(urls), artlink)
    rec = {'tc' : 'P', 'autaff' : [], 'refs' : []}
    try:
        print artlink
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (artlink)
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
    autaff = False
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #volume
            if meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            #journal
            elif meta['name'] == 'citation_journal_title':
                if meta['content'] == 'Frontiers in Astronomy and Space Sciences':
                    rec['jnl'] = 'Front.Astron.Space Sci.'
                elif meta['content'] == 'Frontiers in Physics':
                    rec['jnl'] = 'Front.in Phys.'
                else:
                    print 'do not know journal "%s"!' % (meta['content'])
                    sys.exit(0)
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #pages
            elif meta['name'] == 'citation_pages':
                rec['p1'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split(' *; *', meta['content'])
            #absract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'citation_online_date':
                rec['date'] = meta['content']
            #year
            elif meta['name'] == 'citation_date':
                rec['year'] = meta['content']
            #autaff
            elif meta['name'] == 'citation_author':
                if autaff:
                    rec['autaff'].append(autaff)
                autaff = [ meta['content'] ]
            elif meta['name'] == 'citation_author_institution':
                autaff.append(meta['content'])
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                autaff.append('ORCID:%s' % (orcid))
                orcidsfound = True
            elif meta['name'] == 'citation_author_email':
                if meta['content']:
                    email = meta['content']
                    autaff.append('EMAIL:%s' % (email))    
    if autaff:
        rec['autaff'].append(autaff)
    #section
    for a in artpage.body.find_all('a', attrs = {'data-test-id' : 'section-link'}):
        rec['note'] = [ a.text.strip() ]
    #references
    for div in artpage.body.find_all('div', attrs = {'class' : 'References'}):
        for a in div.find_all('a'):
            a.replace_with('')
        rec['refs'].append([('x', div.text.strip())])
    recs.append(rec)



                                       
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
 
