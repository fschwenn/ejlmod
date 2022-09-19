# -*- coding: UTF-8 -*-
#!/usr/bin/python
#Program to digest feeds from https://www.scientific.net/
# FS 2021-11-18

import ejlmod2
import re
import os
import unicodedata
import string
import codecs
import urllib2
import urlparse
from bs4 import BeautifulSoup
import sys
import datetime
from ftplib import FTP
import zipfile

scientificdir = '/afs/desy.de/group/library/publisherdata/scientific'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

publisher = 'Trans Tech Publications Ltd.'

#current timestamp (or other unique mark)
if len(sys.argv) > 1:
    cday = sys.argv[1]
else:
    now = datetime.datetime.now()
    cday = '%4d-%02d-%02d-%02d-%02d' % (now.year, now.month, now.day, now.hour, now.minute)


# uninteresting journals:
juninteresting = ['JBBBE', 'JBBTE', 'MSF', 'RC', 'FoMSE', 'SC', 'EI', 'SBC', 'MSFo', 'CTA']
# interesting journals:
jninteresting = ['AMM', 'AMR', 'DDF', 'AEF', 'SSP', 'KEM', 'JERA', 'JNanoR', 'AST']
#dictionary of journal names
# journal-id : [file name, INPIRE journal name, type code, do not go below this volume] (2015)
jc = {'AEF'    : ['scientificAEF',    'Advanced Engineering Forum', 'P', 12],
      'AMM'    : ['scientificAMM',    'Appl.Mech.Mater.', 'P', 722], #!!
      'JBBBE'  : ['scientificJBBBE',  'Journal of Biomimetics, Biomaterials and Biomedical Engineering', 'P'],
      'JBBTE'  : ['scientificJBBTE',  'Biomimetics, Biomaterials & Tissue Engineering', 'P'],#bis 2014.03, danach als JBBTE fortgefuehrt
      'JERA'   : ['scientificJERA',   'International Journal of Engineering Research in Africa', 'P', 13],
      'AMR'    : ['scientificAMR',    'Adv.Mater.Res.', 'P', 1082], #!!
      'DDF'    : ['scientificDDF',    'Defect Diff.Forum', 'P', 360],#!
      'DF'     : ['scientificDF',     'Diffusion Foundations', 'P'],#bis 2021.04, danach als DFMA fortgefuehrt
      'DFMA'   : ['scientificDFMA',   'Diffusion Foundations and Materials Applications', 'P', 2],
      'EI'     : ['scientificEI',     'Engineering Innovations', 'P'],
      'JMNM'   : ['scientificJMNM',   'Journal of Metastable and Nanocrystalline Materials', 'P', 0],
      'JNanoR' : ['scientificJNanoR', 'J.Nano Res.', 'P', 29],
      'KEM'    : ['scientificKEM',    'Key Eng.Mater.', 'P', 636], #!
      'MSF'    : ['scientificMSF',    'Materials Science Forum', 'P', 0],
      'MSFo'   : ['scientificMSF',    'Mater.Sci.Forum', 'P'], #!
      'NH'     : ['scientificNH',     'Nano Hybrids', 'P'],  #bis 2016.05, danach als NHC fortgefuehrt
      'NHC'    : ['scientificNHC',    'Nano Hybrids and Composites', 'P', 8],
      'SSP'    : ['scientificSSP',    'Solid State Phenom.', 'P', 225], #!
      'AST'    : ['scientificAST',    'Adv.Sci.Tech.', 'P', 96],
      'CTA'    : ['scientificCTA',    'Construction Technologies and Architecture', 'P', 0]}

#check server and download all new zip-files
revol = re.compile('\D*(\d+).*')
def downloadzipfiles():
    done = os.listdir(os.path.join(scientificdir, 'done'))
    ftp = FTP("ftp.scientific.net")
    ftp.login("inspireHep", "inspire94")
    ftp.cwd('Jats')
    ftp.cwd('ByTitle')
    todo = []
    for journal in ftp.nlst():
        if journal in jc.keys():
            if journal in jninteresting:
                ftp.cwd(journal)
                for datei in ftp.nlst():
                    if not datei in done:
                        if len(jc[journal]) > 3:
                            vol = int(revol.sub(r'\1', datei))
                            if vol < jc[journal][3]:
                                continue                                                    
                        f2 = open(os.path.join(scientificdir, datei), "wb")
                        ftp.retrbinary("RETR " + datei,f2.write)                        
                        f2.close()
                        print 'downloaded %s' % (datei)
                        todo.append((journal, datei))
                ftp.cwd('..')
        elif not journal in juninteresting:
            os.system('echo "check https://www.scientific.net/%s" | mail -s "[SCIENTIFIC] unknown journal" %s' % (journal, 'florian.schwennsen@desy.de'))
    return todo

#process one zip-file
rexml = re.compile('\.xml$')
def harvestvolume(journal, datei):
    print ' ', datei
    zfile = zipfile.ZipFile(os.path.join(scientificdir, datei))
    zfile.extractall(scientificdir)
    recs = []
    for adatei in os.listdir(scientificdir):
        if rexml.search(adatei):
            rec = convertarticle(journal, os.path.join(scientificdir, adatei))
            if rec:
                recs.append(rec)
            else:
                os.system('rm %s/%s %s/*xml' % (scientificdir, datei, scientificdir))
                return 
    if recs:
        if 'vol' in recs[-1].keys():
            jnlfilename = '%s%s' % (jc[journal][0], recs[-1]['vol'])
        else:
            jnlfilename = '%s.%s' % (jc[journal][0], cday)
        xmlf = os.path.join(xmldir, jnlfilename+'.xml')
        xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
        ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
        xmlfile.close()
        #retrival
        retfiles_text = open(retfiles_path, "r").read()
        line = jnlfilename+'.xml'+ "\n"
        if not line in retfiles_text:
            retfiles = open(retfiles_path, "a")
            retfiles.write(line)
            retfiles.close()
        os.system('mv %s/%s %s/done/%s' % (scientificdir, datei, scientificdir, datei))
        os.system('rm %s/*xml' % (scientificdir))
    else:
        print '  NO RECORDS IN %s' % (datei)
    return
            

###clean formulas in tag
def cleanformulas(tag):
    #change html-tags into LaTeX
    for italic in tag.find_all('italic'):
        it = italic.text.strip()
        #appears within sub/sup :(
        #  italic.replace_with('$%s$' % (it))
        italic.replace_with(it)
    for sub in tag.find_all('sub'):
        st = sub.text.strip()
        sub.replace_with('$_{%s}$' % (st))
    for sup in tag.find_all('sup'):
        st = sup.text.strip()
        sup.replace_with('$^{%s}$' % (st))
    #handle MathML/LaTeX formulas
    for inlineformula in tag.find_all(['inline-formula', 'disp-formula']):
        mmls = inlineformula.find_all('mml:math')
        tms = inlineformula.find_all('tex-math')
        #if len(mmls) == 1:
        #    inlineformula.replace_with(mmls[0])
        if len(tms) == 1:
            for tm in tms:
                tmt = re.sub('  +', ' ', re.sub('[\n\t\r]', '', tm.text.strip()))
                tmt = re.sub('.*begin.document..(.*)..end.document.*', r'\1', tmt)
                inlineformula.replace_with(tmt)
        else:
            print 'DECOMPOSE', inlineformula
            inlineformula.decompose()            
    output = tag.text.strip()
    #MML output = ''
    #MML for tt in tag.contents:
    #MML     output += unicode(tt)
    #unite subsequent LaTeX formulas
    output = re.sub('\$\$', '', output)
    return output

#extract references
def get_references(rl):
    refs =  []
    #convert individual references
    for ref in rl.find_all('ref'):
        for mc in ref.find_all('mixed-citation'):
            (doi, arxiv) = ('', '')
            for el in mc.find_all('ext-link', attrs = {'ext-link-type' : 'doi'}):
                if el.has_attr('xlink:href'):
                    link = el['xlink:href']
                    if re.search('arxiv.org', link):
                        arxiv = re.sub(' ', '', el.text.strip())
                        arxiv = re.sub('^\[', '', arxiv)
                        arxiv = re.sub('(\d)\]$', r'\1', arxiv)
                        if re.search('^\d{4}\.\d', arxiv):
                            arxiv = 'arXiv:' + arxiv
                        elif re.search('ar[xX]iv\:[a-z\-]+\/\d',  arxiv):
                            arxiv = arxiv[6:]
                            #el.decompose()
                    if re.search('doi.org\/10', link):
                        doi = re.sub('.*doi.org\/', '', link)
                        #el.decompose()
            #all together
            reference = [('x', cleanformulas(mc))]
            if doi:
                reference.append(('a', 'doi:'+doi))
            if arxiv:
                reference.append(('r', arxiv))
            refs.append(reference)
    return refs

###convert individual JATS file to record
def convertarticle(journal, filename):
    print '  ', filename
    rec = {'jnl' : jc[journal][1], 'tc' : jc[journal][2],
           'note' : [], 'aff' : [], 'auts' : [], 'col' : []}
    #read file
    inf = codecs.EncodedFile(codecs.open(filename, mode='rb'), 'utf8')
    lines = inf.readlines()
    inf.close()
    article = BeautifulSoup(''.join(lines), features="lxml")
    metas = article.find_all('article-meta')
    for meta in metas:
        #title
        for tg in meta.find_all('title-group'):
            for tit in tg.find_all('article-title'):
                rec['tit'] = tit.text.strip()
        #DOI
        for aid in meta.find_all('article-id', attrs = {'pub-id-type' : 'doi'}):
            rec['doi'] = aid.text.strip()
        #arXiv number
        for aid in meta.find_all('article-id', attrs = {'pub-id-type' : 'arxiv'}):
            rec['arxiv'] = aid.text.strip()
        #year
        pds = meta.find_all('pub-date', attrs = {'pub-type' : 'ppub'})
        if not pds:
            pds = meta.find_all('pub-date', attrs = {'pub-type' : 'eub'})
        for pd in pds:
            for year in pd.find_all('year'):
                rec['year'] = year.text.strip()
        #date
        pds = meta.find_all('pub-date', attrs = {'date-type' : 'epub'})
        if not pds:
            pds = meta.find_all('pub-date', attrs = {'date-type' : 'pub', 'publication-format' : 'electronic'})
        for pd in pds:
            for year in pd.find_all('year'):
                rec['date'] = year.text.strip()
            for month in pd.find_all('month'):
                rec['date'] += '-' + month.text.strip()
            for day in pd.find_all('day'):
                rec['date'] += '-' + day.text.strip()
        #volume
        for vol in meta.find_all('volume'):
            rec['vol'] = vol.text.strip()        
        #issue
        for iss in meta.find_all('issue'):
            rec['issue'] = iss.text.strip()
        #first page
        for p1 in meta.find_all('fpage'):
            rec['p1'] = p1.text.strip()
        #last page
        for p2 in meta.find_all('lpage'):
            rec['p2'] = p2.text.strip()
        #abstract
        for abstract in meta.find_all('abstract'):
            rec['abs'] = ''
            for p in abstract.find_all('p'):
                rec['abs'] += cleanformulas(p)
        #license
        for permissions in meta.find_all('permissions'):
            for licence in permissions.find_all('license', attrs = {'license-type' : 'open-access'}):
                if licence.has_attr('xlink:href'):
                    if re.search('creativecommons.org', licence['xlink:href']):
                        rec['license'] = {'url' : licence['xlink:href']}
                        rec['FFT'] = 'https://www.scientific.net/%s.%s.%s.pdf' % (journal, rec['vol'], rec['p1'])
        #conference (<conf-name>, <conf-date>, <conf-loc>)
        for conf in meta.find_all('conference'):
            confnote = conf.text.strip()
            rec['note'].append(confnote)
        #keywords
        kwgs = meta.find_all('kwd-group', attrs = {'kwd-group-type' : 'author'})
        if not kwgs:
            kwgs = meta.find_all('kwd-group')            
        for kwg in kwgs:
            rec['keyw'] = []
            for kw in kwg.find_all('kwd'):
                rec['keyw'].append(kw.text.strip())
        #corrected article
        for ra in meta.find_all('related-article', attrs = {'related-article-type' : 'corrected-article'}):
            if ra.has_attr('xlink:href'):
                rec['tit'] += ' [doi: %s]' % (ra['xlink:href'])      
        #affiliations
        for aff in meta.find_all('aff'):
            afftext = ''
            #Division
            for od in aff.find_all('institution'):
                afftext += od.text.strip() + ', '
            #address
            for postbox in aff.find_all('addr-line'):
                afftext += postbox.text.strip() + ', '
            #Postal Code
            for pc in aff.find_all('postal-code'):
                afftext += pc.text.strip() + ' '
            #City
            for city in aff.find_all('city'):
                afftext += city.text.strip() + ', '
            #State
            for state in aff.find_all('state'):
                afftext += state.text.strip() + ', '
            #Country
            for country in aff.find_all('country'):
                afftext += country.text.strip()
            rec['aff'].append('%s= %s' % (aff['id'], re.sub('[\n\t\r]', ' ', afftext)))
        #check for editor
        authortype = 'author'
        for contrib in meta.find_all('contrib', attrs = {'contrib-type' : authortype}):
            #authors
            for name in contrib.find_all('name'):
                for sn in name.find_all('surname'):
                    authorname = sn.text.strip()
                for gn in name.find_all('given-names'):
                    authorname += ', %s' % (gn.text.strip())
                #editor
                if authortype == 'editor':
                    authorname += ' (ed.)'
                #ORCID
                for cid in contrib.find_all('contrib-id', attrs = {'contrib-id-type' : 'orcid'}):
                    authorname += re.sub('.*\/', ', ORCID:', cid.text.strip())
                #Email
                if not re.search('ORCID:', authorname):
                    for email in contrib.find_all('email'):
                        authorname += ', EMAIL:' + email.text.strip()
                rec['auts'].append(authorname)
                #Affiliation
                for xref in contrib.find_all('xref', attrs = {'ref-type' : 'aff'}):
                    rec['auts'].append('=%s' % (xref['rid']))
    #references
    for rl in article.find_all('ref-list'):
        rec['refs'] = get_references(rl)
    if 'doi' in rec.keys() and rec['doi']:
        print '   ', rec.keys()
        return rec
    else:
        print '  NO DOI IN ', filename
        return False    


for (journal, datei) in downloadzipfiles():
    harvestvolume(journal, datei)
os.system('rm %s/*xml' % (scientificdir))
