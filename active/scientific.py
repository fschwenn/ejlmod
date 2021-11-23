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

scientificdir = '/afs/desy.de/group/library/publisherdata/scientific'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'Trans Tech Publications Ltd.'

#current timestamp (or other unique mark)
cday = sys.argv[1]

# uninteresting journals:
juninteresting = ['JBBBE']
#dictionary of journal names
# journal-id : [file name, INPIRE journal name, type code]
jc = {'AEF'   : ['scientificAEF',   'Advanced Engineering Forum', 'P'],
      'AMM'   : ['scientificAMM',   'Applied Mechanics and Materials', 'P'], #!!
      'JBBBE' : ['scientificJBBBE', 'Journal of Biomimetics, Biomaterials and Biomedical Engineering', 'P'],
      'JERA'  : ['scientificJERA',  'International Journal of Engineering Research in Africa', 'P'],
      'AMR'   : ['scientificAMR',   'Advanced Materials Research', 'P'], #!!
      'DDF'   : ['scientificDDF',   'Defect and Diffusion Forum', 'P'],
      'DFMA'  : ['scientificDFMA',  'Diffusion Foundations and Materials Applications', 'P'],
      'JMNM'  : ['scientificJMNM',  'Journal of Metastable and Nanocrystalline Materials', 'P'],
      'AMMJNanoR' : ['scientificJNanoR', 'Journal of Nano Research', 'P'],
      'KEM'   : ['scientificKEM',   'Key Engineering Materials', 'P'], #!
      'MSF'   : ['scientificMSF',   'Mater.Sci.Forum', 'P'], #!
      'NHC'   : ['scientificNHC',   'Nano Hybrids and Composites', 'P'],
      'SSP'   : ['scientificSSP',   'Solid State Phenomena', 'P'], #!
      'AST'   : ['scientificAST',   'Advances in Science and Technology', 'P'],
      'CTA'   : ['scientificCTA',   'Construction Technologies and Architecture', 'P']}


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
            (doi, arxiv) = ('', '', '')
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
def convertarticle(journalnumber, filename, contlevel):
    rec = {'jnl' : jc[journalnumber][1], 'tc' : jc[journalnumber][4],
           'note' : [], 'aff' : [], 'auts' : [], 'col' : []}
    #read file
    inf = codecs.EncodedFile(codecs.open(filename, mode='rb'), 'utf8')
    article = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    metas = article.find_all('book-meta')
    for meta in metas:
        #DOI
        for aid in meta.find_all('article-id', attrs = {'pub-id-type' : 'doi'}):
            rec['doi'] = aid.text.strip()
        #arXiv number
        for aid in meta.find_all('article-id', attrs = {'pub-id-type' : 'arxiv'}):
            rec['arxiv'] = aid.text.strip()
        #year
        pds = meta.find_all('pub-date', attrs = {'pub-type' : 'ppub'})
        if not pds:
            pds = meta.find_all('pub-date', attrs = {'pub-type' : 'eub'}):
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
            rec['vol'] = jc[journalnumber][2] + vol.text.strip()        
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
        for aff in cg.find_all('aff'):
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
            for state in aff.find_all('state'}):
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
    for rl in article.find_all('ref-list', attrs = {'id' : 'Bib1'}):
        rec['refs'] = get_references(rl)
    return rec

    
###go through issue directory, collect records
def convertissue(journalnumber, dirname):
    recs = []
    for artdir in os.listdir(dirname):
        print ' - %s' % (artdir)
        artdirfullpath = os.path.join(dirname, artdir)
        if os.path.isdir(artdirfullpath):
            for filename in os.listdir(artdirfullpath):
                if re.search('Meta$', filename):
                    fullfilename = os.path.join(artdirfullpath, filename)
                    rec = convertarticle(journalnumber, fullfilename, 'article')
                    if rec: recs.append(rec)
    print ' -> %i records' % (len(recs))
    if recs:
        if 'vol' in rec.keys():
            if 'issue' in rec.keys():
                jnlfilename = re.sub(' ', '_', '%s%s.%s.%s' % (jc[journalnumber][0], rec['vol'], rec['issue'], cday))
            else:
                jnlfilename = '%s%s.%s' % (jc[journalnumber][0], rec['vol'], cday)
        else:
            jnlfilename = '%s.%s' % (jc[journalnumber][0], cday)
        return (jnlfilename, recs)
    else:
        return ('', [])


###################################################
###crawl through directories of journal/book series
for dirlev1 in os.listdir(sprdir):
    dirlev1fullpath = os.path.join(sprdir, dirlev1)
    #skip non 'BSE'/'JOU' directories
    if not os.path.isdir(dirlev1fullpath):
        continue
    if ((dirlev1fullpath.find('BSE') == -1) and (dirlev1fullpath.find('JOU') == -1)):
        continue
    #extract Springer-number of journal/book
    journalnumber = dirlev1[4:]
    #skip uninteresting journals
    if journalnumber in juninteresting:
        print journalnumber, 'uninteresting'
        continue
    #journal not in list
    if not journalnumber in jc.keys():
        print 'journal skipped: ' + journalnumber
        os.system('echo "check www.springer.com/journal/%s" | mail -s "[SPRINGER] unknown journal" %s' % (journalnumber, 'florian.schwennsen@desy.de'))
        continue
    else:
        print dirlev1fullpath, journalnumber, jc[journalnumber]
    #crawl through directories of volumes (to check for online first)
    for dirlev2 in os.listdir(dirlev1fullpath):
        dirlev2fullpath = os.path.join(dirlev1fullpath, dirlev2)
        onlinefirstpath = os.path.join(dirlev1fullpath, cday)
        #crawl through directories of issues looking for online first articles
        for dirlev3 in os.listdir(dirlev2fullpath):
            #online first create artifical issue directory
            if ('ART' in dirlev3):
		print ' fake ' + dirlev3
                os.renames(os.path.join(dirlev2fullpath, dirlev3), os.path.join(onlinefirstpath, dirlev3))
    #crawl through directories of volumes
    for dirlev2 in os.listdir(dirlev1fullpath):
        dirlev2fullpath = os.path.join(dirlev1fullpath, dirlev2)
        onlinefirstpath = os.path.join(dirlev1fullpath, cday)
        #Book
        if 'BOK' in dirlev2:
            print '==={ %s/%s }==={ %s }===' % (dirlev1, dirlev2, jc[journalnumber][1])
            (jnlfilename, recs) = convertbook(journalnumber, dirlev2fullpath)
            #write xml
            xmlf = os.path.join(xmldir, jnlfilename+'.xml')
            xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
            ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
            xmlfile.close()
            #retrival
            retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
            retfiles_text = open(retfiles_path, "r").read()
            line = jnlfilename+'.xml'+ "\n"
            if not line in retfiles_text:
                retfiles = open(retfiles_path, "a")
                retfiles.write(line)
                retfiles.close()
        #Journal: crawl through directories of issues
        else:
            for dirlev3 in os.listdir(dirlev2fullpath):
                print '==={ %s/%s/%s }==={ %s%s }===' % (dirlev1, dirlev2, dirlev3, jc[journalnumber][1], jc[journalnumber][2])
                dirlev3fullpath = os.path.join(dirlev2fullpath, dirlev3)
                (jnlfilename, recs) = convertissue(journalnumber, dirlev3fullpath)
                #skip online first at the moment
                if 'OF' in jnlfilename:
                    print 'skip online first'
                elif recs:
                    #write xml
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



