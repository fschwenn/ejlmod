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


boring = ['Biochemistry', 'Biomedical Services', 'Chemistry', 'Classics Faculty',
          'Clinical Neurosciences', 'Education', 'Engineering Science',
          'English Faculty', 'Experimental Psychology', 'History Faculty', 'Law',
          'Materials', 'Medieval & Modern Languages Faculty', 'Oriental Studies Faculty',
          'Pathology Dunn School', 'Pharmacology', 'Philosophy Faculty',
          'Physiology Anatomy & Genetics', 'Social Policy & Intervention', 'Sociology',
          'Surgical Sciences', 'Theology Faculty', 'NDORMS', 'Earth Sciences', 'Economics',
          'International Development', 'Oncology', 'OSGA', 'Plant Sciences', 'Psychiatry',
          'RDM', 'Ruskin School of Art', 'SAME', 'School of Archaeology', 'SOGE', 'Zoology',
          'Blavatnik School of Government', 'Continuing Education',
          'Linguistics Philology and Phonetics Faculty', 'Music Faculty',
          'Oxford Internet Institute', 'Paediatrics', 'Politics & Int Relations',
          'Primary Care Health Sciences', 'Saïd Business School',
          "Women's & Reproductive Health", 'MSD', 'HUMS', 'SSD']
supdeptofc= {'Condensed Matter Physics' : 'f',
             'Mathematical Institute' : 'm',
             'Astrophysics' : 'a'}

tocurls = []
prerecs = []
#include records with unknown date
for page in range(pagesnodate):
    #tocurls.append('https://ora.ox.ac.uk/?f%5Bf_degree_level%5D%5B%5D=Doctoral&f%5Bf_type_of_work%5D%5B%5D=Thesis&page=' + str(page+1) + '&per_page=' + str(rpp) + '&range%5Bf_item_year%5D%5Bmissing%5D=true&search_field=all_fields&sort=publication_date+desc')
    tocurls.append('https://ora.ox.ac.uk/?f%5Bf_thesis_degree_level%5D%5B%5D=Doctoral&f%5Bf_type_of_work%5D%5B%5D=Thesis&per_page=' + str(rpp) + '&q=&search_field=all_fields&sort=record_publication_date+desc&page=' + str(page+1))
#check date range
#for page in range(pagesdate):
#    tocurls.append('https://ora.ox.ac.uk/?f%5Bf_degree_level%5D%5B%5D=Doctoral&f%5Bf_type_of_work%5D%5B%5D=Thesis&page=' + str(page+1) + '&per_page=' + str(rpp) + '&search_field=all_fields&sort=publication_date+desc')

i = 0
for tocurl in tocurls:
    i += 1
    print '==={ %i/%i }==={ %s }===' % (i, len(tocurls), tocurl)
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")

    #for div in tocpage.find_all('div', attrs = {'class' : 'response_doc'}):
    for div in tocpage.find_all('section', attrs = {'class' : 'document-metadata-header'}):
        year = False
        rec = {'jnl' : 'BOOK', 'tc' : typecode, 'keyw' : [], 'note' : [],
               'autaff' : [], 'supervisor' : []}
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
        if rec['link'] in ['https://ora.ox.ac.uk/objects/uuid:86748e44-8ac2-4883-8e20-933ee40d20f2',
                           'https://ora.ox.ac.uk/objects/uuid:49a473a0-3d35-4e2e-966a-613ac5c0406b']:
            continue
        if year:
            if year > now.year - years:
                prerecs.append(rec)
        else:
            prerecs.append(rec)
    print len(prerecs)

i = 0
recs = []
for rec in prerecs:
    interesting = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
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
            #elif meta['name'] == 'citation_author':
            #    rec['auts'] = [ meta['content'] ]
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append(meta['content'])
    #detailed author/supervisor informations
    for div in artpage.body.find_all('div', attrs = {'style' : 'padding-bottom:10px'}):
        (diision, dep, subdep, role, orcid) = ('', '', '', '', '')
        for a in div.find_all('a', attrs = {'style' : 'text-decoration:none;'}):
            for span in a.find_all('span'):
                span.decompose()
            person = [re.sub('\n', '', a.text).strip()]
        for div2 in div.find_all('div', attrs = {'id' : ['authorsDetails0', 'contributorsDetails0']}):
            for child in div2.children:
                try:
                    cn = child.name
                    ct = child.text.strip()
                except:
                    continue
                if cn == 'dt':
                    dt = ct
                elif cn == 'dd':
                    if dt == 'Department:':
                        dep = ct
                    elif dt == 'Sub department:':
                        subdep = ct
                    elif dt == 'Division:':
                        division = ct
                    elif dt == 'Role:':
                        role = ct
                    elif dt == 'ORCID:':
                        person.append('ORCID:'+ re.sub('.*org\/', '', ct))
            rec['note'].append('XX %s | %s | %s | %s' % (role, division, dep, subdep))
        if role == 'Supervisor':
            rec['supervisor'].append(person)
        elif role in ['Author', 'Author, Author']:
            rec['autaff'].append(person + [publisher])
            if dep in boring or division in boring:
                interesting = False
            elif subdep in supdeptofc.keys():
                rec['fc'] = supdeptofc[subdep]
        else:
            rec['note'].append('ROLE:%s ???' % (role))
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    #bad metadata
    if len(rec['autaff']) == 0:
        rec['autaff'] = [[ 'Mustermann, Martin' ]]
    if interesting:
        print ' ', rec.keys()
        recs.append(rec)


#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
