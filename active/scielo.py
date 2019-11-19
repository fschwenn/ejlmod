# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest scielo.org
# FS 2017-03-27

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'

jnl = sys.argv[1]
year = sys.argv[2]
issue = sys.argv[3]

jnlfilename = jnl+year+'.'+issue
typecode = 'P'

if   (jnl == 'rbef'): 
    trunc = 'http://www.scielo.br'
    issn = '1806-1117'
    jnlname = 'Rev.Bras.Ens.Fis.'
    publisher = 'Sociedade Brasileira de Fisica'
    #despite its name it does not contain reviews
    #typecode = 'R'
elif (jnl == 'rmaa'):
    trunc = 'http://www.scielo.org.mx'
    issn = '0185-1101'
    jnlname = 'Rev.Mex.Astron.Astrofis.'
    publisher = 'National Autonomous University of Mexico'
else:
    print 'Dont know journal %s!' % (jnl)
    sys.exit(0)

tocurl = '%s/scielo.php?script=sci_issuetoc&pid=%s%s%04i&lng=en&nrm=iso' % (trunc, issn, year, int(issue))
print "get table of content of %s%s.%s via %s..." %(jnlname, year, issue, tocurl)
tocpage = BeautifulSoup(urllib2.urlopen(tocurl))

note = ''
recs = []



alldois = []
for table in tocpage.body.find_all('table'):
    for td in table.find_all('td'):
        arturl = False
        absurl = False
        rec = {'jnl' : jnlname, 'year' : year, 'issue' : issue, 'tc' : typecode,
               'autaff' : [], 'refs' : []}
        for b in td.find_all('B'):
            rec['tit'] = b.text
        for a in td.find_all('a'):
            if a.has_attr('href'):
                if re.search('^pdf', a.text):
                    rec['FFT'] = trunc + a['href']
                    if re.search('\-', a['href']):
                        rec['p1'] = re.sub('.*\-(.*?)\.pdf', r'\1', rec['FFT'])
                elif re.search('^text in', a.text):
                    language = re.sub('text in ', '', a.text.strip())
                    if not re.search('nglish', language):
                        rec['language'] = language
                    arturl = a['href']
                elif re.search('abstract *in *English', a.text):
                    absurl = a['href']                    
        if absurl:
            time.sleep(3)
            #more informations from abstract page
            print '   more informations from abstract page'
            try:
                abspage = BeautifulSoup(urllib2.urlopen(absurl))
            except:
                print '      wait 5 minutes to get', absurl
                time.sleep(300)
                abspage = BeautifulSoup(urllib2.urlopen(absurl))
            for p in abspage.find_all('p'):
                ptext = re.sub('[\n\t]', ' ', p.text.strip())
                if not rec.has_key('abs'):                    
                    rec['abs'] = ptext
                    #print '?ABSTRACT:', ptext
                    for dochnicht in p.find_all('a'):
                        del rec['abs']
                        break
                    for dochnicht in p.find_all('A'):
                        del rec['abs']
                        break
                    if rec.has_key('abs'):            
                        #print '!ABSTRACT:', ptext     
                        if len(ptext) < 10:
                            del rec['abs']
                if re.search('Keywords', ptext):
                    keywords = re.sub('\. *$', '', re.sub('Keywords *: *', '', ptext))
                    rec['keyw'] = re.split(' *; *', keywords)
        if arturl:
            time.sleep(3)
            #more informations from article page
            print '   more informations from article page'
            try:
                artpage = BeautifulSoup(urllib2.urlopen(arturl))
            except:
                print '      wait 5 minutes to get', arturl
                time.sleep(300)
                artpage = BeautifulSoup(urllib2.urlopen(arturl))
            autaffs = []
            for meta in artpage.find_all('meta'):
                if meta.has_attr('name') and meta.has_attr('content'):
                    if meta['name'] == 'citation_volume':
                        rec['vol'] = meta['content']
                    elif meta['name'] == 'citation_doi':
                        if meta['content']:
                            rec['doi'] = meta['content']
                    elif meta['name'] == 'citation_title':
                        rec['tit'] = meta['content']
                    elif meta['name'] == 'citation_firstpage':
                        if meta['content'] and meta['content'] != "0":
                            rec['p1'] =  meta['content']
                    elif meta['name'] == 'citation_lastpage':
                        if meta['content'] and meta['content'] != "0":
                            rec['p2'] =  meta['content']
                    elif 'citation_author' == meta['name']:
                        aut = meta['content']
                        autaffs.append([aut])
                    elif 'citation_author_institution' == meta['name']:
                        if len(autaffs) > 0:
                            if not meta['content'] in autaffs[-1]:
                                autaffs[-1].append(meta['content'])  
            for autaff in autaffs:
                if not autaff in rec['autaff']:
                    rec['autaff'].append(autaff)
            for licence in artpage.find_all('a', attrs = {'rel' : 'license'}):
                rec['licence'] = {'url' : licence['href']}
            for p in artpage.find_all('p', attrs = {'class' : 'ref'}):
                for links in p.find_all('a'):
                    if links.text == 'Links':
                        links.replace_with('')
                rec['refs'].append([('x', p.text)])
            #keywords
            for p in artpage.find_all('p'):
                for b in p.find_all('b'):
                    if re.search('[kK]ey [wW]ords', b.text):
                        b.replace_with('')
                    rec['keyw'] = re.split('; ', p.text.strip())
        if 'p1' in rec.keys():
            print rec.keys()
            if not 'doi' in rec.keys():
                rec['doi'] = '20.2000/SCIELO/%s/%s/%s/%s' % (jnl, year, issue, rec['p1'])
            if not rec['doi'] in alldois:
                recs.append(rec)
                alldois.append(rec['doi'])






xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
