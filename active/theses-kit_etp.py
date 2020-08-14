# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from Karlsruhe Insitute of Technolgy ETP
# FS 2020-01-13

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
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'KIT'

typecode = 'T'

jnlfilename = 'THESES-KIT_ETP-%s' % (stampoftoday)
pages = 18 
#tocurl = 'https://publish.etp.kit.edu/search?page=1&size=20&q=resource_type.type:%20thesis&sort=-publication_date&subtype=phd-thesis'
tocurl = 'https://publish.etp.kit.edu/oai2d?verb=ListRecords&metadataPrefix=marcxml&from=%4d-01-01' % (now.year-1)

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}

records = []
cls = 999
for i in range(pages):
    if 100*i <= cls:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
        for record in tocpage.find_all('record'):
            for df in record.find_all('datafield', attrs = {'tag' : '980'}):
                for sf in df.find_all('subfield', attrs = {'code' : 'b'}):
                    if sf.text.strip() == 'phd-thesis':
                        records.append(record)
        print '---{ %i/%i }---{ %s }---{ %i/%i }---' % (i+1, pages, tocurl, len(records), cls)
        for rt in tocpage.find_all('resumptiontoken'):
            tocurl = 'https://publish.etp.kit.edu/oai2d?verb=ListRecords&resumptionToken=' + rt.text.strip()
            cls = int(rt['completelistsize'])
        time.sleep(1)

i = 0
recs = []
for record in records:
    i += 1 
    print '---[ %i/%i ]---[ %i ]---' % (i, len(records), len(recs))
    rec = {'jnl' : 'BOOK', 'tc' : 'T', 'keyw' : []}
    isnew = False
    for cf in record.find_all('controlfield', attrs = {'tag' : '001'}):
        recordid = cf.text.strip()
        rec['link'] = 'https://publish.etp.kit.edu/record/' + recordid
        rec['doi'] = '20.2000/KIT_ETP/' + recordid
    #DOI
    for df in record.find_all('datafield', attrs = {'tag' : '024'}):
        for sf in df.find_all('subfield', attrs = {'code' : '2'}):
            doityp = sf.text.strip()
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec[doityp] = sf.text.strip()
    #pages
    for df in record.find_all('datafield', attrs = {'tag' : '773'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'g'}):
            if re.search('\d', sf.text):
                pages = int(re.sub('\D*(\d+).*', r'\1', sf.text))
                if 0 < pages < 500:
                    rec['pages'] = str(pages)
    #title
    for df in record.find_all('datafield', attrs = {'tag' : '245'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['tit'] = sf.text.strip()
    #author
    for datafield in record.find_all('datafield', attrs = {'tag' : '100'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            rec['autaff'] = [[ subfield.text.strip() ]]
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'u'}):
            rec['autaff'][0].append( subfield.text.strip() )
    #title
    for datafield in record.find_all('datafield', attrs = {'tag' : '245'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            rec['tit'] =  subfield.text.strip()  
    #reportnumber
    for datafield in record.find_all('datafield', attrs = {'tag' : '909'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'v'}):
            if rec.has_key('rn'):
                rec['rn'].append(re.sub(' ', '-', subfield.text.strip()))
            else:
                rec['rn'] = [ re.sub(' ', '-', subfield.text.strip()) ]
    #language
    for datafield in record.find_all('datafield', attrs = {'tag' : '041'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            if not subfield.text.strip() in ['eng', 'English']:
                rec['language'] = subfield.text.strip()
    #date
    for datafield in record.find_all('datafield', attrs = {'tag' : '260'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'c'}):
            rec['date'] = subfield.text.strip()
            year = int(re.sub('.*([12]\d\d\d).*', r'\1', rec['date']))
            if year > now.year - 2:
                isnew = True
    #abstract
    for datafield in record.find_all('datafield', attrs = {'tag' : '520'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            rec['abs'] = subfield.text.strip()
    #FFT
    for datafield in record.find_all('datafield', attrs = {'tag' : '542'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'l'}):
            if subfield.text.strip() == 'open':
                for df in record.find_all('datafield', attrs = {'tag' : '856'}):
                    for sf in df.find_all('subfield', attrs = {'code' : 'u'}):
                        url = subfield.text.strip()
                        if re.search('\.pdf$', url):
                            rec['FFT'] = url
    #hidden PDF
    if not 'FFT' in rec.keys():
        for df in record.find_all('datafield', attrs = {'tag' : '856'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'u'}):
                url = subfield.text.strip()
                if re.search('\.pdf$', url):
                    rec['hidden'] = url
    #experiment
    for datafield in record.find_all('datafield', attrs = {'tag' : '980'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            exp = subfield.text.strip()
            if exp == 'user-cms':
                rec['exp'] = 'CERN-LHC-CMS'
            elif exp == 'user-belle':
                rec['exp'] = 'KEK-BF-BELLE-II'
            elif exp == 'user-katrin':
                rec['exp'] = 'KATRIN'
            elif exp == 'user-cdf':
                rec['exp'] = 'FNAL-E-0830'
            elif exp == 'user-delphi':
                rec['exp'] = 'CERN-LEP-DELPHI'    
    #check record page for more information
    if isnew:
        req = urllib2.Request(rec['link'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
        #keywords        
        for a in artpage.find_all('a', attrs = {'class' : 'label-link'}):
            for span in a.find_all('span'):
                rec['keyw'].append(span.text.strip())
        #report number
        for div in artpage.find_all('div', attrs = {'class' : 'metadata'}):
            for dl in div.find_all('dl'):
                rncoming = False
                for child in dl.children:
                    try:
                        child.text
                    except:
                        continue
                    if rncoming:
                        if rec.has_key('rn'):
                            rec['rn'].append(re.sub('[ \/]', '-', child.text.strip()))
                        else:
                            rec['rn'] = [re.sub('[ \/]', '-', child.text.strip())]
                        rncoming = False
                    if child.text.strip() == 'Report Number':
                        rncoming = True
        time.sleep(10)        
    if isnew:
        if not rec in recs:
            recs.append(rec)
    else:
        print '     old thesis'
            
            
    
            
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
 
            
    
