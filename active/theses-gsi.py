# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from GSI
# FS 2020-07-08

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

publisher = 'Darmstadt, GSI '

uninteresting = ['Von Materie zu Materialien und Leben', 'Krebsforschung']


for year in range(now.year-1, now.year+1):
    jnlfilename = 'THESES-GSI-%s_%i' % (stampoftoday, year)
    tocurl = 'https://repository.gsi.de/search?ln=de&cc=PhDThesis&p=260__c%3A' + str(year) + '&f=&action_search=Suchen&c=PhDThesis&c=&sf=&so=d&rm=&rg=200&sc=1&of=xm'
    time.sleep(2)
    print '==={ %i }==={ %s }===' % (year, tocurl)
    recs = []
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    for record in tocpage.find_all('record'):
        rec = {'jnl' : 'BOOK', 'tc' : 'T', 'rn' : [], 'date' : str(year), 'year' : str(year),
               'oa' : False, 'note' : []}
        #record id
        for cf in record.find_all('controlfield', attrs = {'tag' : '001'}):
            recordid = cf.text.strip()
            print '---{ http://repository.gsi.de/record/%s }---' % (recordid)
        #reportnumber
        for df in record.find_all('datafield', attrs = {'tag' : '037'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['rn'].append(sf.text.strip())
        #language
        for df in record.find_all('datafield', attrs = {'tag' : '041'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                if not sf.text.strip() in ['eng', 'English']:
                    rec['language'] = sf.text.strip()
        #author
        for df in record.find_all('datafield', attrs = {'tag' : '100'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['autaff'] = [[ sf.text.strip() ]]
        #affiliation
        for df in record.find_all('datafield', attrs = {'tag' : '502'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'c'}):
                rec['autaff'][0].append(sf.text.strip())
        #DOI
        for df in record.find_all('datafield', attrs = {'tag' : '024'}):
            for sf in df.find_all('subfield', attrs = {'code' : '2'}):                
                doityp = sf.text.strip().lower()
                if doityp == 'datacite_doi': doityp = 'doi'
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):                
                rec[doityp] = sf.text.strip()
        #title
        for df in record.find_all('datafield', attrs = {'tag' : '245'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['tit'] = sf.text.strip()
        #pages
        for df in record.find_all('datafield', attrs = {'tag' : '300'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                if re.search('\d', sf.text):
                    pages = int(re.sub('\D*(\d+).*', r'\1', sf.text))
                    if 0 < pages < 500:
                        rec['pages'] = str(pages)
        #abstract
        for df in record.find_all('datafield', attrs = {'tag' : '520'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['abs'] = sf.text.strip()
        #open access
        for df in record.find_all('datafield', attrs = {'tag' : '915'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                sft = sf.text.strip()
                if re.search('Creative Commons.*CC', sft):
                    rec['license'] = {'statement' : re.sub(' ', '-', re.sub('.*(CC.*)', r'\1', sft))}
                    rec['oa'] = True
                elif sft == 'OpenAccess':
                    rec['oa'] = True

        #comment
        for df in record.find_all('datafield', attrs = {'tag' : '500'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['note'].append(sf.text.strip())
        #fulltext
        for df in record.find_all('datafield', attrs = {'tag' : '856'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'u'}):
                url = sf.text.strip()
                if re.search('\.pdf$', url):
                    if rec['oa']:
                        rec['FFT'] = url
                    else:
                        rec['hidden'] = url
        #experiment
        for df in record.find_all('datafield', attrs = {'tag' : '920'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'l'}):
                exp = sf.text.strip()
                if exp in ['PANDA Detektoren', 'Collaboration FAIR: PANDA']:
                    rec['exp'] = 'GSI-FAIR-PANDA'
                elif exp in ['CBM', 'Collaboration FAIR: CBM']:
                    rec['exp'] = 'GSI-FAIR-CBM'
        #pseudo-DOI
        if not ('doi' in rec.keys() or 'hdl' in rec.keys()):
            rec['link'] = 'https://repository.gsi.de/record/' + recordid
            if not 'urn' in rec.keys():
                rec['doi'] = '20.2000/GSI/' + recordid
        #subject
        keepit = True
        for df in record.find_all('datafield', attrs = {'tag' : '913'}):
            for sf in df.find_all('subfield', attrs = {'code' : 'l'}):
                subject = sf.text.strip()
                if subject in uninteresting:
                    print '   skip', subject
                    keepit = False
                else:
                    rec['note'].append(subject)
        if keepit:
            print '  ', rec.keys()
            recs.append(rec)
            
    #closing of files and printing
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writeXML(recs, xmlfile, publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
 
            
    
