#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Taylor and Francis
# FS 2016-06-27.

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
import urllib2
import urlparse
from bs4 import BeautifulSoup
import time

import datetime

ejdir = '/afs/desy.de/user/l/library/dok/ejl'
tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

def tfstrip(x): return x.strip()

publisher = 'Taylor and Francis'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]

if   (jnl == 'tnst20'):
    jnlname = 'J.Nucl.Sci.Tech.'
elif (jnl == 'tcph20'):
    jnlname = 'Contemp.Phys.'
elif (jnl == 'tmop20'):
    jnlname = 'J.Mod.Opt.'
elif (jnl == 'gaat20'):
    jnlname = 'Astron.Astrophys.Trans.'
elif (jnl == 'ggaf20'):
    jnlname = 'Geophys.Astrophys.Fluid Dynamics'
elif (jnl == 'gsrn20'):
    jnlname = 'Synchrotron Radiat.News'
elif (jnl == 'tadp20'):
    jnlname = 'Adv.Phys.'
elif (jnl == 'tphm20'):
    jnlname = 'Phil.Mag.'
elif (jnl == 'gnpn20'):
    jnlname = 'Nucl.Phys.News'
elif (jnl == 'tnmp20'):
    jnlname = 'J.Nonlin.Math.Phys.'
elif (jnl == 'tapx20'):
    jnlname = 'Adv.Phys.X'
elif (jnl == 'uexm20'):
    jnlname = 'Exper.Math.'
elif (jnl == 'gitr20'):
    jnlname = 'Integral Transform.Spec.Funct.'
elif (jnl == 'glma20'):
    jnlname = 'Linear Multilinear Alg.'

if jnl in ['tapx20']:
    jnlfilename = "%s.%s.%s.%s" % (jnl, vol, issue, stampoftoday)
else:
    jnlfilename = "%s.%s.%s" % (jnl, vol, issue)


print 'get table of content from http://www.tandfonline.com/toc/%s/%s/%s' % (jnl, vol, issue)
#page = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('http://www.tandfonline.com/toc/%s/%s/%s' % (jnl, vol, issue)))
if not os.path.isfile('/tmp/tandf_%s' % (jnlfilename)):
    os.system("wget -T 300 -t 3 -q -O /tmp/tandf_%s http://www.tandfonline.com/toc/%s/%s/%s" % (jnlfilename, jnl, vol, issue))
inf = open('/tmp/tandf_%s' % (jnlfilename), 'r')
page = BeautifulSoup(''.join(inf.readlines()))
inf.close()

              
#get year
for div in page.body.find_all('div', attrs = {'class' : 'hd prevNextLink'}):
    year = re.sub('.* ([21]\d\d\d) .*', r'\1', re.sub('\n', ' ', div.text.strip()))


recs = []
inputs = page.body.find_all('input', attrs = {'name' : 'doi'})
tc = 'P'
i = 0
for adoi in page.body.find_all('a'):
    i += 1
    if not adoi.has_attr('href'):
        continue
#    if not re.search('^Full Text', adoi.text):
    if not re.search('^PDF', adoi.text):
        continue
    if jnl == 'tcph20':
        tc = 'IR'
    elif jnl in ['gnpn20', 'gsrn20']:
        tc = ''
    rec = {'jnl' : jnlname, 'tc' : tc, 'vol' : vol, 'issue' : issue, 'autaff' : [], 'note' : []}
    rec['doi'] = re.sub('.*\/(10\..*)', r'\1', adoi['href'])    
    print '%i %s' % (i, rec['doi'])
#    try:
#        apage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('http://www.tandfonline.com/doi/ref/%s' % (rec['doi'])))
#    except:
#        try:
#            print 'try 5 minutes later'
#            time.sleep(300)
#            apage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('http://www.tandfonline.com/doi/ref/%s' % (rec['doi'])))
#        except:
#            print 'try without references'
#            apage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('http://www.tandfonline.com/doi/full/%s' % (rec['doi'])))
    artfilname = '/tmp/tandf_%s_%i' % (jnlfilename, i)
    if not os.path.isfile(artfilname):
        try:
            os.system("wget -T 300 -t 3 -q -O %s http://www.tandfonline.com/doi/ref/%s" % (artfilname, rec['doi']))
        except:
            print 'try without references'
            os.system("wget -T 300 -t 3 -q -O %s http://www.tandfonline.com/doi/full/%s" % (artfilname, rec['doi']))
        time.sleep(10)        
    #inf = open(artfilname)
    inf = codecs.EncodedFile(open(artfilname, mode='rb'), "utf8")
    apage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    #cnum
    if len(sys.argv) > 4:
        rec['tc'] = 'C'
        rec['cnum'] = sys.argv[4]
    for meta in apage.head.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'dc.Title':
                rec['tit'] = meta['content']
            #abstract
            elif meta['name'] == 'dc.Description':
                rec['abs'] = re.sub('^ABSTRACT', '', meta['content'])
            #date
            elif meta['name'] == 'dc.Date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
                if re.search(',.*,.*,.*,', meta['content']) and len(rec['keyw']) == 1:
                    rec['keyw'] = re.split(',', meta['content'])
    #article type
    for div in apage.body.find_all('div', attrs = {'class' : 'toc-heading'}):
        for h3 in div.find_all('h3'):
            rec['note'].append(h3.text.strip())
        for h2 in div.find_all('h2'):
            rec['note'].append(h3.text.strip())
    #year
    for h2 in apage.body.find_all('h2'):
        if re.search('Volume \d.* \d\d\d\d', h2.text):
            rec['year'] = re.sub('.* (\d\d\d\d).*', r'\1', re.sub('\n', ' ', h2.text.strip()))
    #pdf
    #authors
    for span in apage.body.find_all('div', attrs = {'class' : 'hlFld-ContribAuthor'}):
        for a in span.find_all('a', attrs = {'class' : 'entryAuthor'}):
            aff = ''
            for span2 in a.find_all('span', attrs = {'class' : 'overlay'}):
                aff = re.sub(' *, *', ' - ', span2.text.strip())
                span2.replace_with('')
            autaff = [ re.sub('(.*) (.*)', r'\2, \1', a.text.strip()) ]
            if aff:
                autaff.append(aff)
            rec['autaff'].append(autaff)                
    #pages
    for span in apage.body.find_all('span', attrs = {'class' : 'contentItemPageRange'}):
        pages = re.sub('[Pp]ages? *', '', span.text).strip()
        try:
            [rec['p1'], rec['p2']] = re.split('\-', pages)
        except:
            rec['p1'] = re.sub('Article: ', '', pages)

    #references
    for ul in apage.body.find_all('ul', attrs = {'class' : 'references numeric-ordered-list'}):
        rec['refs'] = []
        for li in ul.find_all('li'):
            rdoi = ''
            for a in li.find_all('a'):                
                if a.has_attr('href'):
                    if re.search('Cross[rR]ef', a.text):
                        rdoi = re.sub('.*=', ', DOI: ', a['href'])
                        a.replace_with('')
                    elif re.search('Web of Science', a.text):
                        if not rdoi:
                            rdoi = re.sub('.*doi=', ', DOI: ', a['href'])
                            rdoi = re.sub('\&.*', '', rdoi)
                        a.replace_with('')
                    elif re.search('(PubMed|Taylor|Google Scholar)', a.text):
                        a.replace_with('')                        
            lit = re.sub('\. *$', '', li.text)
            lit = re.sub('\xa0', ' ', li.text)
            lit = re.sub('[\n\t]', ' ', lit)
            lit = re.sub(',\s*,', ',', lit)
            lit = re.sub(',\s*,', ',', lit)
            lit = re.sub('; *(\d)', r', \1', lit)
            if rdoi:
                rdoi = re.sub('%2F', '/', rdoi)
                rdoi = re.sub('%28', '(', rdoi)
                rdoi = re.sub('%29', ')', rdoi)
                rec['refs'].append([('x',  re.sub(',\s*,', ',', lit + rdoi))])
            else:
                rec['refs'].append([('x', lit)])
    if rec.has_key('note') and rec['note'] and rec['note'][0] in ['Book reviews', 'Essay reviews']:
        continue
    elif rec.has_key('note') and rec['note'] and rec['note'][0] in ['Review Article']:
        rec['tc'] += 'R'
        recs.append(rec)
    else:
        recs.append(rec)





xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(open(xmlf,mode='wb'),"utf8")
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()






