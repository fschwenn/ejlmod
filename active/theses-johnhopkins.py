# -*- coding: utf-8 -*-
#harvest theses from Johns Hopkins U. (main) 
#FS: 2019-12-11


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Johns Hopkins U. (main)'

rpp = 100
pages = 2

rftnogo = ['School+of+Medicine', 'Neuroscience', 'Biomedical+Engineering', 'Mechanical+Engineering', 'Biology',
           'Chemistry', 'Anthropology', 'Clinical+Investigation', 'Environmental+Health+%26+Engineering',
           'Materials+Science+%26+Engineering', 'Materials+Science+and+Engineering', 'Mental+Health',
           'Physiology', 'Population%2C+Family+and+Reproductive+Health', 'Pharmacology+and+Molecular+Sciences',
           'Electrical+Engineering', 'Graduate+Training+Program+in+Clinical+Investigation',
           'Molecular+Microbiology+and+Immunology', 'Sociology', 'Biochemistry', 'Civil+Engineering', 'Economics',
           'Entrepreneurial+Leadership+in+Education', 'History', 'Human+Genetics+and+Molecular+Biology', 'Nursing',
           'Public+Health+Studies', 'Biostatistics', 'Cellular+and+Molecular+Medicine', 'Environmental+Health+and+Engineering',
           'Chemical+%26+Biomolecular+Engineering', 'Chemical+and+Biomolecular+Engineering',
           'Electrical+and+Computer+Engineering', 'Biochemistry%2C+Cellular+and+Molecular+Biology',
           'Cell+Biology', 'Cellular+%26+Molecular+Medicine', 'Health+Policy+and+Management', 'Immunology',
           'Biophysics', 'Education', 'Epidemiology', 'International+Health', 'Chemistry',
           'School+of+Medicine', 'Bloomberg+School+of+Public+Health']
rerft = re.compile('.amp;.*')
def rftcheck(tag):
    for rftdegree in re.split('.rft.degree=', tag['title'].strip())[1:]:
        rftdegree = rerft.sub('', rftdegree)
        if rftdegree in rftnogo:
            #print '   :( %s :(' % (rftdegree)
            return False
    return True

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for j in range(pages):
    tocurl = 'https://jscholarship.library.jhu.edu/handle/1774.2/838/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(j*rpp) + '&etal=-1&order=DESC'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    relevant = 0
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for span in div.find_all('span', title=re.compile('rft.degree=Doctor')):
            if rftcheck(span):
                for a in div.find_all('a'):
                    rec['link'] = 'https://jscholarship.library.jhu.edu' + a['href'] #+ '?show=full'
                    #rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    rec['doi'] = '20.2000/JohnHopkins/' + re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
                    relevant += 1
    print '---{ %i/%i }---{  %i/%i +> %i/%i }---' % (j, pages, relevant, len(divs), len(recs), pages*rpp)
    time.sleep(30)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
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
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                else:
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'pdf_url' in rec.keys():
                rec['FFT'] = rec['pdf_url']
            else:
                for div in artpage.find_all('div'):
                    for a2 in div.find_all('a'):
                        if a2.has_attr('href') and re.search('bistream.*\.pdf', a['href']):
                            divt = div.text.strip()
                            if re.search('Restricted', divt):
                                print divt
                            else:
                                rec['FFT'] = 'https://ecommons.cornell.edu' + re.sub('\?.*', '', a['href'])
    print '  ', rec.keys()
jnlfilename = 'THESES-JOHN_HOPKINS-%s' % (stampoftoday)

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
