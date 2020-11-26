# -*- coding: utf-8 -*-
#harvest theses from Valencia U.
#FS: 2019-11-26

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
import mechanize
import unicodedata

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Valencia (main)'


numberofpages = 2
recordsperpage = 20

#for subj in [('164', 'math'), ('165', 'astro'), ('166', 'phys')]:
for subj in [('165', 'astro'), ('166', 'phys')]:
    prerecs = []
    recs = []
    jnlfilename = 'THESES-VALENCIA-%s_%s' % (stampoftoday, subj[1])
    #tocurl = 'http://roderic.uv.es/handle/10550/' + subj[0] + '/browse?value=info%3Aeu-repo%2Fsemantics%2FdoctoralThesis&type=type'
    #print tocurl

    #br = mechanize.Browser()
    #br.set_handle_robots(False)   # ignore robots
    #br.set_handle_refresh(False)  # can sometimes hang without this
    #br.addheaders = [('User-agent', 'Firefox')]
    #response = br.open(tocurl)
    #br.form = list(br.forms())[2]
    ##select 'sort by'
    #control = br.form.find_control("sort_by")
    #control.value = ["4"]
    ##select 'sorting order'
    #control = br.form.find_control("order")
    #control.value = ["DESC"]
    ##results per page
    #control = br.form.find_control("rpp")
    #control.value = ["20"]
    #response = br.submit()

    #tocpage = BeautifulSoup(response.read())
    for pn in range(numberofpages):
        tocurl = 'http://roderic.uv.es/handle/10550/' + subj[0] + '/browse?order=DESC&rpp=' + str(recordsperpage) + '&sort_by=4&etal=-1&offset=' + str(pn * recordsperpage) + '&type=title'
        print '==={ %i/%i }==={ %s }===' % (pn+1, numberofpages, tocurl)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)) 
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
            for a in div.find_all('a'):
                rec['artlink'] = 'http://roderic.uv.es' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/(.*\d).*', r'\1', a['href'])
                prerecs.append(rec)
        time.sleep(10)

    i = 0
    for rec in prerecs:
        i += 1
        print '---{ %s }---{ %i/%i (%i) }---{ %s }------' % (subj[1], i, len(prerecs), len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            time.sleep(5)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            except:
                print "no access to %s" % (rec['artlink'])
                continue     
        for span in artpage.find_all('span', attrs = {'class' : 'bold'}):
            spant = span.text.strip()
            if re.search('document', spant):
                arttype = re.sub('.* is a *(.*)Date.*', r'\1', spant)
                arttype = re.sub('.* un.a *(.*),.*', r'\1', arttype)
                rec['arttype'] = arttype
        if not rec['arttype'] in ['tesis', 'tesi']:
            print 'skip articletype:', unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', arttype)).encode('ascii','ignore'),'utf-8')
            continue
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #author
                if meta['name'] == 'DC.creator':
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
                    rec['autaff'][-1].append(publisher)
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    if not meta.has_attr('xml:lang'):
                        rec['supervisor'].append([meta['content']])
                #date
                elif meta['name'] == 'DCTERMS.issued':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    for keyw in re.split(' *; *', meta['content']):
                        rec['keyw'].append(keyw)
                #language
                elif meta['name'] == 'DC.language':
                    if meta['content'] == 'es':
                        rec['language'] = 'spanish'
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['hidden'] = meta['content']
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    rec['abs'] = meta['content']
                elif meta['name'] == 'DC.description':
                    rec['abs'] = meta['content']
                #license            
                elif meta['name'] == 'DC.rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
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
