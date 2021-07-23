# -*- coding: utf-8 -*-
#harvest Pittsburgh Theses
#FS: 2020-02-04


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Pittsburgh (main)'
hdr = {'User-Agent' : 'Magic Browser'}



recs = []
jnlfilename = 'THESES-PITTSBURGH-%s' % (stampoftoday)
for year in [now.year-1, now.year]:
    tocurl = 'https://d-scholarship.pitt.edu/cgi/search/archive/advanced?screen=Search&dataset=archive&_action_search=Search&documents_merge=ALL&documents=&title_merge=ALL&title=&creators_name_merge=ALL&creators_name=&creators_id_merge=ALL&creators_id=&creators_orcid=&contributors_name_merge=ALL&contributors_name=&contributors_type_merge=ANY&etdcommittee_name_merge=ALL&etdcommittee_name=&corp_creators_merge=ALL&corp_creators=&abstract_merge=ALL&abstract=&date='+ str(year) + '&datestamp=&lastmod=&degree=PhD&keywords_merge=ALL&keywords=&divisions=sch_as_appliedmathematics&divisions=sch_as_appliedstatistics&divisions=sch_as_astronomy&divisions=sch_as_compsci&divisions=sch_as_math&divisions=sch_as_philosophy&divisions=sch_as_physics&divisions=sch_fas_mathematics&divisions=sch_fas_philosophy&divisions=sch_fas_physics&divisions=sch_compinfo&divisions_merge=ANY&centers_merge=ANY&event_title_merge=ALL&event_title=&department_merge=ALL&department=&editors_name_merge=ALL&editors_name=&refereed=EITHER&publication_merge=ALL&publication=&issn_merge=ALL&issn=&funders_merge=ALL&funders=&projects_merge=ALL&projects=&note_merge=ALL&note=&other_id_merge=ALL&other_id=&pmcid_merge=ALL&pmcid=&pmid_merge=ALL&pmid=&mesh_headings_merge=ALL&mesh_headings=&chemical_names_merge=ALL&chemical_names=&grants_grantid_merge=ALL&grants_grantid=&grants_agency_merge=ALL&grants_agency=&grants_country_merge=ALL&grants_country=&etdurn_merge=ALL&etdurn=&etd_approval_date=&etd_release_date=&etd_submission_date=&etd_defense_date=&etd_patent_pending=EITHER&userid=&satisfyall=ALL&order='
    yearcomplete = False
    while not yearcomplete:
        print year, tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
            for a in tr.find_all('a'):
                if a.has_attr('href') and re.search('d.scholarship.pitt.edu\/\d', a['href']):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : a['href'], 'year' : str(year), 'note' : []}
                    rec['tit'] = a.text.strip()
                    rec['link'] = a['href']
                    rec['doi'] = '20.2000/Pittsburgh/' + re.sub('\D', '', a['href'])
                    recs.append(rec)
        for span in tocpage.body.find_all('span', attrs = {'class' : 'ep_search_control'}):
            yearcomplete = True
            for a in span.find_all('a'):
                if a.has_attr('href') and a.text.strip() == 'Next':
                    tocurl = 'https://d-scholarship.pitt.edu' + a['href']
                    yearcomplete = False

    i = 0
    for rec in recs:
        i += 1
        print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(3)
        except:
            try:
                print 'retry %s in 180 seconds' % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            except:
                print 'no access to %s' % (rec['link'])
                continue
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'eprints.creators_name':
                    rec['autaff'] = [[ meta['content'] ]]
                elif meta['name'] == 'eprints.creators_email':
                    rec['autaff'][-1].append('EMAIL:'+meta['content'])
                #ORCID
                elif meta['name'] == 'eprints.creators_orcid':
                    rec['autaff'][-1].append(re.sub('.*(\d{4}\-\d{4}\-\d{4}\-\d{4}).*', r'ORCID:\1', meta['content']))
                #keywords
                elif meta['name'] == 'eprints.keywords':
                    rec['keyw'] = re.split(', ', meta['content'])
                #abstract
                elif meta['name'] == 'eprints.abstract':
                    rec['abs'] = meta['content']
                #date
                elif meta['name'] == 'DC.date':
                    rec['date'] = meta['content']
                #DOI
                elif meta['name'] == 'eprints.doi':
                    rec['doi'] = meta['content']
                #number of pages
                elif meta['name'] == 'eprints.pages':
                    rec['pages'] = meta['content']
                #PDF
                elif meta['name'] == 'eprints.document_url':
                    rec['hidden'] = meta['content']
                #department
                elif meta['name'] == 'eprints.divisions':
                    rec['department'] = meta['content']
                    rec['note'].append(rec['department'])
        rec['autaff'][-1].append(publisher)
        print '  ', rec.keys()
                    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path,'a')
    retfiles.write(line)
    retfiles.close()


