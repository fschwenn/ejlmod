# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest crossref-xmls
# FS 2015-12-03


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
import time
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

inf = codecs.EncodedFile(codecs.open(sys.argv[1], mode='rb'), 'utf8')
crossref = BeautifulSoup(''.join(inf.readlines()))
inf.close()

jnlfilename =  re.sub('.*\/', '', sys.argv[1])
jnlfilename =  re.sub('.xml', '', jnlfilename)

for registrant in crossref.body.find_all('registrant'):
    publisher = registrant.text

recs = []
for journal in crossref.body.find_all('journal'):
    #metadata of this issue/ volume
    for journal_metadata in journal.find_all('journal_metadata'):
        for full_title in journal_metadata.find_all('full_title'):
            jtit = full_title.text
    (jvol, jiss, jdate, m, d, y) = (False, False, False, False, False, False)
    for journal_issue in journal.find_all('journal_issue'):
        for issue in journal_issue.find_all('issue'):
            jiss = issue.text
        for month in journal_issue.find_all('month'): m = int(month.text)
        for day  in journal_issue.find_all('day'): d = int(day.text)
        for year in journal_issue.find_all('year'): y = year.text
        if y:
            if m:
                if d:
                    jdate = '%4s-%02i-%02i' % (y, m, d)
                else:
                    jdate = '%4s-%02i' % (y, m)
            else:
                jdate = y                    
    for journal_volume in journal.find_all('journal_volume'):
        for volume in journal.find_all('volume'):
            jvol = volume.text
    #metadata of article
    for journal_article in journal.find_all('journal_article'):
        rec = {'tc' : 'P', 'refs' : []}
        #pbn
        if jvol: rec['vol'] = jvol
        if jiss: rec['iss'] = jiss
        if jdate: rec['date'] = jdate
        if jtit == 'Acta Physica Polonica A':
            rec['jnl'] = 'Acta Phys.Polon.'
            rec['vol'] = 'A' + rec['vol']
        else:
            rec['jnl'] = jtit
        for publication_date in journal_article.find_all('publication_date', attr = {'media_type' : 'print'}):
            for year in publication_date.find_all('year'):
                rec['year'] = year.text
        for first_page in journal_article.find_all('first_page'):
            rec['p1'] = first_page.text
        for last_page in journal_article.find_all('last_page'):
            rec['p2'] = last_page.text
        #DOI
        for doi_data in journal_article.find_all('doi_data'):
            for doi in doi_data.find_all('doi'):
                rec['doi'] = doi.text
            if jtit in ['Acta Physica Polonica A']:
                for resource in doi_data.find_all('resource'):
                    rec['FFT'] = resource.text
        #title
        for titles in journal_article.find_all('titles'):
            for title in titles.find_all('title'): rec['tit'] = title.text
        #authors
        for contributors in journal_article.find_all('contributors'):
            rec['autaff'] = []
            for person_name in contributors.find_all('person_name'):
                author = ''
                for surname in person_name.find_all('surname'): 
                    author = surname.text
                for given_name in person_name.find_all('given_name'):
                    author += ', %s' % (given_name.text)
                if person_name.has_attr('contributor_role') and person_name['contributor_role'] == 'editor':
                    author += ' (Ed.)'
                autaff = [author]
                for affiliation in person_name.find_all('affiliation'):
                    autaff.append(affiliation.text)
                rec['autaff'].append(autaff)                
        #references
        for citation_list in journal_article.find_all('citation_list'):
            for citation in citation_list.find_all('citation'):
                ref = ''
                for unstructured_citation in citation.find_all('unstructured_citation'):
                    ref += unstructured_citation.text
                for doi in citation.find_all('doi'):
                    ref += ', DOI: %s' % (doi.text)
                rec['refs'].append([('x', ref)])
        recs.append(rec)






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
