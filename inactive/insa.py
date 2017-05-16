# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Indian National Science Academy
# FS 2015-06-25

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
def tfstrip(x): return x.strip()
def fsunwrap(tag):
    try: 
        for em in tag.find_all('em'):
            cont = em.string
            em.replace_with(cont)
    except:
        print 'fsunwrap-em-problem'
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

publisher = 'Indian National Science Academy'
abstrunk = 'http://insa.nic.in/UI/Abstract.aspx?Aid='
link = sys.argv[1]
vol = sys.argv[2]
year = sys.argv[3]
iss = sys.argv[4]
if len(sys.argv) > 5:
    cnum = sys.argv[5]


jnlfilename = 'pinsa'+vol+'.'+iss
jnlname = 'Proc.Indian Natl.Sci.Acad.'

toc = BeautifulSoup(urllib2.urlopen(link))


typecode = 'R'
note = ''
recs = []

doihash = {}
kwshash = {}
kws = 'blank'
for meta in toc.head.find_all('meta'):
    if meta.attrs.has_key('name'):
        if meta['name'] == 'Citation_Article_Title':
            title = meta['content'].strip()
        elif meta['name'] == 'Citation_Author':
            author = meta['content']
        elif meta['name'] == 'Citation_DOI_Number':
            doi = meta['content']
        elif meta['name'] == 'Citation_Keyword':
            kws = meta['content']
        elif meta['name'] == 'Citation_Year':
            doihash[title] = doi
            if kws != 'blank':
                kwshash[title] = kws
            kws = 'blank'

#doihash['Soft and hard interactions in proton-proton collisions at LHC energies'] = '10.16943/ptinsa/2015/v81i1/48071'

for div in toc.body.find_all('div', attrs={'class' : 'row'}):
    rec = {'issue' : iss, 'vol' : vol, 'jnl' : jnlname, 'note' : [], 'year' : year, 'tc' : typecode}
    if len(sys.argv) > 5:
        rec['cnum'] = cnum
    for div2 in div.find_all('div', attrs={'class' : 'question col-xs-11'}):
        for a in div2.find_all('a'):
            rec['FFT'] = re.sub('^\.\.', 'http://insa.nic.in', a['href'])
            rec['link'] = re.sub('^\.\.', 'http://insa.nic.in', a['href'])
            rec['tit'] = a.text.strip()
            if doihash.has_key(rec['tit']):
                rec['doi'] = doihash[rec['tit']]
            else:
                print 'NO DOI FOR', rec['tit']
            if kwshash.has_key(rec['tit']):
                rec['kw'] = re.split(' *, *', kwshash[rec['tit']])
    for div2 in div.find_all('div', attrs={'class' : 'author col-xs-12'}):
        for a in div2.find_all('a', attrs={'href' : '#'}):
            abslink = abstrunk + re.sub('.*\((\d*)\).*', r'\1', a['onclick'])
            abstract = BeautifulSoup(urllib2.urlopen(abslink))
            for span in abstract.body.find_all('span', attrs={'id' : 'lblAbstract'}):
                rec['abs'] = span.text
            print abslink
        text = div2.text
        #print text
        author = re.sub(' *Abstract.*', '', text)
        author = re.sub('^([A-Z]) ', r'\1. ', author)
        author = re.sub(' ([A-Z]) ', r' \1. ', author)
        author = re.sub('^([A-Z])([A-Z]) ', r'\1.\2. ', author)
        rec['auts'] = [ re.sub('(.*) (.*)', r'\2, \1', author) ]
        if re.search('Abstract.*PP', text):
            pagerange = re.sub('.*PP. *', '', text)
            rec['p1'] = re.sub('\-.*', '', pagerange)
            rec['p2'] = re.sub('.*\-', '', pagerange)
        else:
            rec['p1'] = re.sub('.*_(.*).pdf', r'\1', rec['FFT'])
    if rec.has_key('tit'):
        recs.append(rec)


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
