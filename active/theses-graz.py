# -*- coding: utf-8 -*-
#harvest theses from Graz
#FS: 2020-08-28


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Graz U.'
rpp = 20

jnlfilename = 'THESES-GRAZ-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'https://unipub.uni-graz.at/obvugroa/nav/classification/110928?max=' + str(rpp) + '&facets=type%3D%22oaDoctoralThesis%22&o=desc&s=date'
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'miniTitleinfo'}):
    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
    for a in div.find_all('a'):
            rec['link'] = 'https://unipub.uni-graz.at' + a['href']
            rec['tit'] = a.text.strip()
    for div2 in div.find_all('div', attrs = {'class' : 'origin'}):
        rec['year'] = re.sub('.*?([12]\d\d\d).*', r'\1', div2.text.strip())
        rec['date'] = rec['year']
        if int(rec['year']) > now.year-2:
            recs.append(rec)
        else:
            print '  skip', rec['year']

            
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            req = urllib2.Request(rec['link'], headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #date
            #elif meta['name'] == 'citation_publication_date':
            #    rec['date'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    for table in artpage.body.find_all('table', attrs = {'id' : 'titleInfoMetadata'}):
        #supervisor
        for tr in table.find_all('tr', attrs = {'id' : 'mods_name-roleTerm_Censor'}):
            for a in tr.find_all('A'):
                rec['supervisor'].append([a.text.strip()])
        #pages
        for tr in table.find_all('tr', attrs = {'id' : 'mods_physicalDescriptionExtent'}):
            for span in tr.find_all('span', attrs = {'class' : 'extent'}):
                if re.search('\d\d', span.text):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', span.text.strip())
        #language
        for tr in table.find_all('tr', attrs = {'id' : 'mods_languageLanguageTerm'}):
            for td in tr.find_all('td', attrs = {'class' : 'value'}):
                tdt = td.text.strip()
                if tdt != 'Englisch':
                    rec['language'] = tdt
        #keywords
        for tr in table.find_all('tr', attrs = {'id' : 'mods_subjectAuthority'}):
            for span in tr.find_all('span', attrs = {'class' : 'topic'}):
                rec['keyw'].append(re.sub(' *\/$', '', span.text.strip()))
        #urn
        for tr in table.find_all('tr', attrs = {'id' : 'mods_IdentifierUrn'}):
            for td in tr.find_all('td', attrs = {'class' : 'value'}):
                rec['urn'] = td.text.strip()
    #license
    #for table in artpage.body.find_all('table', attrs = {'id' : 'titleInfoLicenceinfo'}):
    #    for span in table.find_all('span', attrs = {'class' : 'licenseInfo'}):
    #        rec['note'].append(span.text.strip())
    #abstract
    for table in artpage.body.find_all('table', attrs = {'id' : 'titleInfoAbstract'}):
        lang = False
        #check language
        for tr in table.find_all('tr'):
            for td in tr.find_all('td', attrs = {'class' : 'tdSubheader'}):
                if re.search('German', td.text) or re.search('Deutsch', td.text):
                    lang = 'ger'
                elif re.search('Englisc?h', td.text):
                    lang = 'eng'
                else:
                    lang = 'oth'
            #check abstract
            if lang:
                for td in tr.find_all('td', attrs = {'class' : 'titleAddContent'}):
                    rec['abs'+lang] = td.text.strip()
                    lang = False
        #consolidate
        if 'abseng' in rec.keys():
            rec['abs'] = rec['abseng']
        elif 'absoth' in rec.keys():
            rec['abs'] = rec['absoth']
        elif 'absger'in rec.keys():
            rec['abs'] = rec['absger']
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
