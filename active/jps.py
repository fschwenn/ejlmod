# -*- coding: UTF-8 -*-
##!/usr/bin/python
#program to harvest journals of the Physical Society of Japan
# FS 2015-02-20

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
#import cookielib
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
jnl = sys.argv[1]
publisher = 'Physical Society of Japan'
urltrunc = 'http://journals.jps.jp'
if jnl == 'jpsj':
    jnlname = 'J.Phys.Soc.Jap.'
    vol = sys.argv[2]
    issue = sys.argv[3]
    year = sys.argv[4]
    jnlfilename = jnl+vol+'.'+issue
    toclink = '%s/toc/%s/%s/%s/%s' % (urltrunc, jnl, year, vol, issue)
    tc = 'P'
else:
    jnlname = 'JPS Conf.Proc.'
    volname = sys.argv[2]
    jnlfilename = 'jpsjcp.%s' % (volname)
    toclink = '%s/doi/book/10.7566/%s'  % (urltrunc, volname)
    tc = 'C'    

def fsunwrap(tag):
    try: 
        for i in tag.find_all('i'):
            cont = i.string
            i.replace_with(cont)
    except:
        print 'fsunwrap-i-problem'
    try: 
        for b in tag.find_all('b'):
            cont = b.string
            b.replace_with(cont)
    except:
        print 'fsunwrap-b-problem'
    try: 
        for sup in tag.find_all('sup'):
            cont = sup.string
            sup.replace_with('^'+cont)
    except:
        print 'fsunwrap-sup-problem'
    try: 
        for sub in tag.find_all('sub'):
            cont = sub.string
            sub.replace_with('_'+cont)
    except:
        print 'fsunwrap-sub-problem'
    try: 
        for form in tag.find_all('formula',attrs={'formulatype': 'inline'}):
            form.replace_with(' [FORMULA] ')
    except:
        print 'fsunwrap-form-problem'
    return tag



try:
    print toclink
    toc = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
except:
    print "retry '%s' in 180 seconds" % (toclink)
    time.sleep(180)
    toc = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))

#check licence
licenseurl =False
for a in toc.body.find_all('a'):
    if a.has_attr('href') and re.search('creativecommons.org', a['href']):
        licenseurl = a['href']

recs = []
(noteA, noteB) = ('', '')
for tag in toc.body.find_all():
    if tag.name == 'h2' and tag.has_attr('class') and tag['class'] == ['header-bar', 'header-dark-gray', 'no-corner', 'clear', 'subject']:
        noteA = tag.text
        print noteA
    if tag.name == 'h2' and tag.has_attr('class') and tag['class'] == ['title-group', 'level1']:
        noteB = tag.text
        print noteB
    elif tag.name == 'div' and tag.has_attr('class') and tag['class'] == ['item', 'clearfix']:
        rec = {'jnl' : jnlname, 'tc' : tc, 'note' : [], 'auts' : [], 'aff' : [], 'refs' : []}
        if noteA != '': rec['note'].append(noteA)
        if noteB != '': rec['note'].append(noteB)
        for span in tag.find_all('span', attrs = {'class' : 'hlFld-Title'}):
            rec['tit'] = span.text
        for inp in tag.find_all('input', attrs = {'name' : 'doi'}):
            rec['doi'] = inp['value']
            abslink = '%s/doi/abs/%s' % (urltrunc, rec['doi'])
            reflink = '%s/doi/ref/%s' % (urltrunc, rec['doi'])
            #pbn
            if jnl == 'jpsj':
                rec['vol'] = vol
                rec['issue'] = issue
                rec['year'] = year
            else:
                rec['vol'] = re.sub('.*\/.*?\.(\d+)\..*', r'\1', rec['doi'])
                if len(sys.argv) > 3:
                    rec['cnum'] = sys.argv[3]
                    if licenseurl:
                        rec['licence'] = {'url' : licenseurl}
                        rec['FFT'] = 'http://journals.jps.jp/doi/pdf/%s' % (rec['doi'])
                    elif len(sys.argv) > 4:
                        rec['licence'] = {'statement' : sys.argv[4]}
                        rec['FFT'] = 'http://journals.jps.jp/doi/pdf/%s' % (rec['doi'])
            rec['p1'] = re.sub('.*\.', '', rec['doi'])\
            #check abstract page
            try:
                time.sleep(23)
                print abslink
                abs = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(abslink))
            except:
                print "retry '%s' in 180 seconds" % (abslink)
                time.sleep(180)
                abs = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(abslink))
            #abstract
            for div in abs.body.find_all('div', attrs = {'class' : 'NLM_abstract'}):
                for p in div.find_all('p'):
                    rec['abs'] = fsunwrap(p).get_text()
            if not rec.has_key('abs'):
                for div in abs.body.find_all('div', attrs = {'class' : 'abstractSection'}):
                    for p in div.find_all('p'):
                        rec['abs'] = fsunwrap(p).get_text()
            #pages
            for div in abs.body.find_all('div', attrs = {'class' : 'chapterHeader'}):
                if re.search('\d page', div.text):
                    rec['pages'] = re.sub('.*\[(\d+) page.*',  r'\1', re.sub('[\r\n]', '', div.text))
                if jnlname == 'JPS Conf.Proc.':
                    rec['year'] = re.sub('.*\((\d\d\d\d)\).*',  r'\1', re.sub('[\r\n]', '', div.text))
            #authors
            for div in abs.body.find_all('div', attrs = {'class' : 'authors'}):
                for tag in div.find_all():
                    if tag.name == 'a' and tag.has_attr('class'):
                        if  tag['class'] == ['entryAuthor']:
                            rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', tag.text.strip()))
                        elif tag['class'] == ['ref', 'aff']:
                            for sup in tag.find_all('sup'):
                                rec['auts'].append('=Aff'+sup.text)
            #affiliations
            for span in abs.body.find_all(attrs = {'class' : 'NLM_aff'}):
                for sup in span.find_all('sup'):
                    sup.replace_with('Aff'+sup.string+'= ')
                rec['aff'].append(span.text.strip())
            #licence
            for licence in abs.body.find_all('license-p'):
                for a in licence.find_all('a'):
                    if re.search('Creative Commons', a.text):
                        rec['licence'] = {'url' : a['href']}
            if jnl == 'jpsjcp':
                rec['licence'] = {'url' : 'http://creativecommons.org/licenses/by/4.0/'}
                rec['FFT'] = 'http://journals.jps.jp/doi/pdf/%s' % (rec['doi'])
            #references
            #if jnl == 'jpsj':
            if True:
                try:
                    print reflink
                    time.sleep(11)
                    ref = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(reflink))
                except:
                    print "retry '%s' in 180 seconds" % (reflink)
                    time.sleep(180)
                    ref = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(reflink))
                for li in ref.find_all('li'):                
                    if li.has_attr('id'):
                        iref = [('o', li['id'])]
                        for script in li.find_all('script', attrs = {'type' : 'text/javascript'}):
                            #javascript = re.split(',', script.text.strip())
                            #if javascript[0] == 'genRefLink(16':
                            #    idoi = re.sub('.*?(10\..*?)\'.*', r'\1', javascript[2])
                            #    idoi = re.sub('%2F', '/', idoi)
                            #    iref.append(('a', idoi))
                            script.replace_with('')
                        if len(iref) == 1:
                            iref= [('x', li.text.strip())]
                        rec['refs'].append(iref)
            else:
                rec['FFT'] = 'http://journals.jps.jp/doi/pdf/%s' % (rec['doi'])

        print rec
        recs.append(rec)



xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
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
