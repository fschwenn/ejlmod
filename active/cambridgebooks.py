# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Cambridge-journals
# FS 2015-02-12


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
import time
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'Cambridge University Press'

toclink = sys.argv[1]

        
try:
    #toc = BeautifulSoup(urllib2.urlopen(toclink))
    toc = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
except:
    print "retry in 180 seconds"
    time.sleep(180)
    #toc = BeautifulSoup(urllib2.urlopen(toclink))
    toc = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
recs = []

rec = {'tc' : 'B', 'jnl' : 'BOOK', 'isbns' : [], 'autaff' : [], 'abs' : '', 'link' : toclink}
#title
for h1 in toc.body.find_all('h1', attrs = {'itemprop' : 'name'}):
    rec['tit'] = h1.text
for ul in toc.body.find_all('ul', attrs = {'class' : 'productDetails'}):
    #date
    for meta in ul.find_all('meta', attrs = {'itemprop' : 'datePublished'}):
        rec['date'] = meta['content']
        #rec['year'] = rec['date'][:4]
    #ISBN
    for span in ul.find_all('span', attrs = {'itemprop' : 'bookFormat'}):
        bookFormat = span.text
    for span in ul.find_all('span', attrs = {'itemprop' : 'isbn'}):
        isbn = span.text
        rec['doi'] = '30.3000/cambridge' + isbn
        if bookFormat in ['Hardback', 'Paperback']:
            rec['isbns'].append([('a', isbn), ('b', 'Print')])
        elif bookFormat in ['Adobe eBook Reader']:
            rec['isbns'].append([('a', isbn), ('b', 'eBook')])
        else:
            rec['isbns'].append([('a', isbn), ('b', bookFormat)])
#other formats
for h4 in toc.body.find_all('h4', attrs = {'class' : 'otherFormats'}):
    for a in h4.find_all('a'):
        otherformattoclink = re.sub('\?.*', '', toclink) + a['href']
        otherformattoc = BeautifulSoup(urllib2.urlopen(otherformattoclink))
        for ul in otherformattoc.body.find_all('ul', attrs = {'class' : 'productDetails'}):
            #ISBN
            for span in ul.find_all('span', attrs = {'itemprop' : 'bookFormat'}):
                bookFormat = span.text
                for span in ul.find_all('span', attrs = {'itemprop' : 'isbn'}):
                    isbn = span.text
                    if bookFormat in ['Hardback', 'Paperback']:
                        rec['isbns'].append([('a', isbn), ('b', 'Print')])
                    elif bookFormat in ['Adobe eBook Reader']:
                        rec['isbns'].append([('a', isbn), ('b', 'eBook')])
                    else:
                        rec['isbns'].append([('a', isbn), ('b', bookFormat)])
#authors:
#for li in toc.body.find_all('li', attrs = {'itemprop' : 'author'}):
#    for a in li.find_all('a', attrs = {'href' : '#bookPeople'}):
#        for span in a.find_all('span', attrs = {'itemprop' : 'name'}):
#            name = span.text
#            autaff = [ re.sub('(.*) (.*)', r'\2, \1', name) ]
#    for span in li.find_all('span', attrs = {'itemprop' : 'affiliation'}):
#        autaff.append(span.text)
#    rec['autaff'].append(autaff)
autaff = []
for li in toc.body.find_all('li', attrs = {'id' : 'authorsTab'}):
    for tag in li.find_all():
        if tag.name == 'strong':
            if len(autaff) > 0:
                rec['autaff'].append(autaff)
            autaff = [ re.sub('(.*) (.*)', r'\2, \1', tag.text) ]
        elif tag.name == 'em':
            autaff.append(tag.text)
rec['autaff'].append(autaff)
#abstract
for li in toc.body.find_all('li', attrs = {'id' : 'descriptionTab'}):
    for p in li.find_all('p'):
        rec['abs'] += p.text
        break
#pages
for span in toc.body.find_all('span', attrs = {'itemprop' : 'numberOfPages'}):
        rec['pages'] = span.text

recs.append(rec)


#print recs

jnlfilename = 'CambridgeBook' + isbn + re.sub('[ ,\.,:;\?!\-]', '', rec['tit'])

print jnlfilename




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
