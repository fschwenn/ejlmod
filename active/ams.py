# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest http://www.ams.org
# FS 2016-07-22

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
import datetime
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'




jrnid = sys.argv[1]
year = sys.argv[2]
jnlfilename = 'ams_%s%s' % (jrnid, year)
(vol, iss) = ('0', '0')
if len(sys.argv) > 3:
    vol = sys.argv[3]
    jnlfilename += '.%s' % (vol)
    if len(sys.argv) > 4:
        iss = sys.argv[4]
        jnlfilename += '.%s' % (iss)
    


jnldict = {'ecgd' : {'tit' : 'Conform.Geom.Dyn.',
                     'link' : 'home-%s.html' % (year),
                     'oa' : True},
           'jams' : {'tit' : 'J.Am.Math.Soc.',
                     'link' : '%s-%s-%02i/home.html' % (year, vol, int(iss)),
                     'embargo' : 5}, 
           'mcom' : {'tit' : 'Math.Comput.',
                     'link' : '%s-%s-%s/home.html' % (year, vol, iss),
                     'embargo' : 5}, 
#           'memoirs' : {'tit' : 'Mem.Am.Math.Soc.',
           'proc' : {'tit' : 'Proc.Am.Math.Soc.',
                     'link' : '%s-%s-%02i/home.html' % (year, vol, int(iss)),
                     'embargo' : 5}, 
           'bproc' : {'tit' : 'Proc.Am.Math.Soc.Ser.B',
                      'link' : 'home-%s.html' % (year),
                      'oa' : True},
           'ert' : {'tit' : 'Represent.Theory',
                      'link' : 'home-%s.html' % (year),
                      'oa' : True},
           'tran' : {'tit' : 'Trans.Am.Math.Soc.',
                     'link' : '%s-%s-%02i/home.html' % (year, vol, int(iss)),
                     'embargo' : 5}, 
           'btran' : {'tit' : 'Trans.Am.Math.Soc.Ser.B',
                      'link' : 'home-%s.html' % (year),
                      'oa' : True},
           #member journals
           #          '' : {'tit' : 'Not.Amer.Math.Soc.',
           'bull' : {'tit' : 'Bull.Am.Math.Soc.',
                     'link' : '%s-%s-%02i/home.html' % (year, vol, int(iss)),
                     'oa' : True}, 
           #           '' : {'tit' : 'Abstracts Amer.Math.Soc.',
           #translation journals
           'spmj' : {'tit' : 'St.Petersburg Math.J.',
                     'link' : '%s-%s-%02i/home.html' % (year, vol, int(iss)),
                     'embargo' : 5},
           'tpms' : {'tit' : 'Theor.Probab.Math.Stat.',
                     'link' : '%s-%s-00/home.html' % (year, vol),
                     'oa' : True}, 
           'mosc' : {'tit' : 'Trans.Moscow Math.Soc.',
                     'link' : '%s-%s-00/home.html' % (year, vol),
                     'embargo' : 6},
           #distributed journals
           'qam' : {'tit' : 'Q.Appl.Math.',
                    'link' : '%s-%s-%02i/home.html' % (year, vol, int(iss)),
                    'oa' : False}, 
           #           'mmj' : {'tit' : 'Moscow Math.J.',
           #           'jrms' : {'tit' : 'Ramanujan J.',
           #           '' : {'tit' : 'Asterisque',
           #           '' : {'tit' : 'Bull.Soc.Math.Fr.',
           #           '' : {'tit' : 'Mem.Soc.Math.France',
           #           'jot' : {'tit' : 'J.Operator Theor.',
           'jag' : {'tit' : 'J.Alg.Geom.',
                     'link' : '%s-%s-%02i/home.html' % (year, vol, int(iss)),
                     'oa' : False},}
#           '' : {'tit' : 'Annales Sci.Ecole Norm.Sup.',


#bad cerificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


#check embargo time
if jnldict[jrnid].has_key('embargo'):
    now = datetime.datetime.now()
    if now.year - int(year) > jnldict[jrnid]['embargo']:
        jnldict[jrnid]['oa'] = True

publisher = 'AMS'

tocurl = 'http://www.ams.org/journals/%s/%s' % (jrnid, jnldict[jrnid]['link'])
print tocurl
tocpage = BeautifulSoup(urllib2.urlopen(tocurl, context=ctx))



artlinks = []
for a in tocpage.body.find_all('a'):
    if a.has_attr('href') and re.search('article information', a.text):
        artlinks.append(re.sub('^(.*\/).*', r'\1', tocurl) + a['href'])


print artlinks 


recs = []
for artlink in artlinks:
    try:
        articlepage = BeautifulSoup(urllib2.urlopen(artlink, context=ctx))
        time.sleep(10)
    except:
        print " - sleep -"
        time.sleep(300)
        articlepage = BeautifulSoup(urllib2.urlopen(artlink, context=ctx))
    rec = {'jnl' : jnldict[jrnid]['tit'], 'tc' : 'P', 'year' : year, 
           'autaff' : [], 'link' : artlink}
    if jrnid == 'spmj':
        rec['note'] = [ 'translation of "Alg.Anal." ']
    for meta in articlepage.head.find_all('meta'):
        if meta.has_attr('name'):
            #pdf
            if meta['name'] == 'citation_pdf_url':
                rec['link'] = meta['content']
                if jnldict[jrnid].has_key('oa') and jnldict[jrnid]['oa']:
                    rec['FFT'] = meta['content']
            #date
            elif meta['name'] == 'citation_online_date':
                rec['date'] = re.sub('\/', '-', meta['content'])
            #authors
            elif 'citation_author' == meta['name']:
                rec['autaff'].append([meta['content']])
            elif 'citation_author_institution' == meta['name']:
                if len(rec['autaff']) > 0:
                    rec['autaff'][-1].append(meta['content'])                  
            #pbn
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content']
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #doi
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                if rec.has_key('keyw'):
                    rec['keyw'].append(meta['content'])
                else:
                    rec['keyw'] = [ meta['content'] ]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #
            elif meta['name'] == '':
                rec[''] = meta['content']
    #abstract
    for p in articlepage.body.find_all('p'):
        for a in p.find_all('a', attrs = {'name' : 'Abstract'}):
            rec['abs'] = re.sub(' *Abstract: *', '', p.text.strip())
    #references
    rec['refs'] = []
    for span in articlepage.body.find_all('span', attrs = {'class' : 'references'}):
        for dd in span.find_all('dd'):
            rec['refs'].append([('x', dd.text)])
    print rec
    recs.append(rec)


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
