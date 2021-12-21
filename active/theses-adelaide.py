# -*- coding: utf-8 -*-
#harvest theses from  Adelaide U.
#FS: 2020-02-12


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Adelaide U.'


pages = 2
rpp = 100
uninterestingdepartments = ['School of Animal and Veterinary Sciences', 'Adelaide Law School',
                            'Adelaide Medical School : Ophthalmology and Visual Sciences',
                            'Australian School of Petroleum', 'Business School',
                            'Centre for Global Food &amp; Resources', 'Politics &amp; International Studies',
                            'School of Architecture and Built Environment',
                            'School of Biological Sciences : Ecology and Environmental Science',
                            'School of Chemical Engineering &amp; Advanced Materials', 'School of Chemical Engineering',
                            'School of Dentistry', 'School of Electrical and Electronic Engineering',
                            'School of Humanities : Art History', 'School of Humanities : History',
                            'School of Mechanical Engineering', 'School of Physical Sciences: Chemistry',
                            'School of Physical Sciences : Earth Sciences', 'School of Psychology',
                            'School of Public Health', 'School of Social Sciences : Politics &amp; International Studies',
                            'School of Social Sciences : Sociology, Criminology &amp; Gender Studies',
                            'The Centre for Global Food and Resources', 'School of Biological Sciences',
                            'School of Biological Sciences : Ecology and Environmental Sciences',
                            'School of Humanities : Media', 'Adelaide Medical School', 'Centre for Global Food and Resources',
                            'Entrepreneurship, Commercialisation and Innovation Centre', 'School of Agriculture, Food and Wine',
                            'School of Civil, Environmental and Mining Engineering', 'School of Economics',
                            'School of Physical Sciences : Chemistry',
                            #'School of Computer Science',
                            'School of Electrical and Electronic', 'Adelaide Business School', 'Adelaide Dental School',
                            'Adelaide Medical School : Psychiatry', 'Adelaide Nursing School',
                            'Anthropology &amp; Development Studies', 'Biological Sciences', 'Centre for Traumatic Stress Studies',
                            'Elder Conservatorium of Music', 'Institute for International Trade', 'Joanna Briggs Institute',
                            'School of Biological Sciences : Australian Centre for Ancient DNA',
                            'School of Biological Sciences : Molecular and Biomedical Science',
                            'School of Chemical Engineering and Advanced Materials', 'School of Education',
                            'School of History and Politics : Politics',
                            'School of Humanities : Classics, Archaeology &amp; Ancient History',
                            'School of Humanities : English &amp; Creative Writing',
                            'School of Humanities : English and Creative Writing', 'School of Humanities : French Studies',
                            'School of Humanities : Philosophy', 'School of Medicine', 'School of Nursing',
                            'School of Population Health : Public Health',
                            'School of Social Sciences : Anthropology and School of Social Sciences : Anthropology and Development Studies',
                            'School of Social Sciences: Anthropology and Development Studies', 'School of Social Sciences : Asian Studies',
                            'School of Social Sciences : Geography, Environment',
                            'School of Social Sciences : Geography, Environment &amp; Population',
                            'School of Social Sciences: Geography, Environment &amp; Population',
                            'School of Social Sciences : Geography, Environment and Population',
                            'School of Social Sciences: Politics &amp; International Studies',
                            'School of Social Sciences : Politics and International Studies',
                            'School of Social Sciences : Sociology, Criminology and Gender Studies',
                            'School of Social Sciences', 'The Joanna Briggs Institute', 'Anthropology &amp; Development Studies',
                            'Centre for Global Food &amp; Resources', 'Physical Sciences', 'Politics &amp; International Studies',
                            'School of Chemical Engineering &amp; Advanced Materials', 'School of Chemical Engineering and Advanced Materials',
                            'School of Humanities : Classics, Archaeology &amp; Ancient History',
                            'School of Humanities : English &amp; Creative Writing',
                            'School of Social Sciences : Anthropology and School of Social Sciences : Anthropology and Development Studies',
                            'School of Social Sciences : Geography, Environment',
                            'School of Social Sciences : Geography, Environment &amp; Population',
                            'School of Social Sciences: Geography, Environment &amp; Population',
                            'School of Social Sciences : Politics &amp; International Studies',
                            'School of Social Sciences: Politics &amp; International Studies',
                            'School of Social Sciences : Sociology, Criminology &amp; Gender Studies', 'The Joanna Briggs Institute']

jnlfilename = 'THESES-ADELAIDE-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://digital.library.adelaide.edu.au/dspace/handle/2440/14760/simple-search?query=&rpp=' + str(rpp) + '&sort_by=dc.date.issued_dt&order=DESC&etal=0&submit_search=Update&start=' + str(page*rpp)
    print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
    try:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr'):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'keyw' : [], 'note' : []}
        for a in tr.find_all('a'):
            if a.has_attr('href') and re.search('dspace\/handle', a['href']):
                rec['artlink'] = 'https://digital.library.adelaide.edu.au' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                prerecs.append(rec)
    time.sleep(15)

            
i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(2)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
                rec['autaff'][-1].append(publisher)
            #supervisor
            if meta['name'] == 'DC.contributor':
                if meta.has_attr('xml:lang'):
                    rec['department'] = meta['content']
                    rec['note'].append(rec['department'])
                else:
                    rec['supervisor'].append([ meta['content'] ])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = re.sub('\[EMBARGOED\] ', '', meta['content'])
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    #license
    for a in artpage.body.find_all('a'):
        if re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' :  a['href']}
    if 'department' in rec.keys() and rec['department'] in uninterestingdepartments:
        continue
    else:
        print '   ', rec.keys()
        recs.append(rec)

            
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
