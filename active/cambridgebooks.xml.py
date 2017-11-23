# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Cambridge-Books
# FS 2017-08-22


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
import time
import datetime
from bs4 import BeautifulSoup
import json


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'Cambridge University Press'
urltrunc = 'http://www.cambridge.org/de/academic/subjects'

serieses = ['physics/particle-physics-and-nuclear-physics',
            'physics/history-philosophy-and-foundations-physics',
            'physics/cosmology-relativity-and-gravitation',                        
            'physics/quantum-physics-quantum-information-and-quantum-computation',
            'physics/theoretical-physics-and-mathematical-physics',
            'physics/mathematical-methods',
            'physics/theoretical-physics-and-mathematical-physics',
            'mathematics/mathematical-physics',
            'physics/astrophysics',
            'physics/cosmology-relativity-and-gravitation']

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

#scan serieses
for series in serieses:
    prerecs = []
    toclink = '%s/%s/' % (urltrunc, series)
    subject = re.sub('.*\/', '', series)
    print '---{ %s }---' % (series)
    tocreq = urllib2.Request(toclink, headers={'User-Agent' : "Magic Browser"}) 
    toc = BeautifulSoup(urllib2.urlopen(tocreq))
    for div in toc.body.find_all('div', attrs = {'class' : 'bookDetailsWrap'}):
        for h2 in div.find_all('h2'):
            for a in h2.find_all('a'):
                artlink = a['href']
                rec = {'tit' : a.text.strip(), 'artlink' : artlink, 'note' : [ subject ],
                       'autaff' : [], 'tc' : 'B', 'jnl' : 'BOOK', }
                prerecs.append(rec)
                print ' ', rec['tit']
    time.sleep(130)

    #scan individual book pages
    i = 0
    recs = []
    for rec in prerecs:
        i += 1
        artreq = urllib2.Request(rec['artlink'], headers={'User-Agent' : "Magic Browser"}) 
        art = BeautifulSoup(urllib2.urlopen(artreq))
        for script in art.head.find_all('script', attrs = {'type' : 'application/ld+json'}):
            metadata = json.loads(script.text)
            rec['isbn'] = metadata['isbn']
            rec['link'] = metadata['@id']
            rec['pages'] = metadata['numberOfPages']
            rec['abs'] = metadata['description']
            rec['date'] = metadata['datePublished']
            if metadata.has_key('author'):
                for author in metadata['author']:
                    autaff = [ author['name'] ] 
                    if author.has_key('affiliation'):
                        autaff.append(author['affiliation']['name'])
                    rec['autaff'].append(autaff)
            else:
                for editor in metadata['editor']:
                    autaff = [ editor['name'] + ' (Ed.)' ] 
                    if editor.has_key('affiliation'):
                        autaff.append(editor['affiliation']['name'])
                    rec['autaff'].append(autaff)                
            rec['doi'] = '30.3000/cambridge' + metadata['isbn']
            if rec['date'] in ['No date available'] or rec['date'] > stampoftoday:
                print ' [%2i/%2i] delete "%s" because date=%s' % (i, len(prerecs), rec['tit'], rec['date'])
            else:
                print ' [%2i/%2i] added "%s"' % (i, len(prerecs), rec['tit'])
                recs.append(rec)
        time.sleep(20+i)

    jnlfilename = 'CambridgeBooks_%s_%s' % (re.sub('([a-z])([a-z]+).?', r'\1', series), stampoftoday)

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
