# -*- coding: utf-8 -*-
#harvest theses from Giessen
#FS: 2021-02-09


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Giessen (main)'

rpp = 20
pages = 1

hdr = {'User-Agent' : 'Magic Browser'}

recs = []
links = ['http://geb.uni-giessen.de/geb/frontdoor.php?source_opus=2127&la=de']
for fac in ['170410', '170010', '170110']:
    for page in range(pages):
        tocurl = 'http://geb.uni-giessen.de/geb/ergebnis.php?startindex=' + str(rpp) + '&dir=&page=' + str(page+1) + '&suchfeld1=oi.inst_nr&suchwert1=' + fac + '&suchfeld2=person&suchwert2=&suchfeld3=type&suchwert3=8&opt1=AND&opt2=AND&suchart=teil&sort=o.date_year%20DESC,%20o.title&sprache=&Lines_Displayed=' + str(rpp) + '&la=de'
        print '===={ %s }==={ %i/%i }==={ %s }===' % (fac, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for tr in tocpage.body.find_all('tr'):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
            for a in tr.find_all('a'):
                if a.has_attr('href') and re.search('source_opus=', a['href']):
                    rec['link'] = a['href']
                    if rec['link'] in links:
                        print ' skip'
                    else:
                        links.append(rec['link'])
                        for b in tr.find_all('b'):
                            if re.search('^\d\d\d\d$', b.text.strip()):
                                rec['year'] = b.text.strip()
                                if rec['year'] > now.year - 2:
                                    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'DC.Creator.PersonalName':
                    rec['autaff'] = [[ meta['content'] ]]
                #language
                elif meta['name'] == 'DC.Language':
                    if meta['content'] == 'ger':
                        rec['language'] = 'german'
                elif meta['name'] == 'DC.Identifier':
                    #URN
                    if re.search('nbn-resolving.de\/urn', meta['content']):
                        rec['urn'] = re.sub('.*nbn-resolving.de\/', '',  meta['content'])
                #title
                elif meta['name'] == 'DC.Title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'DC.Date.Creation_of_intellectual_content':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.Subject':
                    if meta.has_attr('scheme'):
                        if meta['scheme'] == 'freetext':
                            for keyw in re.split(' *; *', meta['content']):
                                for kw2 in re.split(' , ', keyw):
                                    if not kw2 in rec['keyw']:
                                        rec['keyw'].append(kw2)
                        elif meta['scheme'] == 'DDC-Sachgruppe':
                            rec['ddc'] = meta['content']           
                            rec['note'].append(meta['content'])
                #abstract
                elif meta['name'] == 'DC.Description':
                    if meta.has_attr('lang'):
                        if meta['lang'] == 'en':
                            rec['abs'] = meta['content']
                        elif meta['lang'] == 'de_DE':
                            rec['abs_de'] = meta['content']
    for tr in artpage.find_all('tr'):
        trt = re.sub('.*?: *', '', re.sub('[\n\t\r]', '', tr.text.strip()))
        for td in tr.find_all('td', attrs = {'class' : 'frontdoor'}):            
            #FFT
            if re.search('Volltext', tr.text):
                for a in tr.find_all('a'):
                    if a.has_attr('href') and re.search('pdf$', a['href']):
                        rec['hidden'] = a['href']
            #PACS
            elif re.search('PACS.*Klassifik', tr.text):
                rec['pacs'] = re.split(' *, *', trt)
            #Institut
            elif re.search('Institut:', tr.text):
                if trt == 'II. Physikalisches Institut':
                    rec['inst'] = 'U. Giessen, II. Phys. Inst.'
                elif re.search('Theoretische Physik', trt):
                    rec['inst'] = 'Giessen U.'
                elif re.search('Kernphysik', trt):
                    rec['inst'] = 'Giessen U., Inst. Kernphys.'
                else:
                    rec['inst'] = '%s, Justus-Liebig-Universitat Giessen, Germany' % (trt)
                
    #aff
    if 'inst' in rec.keys():
        rec['autaff'][-1].append(rec['inst'])
    else:
        rec['autaff'][-1].append(publisher)
    #abstract
    if not 'abs' in rec.keys() and 'abs_de' in rec.keys():
        rec['abs'] = rec['abs_de']
    print '  ', rec.keys()

jnlfilename = 'THESES-GIESSEN-%s' % (stampoftoday)


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
