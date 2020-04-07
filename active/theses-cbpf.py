# -*- coding: utf-8 -*-
#harvest theses from Rio de Janeiro, CBPF
#FS: 2020-03-26

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
import mechanize

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
pages = 1

publisher = 'Rio de Janeiro, CBPF'

tocurl = 'http://cbpfindex.cbpf.br/index.php?moduleFile=listPublications&pubType=9'
jnlfilename = 'THESES-CBPF-%s' % (stampoftoday)

br = mechanize.Browser()
br.set_handle_robots(False)   # ignore robots
br.set_handle_refresh(False)  # can sometimes hang without this
br.addheaders = [('User-agent', 'Firefox')]
response = br.open(tocurl)

recs = []
for page in range(pages):
    tocpage = BeautifulSoup(response.read())
    print '---{ %i/%i }---' % (page+1, pages)
    for a in tocpage.body.find_all('a', attrs = {'title' : 'Ver detalhes'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : []}        
        rec['link'] = 'http://cbpfindex.cbpf.br/' + a['href']
        rec['doi'] = '20.2000/CBPF/' + re.sub('\D', '', a['href'])
        print '  ', rec['link']
        recs.append(rec)
    #click to next page
    br.form = list(br.forms())[2]
    control = br.form.find_control('start')
    control.readonly = False
    control.value = "%i" % (16*page+32)
    time.sleep(5)
    response = br.submit()
    
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(8)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    #title
    for td in artpage.body.find_all('td', attrs = {'class' : 'pubTitle'}):
        rec['tit'] = td.text.strip()
    for td in artpage.body.find_all('td'):
        parts = re.split(': *', td.text.strip())
        if len(parts) == 2:
            #date
            if re.search('Publica', parts[0]):
                if re.search('\d\d\/\d\d\/\d\d\d\d', parts[1]):
                    rec['date'] = re.sub('.*(\d\d).(\d\d).(\d\d\d\d).*', r'\3-\2-\1', parts[1])
                elif re.search('\d\d\d\d', parts[1]):
                    rec['date'] = re.sub('.*(\d\d\d\d).*', r'\1', parts[1])
            #author
            elif re.search('Aluno', parts[0]):
                rec['autaff'] = [[parts[1].strip(), publisher]]
            #supervisor
            elif re.search('Orientador', parts[0]):
                rec['supervisor'].append([parts[1].strip()])
            #department
            #elif re.search('Institui', parts[0]):
            #    rec['department'] = parts[1].strip()
            #    rec['note'] = [rec['department']]
            #abstract
            elif re.search('Resum', parts[0]):
                rec['abs'] = parts[1].strip()
            #defense date
            elif re.search('Data da defesa', parts[0]):
                if re.search('\d\d\/\d\d\/\d\d\d\d', parts[1]):
                    rec['MARC'] = [('500', [('a', re.sub('.*(\d\d).(\d\d).(\d\d\d\d).*', r'Presented on \3-\2-\1', parts[1]))])]
                elif re.search('\d\d\d\d', parts[1]):
                    rec['MARC'] = [('500', [('a', re.sub('.*(\d\d\d\d).*', r'Presented on \1', parts[1]))])]
    #PDF
    for a in artpage.body.find_all('a'):
        for img in a.find_all('img'):
            if re.search('Download do PDF', a.text):
                rec['hidden'] = 'http://cbpfindex.cbpf.br/' + a['href']


        
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
