# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest African Journal of Mathematical Physics
# FS 2015-12-07
#
#one time job

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

jnlfilename = 'AJMP'

xmlf    = os.path.join(xmldir,jnlfilename+'.xml')



issues = [('http://www.fsr.ac.ma/GNPHE/ajmpVolume10N1-2011/index.htm', 10, 1, 2011, 'http://www.fsr.ac.ma/GNPHE/ajmpVolume10N1-2011/authors.htm'), 
          ('http://www.fsr.ac.ma/GNPHE/ajmpVolume9N1-2010/index.htm', 9, 1, 2010, 'http://www.fsr.ac.ma/GNPHE/ajmpVolume9N1-2010/authors.htm'), 
          ('http://www.fsr.ac.ma/GNPHE/ajmpVolume8N1-2010/index.htm', 8, 1, 2010, 'http://www.fsr.ac.ma/GNPHE/ajmpVolume8N1-2010/authors.htm'),
          ('http://www.fsr.ac.ma/GNPHE/ajmpVolume7N1-2009/index.htm', 7, 1, 2009, 'http://www.fsr.ac.ma/GNPHE/ajmpVolume7N1-2009/authors.htm')]
#          ('http://www.fsr.ac.ma/GNPHE/ajmpVolume6N1-2008/index.htm', 6, 1, 2008, 'http://www.fsr.ac.ma/GNPHE/ajmpVolume6N1-2008/authors.htm'),
#          ('http://www.fsr.ac.ma/GNPHE/ajmpvolume5-2007/index.htm', 5, 1, 2007, 'http://www.fsr.ac.ma/GNPHE/ajmpvolume5-2007/authors.htm'),
#          ('http://www.fsr.ac.ma/GNPHE/ajmpvolume4-2007/index.htm', 4, 1, 2007, 'http://www.fsr.ac.ma/GNPHE/ajmpvolume4-2007/authors.htm'),
#          ('http://www.fsr.ac.ma/GNPHE/ajmpvolume3-2006/index.htm', 3, 1, 2006, 'http://www.fsr.ac.ma/GNPHE/ajmpvolume3-2006/authors.htm'),
#          ('http://www.fsr.ac.ma/GNPHE/ajmpVolume2N2-2005/index.htm', 2, 2, 2005, 'http://www.fsr.ac.ma/GNPHE/ajmpVolume2N2-2005/authors.htm'),
#          ('http://www.fsr.ac.ma/GNPHE/ajmpvolume2N1-2005/index.htm', 2, 1, 2005, 'http://www.fsr.ac.ma/GNPHE/ajmpvolume2N1-2005/authors.htm'),
#          ('http://www.fsr.ac.ma/GNPHE/ajmpvolume1N2-2004/index.htm', 1, 2, 2004, 'http://www.fsr.ac.ma/GNPHE/ajmpvolume1N2-2004/authors.htm'),
#          ('http://www.fsr.ac.ma/GNPHE/ajmpvolume1N1-2004/index.htm', 1, 1, 2004, 'http://www.fsr.ac.ma/GNPHE/ajmpvolume1N1-2004/authors.htm')]

publisher = 'GNPHE'

recs = []
for issue in issues:
    toc1 = BeautifulSoup(urllib2.urlopen(issue[0]))
    toc2 = BeautifulSoup(urllib2.urlopen(issue[4]))
    print '++++++++++++++++++++'
    print issue[0]
    pages = []
    for table in toc2.body.find_all('table', attrs = {'width' : '90%'}):
        for div in table.find_all('div'):
            pages.append(re.sub('[\r\n\t]', '', div.text).strip())
    print pages
    links = []
    for a in toc1.body.find_all('a'):
        if a.text.strip() == 'pdf':
            link = re.sub('index.htm', a['href'], issue[0])
            links.append(link)
    print links
    counter = 0
    tc = 'P'
    for blockquote in toc1.body.find_all('blockquote'):    
        for strong in blockquote.find_all('strong'):
            if strong.text.strip() == 'Review Article':
                tc = 'R'
            elif strong.text.strip() == 'Research Papers':
                tc = 'P'
        rec = {'tc' : tc, 'jnl' : 'Afr.J.Math.Phys.', 'vol' : str(issue[1]), 
               'iss' : str(issue[2]), 'year' : str(issue[3]), 'aut' : []}
        for div in blockquote.find_all('div', attrs = {'align' : 'left'}):
            divtext = re.sub('  +', ' ', re.sub('[\r\n\t]', '', div.text).strip())
            if re.search('^Title:', divtext):
                rec['tit'] = re.sub('^Title: *', '', divtext)
                print ' - ', rec['tit']
            elif re.search('^Authors?:', divtext):
                authors = re.sub('^Authors?: *', '', divtext)
                authors = re.sub(' and ', ', ', authors)
                for author in re.split(', ', authors):
                    rec['aut'].append(re.sub('(.*) (.*)', r'\2, \1', author))
        for div in blockquote.find_all('div', attrs = {'align' : 'justify'}):
            rec['abs'] = re.sub('  +', ' ', re.sub('[\r\n\t]', '', re.sub('[\r\n\t]', '', div.text).strip()))
        if not rec.has_key('tit'):
            for font in blockquote.find_all('font'):
                divtext = re.sub('  +', ' ', re.sub('[\r\n\t]', '', font.text).strip())
                if re.search('^Title:', divtext):
                    rec['tit'] = re.sub('^Title: *', '', divtext)
                    print ' . ', rec['tit']
                elif re.search('^Authors?:', divtext):
                    authors = re.sub('^Authors?: *', '', divtext)
                    authors = re.sub(' and ', ', ', authors)
                    for author in re.split(', ', authors):
                        rec['aut'].append(re.sub('(.*) (.*)', r'\2, \1', author))
            blocktext = re.sub('[\r\n\t]', '', blockquote.text).strip()
            if re.search('Abstract:', blocktext):
                rec['abs'] = re.sub('  +', ' ', re.sub('[\r\n\t]', '', re.sub('.*Abstract: ', '', blocktext))).strip()
        if rec.has_key('tit'):
            if rec['tit'] == 'Optimisation Topologique d\'une Structure Elastique via la Décomposition du Domaines' and counter ==2:
                continue
            if rec['tit'] == 'Stability of Some Solitonic Systems with Real Scalar Fields' and counter ==2:
                continue
            print rec
            print '   ->', counter
            rec['p1'] = re.sub('\-.*', '', pages[counter])
            rec['p2'] = re.sub('.*\-', '', pages[counter])
            rec['FFT'] = links[counter]
            recs.append(rec)
            print rec
            counter += 1
    print len(links), len(pages), counter
                
            

    
           

#closing of files and printing
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
 
