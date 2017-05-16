#program to harvest frascati
#needs 'Handarbeit' in advance
import os
import ejlmod2
import re
import sys
import codecs


volume = '59'
cnum = 'C14-05-12.2'
year = '2014'

tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

publisher = 'Frascati'


jnlfilename = 'frascati%s_%s' % (volume, cnum)
inf = open('/afs/desy.de/user/s/schwenn/frascati%s' % (volume), 'r')
recs = []
proceedingspdf = '~/tmp/Volume%s.pdf' % (volume)
pageoffset = 5

i = 0
note = ''
for line in inf.readlines():
    if line[0] == '#':
        note = line[1:].strip()
    else:
        rec = {'year' : year, 'jnl' : 'Frascati Phys.Ser.', 'vol' : volume, 'cnum' : cnum, 'tc' : 'C'}
        if note != '':
            rec['notes'] = [note]
        parts = re.split(' *___ *', line.strip())
        print parts
        rec['tit'] = parts[1]
        pparts = re.split(' *; *', parts[0])    
        rec['auts'] = [re.sub('(.*) (.*)', r'\2, \1', pparts[0])]
        if len(pparts) > 1:
            rec['col'] = []
            for col in pparts[1:]:
                rec['col'].append(col)
        rec['p1'] = parts[2]
        rec['FFT'] = 'http://www.desy.de/~schwenn/%s.%s.pdf' % (jnlfilename, rec['p1'])
        recs.append(rec)
inf.close()

firstpages = [int(rec['p1']) for rec in recs]
for i in range(len(firstpages)-1):
    print 'extracting paper', firstpages[i]
    os.system('pdftk %s cat %i-%i output ~/www/%s.%i.pdf' % (proceedingspdf, firstpages[i]+pageoffset, firstpages[i+1]+pageoffset-1, jnlfilename, firstpages[i]))
os.system('pdftk %s cat %i-end output ~/www/%s.%i.pdf' % (proceedingspdf, firstpages[-1]+pageoffset, jnlfilename, firstpages[-1]))




xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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




