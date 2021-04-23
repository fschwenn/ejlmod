# -*- coding: utf-8 -*-
#harvest Oxford University Reseach Archive for theses
#FS: 2018-01-25


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)


years = 2
pagesdate = 1
pagesnodate = 12
rpp = 100
publisher = 'Oxford University'

typecode = 'T'

jnlfilename = 'THESES-ORA-%s' % (stampoftoday)


nonsubjects = []
for word in ['Africa', 'Ancient', 'Animal', 'Anthropology', 'Architecture', 'Biolog', 'Cancer',
             'China', 'Clima', 'Law', 'history', 'Economic', 'Econometric', 'Education',
             'literature', 'poetry', 'Therapy', 'Geolog', 'Medic', 'Psychiatr', 'Philosoph',
             'Music', 'Oncology', 'Politic', 'Public', 'religi', 'social', 'Sociolog',
             'Neuroscience', 'Genetics', 'Oceanic', 'disease', 'Archeology', 'Linguistics',
             'zoology', 'Biophysics', 'Orthopaedics', 'Bioinformatics', 'Metallurgy',
             'Aerodynamics', 'Zoological', 'Business', 'Neuroscience', 'Physiology', 'Geophysics',
             'Physiology', 'Pharmacology', 'Metabolism', 'Agriculture', 'Anaesthetics', 'Anatomy',
             'Antibiotics', 'Anxiety', 'linguistics', 'Arabic', 'Neuroscience', 'Biblical',
             'Biodiversity', 'Biomimetic', 'Biosensors', 'Blood', 'Botanical', 'Buddhism',
             'Business', 'Children', 'Chinese', 'Criminology', 'Asia', 'haematology', 'Clinical',
             'Neuropathology', 'Settlement', 'Italian', 'Tumour', 'Gynaecology', 
             'Surgery', 'Urban', 'Weather', 'Biochemi', 'Ophthalmology', 'Neurosciences',
             'Theolog', 'Psychology', 'Epidemiology', 'Archaeolog', 'Chemistr', 'Neolithic',
             'Vaccination', 'Woman', 'Immunology', 'Geography']:
    nonsubjects.append(re.compile(word, re.IGNORECASE))

tocurls = []
prerecs = []
#include records with unknown date
for page in range(pagesnodate):
    tocurls.append('https://ora.ox.ac.uk/?f%5Bf_degree_level%5D%5B%5D=Doctoral&f%5Bf_type_of_work%5D%5B%5D=Thesis&page=' + str(page+1) + '&per_page=' + str(rpp) + '&range%5Bf_item_year%5D%5Bmissing%5D=true&search_field=all_fields&sort=publication_date+desc')
#check date range
for page in range(pagesdate):
    tocurls.append('https://ora.ox.ac.uk/?f%5Bf_degree_level%5D%5B%5D=Doctoral&f%5Bf_type_of_work%5D%5B%5D=Thesis&page=' + str(page+1) + '&per_page=' + str(rpp) + '&search_field=all_fields&sort=publication_date+desc')

i = 0
for tocurl in tocurls:
    i += 1
    print '==={ %i/%i }==={ %s }===' % (i, len(tocurls), tocurl)
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

    #for div in tocpage.find_all('div', attrs = {'class' : 'response_doc'}):
    for div in tocpage.find_all('section', attrs = {'class' : 'document-metadata-header'}):
        year = False
        rec = {'jnl' : 'BOOK', 'tc' : typecode, 'keyw' : [], 'note' : []}
        for li in div.find_all('li'):
            lit = li.text.strip()
            if re.search('^[12]\d\d\d', lit):
                rec['date'] = li.text.strip()
                year = int(re.sub('.*([12]\d\d\d).*', r'\1', rec['date']))
        for h3 in div.find_all('h3'):
            rec['tit'] = h3.text.strip()
            for a in h3.find_all('a'):
                rec['link'] = 'https://ora.ox.ac.uk' + a['href']
                rec['doi'] = re.sub('.*:', '20.2000/', a['href'])
        if year:
            if year > now.year - years:
                prerecs.append(rec)
        else:
            prerecs.append(rec)
    print len(prerecs)
 
i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))

    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #fulltext
            if meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'prism.keyword':
                rec['keyw'].append(meta['content'])
            #author
            elif meta['name'] == 'citation_author':
                rec['auts'] = [ meta['content'] ]
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append(meta['content'])
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    #bad metadata
    if not rec.has_key('auts'):
        rec['auts'] = [ 'Mustermann, Martin' ]
    interesting = True
    for note in rec['note']:
        if interesting:
            for word in nonsubjects:
                if word.search(note):
                    print '  skip ', note
                    interesting = False
                    break
    if interesting:
        print ' ', rec.keys()
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
