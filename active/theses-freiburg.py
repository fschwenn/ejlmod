# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from Freiburg U.
# FS 2020-01-20

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import datetime
import time 

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Freiburg U.'

typecode = 'T'

pages = 4
startyear = now.year - 1
stopyear = now.year + 1

jnlfilename = 'THESES-FREIBURG-%s_%s' % (stampoftoday, startyear)

records = []
for ddc in ['530', '500', '510']:
    cls = 999
    tocurl = 'https://freidok.uni-freiburg.de/oai/oai2.php?metadataPrefix=marcxml&verb=ListRecords&metadataPrefix=marcxml&set=ddc:%s&from=%i-01-01&until=%s-01-01' % (ddc, startyear, stopyear)
    rpp = 1
    for i in range(pages):
        if rpp*i <= cls:
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
            for record in tocpage.find_all('record'):
                for setspec in record.find_all('setspec'):
                    if setspec.text == 'pub-type:doctoral_thesis':
                        records.append(record)
            print '---{ %s }---{ %i/%i }---{ %s }---{ %i/%i }---' % (ddc, i+1, pages, tocurl, len(records), cls)
            cls = 0
            for rt in tocpage.find_all('resumptiontoken'):
                tocurl = 'https://freidok.uni-freiburg.de/oai/oai2.php?verb=ListRecords&resumptionToken=' + rt.text.strip()
                cls = int(rt['completelistsize'])
                if rpp == 1:
                    rpp = int(rt['cursor'])
            time.sleep(3)

i = 0
recs = []
for record in records:
    i += 1 
    print '---[ %i/%i ]---[ %i ]---' % (i, len(records), len(recs))
    rec = {'jnl' : 'BOOK', 'tc' : 'T', 'keyw' : [], 'supervisor' : []}
    isnew = False
    #DOI/URN
    for df in record.find_all('datafield', attrs = {'tag' : '024'}):
        for sf in df.find_all('subfield', attrs = {'code' : '2'}):
            doityp = sf.text.strip()
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec[doityp] = sf.text.strip()
    #title
    for df in record.find_all('datafield', attrs = {'tag' : '245'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['tit'] = sf.text.strip()
    #author
    for df in record.find_all('datafield', attrs = {'tag' : '100'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['autaff'] = [[ sf.text.strip() ]]
        for sf in df.find_all('subfield', attrs = {'code' : '0'}):
            sft = sf.text.strip()
            if re.search('\(orcid\)', sft):
                rec['autaff'][-1].append(re.sub('.*\)', 'ORCID:', sft))
        rec['autaff'][-1].append(publisher)
    #supervisor
    for df in record.find_all('datafield', attrs = {'tag' : '700'}):
        for sf in df.find_all('subfield', attrs = {'code' : '4'}):
            if sf.text == 'dgs':
                rec['supervisor'].append([ sf.text.strip() ])
                for sf2 in df.find_all('subfield', attrs = {'code' : '0'}):
                    sft = sf2.text.strip()
                    if re.search('\(orcid\)', sft):
                        rec['supervisor'][-1].append(re.sub('.*\)', 'ORCID:', sft))
                rec['supervisor'][-1].append(publisher)
    #PDF
    for df2 in record.find_all('datafield', attrs = {'tag' : '856'}):
        for sf2 in df2.find_all('subfield', attrs = {'code' : 'x'}):
            if sf2.text == 'Transfer-URL':
                for sf3 in df2.find_all('subfield', attrs = {'code' : 'u'}):
                    rec['pdf_url'] = sf3.text
    #licence and FFT
    for df in record.find_all('datafield', attrs = {'tag' : '506'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'f'}):
            if re.search('(cc|CC)', sf.text):
                rec['licence'] = {'statement' : sf.text.strip()}
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
    #upload PDF at least hidden
    if 'pdf_url' in rec.keys() and not 'FFT' in rec.keys():
        rec['hidden'] = rec['pdf_url']
    #title
    for df in record.find_all('datafield', attrs = {'tag' : '245'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['tit'] =  sf.text.strip()  
    #language
    for df in record.find_all('datafield', attrs = {'tag' : '041'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            if sf.text.strip() == 'ger':
                rec['language'] = 'german'
            elif not sf.text.strip() in ['eng', 'English']:
                rec['language'] = sf.text.strip()
    #date
    for df in record.find_all('datafield', attrs = {'tag' : '264'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'c'}):
            rec['date'] = sf.text.strip()
            year = int(re.sub('.*([12]\d\d\d).*', r'\1', rec['date']))
            if year >= startyear:
                isnew = True
    #abstract
    for df in record.find_all('datafield', attrs = {'tag' : '520'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['abs'] = sf.text.strip()
    #keywords
    for df in record.find_all('datafield', attrs = {'tag' : ['650', '653']}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['keyw'].append(sf.text.strip())
    #DOI fall back
    if not 'doi' in rec.keys():
        for cf in record.find_all('controlfield', attrs = {'tag' : '001'}):
            recordid = cf.text.strip()
            rec['link'] = 'https://publish.etp.kit.edu/record/' + recordid
            rec['doi'] = '20.2000/Freiburg/' + recordid
                   
    if isnew:
        if not rec in recs:
            recs.append(rec)
        else:
            print rec['doi'], 'already in'
    else:
        print '     old thesis'
            
            
    
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
 
            
    
