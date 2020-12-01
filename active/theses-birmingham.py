# -*- coding: utf-8 -*-
#harvest theses from Birmingham U.
#FS: 2020-11-26

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

publisher = 'Birmingham U.'

rpp = 20
subjects = [('QC', 'phys'), ('QB', 'astro'), ('QA', 'math'), ('Q', 'general')]
levels = [('d_ph', 1), ('higher', 1)]
hdr = {'User-Agent' : 'Magic Browser'}

alldois = []
for (sj, subject) in subjects:
    jnlfilename = 'THESES-BIRMINGHAM-%s_%s' % (stampoftoday, subject)
    recs = []
    for (level, pages) in levels:
        for page in range(pages):
            tocurl = 'https://etheses.bham.ac.uk/cgi/search/archive/advanced?screen=Search&dataset=archive&tit_abs_ft_merge=ALL&tit_abs_ft=&fulltext_merge=ALL&fulltext=&anyname_merge=ALL&anyname=&title_merge=ALL&title=&abstract_merge=ALL&abstract=&keywords_merge=ALL&keywords=&subjects=' + sj + '&subjects_merge=ANY&divisions=10col_ephy&department_merge=ALL&department=&funders_merge=ANY&projects_merge=ALL&projects=&supervisors_name_merge=ALL&supervisors_name=&thesis_type=' + level + '&date=&satisfyall=ALL&order=-date%2Fcreators_name%2Ftitle&_action_search=Search&search_offset=' + str(page*rpp)
            print '==={ %s %s }==={ %i/%i }==={ %s }===' % (subject, level, page+1, pages, tocurl)
            try:
                time.sleep(3)
                req = urllib2.Request(tocurl, headers=hdr)
                tocpage = BeautifulSoup(urllib2.urlopen(req))
            except:
                print "retry in 300 seconds"
                time.sleep(300)
                req = urllib2.Request(tocurl, headers=hdr)
            for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'autaff' : [], 'supervisor' : []}
                for a in tr.find_all('a'):
                    if a.has_attr('href') and re.search('eprint', a['href']):
                        rec['link'] = a['href']
                        rec['doi'] = '20.2000/Birmingham/' + re.sub('\D', '', a['href'])
                        if level == 'higher':
                            rec['note'].append('higher level degree')
                        if not rec['doi'] in alldois:
                            recs.append(rec)
                            alldois.append(rec['doi'])
            print '  %i recs so far' % (len(recs))
    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }---' % (subject, i, len(recs), rec['link'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(3)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            except:
                print "no access to %s" % (rec['link'])
                continue
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'eprints.creators_name':
                    rec['autaff'] = [[ meta['content'] ]]
                elif meta['name'] == 'eprints.creators_orcid':
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                #title
                elif meta['name'] == 'eprints.title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'eprints.dates_date':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'eprints.keywords':
                    for keyw in re.split(' *, +', meta['content']):
                        rec['keyw'].append(keyw)
                #FFT
                elif meta['name'] == 'eprints.document_url':
                    rec['hidden'] = meta['content']
                #abstract
                elif meta['name'] == 'eprints.abstract':
                    rec['abs'] = meta['content']
        rec['autaff'][-1].append(publisher)
        #supervisors
        for tr in artpage.body.find_all('tr'):
            for th in tr.find_all('th'):
                if th.text.strip() == 'Supervisor(s):':
                    for tr2 in tr.find_all('tr'):
                        for td in tr2.find_all('td'):
                            #name
                            for span in td.find_all('span', attrs = {'class' : 'person_name'}):
                                rec['supervisor'].append([td.text.strip()])
                            #orcid
                            for a in td.find_all('a'):
                                if re.search('orcid.org', a.text):
                                    rec['supervisor'][-1].append(re.sub('.*org\/', 'ORCID:', a.text.strip()))
                            #email
                            if re.search('@', td.text):
                                rec['supervisor'][-1].append('EMAIL:' + td.text.strip())
        print '  ', rec.keys()

    #closing of files and printing
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writeXML(recs, xmlfile, publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()

