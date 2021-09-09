# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest PoS
# FS 2019-06-03


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

nr = sys.argv[1]
vol = sys.argv[2]
year = sys.argv[3]

htmlentity = re.compile(r'&#x.*?;')
def lam(x):                                                
    x  = x.group()
    return unichr(int(x[3:-1], 16))
def validxml(string):
    if type(string) == type(()):
        return tuple([validxml(part) for part in string])
    elif type(string) == type([]):
        return [validxml(part) for part in string]
    else:
        #print '--->',string
        string = htmlentity.sub(lam, string)
        string = re.sub('&','&amp;',string)
        string = re.sub('>','&gt;',string)
        string = re.sub('<','&lt;',string)
        string = re.sub('"','&quot;',string)
        string = re.sub('\'','&apos;',string)
        return re.sub('  +', ' ', string)


xmldir = os.path.join('/afs/desy.de/group/library/preprints/incoming', vol)

if not os.path.isdir(xmldir):
    os.system('mkdir %s' % (xmldir))

tocurl = 'https://pos.sissa.it/%s/' % (nr)
tocpage = BeautifulSoup(urllib2.urlopen(tocurl))

note = False
for tr in tocpage.body.find_all('tr'):
    print tr.text
    if tr.has_attr('class'):
        note = tr.text.strip()
        print '===[ %s ]===' % (note)
    arturl = False
    rec = {'540  ' : [[('a', 'CC-BY-NC-ND-4.0')]],
           '980  ' : [[('a', 'ConferencePaper')], [('a', 'HEP')]]}
    if len(sys.argv) > 4:
        rec['cnum'] = sys.argv[4]
    for span in tr.find_all('span', attrs = {'class' : 'contrib_title'}):
        rec['245  '] = [[('a', span.text.strip())]]
    for span in tr.find_all('span', attrs = {'class' : 'contrib_code'}):
        for a in span.find_all('a'):
            arturl = 'https://pos.sissa.it' + a['href']
            rec['8564 '] = [[('u', arturl + 'pdf')]]
            rec['FFT  '] = [[('a', arturl + 'pdf'),
                            ('t', 'PoS'),
                            ('d', 'Fulltext')]]
            #if note: rec['599  '] = [[('a', note)]]
            if note: rec['595  '] = [[('a', note)]]
            print arturl
            p1 = re.sub('.*\/(\d+).*', r'\1',  a['href'])
            rec['773  '] = [[('c', p1), ('y', year), ('v', vol), ('p', 'PoS')]]
    if not arturl:
        continue
    artpage = BeautifulSoup(urllib2.urlopen(arturl))
    auts = '100  '
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_author':
                if re.search('behalf of', meta['content']):
                    col = re.sub('.*behalf of ', '', meta['content'])
                    col = re.sub('^the ', '', col)
                    col = re.sub(' [Cc]ollaboration,?$', '', col)
                    rec['710  '] = [[('g', col)]]
                elif auts in rec.keys():
                    rec[auts].append([('a', meta['content'])])
                else:
                    rec[auts] = [[('a', meta['content'])]]
                    auts = '700  '
            elif meta['name'] == 'citation_publication_date':
                rec['260  '] = [[('c', meta['content'])]]
            elif meta['name'] == 'citation_doi':
                rec['0247 '] = [[('a', meta['content']), ('2', 'DOI')]]
            elif meta['name'] == 'citation_abstract':
                rec['520  '] = [[('a', meta['content'])]]
    if not '0247 ' in rec.keys():
        rec['0247 '] = [[('a', '10.22323/1.%s.%04i' % (nr, int(p1))), ('2', 'DOI')]]
    ouf = codecs.EncodedFile(codecs.open('%s/%s.xml' % (xmldir, p1), mode='wb'), 'utf8')
    ouf.write('<collection>\n')
    ouf.write(' <record>\n')
    print rec.keys()
    for marc in rec.keys():
        #print marc
        for entry in rec[marc]:
            #print entry
            ouf.write('  <datafield tag="%s" ind1="%s" ind2="%s">\n' % (marc[:3], marc[3], marc[4]))
            for subentry in entry:
                try:
                    ouf.write('   <subfield code="%s">%s</subfield>\n' % (subentry[0], validxml(subentry[1])))
                except:
                    ouf.write('   <subfield code="%s">%s</subfield>\n' % (subentry[0], validxml(unicode(subentry[1].encode('ascii', 'ignore'), 'utf-8'))))
            ouf.write('  </datafield>\n')
    ouf.write(' </record>\n')
    ouf.write('</collection>\n')
    ouf.close()
