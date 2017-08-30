# -*- coding: UTF-8 -*-
#program to harvest "New Physics: Sae Mulli"
# FS 2017-08-18


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
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'Korean physical Society'
tc = 'P'
vol = sys.argv[1]
issue = sys.argv[2]

jnlname = 'New Phys.Sae Mulli'
urltrunk = 'http://www.npsm-kps.org/journal'

jnlfilename = "npsm%s.%s" % (vol, issue)
toclink = "%s/list.html?page=1&sort=&scale=500&all_k=&s_t=&s_a=&s_k=&s_v=%s&s_n=%s&spage=&pn=search&year=" % (urltrunk, vol, issue)

print "get table of content..."

try:
    tocpage = BeautifulSoup(urllib2.urlopen(toclink))
except:
    print '%s not found' % (toclink)
    sys.exit(0)


recs = []
recc = re.compile('http.*creativecommons.org')
repacs = re.compile('PACS numbers:? *')
doneartlinks = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'list'}):
    for table in div.find_all('table'):
        for tr in table.find_all('tr'):
            for td in tr.find_all('td', attrs = {'class' : 'j_ti'}):
                rec = {'jnl' : jnlname, 'tc' : tc, 'issue' : issue, 'note' : [], 
                       'auts' : [], 'aff' : [], 'keyw' : [], 'vol' : vol}
                for a in td.find_all('a'):
                    artlink = '%s/%s' % (urltrunk, a['href'])
                    rec['tit'] = a.text.strip()
                if artlink in doneartlinks:
                    continue
                else:
                    doneartlinks.append(artlink)
                time.sleep(10)
                try:
                    artpage = BeautifulSoup(urllib2.urlopen(artlink))
                except:
                    print '%s not found' % (artlink)
                    sys.exit(0)
                for meta in artpage.head.find_all('meta'):
                    if meta.has_attr('name'):
                        if meta['name'] == 'citation_doi':
                            rec['doi'] = meta['content']
                        elif meta['name'] == 'citation_pdf_url':
                            rec['pdf'] = meta['content']
                        elif meta['name'] == 'citation_firstpage':
                            rec['p1'] = meta['content']
                        elif meta['name'] == 'citation_lastpage':
                            rec['p2'] = meta['content']
                        elif meta['name'] == 'citation_keywords':
                            rec['keyw'].append(meta['content'])
                        elif meta['name'] == 'citation_online_date':
                            rec['date'] = meta['content']
                #check for licence
                for a in artpage.body.find_all('a'):
                    if a.has_attr('href'):
                        if recc.search(a['href']):
                            rec['licence'] = {'url' : a['href']}
                            rec['FFT'] = rec['pdf']
                            del rec['pdf']
                #abstract
                for dd in artpage.body.find_all('dd', attrs = {'style' : 'text-align:justify;'}):
                    rec['abs'] = dd.text.strip()
                #PACS
                for dd in artpage.body.find_all('dd', attrs = {'class' : 'j_text_size'}):
                    ddtext = dd.text.strip()
                    if repacs.search(ddtext):
                        rec['pacs'] = re.split(' *, *', repacs.sub('', ddtext))
                #authors and affiliations
                authorstructure = artpage.body.find_all('div', attrs = {'style' : 'padding:10px 0;'})[0]
                for diva in authorstructure.find_all('div', attrs = {'class' : 'bold j_text_size'}):
                    for sup in diva.find_all('sup'):
                        aff = ', =Aff' + sup.text.strip()
                        sup.replace_with(aff)
                    for author in re.split(' *, *', diva.text.strip()):
                        author = re.sub('\*', '', author)
                        if re.search('=Aff', author):
                            rec['auts'].append(author)
                        else:
                            rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', author))
                for diva in authorstructure.find_all('div', attrs = {'class' : 'j_text_size'}):
                    if 'bold' in diva['class']:
                        continue
                    for br in diva.find_all('br'):
                        br.replace_with(';;;')
                    for sup in diva.find_all('sup'):
                        aff = 'Aff%s= ' % (sup.text.strip())
                        sup.replace_with(aff)
                    for divb in diva.find_all('div'):
                        affi = divb.text.strip()
                    if not rec['aff']:
                        affi = diva.text.strip()
                    for aff in re.split(';;;', affi):
                        rec['aff'].append(aff)
                        
                recs.append(rec)
                print rec['doi'], rec['tit']
    
    
#write xml
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
