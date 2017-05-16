# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest http://www.emis.de/proceedings/
# FS 2015-05-19

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
bibclassifycommand = 'python /afs/desy.de/user/l/library/proc/bibclassify/bibclassify_cli.py -n10 -s -k /afs/desy.de/user/l/library/akw/HEPont.rdf '

publisher = 'Electronic Library of Mathematics (ELibM)'
link = sys.argv[1]
urltrunk = re.sub('(.*\/).*', r'\1', link)
jnlfilename = 'EMIS'+re.sub('.*emis.de\/.*?\/(.*)\..*', r'\1', link).replace('/','_',10)
if len(sys.argv) > 2:
    cnum = sys.argv[2]
    jnlfilename += '_'+cnum

xmlf    = os.path.join(xmldir,jnlfilename+'.xml')


print "get table of content..."
if not os.path.isfile("%s/%s.toc" % (tmpdir, jnlfilename)):
    os.system("lynx -source \"%s\" > %s/%s.toc" % (link, tmpdir, jnlfilename))

if re.search('proceedings', link) or len(sys.argv) > 2:
    typecode = 'C'
else:
    typecode = 'P'

tocfil =  open(tmpdir+'/'+jnlfilename+'.toc','r')
recs = []
for line in re.split('<li>', ' '.join(map(tfstrip,tocfil.readlines()))):
    if re.search('doi:10.7546', line):
        line = re.sub('<\/ul>.*', '', line)
        parts = re.split(' *<\/[aA]> *', line.replace('<br>', ''))
        #print parts
        rec = {'tc' : typecode, 'auts' : [], 'jnl' : 'DUMMY'}
        if len(sys.argv) > 2:
            rec['cnum'] = cnum
        rec['tit'] = re.sub('.*?font.*?> *(.*)', r'\1', parts[0])
        rec['tit'] = re.sub(' *<\/font.*', '', rec['tit'])
        rec['tit'] = re.sub(' *<a.*', '', rec['tit'])
        #print parts[-1]
        authors = re.sub('.*doi:10.*?<\/font>', '', parts[-1]).replace(' and ', ', ')
        authors = re.sub(' *<\/font> *', '', authors)
        authors = re.sub(' *<font.*?> *', '', authors)
        authors = re.sub(' *<\/p> *', '', authors)
        for author in re.split(' *, *', authors):
            rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', author))
        for part in parts:  
            if re.search('doi:10.7546', part):
                rec['doi'] = re.sub('.*doi:(10.*?)<.*', r'\1', part)
                doi1 = re.sub('[\/\(\)]', '_', rec['doi'])
                if re.search('\-\d+\-\d+', rec['doi']):
                    pages = re.sub('.*\-(\d+\-\d+)', r'\1', rec['doi'])
                    rec['p1'] = re.sub('\-.*', '', pages)
                    rec['p2'] = re.sub('.*\-', '', pages)        
        for part in parts:  
            if re.search('Abstract', part):
                abslink = urltrunk + re.sub('.*="(.*?)">.Abstract.*', r'\1', part)
                #bibclassify 
                absfile = "%s/%s" % (tmpdir, doi1)
                bbclfile = '/afs/desy.de/user/l/library/tmp/fs'+doi1+'.abs.bib'
                if not os.path.isfile(absfile):
                    print ' -> downloading %s, saving to %s' % (abslink, absfile)
                    os.system('wget -O %s "%s"' % (absfile, abslink))
                if not os.path.isfile(bbclfile):
                    print ' -> BibClassify on %s, saving to %s' % (absfile, bbclfile)
                    os.system(bibclassifycommand+absfile+' > '+bbclfile)
            if re.search('Fulltext . pdf', part):
                rec['link'] = urltrunk + re.sub('.*="(.*?)">.Fulltext . pdf.*', r'\1', part)
                rec['FFT'] = urltrunk + re.sub('.*="(.*?)">.Fulltext . pdf.*', r'\1', part)

        recs.append(rec)

xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#xmlfile  = open(xmlf,'w')
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
