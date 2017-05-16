# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Nuclear Science and Techniques
# FS 2015-10-13

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


publisher = 'Shanghai Institute of Applied Physics, Chinese Academy of Sciences and Chinese Nuclear Society'

#all issues page
volumn = sys.argv[1]
year = sys.argv[2]
tocurl = 'http://www.j.sinap.ac.cn/nst/EN/volumn/volumn_%s.shtml' % (volumn)
tocpage = BeautifulSoup(urllib2.urlopen(tocurl))

artlinks = []
for a in tocpage.body.find_all('a', attrs = {'target' : '_blank'}):
    if a.has_attr('href') and re.search('Abstract', a.text):
        artlinks.append(re.sub('\.\.', 'http://www.j.sinap.ac.cn/nst/EN', a['href']))


recs = []
for artlink in artlinks:
    print artlink
    rec = {'jnl' : 'Nucl.Sci.Tech.', 'tc' : 'P', 'year' : year}
    try:
        articlepage = BeautifulSoup(urllib2.urlopen(artlink))
        time.sleep(1)
    except:
        print " - sleep -"
        time.sleep(300)
        articlepage = BeautifulSoup(urllib2.urlopen(artlink))
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_doi'}):
        rec['doi'] = meta['content']
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_volume'}):
        rec['vol'] = meta['content']
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_issue'}):
        rec['issue'] = meta['content']
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_firstpage'}):
        rec['p1'] = meta['content']
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_title'}):
        rec['tit'] = meta['content'].strip()
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'DC.Description'}):
        rec['abs'] = re.sub('<.?p>', '', meta['content'])
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'DC.Keywords'}):
        rec['keyw'] = re.split(' *, *', meta['content'])
    for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
        rec['link'] = meta['content']
        rec['FFT'] = meta['content']
    rec['auts'] = []
    for td in articlepage.body.find_all('td', attrs = {'class' : 'J_author_EN'}):
        for sup in td.find_all('sup'):
            cont = sup.text.strip()
            if re.search('\d', cont):
                cont = re.sub('^(\d+)', r'; =Aff\1', cont)
                cont = re.sub(',(\d+)', r'; =Aff\1', cont)
                cont = re.sub(',\D+', '', cont)
                sup.replace_with(cont + '; ')
            else:
                sup.replace_with(';')
        authors = re.sub('[,\*]', '; ', td.text)
        authors = re.sub('[ _\s][ _\s]+', ';', authors)
        #print authors
        for aut in re.split(' *; *', authors):
            if re.search('=Aff', aut):
                rec['auts'].append(aut.strip())
            else:
                if len(aut.strip()) > 1:
                    author = re.sub(' ([A-Z])$', r' \1.', aut.strip())
                    author = re.sub(' ([A-Z]) ([A-Z])', r' \1.\2', author)
                    author = re.sub(' ([A-Z]) ([A-Z])', r' \1.\2', author)
                    author = re.sub('([A-Z ]+) (.*)', r'\1, \2', author)
                    rec['auts'].append(author.title())
    for td in articlepage.body.find_all('td', attrs = {'style' : 'line-height:130%'}):
        for sup in td.find_all('sup'):
            if re.search('^\d+$', sup.text):
                cont = sup.text.strip()
                sup.replace_with('; Aff%s= ' % (cont))
        for br in td.find_all('br'):
            br.replace_with(';')
        rec['aff'] = []
        for aff in re.split(' *; *', td.text.strip()):
            if len(aff) > 5:
                rec['aff'].append(aff.strip())
    #print rec
    rec['refs'] = []
    for div in articlepage.body.find_all('div', attrs = {'class' : 'reference_tab_content'}):
        for tr in div.find_all('tr'):
            for a in tr.find_all('a'):
                if a.has_attr('href') and re.search('dx.doi.org', a['href']):
                    a.replace_with(', DOI: %s' % (re.sub('.*dx.doi.org.', '', a['href'])))
            rec['refs'].append([('x', tr.text)])

    recs.append(rec)
jnlfilename = 'nuclst%s.%s' % (rec['vol'], rec['issue'])
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
