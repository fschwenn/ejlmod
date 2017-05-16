# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest world scientific books
# FS 2012-06-01

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
from removehtmlgesocks import removehtmlgesocks



ejdir = '/afs/desy.de/user/l/library/dok/ejl'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
tmpdir = '/tmp'

def tfstrip(x): return x.strip()

typecode = 'P'

publisher = 'World Scientific'
url = sys.argv[1]
jnlfilename = sys.argv[2]
if re.search('worldscibooks',url):
    jnlname = 'BOOK '
if re.search('ijmpcs',url):
    jnlname = 'Int.J.Mod.Phys.Conf.Ser.'
    typecode = 'C'
elif re.search('ijmp',url):
    jnlname = 'Int.J.Mod.Phys.'
elif re.search('mpl',url):
    jnlname = 'Mod.Phys.Lett.'
elif re.search('rast',url):
    jnlname = 'Rev.Accel.Sci.Tech.'
elif re.search('ijqi',url):
    jnlname = 'Int.J.Quant.Inf.'
elif re.search('^saqmbt', jnlfilename):
    jnlname = 'Ser.Adv.Quant.Many Body Theor.'
    typecode = 'S'
elif re.search('worldscibooks',url):
    jnlname = 'BOOK '
    typecode = 'S'

urltrunk = 'http://www.worldscientific.com'


print "get table of content of %s (%s) ..." %(jnlfilename,url)
os.system("lynx -source \"%s\" > %s/%s.toc" % (url,tmpdir,jnlfilename))

print "read table of contents..."
tocfil = open(tmpdir+"/"+jnlfilename+".toc",'r')
note = ''
recs = []
recnr = 1

trl = re.split('<\/table>',''.join(map(tfstrip,tocfil.readlines())))


#for tline in tocfil.readlines():
for tline in trl:
    if re.search('<li class=\"title\-group level',tline):
        note = re.sub('.*<li class=\"title\-group level.*?> *(.*?) *<\/li>.*',r'\1',tline.strip())
        print '--',note
    elif re.search('<div class="subject">',tline):
        note = re.sub('.*<div class="subject">(.*?)<\/div>.*',r'\1',tline.strip())
        print '--',note
    if re.search('href.*doi.*Abstract',tline):
        print '-',recnr,'-'
        articleurl = urltrunk + re.sub('.*href=\"(.*?doi.*?)\"> *Abstract.*',r'\1',tline.strip())
        if re.search(' ',articleurl): continue
        artfilname = "%s/%s.%i" %(tmpdir,jnlfilename,recnr)
        if not os.path.isfile(artfilname):
            os.system("lynx -source \"%s\" > %s" %(articleurl,artfilname))
        if not os.path.isfile(artfilname):
            print 'could not download',articleurl
            sys.exit()
        artfil = open(artfilname,'r')

        #typecode = 'S'
        #jnlname = 'Adv.Ser.Direct.High Energy Phys.'

        rec = {'auts' : [], 'aff' : [], 'jnl' : jnlname, 'note' : [ note ], 'refs' : []}
        if len(sys.argv) > 3:
            rec['cnum'] = sys.argv[3]
            typecode = 'C'
        if re.search('ijmpcs',url):
            rec['vol'] = re.sub('.*?(\d+).*',r'\1',url)
        elif re.search('ijmp',url) or re.search('mpl',url):
            rec['vol'] = re.sub('.*?([a-e])\/(\d+).*',r'\1\2',url).upper()
            rec['issue'] = re.sub('.*(\d+).*',r'\1',url)
        elif re.search('rast',url):
            rec['vol'] = re.sub('.*?(\d+).*',r'\1',url)
        elif re.search('ijqi',url):
            rec['vol'] = re.sub('.*?(\d+).*',r'\1',url)
            rec['iss'] = re.sub('.*\/(\d+).*',r'\1',url)
        elif jnlname == 'Ser.Adv.Quant.Many Body Theor.':
            rec['vol'] = re.sub('.*?(\d+)', r'\1', jnlfilename)
        elif jnlname == 'Adv.Ser.Direct.High Energy Phys.':
            rec['vol'] = re.sub('.*?(\d+)', r'\1', jnlfilename)
            if rec['vol'] == '18':
                rec['year'] = '1998'
            elif rec['vol'] == '16':
                rec['year'] = '1997'
            elif rec['vol'] == '14':
                rec['year'] = '1995'
            elif rec['vol'] == '12':
                rec['year'] = '1993'
            elif rec['vol'] == '11':
                rec['year'] = '1992'
            elif rec['vol'] == '10':
                rec['year'] = '1992'
            elif rec['vol'] == '9':
                rec['year'] = '1992'
            elif rec['vol'] == '7':
                rec['year'] = '1990'
            elif rec['vol'] == '6':
                rec['year'] = '1990'
            elif rec['vol'] == '5':
                rec['year'] = '1989'
            elif rec['vol'] == '4':
                rec['year'] = '1989'
            elif rec['vol'] == '3':
                rec['year'] = '1989'
            elif rec['vol'] == '2':
                rec['year'] = '1988'
            elif rec['vol'] == '1':
                rec['year'] = '1988'
            elif rec['vol'] == '15':
                rec['year'] = '1998'
            elif rec['vol'] == '21':
                rec['year'] = '2010'
        else:
            rec['vol'] = ''
        rec['tc'] = typecode
        rec['doi'] = re.sub('.*abs\/(10.*)',r'\1',articleurl)
        rec['doi'] = re.sub('\?query.*','',rec['doi'])
        #rec['FFT'] = 'http://www.worldscientific.com/doi/pdf/%s' % (rec['doi'])
        doi1 = re.sub('(\(|\)|\/)','_',rec['doi'])
        alines = map(tfstrip,artfil.readlines())
        for aline in alines:
            #aline = removehtmlgesocks(aline)
            #book
            if re.search('^ *pp\. ',aline):
                if re.search('\-',aline):
                    [rec['p1'],rec['p2']] = re.split(' *\- *',re.sub('^ *pp\. ([0-9a-zA-Z\-]*).*',r'\1',aline.strip()))
                else:
                    rec['p1'] = rec['p2'] = re.sub('^ *pp\. ([0-9a-zA-Z]*).*',r'\1',aline.strip())
            if re.search('^ *\(20\d\d\)',aline):
                rec['year'] = re.sub('^ *\((20\d\d)\).*',r'\1',aline.strip())
            if re.search('<div class="NLM_abstract">',aline):
                aline = removehtmlgesocks(aline)
                rec['abs'] = re.sub('.*<div class="NLM_abstract"> *<p> *(.*?)<\/p>.*',r'\1',aline.strip())
                rec['abs'] = re.sub('<\/?i>','',rec['abs'])
            if re.search('<div class="NLM_contrib-group">',aline):   
                authoraff = re.sub('.*<div class="NLM_contrib-group">  *','',removehtmlgesocks(aline).strip())
                authoraff = re.sub('<\/div>(</span> *)?<\/div>.*','',authoraff)
                #print 'AA',authoraff
                affdict = {}
                affind = 1
                for autaff in re.split('<span class="NLM_contrib">',authoraff)[1:]:
                    if len(autaff) > 5:
                        if re.search('[c]Collaboration.*<\/span>',autaff):
                            rec['col'] = re.sub('.*(for|For|on behalf of|On behalf of) the (.*) [Cc]ollaboration.*',r'\2',autaff)
                            if re.search('[Cc]ollaboration',rec['col']):
                                rec['col'] = re.sub('.*\((.*?) [cC]ollaboration.*',r'\1',autaff)
                        else:
                            print '[1]', autaff
                            author = re.sub(' *<div.*','',autaff)
                            author = re.sub(' *<span.*','',author)#neu
                            author = re.sub(' <a .*?>.*?<\/a>', '', author)
                            author = re.sub('\. ([A-Z])\.', r'.\1.',author)
                            author = re.sub(' *<a.*', '', author)
                            author = re.sub(' *<\/span> <\/div>', '', author)
                            print '[2a]', author
                            if len(author) > 2:
                                rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', author))
                                if re.search('<sup>', autaff):
                                    affs = re.sub('<\/sup><\/span><span class="NLM_xref-aff"><sup>',';',autaff)
                                    affs = re.sub('.*<span class="NLM_xref-aff"><sup>(.*?)<\/sup>.*',r'\1',affs)#neu
                                    print '[2e]', affs
                                    if not re.search('<div',affs):
                                        for aff in re.split(';',affs):
                                            if re.search('[a-z0-9]',aff):
                                                aff = re.sub('[ ,]', '', aff)
                                                print '[2b]', aff
                                                rec['auts'].append('=Aff%s' % aff)
                                else:
                                    aff = re.sub('.*<div class="aff">','',autaff)
                                    aff = re.sub('<span class="country">','',aff)
                                    aff = re.sub('<\/.*','',aff)
                                    if not aff == author:
                                        print '[2c]', affind
                                        rec['auts'].append('=Aff%i' % (affind))
                                        if not affdict.has_key(aff):
                                            affdict[aff] = affind
                                            rec['aff'].append('Aff%i= %s' % (affind,aff))
                                            print '[2d]', affind, aff
                                            affind += 1  
                if affind == 1:
                    for aff in re.split('<div class="aff">',authoraff)[1:]:    #neu
                        aff = re.sub('<span class="country">(.*?)<\/span>',r'\1',aff)
                        aff = re.sub('<\/div>.*','',aff)
                        if not aff == author:
                            rec['aff'].append(re.sub('<sup>(.*?)<\/sup>',r'Aff\1= ',removehtmlgesocks(aff),count=1))
                print '[2u]', rec['auts']
                print '[2v]', rec['aff']
            #IJMPCS
            if re.search('This is an Open Access article', aline) and re.search('https...creativecommons.org', aline):
                rec['licence'] = {'link' : re.sub('.*(https...creativecommons.org.*?)".*', r'\1', aline.strip())}
                rec['FFT'] = 'http://www.worldscientific.com/doi/pdf/%s' % (rec['doi'])
            if re.search('copyrightYear',aline):
                rec['p1'] = re.sub('.*<\/b>, *(\d+) .*',r'\1',aline.strip())
                rec['p2'] = rec['p1']
                rec['year'] = re.sub('.*copyrightYear.*?(\d+).*',r'\1',aline.strip())
            if re.search('<div class="abstractSection">',aline):
                aline = removehtmlgesocks(aline)
                rec['abs'] = re.sub('.*<div class="abstractSection"> <p.*?> *(.*?)<\/p>.*',r'\1',aline.strip())
                rec['abs'] = re.sub('<.*?>','',rec['abs'])
            if re.search('<div class="artAuthors">',aline):
#                if re.search('<div class="artAuthors"><\/div>',aline):
#                    rec['auts'] = ['???']
#                else:
#                    authoraff = re.sub('.*<div class="artAuthors">(.*?)<\/div>(<div>)?<\/div>.*',r'\1', removehtmlgesocks(aline).strip())
#                    #print 'AA',authoraff
#                    affdict = {}
#                    affind = 1
#                    for autaff in re.split('<\/div>',authoraff):
#                        if len(autaff) > 5:
#                            author = re.sub(' *<div.*','',autaff)
#                            author = re.sub('\. ([A-Z])\.', r'.\1.',author)
#                            aff = re.sub('.*<li class="listGroup">','',autaff)
#                            aff = re.sub('<span class="country">','',aff)
#                            aff = re.sub('<span class="country">','',aff)
#                            aff = re.sub('<\/.*','',aff)
#                            if not affdict.has_key(aff):
#                                affdict[aff] = affind
#                                rec['aff'].append('Aff%i= %s' % (affind,aff))
#                                affind += 1                            
#                            rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', author))
#                            rec['auts'].append('=Aff%i' % affdict[aff])
#                            #print 'A ',author
#                            #print ' A',aff
                if re.search('<div class="artAuthors"><\/div>',aline):
                    rec['auts'] = ['???']
                else:
                    authoraff = re.sub('.*<div class="artAuthors">(.*?)<p class="fulltext affiliation">.*',r'\1', removehtmlgesocks(aline).strip())
                    if re.search('on.behalf.of', authoraff):
                        rec['col'] = re.sub('.*.on.behalf.of (the )?', '', authoraff)
                        rec['col'] = re.sub(' *[cC]ollaboration.*', '', rec['col'])
                        rec['col'] = re.sub('[\)<].*', '', rec['col'])
                    for autaff in re.split('<\/div>',authoraff):                        
                        autaff = re.sub(' *<div>.*','',autaff)
                        autaff = re.sub('<div class="hlFld-ContribAuthor">','',autaff)
                        author = re.sub('<.*','',autaff)
                        if len(author) < 3: continue
                        rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', author))
                        affs = re.sub('.*?<sup>(.*)</sup>.*', r'\1', autaff)
                        affs = re.sub('</sup></span><span class="NLM_xref-aff"><sup>', '', affs)
                        for aff in re.split(' *, *', affs):
                            rec['auts'].append('=Aff%s' % (aff))
                    affs = re.sub('.*?<p class="fulltext affiliation">(.*)<div class="abstractSection">.*', r'\1', removehtmlgesocks(aline).strip())
                    for aff in  re.split('<\/p>', affs):
                        if re.search('<sup>', aff):
                            aff = re.sub('<p class="fulltext affiliation">', '', aff)
                            aff = re.sub('<span class="country">','',aff)
                            aff = re.sub('<\/span>.*','',aff)
                            rec['aff'].append(re.sub('<sup>(.*)<\/sup>(.*)', r'Aff\1= \2', aff))

                       
            #common
            if re.search('<input type="hidden" name="title"',aline):
                aline = removehtmlgesocks(aline)
                rec['tit'] = re.sub('.*name="title" value="(.*?)\)?".*',r'\1',aline.strip())                  
            if re.search('PACS:',aline):
                rec['pacs'] = re.sub('.*PACS\: *(<\/b>)? *','',aline.strip())
                rec['pacs'] = re.split(' *, *', re.sub('<.*','',rec['pacs']))
            if re.search('<b>Keywords\:',aline):
                rec['authorkeyw'] = []
                for kw in re.split(' *; *',re.sub('.*Keywords\: <\/b> *(.*?) *<\/.*',r'\1',aline.strip())):
                    rec['authorkeyw'].append(re.sub('<kwd.*?>', '', kw))
        if not rec['auts']:
            for aline in alines:
                if re.search('<input type="checkbox" name="author"', aline):
                    author = re.sub('.*> *(.+)<\/label.*', r'\1', aline.strip())
                    author = re.sub('(.*) (.*)', r'\2, \1', author)
                    rec['auts'].append(author)
        print rec
        print "get references"
        reffilname = artfilname+'.ref'
        #if not os.path.isfile(reffilname):
        #    os.system("lynx -source \"%s\" > %s" %(re.sub('abs','ref',articleurl),reffilname))
        if os.path.isfile(reffilname):
            reffil = open(reffilname,'r')
            reflines = ' '.join(map(tfstrip,reffil.readlines()))
            reffil.close()
            reffs = re.split(' *<li class="reference"> *',reflines)
            if len(reffs) > 1:
                print len(reffs)-1,'references were found'
                rec['refs'] = []
                for ref in reffs[1:]:
                    ref = re.sub(' *</li>','',ref)
                    ref = re.sub('\[.*?CrossRef.*?\]','',ref)
                    ref = re.sub('<\/ul>.*','',ref) 
                    rec['refs'].append([('x',ref)])
        #write record                    
        if rec.has_key('tit') and not rec['tit'] in ['LIST OF PARTICIPANTS', 'PREFACE','COMMITTEES, SPONSORS AND PARTICIPANTS', 'PEER-REVIEW STATEMENT','COMMITTEES','CONFERENCE POSTER AND PHOTOS','BACK MATTER','FRONT MATTER']:
            #if not re.search('others', rec['doi']): 
            recs.append(rec)
        recnr += 1

xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
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
