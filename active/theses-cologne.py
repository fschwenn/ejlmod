# -*- coding: utf-8 -*-
#harvest theses from Cologne U. 
#FS: 2019-11-25


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
pagestocheck = 2

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Cologne U.'
jnlfilename = 'THESES-COLOGNE-%s' % (stampoftoday)


divisionsdict = {'inst_50000' : 'Universitaet zu Koeln, Faculty of Mathematics and Natural Sciences, Germany',
                 'inst_50005' : 'Universitaet zu Koeln, I. Physikalisches Institut, Zuelpicher Strasse 77, 50937 Koeln, Germany',
                 'inst_50010' : 'Universitaet zu Koeln, Institute of Physics II, Germany',
                 'inst_50015' : 'Universitaet zu Koeln, Institute of Nuclear Chemistry, Germany',
                 'inst_50050' : 'Universitaet zu Koeln, Institute for Genetics, Germany',
                 'inst_50055' : 'Universitaet zu Koeln, Institut fuer Geophysik und Meteorologie, Germany',
                 'inst_50060' : 'Universitaet zu Koeln, Institute of Computer Science, Germany',
                 'inst_50065' : 'Universitaet zu Koeln, Institute for Nuclear Physics, Germany',
                 'inst_50085' : 'Universitaet zu Koeln, Institute of Physical Chemistry, Germany',
                 'inst_50090' : 'Universitaet zu Koeln, Center for Data and Simulation Science, Germany',
                 'inst_50095' : 'Universitaet zu Koeln, Mathematical Institute, Albertus-Magnus-Platz, 50923 Koeln, Germany',
                 'inst_50110' : 'Forschungszentrum Juelich',
                 'inst_50115' : 'Universitaet zu Koeln, MPI for Plant Breeding Research, Germany',
                 'inst_50120' : 'Universitaet zu Koeln, Institut fuer Biologiedidaktik, Germany',
                 'inst_50135' : 'Universitaet zu Koeln, Institut fuer Mathematikdidaktik, Germany',
                 'inst_50140' : 'Universitaet zu Koeln, Institut fuer Physikdidaktik, Germany',
                 'inst_55110' : 'Universitaet zu Koeln, Institut fuer Geologie und Mineralogie, Germany'}

tocurltrunc = 'https://kups.ub.uni-koeln.de/cgi/search/archive/advanced?cache=1750151&order=-date%2Fcreators_name%2Ftitle&_action_search=1&exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Csubjects%3Asubjects%3AANY%3AEQ%3A510+530+no%7Ctype%3Atype%3AANY%3AEQ%3Athesis%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&screen=Search'
#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
#check content pages
for i in range(pagestocheck):
    tocurl = '%s&search_offset=%i' % (tocurltrunc, 20*i)
    print '---{ %i/%i }---{ %s }---' % (i+1, pagestocheck, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
    time.sleep(2)
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):        
        for a in tr.find_all('a'):
            if re.search('kups.ub.uni\-koeln.de\/\d\d', a['href']):
                trtext = tr.text
                if re.search('Bachelor thesis', trtext):
                    print ' skip Bachelor thesis'
                elif re.search('Master thesis', trtext):
                    print ' skip Master thesis'
                else:                
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'supervisor' : []}
                    rec['link'] = a['href']
                    if not re.search('PhD thesis', trtext):
                        rec['note'].append('unknown thesis type')
                    recs.append(rec)

#check individual thesis pages
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.urlopen(rec['link'], context=ctx))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.open(rec['link'], context=ctx))
        except:
            print "no access to %s" % (rec['link'])
            continue
    #first get author
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.creators_name'}):
        rec['autaff'] = [[ meta['content'] ]]
    #affiliation
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.divisions'}):
        if meta['content'] in divisionsdict.keys():
            rec['autaff'][-1].append(divisionsdict[ meta['content'] ])
        else:
            print 'unknown division', meta['content']
            rec['autaff'][-1].append('Universitaet zu Koeln, Germany')            
    #get abstract
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstract'}):
        rec['abs'] = meta['content']
    #English abstract
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstracttranslated_lang'}):
        if meta['content'] == 'eng':
            for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstracttranslated'}):
                rec['abs'] = meta2['content']
    #other metadata
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #email
            if meta['name'] == 'eprints.creators_id':
                if re.search('@', meta['content']):
                    rec['autaff'][-1].append('EMAIL:%s' % (meta['content']))
            #ORCID
            elif meta['name'] == 'eprints.creators_orcid':
                orcid = re.sub('.*(\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-\d\d\d\d).*', r'\1', meta['content']) 
                rec['autaff'][-1].append('ORCID:%s' % (orcid))
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'eprints.datestamp':
                rec['date'] = meta['content'][:10]
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] += re.split('[,;] ', meta['content'])
            #supervisor
            elif meta['name'] == 'eprints.referee_name':
                rec['supervisor'].append([meta['content'], 'Cologne U.'])
            #URN
            elif meta['name'] == 'eprints.urn':
                rec['urn'] = meta['content']
            #supervisor
            elif meta['name'] == 'eprints.referee':
                rec['supervisor'].append([meta['content'], 'Cologne U.'])
            #language
            elif meta['name'] == 'eprints.language':
                if meta['content'] == 'ger':
                    rec['language'] = 'german'
                    for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.title_translated'}):
                        rec['transtit'] = meta2['content']
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href'):
            if re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.document_url'}):
                    rec['FFT'] = meta2['content']
    #hidden PDF
    if not 'license' in rec.keys():
        for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.document_url'}):
            rec['hidden'] = meta2['content']
    #502
    rec['MARC'] = [('502', [('d', rec['date'][:4]), ('c', 'Cologne U.'), ('b', 'PhD')])]
    print '    ', rec.keys()
    
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


