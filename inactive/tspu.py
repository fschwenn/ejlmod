#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest “Tomsk State Pedagogical University Bulletin”
# FS 2012-06-01

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs


ejdir = '/afs/desy.de/user/l/library/dok/ejl'
tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

def tfstrip(x): return x.strip()
#remove accents from a string
def akzenteabstreifen(string):
    if not type(string) == type(u'unicode'):
        string = unicode(string,'utf-8', errors='ignore')
        if not type(string) == type(u'unicode'):
            return string
        else:
            return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')
    else:
        return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')


publisher = 'Tomsk State Pedagogical University'
jnl = 'tspu'
vol = sys.argv[1]
issue = sys.argv[2]

jnlfilename = jnl+vol+'.'+issue
jnlname = 'TSPU Bulletin'
issn = "1609–624X"

urltrunk = 'http://vestnik.tspu.ru/eng/index.php?option=com_content&task=view&id=3386&Itemid=597&year='


recs = []
print "get table of content of %s%s.%s ..." %(jnl,vol,issue)
#1st step
if not os.path.isfile("%s/%s.toc.1" % (tmpdir,jnlfilename)):
    os.system("lynx -source \"%s%s&number=%s\" |grep article_id > %s/%s.toc.1" % (urltrunk,vol,issue,tmpdir,jnlfilename))
tocfil = open("%s/%s.toc.1" % (tmpdir,jnlfilename),'r')
for tline in map(tfstrip,tocfil.readlines()):
    for part in re.split('<a href=', tline.strip()):
        if re.search('article_id', part):
            rec = {'jnl' : jnlname, 'vol' : vol, 'year' : vol, 'issue' : issue, 'auts' : []}
            rec['link'] = re.sub('.*?\'(.*?)\'.*', r'http://vestnik.tspu.ru/eng/\1', part)
            articleid = re.sub('.*article_id=', '', rec['link'])
            rec['tit'] = re.sub('.*?\'.*?><font.*?>(.*)\/\/.*', r'\1', part)
            print rec['tit']
            artfilname = '%s/%s.%s' %  (tmpdir, jnlfilename, articleid)
            if not os.path.isfile("%s" % (artfilname)):
                os.system("lynx -source '%s' > %s" % (rec['link'], artfilname)) 
            inf = open(artfilname, 'r')
            for line in inf.readlines():
                if re.search('<meta name="description"', line):
                    rec['abs'] = re.sub('.*<meta name="description" content="(.*?)".*', r'\1', akzenteabstreifen(line).strip())
                elif re.search('<meta name="keywords"', line):
                    rec['keyw'] = re.split(', ', re.sub('.*<meta name="keywords" content="(.*?)".*', r'\1', akzenteabstreifen(line).strip()))[:-1]
                elif re.search('Issue.*Pages', line):
                    pages = re.sub('.*Pages\: *(.*?) *<br.*', r'\1', akzenteabstreifen(line).strip())
                    rec['p1'] = re.sub(' *\-.*', '', pages)
                    rec['p2'] = re.sub('.*\- *', '', pages)
                elif re.search('<em>', line):
                    authors = re.sub('.*<em>(.*)<\/em>.*', r'\1', akzenteabstreifen(line).strip())
                    for author in re.split(', ', authors):
                        author = re.sub('([A-Z])\. ', r'\1.', author)
                        rec['auts'].append(re.sub('(.*) (.*)', r'\1, \2', author))
                elif re.search('pdf.jpg', line):
                    rec['FFT'] = re.sub('.*href=(htt.*?pdf)>.*', r'\1', akzenteabstreifen(line).strip())
            print rec
            recs.append(rec)
                    

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
