# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest world scientific books
# FS 2018-07-11

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
import time
from bs4 import BeautifulSoup



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'

def tfstrip(x): return x.strip()

typecode = 'P'

publisher = 'World Scientific'
url = sys.argv[1]
jnlfilename = sys.argv[2]
if re.search('worldscibooks',url):
    jnlname = 'BOOK '
if re.search('ijmpcs',url):
    jnlname = 'Int.J.Mod.Phys.Conf.Ser.'
    typecode = 'C'
elif re.search('ijmp',url):
    jnlname = 'Int.J.Mod.Phys.'
elif re.search('mpl',url):
    jnlname = 'Mod.Phys.Lett.'
elif re.search('rast',url):
    jnlname = 'Rev.Accel.Sci.Tech.'
elif re.search('\/ijqi\/',url):
    jnlname = 'Int.J.Quant.Inf.'
elif re.search('\/ijgmmp\/',url):
    jnlname = 'Int.J.Geom.Meth.Mod.Phys.'
elif re.search('^saqmbt', jnlfilename):
    jnlname = 'Ser.Adv.Quant.Many Body Theor.'
    typecode = 'S'
elif re.search('worldscibooks',url):
    jnlname = 'BOOK '
    typecode = 'S'

urltrunk = 'http://www.worldscientific.com'


print "get table of content of %s (%s) ..." % (jnlfilename,url)
if not os.path.isfile("/tmp/%s.toc" % (jnlfilename)):
    os.system("wget -T 300 -t 3 -q -O /tmp/%s.toc %s" % (jnlfilename, url))
inf = open('/tmp/%s.toc' % (jnlfilename), 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()), features="lxml")
inf.close()


note = []
year = False
for div in tocpage.body.find_all('div', attrs = {'class' : 'banner__meta'}):
    for h1 in div.find_all('h1'):
        note.append(h1.text.strip())
    for div2 in div.find_all('div', attrs = {'class' : 'subtitle'}):        
        note.append(div2.text.strip())
    for span in div.find_all('span', attrs = {'class' : 'doi'}):
        note.append(span.text.strip())
for span in tocpage.body.find_all('span', attrs = {'class' : 'cover-date'}):
    if re.search('\d\d\d\d', span.text):
        year = re.sub('.*?(\d\d\d\d).*', r'\1', span.text)



recs = []
typecode = 'P'
for div in tocpage.body.find_all('div', attrs = {'class' : 'issue-item'}):
    rec = {'note' : note, 'jnl' : jnlname, 'autaff' : []}
    if year:
        rec['year'] = year
    #CNUM
    if len(sys.argv) > 3:
        rec['cnum'] = sys.argv[3]
        typecode = 'C'
    for h5 in div.find_all('h5'):
        #title
        rec['tit'] = h5.text.strip()
        #DOI
        for a in h5.find_all('a'):
            rec['artlink'] = 'https://www.worldscientific.com' + a['href']
            rec['doi'] = a['href'][5:]
    #pages 
    for li in div.find_all('li'):
        lit = li.text.strip()
        if re.search(r'(?i)pages', lit):
            p1p2 = re.sub('\D*(\d.*\d).*', r'\1', lit)
            p1p2parts = re.split('\D+', p1p2)
            rec['p1'] = p1p2parts[0]
            if len(p1p2parts) > 1:
                rec['p2'] = p1p2parts[1]
    #vol
    if re.search('ijmpcs',url):
        rec['vol'] = re.sub('.*?(\d+).*',r'\1',url)
    elif re.search('ijmp',url) or re.search('mpl',url):
        rec['vol'] = re.sub('.*?([a-e])\/(\d+).*',r'\1\2',url).upper()
        rec['issue'] = re.sub('.*(\d+).*',r'\1',url)
    elif re.search('rast',url):
        rec['vol'] = re.sub('.*?(\d+).*',r'\1',url)
    elif re.search('ijqi',url):
        rec['vol'] = re.sub('.*?(\d+).*',r'\1',url)
        rec['issue'] = re.sub('.*\/(\d+).*',r'\1',url)
    elif jnlname == 'Ser.Adv.Quant.Many Body Theor.':
        rec['vol'] = re.sub('.*?(\d+)', r'\1', jnlfilename)
    elif jnlname == 'Adv.Ser.Direct.High Energy Phys.':
        rec['vol'] = re.sub('.*?(\d+)', r'\1', jnlfilename)
    else:
        rec['vol'] = ''
    rec['tc'] = typecode
    if not rec['tit'] in ['FRONT MATTER', 'Front Matter', 'Back Matter', 'BACK MATTER']:
        recs.append(rec)






for i in range(len(recs)):
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), recs[i]['artlink'])
    if not os.path.isfile("/tmp/%s.%i" % (jnlfilename, i)):
        os.system("wget -T 300 -t 3 -q -O /tmp/%s.%i %s" % (jnlfilename, i, recs[i]['artlink']))
        time.sleep(3)
    inf = open('/tmp/%s.%i' % (jnlfilename, i), 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()), features="lxml")
    inf.close()

    #author
    for div in artpage.body.find_all('div'):
        if not div.has_attr('class'):
            continue
        if 'accordion-tabbed__tab-mobile' in div['class'] or \
                'accordion-tabbed__tab-mobile accordion__closed' in div['class']:
            autaff = []
            #first clean affiliation from links
            for p in div.find_all('p'):
                for a in p.find_all('a'):
                    at = a.text
                    a.replace_with(at)
            for div2 in div.find_all('div', attrs = {'class' : 'bottom-info'}):
                div2.replace_with('')
                for a in div.find_all('a'):
                    if a.has_attr('href') and re.search('http', a['href']):
                        continue
                    at = a.text.strip()
                if re.search(r'(?i)COLLABORATION', at):
                    at = re.sub(r'(?i)FOR THE ', '', at)
                    at = re.sub(r'(?i)ON BEHALF OF THE ', '', at)
                    at = re.sub(r'(?i) COLLABORATION.*', '', at)
                    recs[i]['col'] = at
                    continue
                elif re.search('E\-mail Address', at):
                    continue
                else:                
                    autaff.append(at)
            if not autaff:
                for a in div.find_all('a', attrs = {'class' : 'author-name'}):
                    at = a.text.strip()
                if re.search(r'(?i)COLLABORATION', at):
                    at = re.sub(r'(?i)FOR THE ', '', at)
                    at = re.sub(r'(?i)ON BEHALF OF THE ', '', at)
                    at = re.sub(r'(?i) COLLABORATION.*', '', at)
                    recs[i]['col'] = at
                    continue
                elif re.search('E\-mail Address.*protected', at):
                    continue
                else:                    
                    autaff.append(at)
            if autaff:
                for p in div.find_all('p'):
                    pt = p.text.strip()
                    if len(pt) > 1:
                        if not re.search('E\-mail Address.*protected', pt):
                            autaff.append(pt)
                recs[i]['autaff'].append(autaff)
        
                

    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'NLM_abstract'}):
        for p in div.find_all('p'): 
            recs[i]['abs'] = p.text.strip()
    if not 'abs' in recs[i].keys():
        for div in artpage.body.find_all('div', attrs = {'class' : ['abstractSection', 'abstractInFull']}):
            recs[i]['abs'] = div.text.strip()
    #keywords
    for div in artpage.body.find_all('div', attrs = {'class' : 'hlFld-keywords'}):
        recs[i]['keyw'] = []
        for li in div.find_all('li'):
            recs[i]['keyw'].append(li.text.strip())
    #PACS
    for div in artpage.body.find_all('div'):
        for b in div.find_all('b'):
            divt = div.text.strip()
            if re.search('^PACS: *\d\d\.', divt):
                b.decompose()
                recs[i]['pacs'] = re.split(' *[,;] *', div.text.strip())
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            recs[i]['license'] = {'url' : a['href']}
    #FFT
    if 'license' in recs[i].keys():
        for div in artpage.body.find_all('div', attrs = {'class' : 'section__body'}):
            for a in div.find_all('a'):
                if re.search('PDF download', a.text):
                    recs[i]['FFT'] = urltrunk + a['href']
            
            

    print recs[i].keys()
        









xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
