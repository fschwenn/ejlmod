# -*- coding: utf-8 -*-
#harvest theses from Coimbra U.
#FS: 2020-08-25

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
import unicodedata

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Coimbra U.'


numberofpages = 1
rpp = 100

boringdepartments = ['00505UniversidadedeCoimbraFaculdadedeLetras',
                     '00503UniversidadedeCoimbraFaculdadedeEconomia',
                     '00506UniversidadedeCoimbraFaculdadedeMedicina',
                     '00507UniversidadedeCoimbraFaculdadedePsicologiaedeCinciasdaEducao',
                     '00508UniversidadedeCoimbraFaculdadedeCinciasdoDesportoeEducaoFsica',
                     '00509UniversidadedeCoimbraColgiodasArtes',
                     '0505UniversidadedeCoimbraFaculdadedeLetras']


prerecs = []
recs = []
jnlfilename = 'THESES-COIMBRA-%s' % (stampoftoday)
for pn in range(numberofpages):
    tocurl = 'https://estudogeral.sib.uc.pt/handle/10316/15519/browse?type=dateissued&sort_by=2&order=DESC&rpp=' + str(rpp) + '&etal=0&submit_browse=Update&offset='+ str(pn * rpp)
    print '==={ %i/%i }==={ %s }===' % (pn+1, numberofpages, tocurl)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)) 
    for tr in tocpage.body.find_all('tr'):
        year = now.year
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [],
               'oa' : False, 'department' : []}
        #Open Access
        for td in tr.find_all('td', attrs = {'headers' : 't5'}):            
            if re.search('openAccess', td.text):
                rec['oa'] = True
        #year
        for td in tr.find_all('td', attrs = {'headers' : 't1'}):
            if re.search('\d', td.text):
                year = int(re.sub('.*([12]\d\d\d).*', r'\1', td.text.strip()))
        if year > now.year-2:
            for td in tr.find_all('td', attrs = {'headers' : 't2'}):
                for a in td.find_all('a'):
                    if re.search('handle\/\d', a['href']):
                        rec['artlink'] = 'https://estudogeral.sib.uc.pt' + a['href'] + '?mode=full'
                        rec['hdl'] = re.sub('.*handle\/(.*\d).*', r'\1', a['href'])
                        prerecs.append(rec)
    time.sleep(5)



i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue        
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'DC.creator':
                author = meta['content']
                rec['autaff'] = [[ author ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #supervisor
            elif meta['name'] == 'DC.contributor':
                if meta.has_attr('xml:lang'):
                    rec['division'] = meta['content']
                    rec['note'].append(rec['division'])
                else:
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
                if meta['content'] in ['por']:
                    rec['language'] = 'portuguese'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                if rec['oa']:
                    rec['FFT'] = meta['content']
                else:
                    rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' the ', meta['content']): 
                    rec['abs'] = meta['content']
                else:
                    rec['abspt'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
    if not 'abs' in rec.keys():
        if 'abspt' in rec.keys():
            rec['abs'] = rec['abspt']
    for tr in artpage.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
            tdt = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue'}):
            #ORCID of supervisors (dont know to whom of the advisors it belong)
            if tdt == 'crisitem.advisor.orcid':
                pass
            #ORCID of author
            elif tdt == 'crisitem.author.orcid':
                rec['autaff'][-1].append('ORCID:' + td.text.strip())
            #department
            elif tdt == 'thesis.degree.grantorUnit':
                dep = re.sub('\W', '', td.text.strip())
                if dep:
                    rec['department'].append(dep)
                    rec['note'].append(dep)



    rec['autaff'][-1].append(publisher)

    keepit = True
    for dep in rec['department']:
        if dep in boringdepartments:
            print '  skip "%s"' % (dep)
            keepit = False
    if keepit:
        print '  ', rec.keys()
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
