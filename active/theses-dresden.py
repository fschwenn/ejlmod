# -*- coding: utf-8 -*-
#harvest theses from Dresden
#FS: 2020-07-07

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
pages = 3

publisher = 'TU, Dresden (main)'

starturl = 'https://tud.qucosa.de/recherche/?tx_dpf_frontendsearch[action]=extendedSearch&tx_dpf_frontendsearch[controller]=SearchFE'
startyear = now.year-1
stopyear = now.year+1

br = mechanize.Browser()
br.set_handle_robots(False)   # ignore robots
br.set_handle_refresh(False)  # can sometimes hang without this
br.addheaders = [('User-agent', 'Firefox')]
hdr = {'User-Agent' : 'Firefox'}

#select documents
jnlfilename = 'THESES-DRESDEN-%s_%i-%i' % (stampoftoday, startyear, stopyear)
recs = []
prerecs = []
for thesestype in ['doctoral_thesis', 'habilitation_thesis']:
    print thesestype, starturl
    response = br.open(starturl)
    br.form = list(br.forms())[0]
    control = br.form.find_control('tx_dpf_frontendsearch[query][doctype]')
    control.value = [thesestype]
    control = br.form.find_control('tx_dpf_frontendsearch[query][from]')
    control.value = str(startyear)
    control = br.form.find_control('tx_dpf_frontendsearch[query][till]')
    control.value = str(stopyear)
    time.sleep(2)
    response = br.submit()
    baseurl = response.geturl()
    basepage = BeautifulSoup(response)
    for div in basepage.find_all('div', attrs = {'class' : 'search-results'}):
        for span in div.find_all('span'):
            spant = span.text.strip()
            #print spant
            expnr = int(re.sub('\D', '', spant))
            pages = expnr / 20 + 1

    for page in range(pages):
        tocurl = baseurl + '&tx_dpf_frontendsearch[%40widget_0][currentPage]=' + str(page+1)
        print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
        response = br.open(tocurl)
        tocpage = BeautifulSoup(response)
        for ol in tocpage.body.find_all('ol', attrs = {'class' : 'tx-dlf-listview-list'}):
            for li in ol.find_all('li'):
                for a in li.find_all('a'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
                    rec['link'] = 'https://tud.qucosa.de' + a['href']
                    prerecs.append(rec)
                    #print '  ', a.text.strip()
        time.sleep(1)

i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(2)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    for dl in artpage.body.find_all('dl'):
        for child in dl.children:
            try:
                cn = child.name
            except:
                cn = ''
                dtt = ''
            if cn == 'dt':
                dtt = child.text.strip()
            elif cn == 'dd':
                #author
                if dtt == 'AutorIn':
                    aff = False
                    for span in child.find_all('span'):
                        aff = span.text.strip()
                        span.decompose()
                    author = child.text.strip()
                    author = re.sub('^Dr\.\-Ing\. ', '', author)
                    author = re.sub('^Dr\.[a-z \.]+', '', author)
                    author = re.sub('Dipl.-Phys. ', '', author)
                    author = re.sub('Diplom.Physikeri?n? ', '', author)
                    rec['autaff'] = [[ author ]]
                    if aff: rec['autaff'][-1].append(aff)
                    rec['autaff'][-1].append(publisher)
                #title
                elif dtt == 'Titel':
                    rec['tit'] = child.text.strip()
                #abstract
                elif dtt == 'Abstract (EN)':
                    rec['absen'] = child.text.strip()
                elif dtt == 'Abstract (DE)':
                    rec['absde'] = child.text.strip()
                #ddc
                elif dtt == 'Klassifikation (DDC)':
                    rec['ddc' ] =  child.text.strip()
                #URN
                elif dtt == 'URN Qucosa':
                    rec['urn'] = child.text.strip()
                #language
                elif dtt == 'Sprache des Dokumentes':
                    if child.text.strip() == 'Deutsch':
                        rec['language'] = 'german'
                #date
                elif dtt == 'Datum der Einreichung':
                    parts = re.split('\.', child.text.strip())
                    rec['date'] = '%s-%s-%s' % (parts[2], parts[1], parts[0])
                #presentation
                elif dtt == 'Datum der Verteidigung':
                    parts = re.split('\.', child.text.strip())
                    rec['MARC'] = [('500', [('a', 'Presented on %s-%s-%s' % (parts[2], parts[1], parts[0]))])]
                #link
                elif re.search('^Zitierf', dtt):
                    for a in child.find_all('a'):
                        rec['link'] = a['href']
                #keywords
                elif re.search('^Freie Schlagw.*EN', dtt):
                    rec['keywen'] = re.split(', ', child.text.strip())
                elif re.search('^Freie Schlagw.*DE', dtt):
                    rec['keywde'] = re.split(', ', child.text.strip())
                #supervisor
                elif re.search('^BetreuerIn Hochschule', dtt):
                    supervisors = []
                    for li in child.find_all('li'):
                        supervisors.append(li.text.strip())
                    if not supervisors:
                        supervisors.append(child.text.strip())
                    for supervisor in supervisors:
                        supervisor = re.sub('Univ\.\-Prof\.? ', '', supervisor)
                        supervisor = re.sub('Prof\.? ', '', supervisor)
                        supervisor = re.sub('Dr\.\-Ing\.?[a-z \.]+', '', supervisor)
                        supervisor = re.sub('Dr\.[a-z \.]+', '', supervisor)
                        supervisor = re.sub('PD\.', '', supervisor)
                        rec['supervisor'].append([supervisor])
    #german or english keywords/abstracts
    if 'absen' in rec.keys():
        rec['abs'] = rec['absen']
    elif 'absde' in rec.keys():
        rec['abs'] = rec['absde']
    if 'keywen' in rec.keys():
        rec['keyw'] = rec['keywen']
    elif 'keywde' in rec.keys():
        rec['keyw'] = rec['keywde']
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['licence'] = {'url' : a['href']}
    #FFT
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
        if 'licence' in rec.keys():
            rec['FFT'] = meta['content']
        else:
            rec['hidden'] = meta['content']
    #pseudDOI
    if not 'urn' in rec.keys():
        rec['doi'] = '20.2000/DRESDEN/' + re.sub('.*\/', '', rec['link'])
    if 'ddc' in rec.keys() and not rec['ddc'][:2] in ['50', '51', '52', '53']:
        print '     skip'
    else:
        print ' ', rec.keys()
        recs.append(rec)

#closing of files and printing
if recs:
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
