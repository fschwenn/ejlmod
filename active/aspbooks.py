# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest OUP-journals
# FS 2015-01-26

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
#import urllib2
#import urlparse
import time
#from bs4 import BeautifulSoup


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'Astronomical Society of the Pacific'
bookid = sys.argv[1]

jnlfilename = 'aspcs%s' % (bookid)
if len(sys.argv) > 2:
    jnlfilename += '.' + sys.argv[2] 
jnlname = 'ASP Conf.Ser.'


urltrunk = "http://aspbooks.org/a/volumes"

if not os.path.isfile(tmpdir+"/"+jnlfilename+".toc"):
    print "%s/table_of_contents/?book_id=%s" % (urltrunk,bookid)
    os.system('lynx -source "%s/table_of_contents/?book_id=%s" > %s/%s.toc' % (urltrunk,bookid,tmpdir,jnlfilename))

print "read table of contents..."
tocfil = open(tmpdir+"/"+jnlfilename+".toc",'r')
articleIDs = []




typecode = 'C'
note = ''
recs = []
toclines = ''.join(map(tfstrip,tocfil.readlines()))
for line in  re.split('<tr', toclines):
    #print line
    if re.search('>Volume:<', line):
        vol = re.sub('.*Volume.*?<span.*?>(\d+)<.*', r'\1', line.strip())
    if re.search('>Year:<', line):
        year = re.sub('.*Year.*?<span.*?>(\d+)<.*', r'\1', line.strip())
    if re.search('<b>',line):
        note = re.sub('<.*?>', ' ', re.sub('.*<b>(.*?)<.b>.*',r'\1',line.strip()))
    if re.search('href.*article_details',line):
        rec = {'jnl' : jnlname, 'note' : [note], 'tc' : typecode, 'vol' : vol, 'year' : year}
        artlink = urltrunk + re.sub('.*href=".a.volumes(.*?)".*', r'\1', line.strip())
        artfilname = tmpdir+"/"+jnlfilename+'.'+re.sub('.*=', '', artlink)
        rec['link'] = artlink
        rec['fc'] = 'a'
        print artlink
        if not os.path.isfile(artfilname):
            os.system('lynx -source "%s" > %s' % (artlink, artfilname))
            time.sleep(10)
        inf = open(artfilname, 'r')
        artlines = ''.join(map(tfstrip, inf.readlines()))
        for line in  re.split('<tr', artlines):
            if re.search('>Paper:<', line):
                rec['tit'] = re.sub('.*Paper.*<td.*?>(.*?)<.td.*', r'\1', line.strip())
            elif re.search('>Page:<', line):
                rec['p1'] = re.sub('.*Page.*<td>(\d+)<.td.*', r'\1', line.strip())
            elif re.search('>Authors:<', line):
                rec['auts'] = re.split(' *; *', re.sub('.*Authors.*<td.*?>(.*?)<.td.*', r'\1', line.strip()))
            elif re.search('>Abstract:<', line):
                rec['abs'] = re.sub('.*Abstract.*<td>(.*?)<.td>.*', r'\1', line.strip())
            
        if not rec.has_key('tit') or rec['tit'] == '':
            print '!!!! not title'
            print rec
            sys.exit(0)
        if len(sys.argv) > 2:
            rec['cnum'] = sys.argv[2] 
        #print rec
        if len(rec['auts']) > 1 or rec['auts'][0] != '':
            recs.append(rec)

jnlfilename = 'aspcs%s.%s' % (vol, bookid)

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
