# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest PoS
# FS 2019-06-03

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

nr = sys.argv[1]
vol = sys.argv[2]
year = sys.argv[3]

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
ppdfpath = '/afs/desy.de/group/library/publisherdata/pdf'

publisher = 'SISSA'
jnlfilename = 'pos_%s' % (vol)

tocurl = 'https://pos.sissa.it/%s/' % (nr)
tocpage = BeautifulSoup(urllib2.urlopen(tocurl), features="lxml")

note = False
recs = []
recoll = re.compile('.* (with|Measurement|Experimental|Signal|Search).*(ATLAS|ALICE|CMS|DUNE|TOTEM|NA62|MEG|Belle|KM3NeT|KLOE|JUNO|ICARUS|ILD|ICAL|CDF|BABAR|ALEPH|ZEUS|HERA|JAXO).*')
trs = tocpage.body.find_all('tr')
for tr in trs:
    rec = {'vol' : vol, 'tc' : 'C', 'year' : year, 'jnl' : 'PoS', 'auts' : [], 'col' : [], 'fc' : ''}
    #print tr.text
    if tr.has_attr('class'):
        note = tr.text.strip()
        print '===[ %s ]===' % (note)
    arturl = False
    if note:
        rec['note'] = [note]
        if note == 'Accelerators: Physics, Performance, and R&D for future facilities':
            rec['fc'] += 'b'
        elif note == 'Astroparticle Physics and Cosmology':
            rec['fc'] += 'a'
        elif note == 'Computing and Data Handling':
            rec['fc'] += 'c'
        elif note == 'Dark Matter':
            rec['fc'] += 'a'
        elif note == 'Detectors for Future Facilities, R&D, novel techniques':
            rec['fc'] += 'i'
        elif note == 'Formal Theory':
            rec['fc'] += 't'
        elif note == 'Operation, Performance and Upgrade (incl. HL-LHC) of Present Detectors':
            rec['fc'] += 'i'
    #cnum
    if len(sys.argv) > 4:
        rec['cnum'] = sys.argv[4]
    #fc
    if len(sys.argv) > 5:
        rec['fc'] = sys.argv[5]
    #title
    for span in tr.find_all('span', attrs = {'class' : 'contrib_title'}):
        rec['tit'] = span.text.strip()
        
    #articleID
    for span in tr.find_all('span', attrs = {'class' : 'contrib_code'}):
        for a in span.find_all('a'):
            arturl = 'https://pos.sissa.it' + a['href']
            rec['p1'] = re.sub('.*\/(\d+).*', r'\1',  a['href'])
    if not arturl:
        continue
    print arturl
    artpage = BeautifulSoup(urllib2.urlopen(arturl), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #authors
            if meta['name'] == 'citation_author':
                if re.search('behalf of', meta['content']):
                    col = re.sub('.*behalf of ', '', meta['content'])
                    col = re.sub('^the ', '', col)
                    col = re.sub(' [Cc]ollaboration,?$', '', col)
                    rec['col'].append(col)
                else:
                    mc = re.sub(',$', '', meta['content'])
                    if mc in ['IceCube-Gen2', 'FACT', 'Dampe', 'Fermi Large Area Telescope', 'KM3NeT',
                              'The CTA-LST Project', 'Hess', 'Telescope Array', 'Veritas', 'Fermi-LAT',
                              'H.E.S.S.', 'KASCADE Grande', 'LAGO', 'Hawc', 'MAGIC', 'Pierre Auger',
                              'IceCube']:
                        rec['col'].append(mc)
                    else:
                        rec['auts'].append(mc)
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'citation_online_date':
                rec['date'] = meta['content']
                print ' online_date      ', rec['date']
            elif meta['name'] == 'citation_publication_date':
                rec['publication_date'] = meta['content']
                print ' publication_date ', rec['publication_date']
    if not 'date' in rec.keys() and 'publication_date' in rec.keys():
        rec['date'] = rec['publication_date']
    #construct DOI if neccessary
    if not 'doi' in rec.keys():
        rec['doi'] = '10.22323/1.%s.%04i' % (nr, int(rec['p1']))
    #get PDF
    if 'FFT' in rec.keys():
        doi1 = re.sub('[\(\)\/]', '_', rec['doi'])
        doifilename = '%s/10.22323/%s.pdf' % (ppdfpath, doi1)
        if not os.path.isfile(doifilename):
            os.system('wget -q -O %s "%s"' % (doifilename, rec['FFT']))
            time.sleep(10)
        #count pages
        anzahlseiten = os.popen('pdftk %s dump_data output | grep -i NumberO' % (doifilename)).read().strip()
        anzahlseiten = re.sub('.*NumberOfPages. (\d*).*',r'\1',anzahlseiten)
        rec['pages'] = anzahlseiten
        #license
        for div in artpage.find_all('div', attrs = {'class' : 'license'}):
            for a in div.find_all('a'):
                if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                    rec['license'] = {'url' : a['href']}
        recs.append(rec) 
        print '  ', rec['doi'], rec.keys()
    #collaboration from title
    if not rec['col'] and recoll.search(rec['tit']):
        collaboration = recoll.sub(r'\2', rec['tit'])
        rec['col'].append(collaboration)
        rec['fc'] += 'e'
        rec['note'].append('COL=%s guessed from TIT=%s' % (collaboration, rec['tit']))
    

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
