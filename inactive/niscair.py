#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Niscair online Periodicals Repository
# FS 2012-06-01

import os
import ejlmod2
import re
import sys
import unicodedata
import string
from removehtmlgesocks import removehtmlgesocks
import codecs


ejdir = '/afs/desy.de/user/l/library/dok/ejl'
tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

def tfstrip(x): return x.strip()

publisher = 'Niscair'
jnl = 'ijpap'
vol = sys.argv[1]
issue = sys.argv[2]

jnlfilename = jnl+vol+'.'+issue
jnlname = 'Indian J. Pure Appl. Phys. '
issn = "0019-5596"

urltrunk = 'http://nopr.niscair.res.in/handle/123456789/'


recnr = 1
recs = []
print "get table of content of %s%s.%s ..." %(jnlname,vol,issue)
#1st step
os.system("lynx -source \"%s/63\" | grep 'Vol' > %s/%s.toc.1" % (urltrunk,tmpdir,jnlfilename))
tocfil = open("%s/%s.toc.1" % (tmpdir,jnlfilename),'r')
for tline in map(tfstrip,tocfil.readlines()):
    if re.search('option.*Vol.*'+vol,tline):
        link = re.sub('.*option value=\".*\/(.*)\">.*',r'\1',tline)
        print link
#2nd step
os.system("lynx -source \"%s/%s\" | grep 'Vol' > %s/%s.toc.2" % (urltrunk,link,tmpdir,jnlfilename))
tocfil = open("%s/%s.toc.2" % (tmpdir,jnlfilename),'r')
for tline in map(tfstrip,tocfil.readlines()):
    if re.search('option.*\('+issue,tline):
        link = re.sub('.*option value=\".*\/(.*)\">.*',r'\1',tline)
        print link
#3rd step
os.system("lynx -source \"%s/%s\" |grep href > %s/%s.toc" % (urltrunk,link,tmpdir,jnlfilename))
    
tocfil = open("%s/%s.toc" % (tmpdir,jnlfilename),'r')
#for tline in  map(tfstrip,tocfil.readlines()):
tocline = re.sub('\s\s+',' ',' '.join(map(tfstrip,tocfil.readlines())))
for tline in re.split(' *<\/td> *',tocline):
    #print tline
    #tline = akzenteabstreifen(removehtmlgesocks(tline))
    if re.search('<td headers=\"t1\"',tline):
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['vol'] = vol
        rec['typ'] = ''
        rec['jnl'] = jnlname        
        rec['note'] = []
        rec['tc'] = "P"
        rec['link'] = 'http://nopr.niscair.res.in' + re.sub('.*href=\"(.*?)\".*',r'\1',tline)        
        artfilname = tmpdir+"/"+jnlfilename+"."+str(recnr)
        if not os.path.isfile(artfilname):
            print "lynx -source \"%s\" > %s" %(rec['link'],artfilname)
            os.system("lynx -source \"%s\" > %s" %(rec['link'],artfilname))
        artfil = open(artfilname,'r')
        artline = re.sub('\s\s+',' ',' '.join(map(tfstrip,artfil.readlines())))
        for aline in re.split(' *<\/tr> *',artline):
            aline = removehtmlgesocks(aline)
            aline = re.sub('<span .*?>','',aline)
            aline = re.sub('<\/span>','',aline)
            aline = re.sub('<sub>(.*?)<\/sub>',r'_\1',aline)
            aline = re.sub('<sup>(.*?)<\/sup>',r'^\1',aline)
            aline = re.sub('<i .*?>', '',  aline)
            aline = re.sub('<\/?i>', '',  aline)
            aline = re.sub('<img.*?>', ' ?? ',  aline)
            #print aline
            if re.search('class=\"metadataFieldLabel\">Authors',aline):
                authors = re.sub('.*metadataFieldValue\"> *(.*) *<\/td>',r'\1',aline)
                rec['auts'] = re.split(' *<br.*?> *',authors)
            elif re.search('class=\"metadataFieldLabel\">Keywords',aline):
                keywords = re.sub('.*metadataFieldValue\"> *(.*) *<\/td>',r'\1',aline)
                rec['keyw'] = re.split(' *<br.*?> *',keywords)
            elif re.search('class=\"metadataFieldLabel\">Title',aline):
                rec['tit'] = re.sub('.*metadataFieldValue\"> *(.*) *<\/td>',r'\1',aline)
            elif re.search('class=\"metadataFieldLabel\">Issue Date',aline):
                rec['year'] = re.sub('.*metadataFieldValue\">.*?(20\d+) *<\/td>',r'\1',aline)
            elif re.search('class=\"metadataFieldLabel\">Abstract',aline):
                rec['abs'] = re.sub('.*metadataFieldValue\"> *(.*) *<\/td>',r'\1',aline)
            elif re.search('class=\"metadataFieldLabel\">Page',aline):
                rec['p1'] = re.sub('.*metadataFieldValue\"> *(\d+) *\- *(\d+) *<\/td>',r'\1',aline)
                rec['p2'] = re.sub('.*metadataFieldValue\"> *(\d+) *\- *(\d+) *<\/td>',r'\2',aline)
                print "%s%s (%s) %s-%s" % (jnlname,vol,rec['year'],rec['p1'],rec['p2'])
            elif re.search('href.*\.pdf',aline):
                rec['pdf'] = 'http://nopr.niscair.res.in' +re.sub('.*href=\"(.*?\.pdf)\".*',r'\1',aline)
                rec['licence'] = {'a' : 'CC BY-NC-ND 2.5 IN', 'u' : 'http://creativecommons.org/licenses/by-nc-nd/2.5/in', 'b' : 'Niscair'}
                rec['FFT'] = rec['pdf']
                doi1 = re.sub('.*\/(.*?)\.pdf',r'\1',rec['pdf'])
                rec['doi'] = '20.niscair/'+rec['pdf']
        #write record
        recs.append(rec)
        recnr += 1

xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(open(xmlf,mode='wb'),"utf8")
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
