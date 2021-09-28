# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Nuclear Physics and Atomic Energy 
# FS 2018-08-30

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'


publisher = 'Institute for Nuclear Research of the National Academy of Sciences of Ukraine'
typecode = 'P'


jnl = 'Nucl.Phys.Atom.Energy'
vol = sys.argv[1]
issue = sys.argv[2]
jnlfilename = 'nuclphysae%s.%s' % (vol, issue)

    
urltrunk = 'http://jnpae.kinr.kiev.ua/%s.%s.html' % (vol, issue)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))


recs = []
note = False
for h3 in tocpage.body.find_all('h3'):
    year = re.sub('.* (\d+)', r'\1', h3.text.strip())
for child in tocpage.body.descendants:
        try:
            child.name
        except:
            continue
        if child.name == 'b':
            note = child.text.strip()
        elif child.name == 'p':
            if child.has_attr('class'):
                if 'title' in child['class']:
                    rec = {'jnl' : jnl, 'vol' : vol, 'issue' : issue, 
                           'note' : [], 'year' : year, 'refs' : [],
                           'tc' : typecode,
                           'licence' : {'statement' :  'CC-BY-NC-4.0'}}
                    for sup in child.find_all('sup'):
                        supcont = sup.text.strip()
                        sup.replace_with('$^{%s}$' % (supcont))
                    for sub in child.find_all('sub'):
                        subcont = sub.text.strip()
                        sub.replace_with('$_{%s}$' % (subcont))
                    # title
                    rec['tit'] = child.text.strip()
                    if note:
                        rec['note'].append(note)
                    # more details
                    for a in child.find_all('a'):
                        rec['artlink'] = 'http://jnpae.kinr.kiev.ua/' + a['href']
                # authors
                elif 'auth' in child['class']:
                    rec['auts'] = re.split(' *, *', child.text.strip())
                elif 'pg' in child['class']:
                    # pdf link
                    for a in child.find_all('a'):
                        if re.search('Full', a.text):
                            rec['FFT'] = 'http://jnpae.kinr.kiev.ua/' + a['href']
                        if re.search('\(ua\)', a.text):
                            rec['language'] = 'Ukrainian'
                        elif re.search('\(ru\)', a.text):
                            rec['language'] = 'Russian'
                        a.replace_with('')
                    # pages
                    pages = re.sub('[\n\t]', '', child.text.strip())
                    rec['p1'] = re.sub('.*?(\d+).*', r'\1', pages)
                    rec['p2'] = re.sub('.*\D(\d+).*', r'\1', pages)
                    if not 'EVENTS AND PERSONALITIES' in rec['note']:
                        recs.append(rec)

i = 0
reabs = re.compile('.*?Abstract: *')
redoi = re.compile('.*doi\.org\/(10.*)')
rekws = re.compile('.*?Keywords: (.*) References:.*')
repub = re.compile('.*Published online: *(\d+\.\d+\.\d+).*')
for rec in recs:
    i += 1
    if not 'artlink' in rec.keys():
        print 'no article page'
        continue
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    # abstract
    for p in artpage.body.find_all('p', attrs = {'align' : 'justify'}):
        ptext = p.text.strip()
        if reabs.search(ptext):
            rec['abs'] = re.sub('\n', ' ', reabs.sub('', ptext))
    alltext = re.sub('[\n\t]', ' ', artpage.body.text)
    # keywords
    if rekws.search(alltext):
        rec['keyw'] = re.split(' *, *', rekws.sub(r'\1', alltext))
    # publication date
    if repub.search(alltext):
        dparts = re.split('\.', repub.sub(r'\1', alltext))
        rec['date'] = '%4i-%02i-%02i' % (int(dparts[2]), int(dparts[1]), int(dparts[0]))
    #references
    refstart = False
    for child in artpage.body.descendants:        
        try:
            child.name
        except:
            continue
        if child.name == 'a':
            # DOI
            if child.has_attr('href') and not 'doi' in rec.keys():
                if redoi.search(child['href']):
                    rec['doi'] = redoi.sub(r'\1', child['href'])
        elif child.name == 'b' and re.search('References', child.text):
            refstart = True
        elif refstart and child.name == 'p':
            for a in child.find_all('a'):
                if a.has_attr('href') and redoi.search(a['href']):
                    rdoi = redoi.sub(r' DOI: \1', a['href'])
                    a.replace_with(rdoi)
            rec['refs'].append([('x', child.text.strip())])
            



                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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
 
