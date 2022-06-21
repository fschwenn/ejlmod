# -*- coding: utf-8 -*-
#harvest INFN theses
#FS: 2018-02-02


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

expdict = {'CMS' : 'CERN-LHC-CMS',
           'ALICE' : 'CERN-LHC-ALICE',
           'ATLAS' : 'CERN-LHC-ATLAS',
           'LHC-b' : 'CERN-LHC-LHCb',
           'VIRGO' : 'VIRGO'}
           

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'INFN'


tocurl = 'http://www.infn.it/thesis/index.php'
print tocurl

br = mechanize.Browser()
br.set_handle_robots(False)   # ignore robots
br.set_handle_refresh(False)  # can sometimes hang without this
br.addheaders = [('User-agent', 'Firefox')]
response = br.open(tocurl)
for year in [now.year, now.year-1]:
    jnlfilename = 'THESES-INFN-%s_%i' % (stampoftoday, year)
    tids = []
    try:        
        br.select_form("ricerca")
    except:
        print "Immernoch Zugang beschraenkt?"
        sys.exit(0)
    #select year
    control = br.form.find_control("TESI[data_conseguimentoyy]")
    control.value = [str(year)]
    #select all articles per page
    control = br.form.find_control("TESI[paginazione]")
    control.value = ["0"]
    #select PhD
    control = br.form.find_control("TESI[tesi_tipo]")
    control.value = ["1"] #?
    response = br.submit()
    #    br.select_form("prossima")
    #    control = br.form.find_control("start")
    #    control.readonly = False
    #    control.value = "20"
    #    response = br.submit()
    tocpage = BeautifulSoup(response.read())
    for td in tocpage.body.find_all('td', attrs = {'class' : 'bordo'}):
        for a in td.find_all('a'):
            if a.has_attr('name'):
                tids.append(a['name'])
    time.sleep(60)
    recs = []
    i = 0
    for tid  in tids:    
        i += 1
        arturl = 'http://www.infn.it/thesis/thesis_dettaglio.php?tid=%s' % (tid)
        print '---{ %i/%i }---{ %s }------' % (i, len(tids), arturl)
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(arturl))
            time.sleep(8)
        except:
            print "retry %s in 180 seconds" % (arturl)
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(arturl))
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : arturl, 'supervisor' : [], 'date' : str(year)}
        rec['doi'] = '20.2000/INFN/%s' % (tid)
        tabelle = []
        for tr in artpage.body.find_all('tr'):
            trflat = []
            for child in tr.children:
                try:
                    trflat.append(re.sub('  +', ' ', re.sub('[\n\t\r]', ' ', child.text).strip()))
                except:
                    pass
            trflat.append(tr)
            tabelle.append(trflat)
        for tab in tabelle:
            if tab[0] == 'Autore':
                rec['auts'] = [ tab[1] ]
            elif tab[0] == 'Esperimento':
                rec['note'] = [tab[1]]
                if tab[1] in expdict.keys():
                    rec['exp'] = expdict[tab[1]]
            elif tab[0][:9] == 'Universit':
                rec['aff'] = [ tab[1] ]
            elif tab[0] == 'Titolo':
                rec['tit'] = tab[1]
            elif tab[0] == 'Abstract':
                rec['abs'] = tab[1]
            elif tab[0] == 'Relatore/i':
                rec['supervisor'].append([tab[1]])
            elif tab[0] == 'File PDF ':
                for a in tab[-1].find_all('a'):
                    rec['FFT'] = a['href']
        recs.append(rec)
        print '  ', rec.keys()
        
        
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
