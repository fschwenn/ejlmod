# -*- coding: utf-8 -*-
#harvest theses from Rome U. La Sapienza
#FS: 2020-08-10


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Rome U.'

rpp = 10
pages = 2
startyear = now.year - 1
stopyear = now.year + 1

jnlfilename = 'THESES-ROME-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}



artlinks = []
for acadamicfield in ['200022162', '200022158', '200022160', '200022159']:
    for page in range(pages):
        tocurl = 'https://iris.uniroma1.it/simple-search?query=&location=&sort_by=score&order=desc&rpp=' + str(rpp) + '&filter_field_1=publtypeh&filter_type_1=equals&filter_value_1=07+Tesi+di+Dottorato&filter_field_2=dateIssued&filter_type_2=equals&filter_value_2=%5B' + str(startyear) + '+TO+' + str(stopyear) + '2020%5D&etal=0&filtername=ssd&filterquery=academicField' + acadamicfield + '&filtertype=authority&start=' + str(page*rpp)
        tocurl = 'https://iris.uniroma1.it/simple-search?query=&location=&sort_by=score&order=desc&rpp=' + str(rpp) + '&filter_field_1=publtypeh&filter_type_1=equals&filter_value_1=07+Tesi+di+Dottorato&filter_field_2=dateIssued&filter_type_2=equals&filter_value_2=%5B' + str(startyear) + '+TO+' + str(stopyear) + '%5D&etal=0&filtername=ssd&filterquery=academicField' + acadamicfield + '&filtertype=authority&start=' + str(page*rpp)
        print '---{ %s }---{ %i/%i }---{ %s }---' % (acadamicfield, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for div in tocpage.body.find_all('div', attrs = {'class' : 'dataTables_info'}):
            print '  ', div.text.strip()
        for tr in tocpage.body.find_all('tr'):
            for td in tr.find_all('td', attrs = {'headers' : 't1'}):
                for a in td.find_all('a'):
                    artlink = 'https://iris.uniroma1.it/' + a['href']
                    if not artlink in artlinks:
                        artlinks.append(artlink)
        print '   %i article links so far' % (len(artlinks))
        time.sleep(1)


i = 0
recs = []
for artlink in artlinks:
    i += 1
    print '---{ %i/%i }---{ %s?mode=full }------' % (i, len(artlinks), artlink)
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink + '?mode=full'))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink + '?mode=full'))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    rec = {'tc' : 'T', 'jnl' : 'BOOK'}
    rec['hdl'] = re.sub('.*handle\/', '', artlink)
    for tr in artpage.body.find_all('tr'):
        label = ''
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue', 'headers' : 's2'}):
            #keywords
            if label in ['dc.subject.keywords', 'Parole Chiave']:
                rec['keyw'] = re.split('; ', td.text.strip())
            #language
            elif label in ['dc.language.iso', 'Lingua']:
                if not td.text.strip() in ['eng', 'English']:
                    if td.text.strip() in ['ita', 'Italiano']:                        
                        rec['language'] = 'italian'
                    else:                       
                        rec['language'] = td.text.strip()
            #date
            elif label in ['dc.date.issued']:
                rec['date'] = td.text.strip()
            #title
            elif label in ['dc.title']:
                rec['tit'] = td.text.strip()
            #abstract
            elif label in ['dc.description.abstracteng']:
                rec['abs'] = td.text.strip()
            elif label in ['dc.description.abstractita']:
                rec['absita'] = td.text.strip()
            #supervisor
            elif label in ['dc.authority.advisor']:
                rec['supervisor'] = [[ td.text.strip() ]]
            #author
            elif label in ['dc.authority.people']:
                rec['autaff'] = [[ td.text.strip() ]]
            #ORCID
            elif label in ['crisitem.author.ORCID']:
                rec['autaff'][-1].append('ORCID:' + td.text.strip())
    rec['autaff'][-1].append(publisher)
    #fulltext and license
    for div in artpage.body.find_all('div', attrs = {'class' : 'panel-default'}):
        for td in div.find_all('td'):            
            for a in td.find_all('a'):
                if a.has_attr('href'):
                    #license
                    if re.search('creativecommons.org', a['href']):
                        rec['license'] = {'url' : a['href']}
                    #fulltext
                    else:
                        for it in td.find_all('i'):
                            if it.has_attr('title') and re.search('PDF', it['title']):
                                rec['pdflink'] = 'https://iris.uniroma1.it' + a['href']                    
    if 'pdflink' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdflink']
        else:
            rec['hidden'] = rec['pdflink']
    #abstract
    if not 'abs' in rec.keys() and 'absita' in rec.keys():
        rec['abs'] = rec['absita']
    print rec.keys()
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
