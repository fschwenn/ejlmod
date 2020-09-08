# -*- coding: utf-8 -*-
#program to harvest "Symmetry, Integrability and Geometry: Methods and Applications (SIGMA)"
# FS 2012-05-30

import os
import ejlmod2
import re
import sys
import codecs
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

def tfstrip(x): return x.strip()

publisher = 'SIGMA'
year = sys.argv[1]
firstarticle = int(sys.argv[2])
jnl = 'SIGMA'
jnlfilename = 'sigma'+year+'_'+str(firstarticle)



tocurl = 'http://www.emis.de/journals/SIGMA/%s/' % (year)

hdr = {'User-Agent' : 'MagicBrowser'}

req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")

prerecs = {}
for dl in tocpage.body.find_all('dl'):
    rec = {'jnl' : jnl, 'year' : year, 'tc' : 'P', 'auts' : [], 'aff' : [], 'note' : []}
    #title
    for dt in dl.find_all('dt'):
        for b in dt.find_all('b'):
            rec['tit'] = b.text.strip()
    for dd in dl.find_all('dd'):
        ddt = re.sub('[\n\t\r]', ' ', dd.text.strip())
        parts = re.split('SIGMA', ddt)
        #p1
        p1 = int(re.sub('.*\), (\d+), .*', r'\1', parts[1]))
        rec['p1'] = '%03i' % (p1)
        #pages
        rec['pages'] = re.sub('.*?(\d+) page.*', r'\1', parts[1])
    if p1 >= firstarticle:
        time.sleep(1)
        artlink = 'https://www.emis.de/journals/SIGMA/%s/%03i/' % (year, p1)
        print artlink
        req = urllib2.Request(artlink, headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for meta in artpage.head.find_all('meta'):            
            if meta.has_attr('name'):
                #volume
                if meta['name'] == 'citation_volume':
                    rec['vol'] = meta['content']
                #date
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                #DOI
                elif meta['name'] == 'citation_doi':
                    rec['doi'] = meta['content']
                #fulltext
                elif meta['name'] == 'citation_pdf_url':
                    rec['pdf'] = meta['content']
                #keywords
                elif meta['name'] == 'citation_keywords':
                    rec['keyw'] = re.split('; ', meta['content'])
                #bull
                elif meta['name'] == 'citation_arxiv_id':
                    rec['arxiv'] = meta['content']
        bqs = artpage.body.find_all('blockquote')
        #affiliations in superscripts
        for sup in bqs[0].find_all('sup'):    
            if re.search('\)', sup.text):
                aff = re.sub('(.*)\)', r' XXX Aff\1= ', sup.text)
                sup.replace_with(aff)
            else:
                aff = ', =Aff' + sup.text + ', '
                sup.replace_with(aff)
        #authors
        for b in bqs[0].find_all('b'):
            bt = re.sub('[\n\t\r]', ' ', b.text.strip())
            for aut in re.split(' *, *', re.sub(' and ', ', ', bt)):
                if len(aut) > 2:
                    rec['auts'].append(aut)
            b.decompose()
        #affiliations
        bqt = re.sub('[\n\t\r]', ' ', bqs[0].text.strip())
        for aff in re.split('XXX ', bqt):
            if len(aff) > 2:
                rec['aff'].append(aff)                        
        #abstract
        for p in artpage.body.find_all('p'):
            for b in p.find_all('b'):
                if b.text.strip() == 'Abstract':
                    b.decompose()
                    rec['abs'] = p.text.strip()
        #conference?
        for i in artpage.body.find_all('i'):
            if  re.search('Contribution to.*Proceedings', i.text):
                rec['note'].append(i.text.strip())
                rec['tc'] = 'C'
        #refernces
        for ol in artpage.body.find_all('ol'):
            rec['refs'] = []
            for li in ol.find_all('li'):
                rdoi = False
                for a in li.find_all('a'):
                    if a.has_attr('href'):
                        if re.search('doi.org\/10', a['href']):
                            rdoi = re.sub('.*org\/(10.*)', r', DOI: \1', a['href'])
                    else:
                        print '  non-linking anchor!?', a    
                ref = li.text.strip()
                if rdoi:
                    ref = re.sub('\.$', '', ref)
                    ref += rdoi
                rec['refs'].append([('x', ref)])
        print '  ', p1, rec['p1'], rec['doi'], rec.keys()
        prerecs[p1] = rec

keys = prerecs.keys()
keys.sort()
recs = [prerecs[key] for key in keys]
                

xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#xmlfile  = open(xmlf,'w')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()








