#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Electronic Journal of Theoretical Physics
# FS 2012-06-01

import os
#import xml.dom.minidom
#import urllib
import ejlmod2
#import Recode
#import time
import re
import sys
import unicodedata
import string
import codecs

from shutil import copyfile 

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
tmpdir = '/tmp'

def tfstrip(x): return x.strip()

publisher = 'EJTP'
jnl = 'ejtp'
vol = sys.argv[1]
issue = sys.argv[2]

jnlfilename = jnl+vol+'.'+issue
jnlname = 'Electron.J.Theor.Phys.'
issn = "1729-5254"

urltrunk = 'http://www.ejtp.com/ejtpv%si%s' % (vol,issue)
if vol == '12' and issue == '34':
    urltrunk = 'http://www.ejtp.com/iyl2015'

recnr = 1
recs = []
print "get table of content of %s%s.%s via %s ..." %(jnlname,vol,issue, urltrunk)
#print "lynx -source \"%s/PV%sIss%s.html\" > %s/%s.toc" % (urltrunk,vol,issue,tmpdir,jnlfilename)
os.system("lynx -source \"%s\" > %s/%s.toc" % (urltrunk,tmpdir,jnlfilename))
    
tocfil = codecs.open("%s/%s.toc" % (tmpdir,jnlfilename),'r', 'cp1252')
#for tline in  map(tfstrip,tocfil.readlines()):
tocline = re.sub('\s\s+',' ',' '.join(map(tfstrip,tocfil.readlines())))
for tline in re.split(' *<\/tr> *',tocline):
    if re.search('<h1>.*Volume.*20\d+',tline):
        #print tline
        year = re.sub('.*<h1.*Volume.*?\(.*?(20\d+).*',r'\1',tline)
        print year
    elif re.search('href.*\.pdf',tline):
        #print tline
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['year'] = year
        rec['vol'] = vol
        rec['issue'] = issue
        rec['typ'] = ''
        rec['jnl'] = jnlname        
        rec['note'] = []
        rec['tc'] = "P"
        rec['pdf'] = re.sub('.*href=\"(.*?\.pdf)\".*',r'\1',tline)
        rec['p1'] = rec['p2'] = '0'
        #pseudo-DOI
        rec['doi'] = '20.ejtp/'+rec['pdf']

        details = re.split('<\/ *p>',tline)
        for detail in details:
            if re.search('<b>',detail) and not rec.has_key('tit'):
                title = re.sub('.*<b>.*?<span.*?> *(.*?) *<o.*',r'\1',detail)
                title = re.sub(' +',' ',title)
                title = re.sub('^ ','',title)
                title = re.sub(' $','',title)
                title = re.sub('<sub>(.*?)<\/sub>',r'_\1',title)
                title = re.sub('<sup>(.*?)<\/sup>',r'^\1',title)
                title = re.sub('<span.*?>(.*?)<\/span>',r'\1',title)
                if len(title) > 3:
                    rec['tit'] = title
                    print rec['tit']                    
            elif  re.search('<i>',detail):
                detail = re.sub('\&nbsp;', '', detail)
                #print 'A',detail
                authors = re.sub('.*<i><span.*?> *(.*?) *<\/i.*',r'\1',detail)
                authors = re.sub(' and ',', ',authors)
                authors = re.sub('>and ','>, ',authors)
                for author in re.split(' *, +',authors):
                    aut = re.sub('<\/?span.*?>','',author)
                    aut = re.sub('<\/?o.*?>','',aut)
                    aut = re.sub('([A-Z]\.) ([A-Z]\.)',r'\1\2',aut)
                    if len(aut) > 1:
                        rec['auts'].append(re.sub('(.*?) (.*)',r'\2, \1',re.sub('<sup.*','',aut)))
                        print 'A',aut
                    if re.search('<sup>',author):
                        sups = re.sub('.*<sup>(.*?)<.*',r'\1',author)
                        for sup in re.split(' *[;,] *',sups):
                            rec['auts'].append('=Aff'+sup)
            #elif len(rec['auts']) > 0 and not re.search('Full text',detail):
            #    print 'I1',detail
            #    inst = re.sub('<\/?span.*?>','',detail)
            #    inst = re.sub('<\/?[po].*?>','',inst)
            #    inst = re.sub(' *<sup> *(.*?) *<\/sup>',r'Aff\1=',inst)
            #    print 'I2',inst
            #    inst = re.sub('<\/sup>','= ',re.sub(' *<\/?span.*?> *','',inst))
            #    if len(inst) > 6:
            #        rec['aff'].append(re.sub('^ +','',inst))
        #write record
        print "REC",rec
        recnr += 1
        recs.append(rec)

xmlf = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile = open(xmlf, 'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs ,xmlfile, publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
