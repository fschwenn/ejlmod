# -*- coding: UTF-8 -*-
#program to digest feeds journals from the Hindawi journals
# FS 2021-03-11

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup
import zipfile
import datetime
from refextract import extract_references_from_string

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
ejdir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'
feeddir = '/afs/desy.de/group/library/publisherdata/hindawi'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'HINDAWI'
jids = {'AA' : 'Adv.Astron.',
        'AAA' : 'Abstr.Appl.Anal.',
        'ACMP' : 'Adv.Cond.Mat.Phys.',
        'AHEP' : 'Adv.High Energy Phys.',
        'AMP' : 'Adv.Math.Phys.',
        'IJMMS' : 'Int.J.Math.Math.Sci.',
        'JAM' : 'J.Appl.Math.'}

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

#change pubnote to be digestable by refextract
def cleanpubnote(lit):
    if type(lit) == type([]):
        lit = lit[0]
    lit = re.sub(', vol. ', ', ', lit)
    lit = re.sub(', Article ID ', ', ', lit)
    lit = re.sub('\| *', '', lit)
    lit = re.sub('\| *', '', lit)
    lit = re.sub(', article ', ', ', lit)
    lit = re.sub(', aticle [Nn]o\. ', ', ', lit)
    lit = re.sub('\. View at: , DOI:', ', DOI:', lit)
    lit = re.sub('\. View at: *$', '', lit)
    lit = re.sub('Zeitschrift f.r Physik C, ', 'Z.Phys., C', lit)
    lit = re.sub('Zeitschrift f.r Physik C Particles and Fields, ', 'Z.Phys., C', lit)
    lit = re.sub('Zeitschrift f.r Physik', 'Z.Phys.', lit)
    lit = re.sub('Nuclear Physics. B. Theoretical, Phenomenological, and Experimental High Energy Physics. Quantum Field Theory and Statistical Systems, (\d+), [Nn]o. \d+, ', r'Nucl.Phys., B\1, ', lit)
    lit = re.sub('Nuclear Physics. B. Theoretical, Phenomenological, and Experimental High Energy Physics. Quantum Field Theory and Statistical Systems, (\d+), [Nn]o. \d+.\d+, ', r'Nucl.Phys., B\1, ', lit)
    lit = re.sub('Nuclear Physics. B. Theoretical, Phenomenological, and Experimental High Energy Physics. Quantum Field Theory and Statistical Systems, ', 'Nucl.Phys., B', lit)
    lit = re.sub('Physics Reports, (\d+), [Nn]o. \d+, ', r'Phys.Rept., \1, ', lit)
    lit = re.sub('Physics Reports, (\d+), [Nn]o. \d+.\d+, ', r'Phys.Rept., \1, ', lit)
    lit = re.sub('Nuclear Physics A, (\d+), [Nn]o. \d+, ', r'Nucl.Phys., A\1, ', lit)
    lit = re.sub('Nuclear Physics A, (\d+), [Nn]o. \d+.\d+, ', r'Nucl.Phys., A\1, ', lit)
    lit = re.sub('Nuclear Physics B, (\d+), [Nn]o. \d+, ', r'Nucl.Phys., B\1, ', lit)
    lit = re.sub('Nuclear Physics B, (\d+), [Nn]o. \d+.\d+, ', r'Nucl.Phys., B\1, ', lit)
    lit = re.sub('Physics Letters A, (\d+), [Nn]o. \d+, ', r'Phys.Lett., A\1, ', lit)
    lit = re.sub('Physics Letters A, (\d+).\d+, [Nn]o. \d+, ', r'Phys.Lett., A\1, ', lit)
    lit = re.sub('Physics Letters B, (\d+), [Nn]o. \d+, ', r'Phys.Lett., B\1, ', lit)
    lit = re.sub('Physics Letters B, (\d+), [Nn]o. \d+.\d+, ', r'Phys.Lett., B\1, ', lit)
    lit = re.sub('Physical Review ([ABCDEX]),? (\d{1,3}), (no\.|p\.) (\d{3,6})', r'Phys.Rev., \1\2, \4', lit)
    lit = re.sub('Physics Letters B, B', 'Phys.Lett., B', lit)
    lit = re.sub('Physics of the Dark Universe, ', 'Phys.Dark Univ., ', lit)
    lit = re.sub('The European Physical Journal Plus, (\d+), p\. (\d+)', r'Eur.Phys.J.Plus, \1, \2', lit)
    lit = re.sub('The European Physical Journal Plus, ', 'Eur.Phys.J.Plus, ', lit)
    lit = re.sub('Journal of Physics A: Mathematical and General, ', 'J.Phys., A', lit)
    lit = re.sub('Physics Letters.? A. General, Atomic [aA]nd Solid State Physics, ', 'Phys.Lett., A', lit)
    lit = re.sub('Physics Letters. B. Particle Physics, Nuclear Physics,? [aA]nd Cosmology, ', 'Phys.Lett., B', lit)
    lit = re.sub('Physics Letters B. Particle Physics, Nuclear Physics,? [aA]nd Cosmology, ', 'Phys.Lett., B', lit)
    lit = re.sub('International Journal of Modern Physics A. Particles [aA]nd Fields. Gravitation. Cosmology. Nuclear Physics. ', 'Int.J.Mod.Phys., A', lit)
    lit = re.sub('International Journal of Modern Physics A. Particles [aA]nd Fields. Gravitation. Cosmology. ', 'Int.J.Mod.Phys., A', lit)
    lit = re.sub('International Journal of Modern Physics D. Gravitation, Astrophysics, Cosmology, ', 'Int.J.Mod.Phys., D', lit)
    lit = re.sub('Physical Review C *. [nN]uclear [pP]hysics, ', 'Phys.Rev., C', lit)
    lit = re.sub('Physical Review C *. Covering Nuclear Physics, ', 'Phys.Rev., C', lit)
    lit = re.sub('Physical Review D *. Covering Particles, Fields, Gravitation,? [aA]nd Cosmology, ', 'Phys.Rev., D', lit)
    lit = re.sub('Physical Review D *. Particles, Fields, Gravitation,? [aA]nd Cosmology, ', 'Phys.Rev., D', lit)
    lit = re.sub('Physics Letters, Section B: Nuclear, Elementary Particle and High-Energy Physics, ', 'Phys.Lett., B', lit)
    lit = re.sub('Astronomy & Astrophysics *, ', 'Astron.Astrophys., ', lit)
    lit = re.sub('The Astrophysical Journal Letters, (\d+) , [Nn]o. L(\d+)', r'Astrophys.J.Lett., \1, L\2', lit)
    lit = re.sub('European Physical Journal A: Hadrons and Nuclei ', 'Eur.Phys.J., A', lit)
    lit = re.sub('The European Physical Journal A, ', 'Eur.Phys.J., A', lit)
    lit = re.sub('The European Physical Journal B, ', 'Eur.Phys.J., B', lit)
    lit = re.sub('European Physical Journal C: Particles and Fields ', 'Eur.Phys.J., C', lit)
    lit = re.sub('The European Physical Journal C, ', 'Eur.Phys.J., C', lit)
    lit = re.sub('The European Physical Journal D, ', 'Eur.Phys.J., D', lit)
    lit = re.sub('The European Physical Journal E, ', 'Eur.Phys.J., E', lit)
    lit = re.sub('Journal of Physics A: Mathematical and General ', 'J.Phys.,A', lit)
    lit = re.sub('Journal of Physics: Conference Series, ', 'J.Phys.Conf.Ser. ', lit)
    lit = re.sub('Journal of Cosmology and Astroparticle Physics', 'JCAP', lit)
    lit = re.sub('Journal of High Energy Physics', 'JHEP', lit)
    lit = re.sub('Nuclear Physics B.Proceedings Supplements, ', 'Nucl.Phys.Proc.Suppl., ', lit)
    lit = re.sub('Advances in Theoretical and Mathematical Physics', 'Adv.Theor.Math.Phys.', lit)
    lit = re.sub('Physics Letters, Section A: General, Atomic and Solid State Physics, ', 'Phys.Lett., A', lit)
    lit = re.sub('Nuclear Instruments and Methods in Physics Research Section A, ', 'Nucl.Instrum.Meth., A', lit)
    lit = re.sub('Nuclear Instruments and Methods in Physics Research Section B, ', 'Nucl.Instrum.Meth., B', lit)
    lit = re.sub('Nuclear Instruments and Methods in Physics Research Section A: Accelerators, Spectrometers, Detectors and Associated Equipment,? ', 'Nucl.Instrum.Meth., A', lit)
    lit = re.sub(', pp. ', ', ', lit)
    lit = re.sub(u'\u201d', '"', lit)
    lit = re.sub(u'\u201c', '"', lit)
    lit = re.sub(u'\u2013', '-', lit)
    lit = re.sub(u'\u2018', "'", lit)
    lit = re.sub(u'\u2019', "'", lit)
    lit = re.sub(', [Nn]o. [0-9\-]+,? ', ', ', lit)
    return lit

#extract references (copied from springer.nlm.py: mixed-citation->element-citation)
def get_references(rl):
    refs =  []
    #convert individual references
    for ref in rl.find_all('ref'):
        (lt, refno) = ('', '')
        for label in ref.find_all('label'):
            lt = label.text.strip()
            lt = re.sub('\W', '', lt)
            if re.search('\[', lt):
                refno = '%s ' % (lt)
            else:
                refno = '[%s] ' % (lt)
        #journal
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : 'journal'}):
            (title, authors, pbn, doi) = ('', [], '', '')
            #authors
            for nametag in mc.find_all('name'):
                name = ''
                for gn in nametag.find_all('given-names'):
                    name = gn.text.strip()
                for sn in nametag.find_all('surname'):
                    name += ' ' + sn.text.strip()
                authors.append(name)
            #title
            for at in mc.find_all('article-title'):
                #title = at.text.strip()
                title = cleanformulas(at)
            #pubnote
            for source in mc.find_all('source'):
                pbn = source.text.strip()
            for volume in mc.find_all('volume'):
                pbn += ' ' + volume.text.strip()
            for issue in mc.find_all('issue'):
                pbn += ', No. ' + issue.text.strip()
            for year in mc.find_all('year'):
                pbn += ' (%s) ' % (year.text.strip())
            for fpage in mc.find_all('fpage'):
                pbn += ' ' + fpage.text.strip()
            for lpage in mc.find_all('lpage'):
                pbn += '-' + lpage.text.strip()
            #refextract on pbn to normalize it
            repbn = extract_references_from_string(pbn, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}")
            if 'journal_reference' in repbn[0].keys():
                #print ' [refextract] normalize "%s" to "%s"' % (pbn, repbn[0]['journal_reference'])
                pbn = repbn[0]['journal_reference']
            #DOI
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'doi'}):
                doi = pi.text.strip()
            #all together
            if doi:
                reference = [('x', refno + '%s, "%s", %s, DOI: %s' % (', '.join(authors[:4]), title, cleanpubnote(pbn), doi))]
#skip refextract since we have DOI                reference.append(('a', 'doi:'+doi))
#                if lt: reference.append(('o', re.sub('\D', '', lt)))
            else:
                reference = [('x', refno + '%s, "%s", %s' % (', '.join(authors[:4]), title, cleanpubnote(pbn)))]
            refs.append(reference)
        #book
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : ['confproc', 'book']}):
            (atitle, btitle, editors, authors, pbn, bpbn, doi) = ('', '', [], [], '', '', '')
            #authors/editors
            for pg in mc.find_all('person-group'):
                for nametag in mc.find_all('name'):
                    name = ''
                    for gn in nametag.find_all('given-names'):
                        name = gn.text.strip()
                    for sn in nametag.find_all('surname'):
                        name += ' ' + sn.text.strip()
                    if pg['person-group-type'] == 'author':
                        authors.append(name)
                    elif pg['person-group-type'] == 'editor':
                        editors.append(name)
            #title
            for at in mc.find_all('article-title'):
                atitle = cleanformulas(at)
            #book title
            for source in mc.find_all('source'):
                btitle = cleanformulas(source)
            #book pubnote
            for publishername in mc.find_all('publisher-name'):
                bpbn = publishername.text.strip() + ', '
            for publisherloc in mc.find_all('publisher-loc'):
                bpbn += publisherloc.text.strip() + ', '
            for year in mc.find_all('year'):
                bpbn += year.text.strip()
            #pubnote
            for fpage in mc.find_all('fpage'):
                pbn += ' ' + fpage.text.strip()
            for lpage in mc.find_all('lpage'):
                pbn += '-' + lpage.text.strip()
            #all together
            if atitle:
                refs.append([('x', refno + '%s: "%s", pages %s in: %s: %s, %s' % (', '.join(authors[:4]), atitle, pbn, ', '.join(editors), btitle, bpbn))])
            else:
                refs.append([('x', refno + '%s: "%s", %s' % (', '.join(authors[:4]), btitle, bpbn))])
        #other
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : 'other'}):
            (doi, recid, arxiv) = ('', '', '')
            #INSPIRE links
            inspirelink = ''
            for el in mc.find_all('ext-link', attrs = {'ext-link-type' : 'uri'}):
                if el.has_attr('xlink:href'):
                    link = el['xlink:href']
                    if re.search('inspirehep.net.*IRN', link):
                        irn = re.sub('.*\D', '', link)
                        #inspire2 for recid in search_pattern(p='970__a:SPIRES-' + irn):
                        #inspire2    inspirelink += ', https://old.inspirehep.net/record/%i' % (recid)
                        #inspire2 el.decompose()
                    elif re.search('inspirehep.net.*recid', link):
                        recid = re.sub('.*\D', '', link)
                        inspirelink += ', https://old.inspirehep.net/record/%s' % (recid)
                        el.decompose()
                    elif re.search('inspirehep.net', link):
                        el.decompose()
                    elif re.search('arxiv.org', link) and not re.search('submit', link):
                        arxiv = re.sub(' ', '', el.text.strip())
                        arxiv = re.sub('^\[', '', arxiv)
                        arxiv = re.sub('(\d)\]$', r'\1', arxiv)
                        if re.search('^\d{4}\.\d', arxiv):
                            arxiv = 'arXiv:' + arxiv
                        elif re.search('ar[xX]iv\:[a-z\-]+\/\d',  arxiv):
                            arxiv = arxiv[6:]
                        el.decompose()
            #missing spaces?
            for bold in mc.find_all('bold'):
                bt = bold.text.strip()
                bold.replace_with(' %s ' % (bt))
            #DOI
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'doi'}):
                doi = pi.text.strip()
                pi.replace_with(', DOI: %s' % (doi))
            #all together
            reference = [('x', refno + cleanpubnote(cleanformulas(mc)))]
#            if doi:
#                reference.append(('a', 'doi:'+doi))
#            if recid:
#                reference.append(('0', str(recid)))
#            if arxiv:
#                reference.append(('r', arxiv))
#            if doi or recid or arxiv:
#                if lt: reference.append(('o', re.sub('\D', '', lt)))
            refs.append(reference)
    return refs


#extract individual article
def extractrecord(publisherfile):
    inf = codecs.EncodedFile(codecs.open(publisherfile, mode='rb'), 'utf8')
    hindawirecord = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    rec = {'tc' : 'P', 'aff' : [], 'auts' : [], 'note' : []}
    category = False
    #FRONT
    for front in hindawirecord.find_all('front'):
        #journalname
        for jid in front.find_all('journal-id'):
            if jid.text in jids.keys():
                rec['jnl'] = jids[jid.text]
        #article id
        for aid in front.find_all('article-id'):
            if aid.has_attr('pub-id-type'):
                if aid['pub-id-type'] == 'publisher-id':
                    rec['p1'] = aid.text
                elif aid['pub-id-type'] == 'doi':
                    rec['doi'] = aid.text
                elif aid['pub-id-type'] == 'arxiv':
                    if aid.text != 'null':
                        rec['arxiv'] = aid.text
        #volume
        for vol in front.find_all('volume'):
            rec['vol'] = vol.text
        #pages
        for pgs in front.find_all('page-count'):
            rec['pages'] = pgs['count']
        #article category
        for ac in front.find_all('article-categories'):
            category = ac.text
            rec['note'].append(category)
        #title
        for at in front.find_all('article-title'):
            rec['tit'] = at.text
        #date
        for pd in front.find_all('pub-date', attrs = {'pub-type' : 'archival-date'}):
            for year in pd.find_all('year'):
                rec['date'] = year.text.strip()
            for month in pd.find_all('month'):
                rec['date'] += '-' + month.text.strip()
            for day in pd.find_all('day'):
                rec['date'] += '-' + day.text.strip()
        #abstract
        for abstract in front.find_all('abstract'):
            rec['abs'] = abstract.text
        #license
        for permissions in front.find_all('permissions'):
            for licence in permissions.find_all('license'):
                if licence.has_attr('xlink:href'):
                    if re.search('creativecommons.org', licence['xlink:href']):
                        rec['license'] = {'url' : licence['xlink:href']}
                        rec['FFT'] = 'http://downloads.hindawi.com/journals/%s/%s/%s.pdf' % (jid.text.lower(), rec['vol'], rec['p1'])
        #affiliations
        for aff in front.find_all('aff'):
            for al in aff.find_all(['addr-line', 'country']):
                alt = al.text + ', '
                al.replace_with(alt)
            for sup in aff.find_all('sup'):
                sup.decompose()
            for el in aff.find_all('ext-link'):
                elt = ' link: ' + el.text
            rec['aff'].append('%s= %s' % (aff['id'], aff.text))
        #authors
        for contrib in front.find_all('contrib', attrs = {'contrib-type' : 'author'}):
            for name in contrib.find_all('name'):
                for sn in name.find_all('surname'):
                    authorname = sn.text.strip()
                for gn in name.find_all('given-names'):
                    authorname += ', %s' % (gn.text.strip())
                #ORCID
                for cid in contrib.find_all('contrib-id', attrs = {'contrib-id-type' : 'orcid'}):
                    authorname += re.sub('.*\/', ', ORCID:', cid.text.strip())
                #Email
                if not re.search('ORCID:', authorname):
                    for email in contrib.find_all('email'):
                        authorname += ', EMAIL:' + email.text
                rec['auts'].append(authorname)
                #Affiliation
                for xref in contrib.find_all('xref', attrs = {'ref-type' : 'aff'}):
                    rec['auts'].append('=%s' % (xref['rid']))
    #BACK
    for back in hindawirecord.find_all('back'):
        for rl in back.find_all('ref-list'):
            rec['refs'] = get_references(rl)
    if category and category in ['Editorial']:
        print '  skip %s' % (category)
        return False
    else:
        print '  ', rec.keys()
        return rec

#check for new zips
todo = []
for datei in os.listdir(feeddir):
    if re.search('hindawi.*zip$', datei):
        print '[%s]' % (datei)
        todo.append(datei)
        os.system('cp %s/%s %s/tmp/' % (feeddir, datei, feeddir))
        zfile = zipfile.ZipFile(os.path.join(feeddir, 'tmp', datei))
        zfile.extractall(os.path.join(feeddir, 'tmp'))

#scan feed directory
for ordner in os.listdir(os.path.join(feeddir, 'tmp')):
    if os.path.isdir(os.path.join(feeddir, 'tmp', ordner)):
        for ordner2 in os.listdir(os.path.join(feeddir, 'tmp', ordner)):
            for ordner3 in os.listdir(os.path.join(feeddir, 'tmp', ordner, ordner2)):
                print '---{ %s }---' % (ordner3)
                recs = []
                for datei in os.listdir(os.path.join(feeddir, 'tmp', ordner, ordner2, ordner3)):
                    rec = extractrecord(os.path.join(feeddir, 'tmp', ordner, ordner2, ordner3, datei))
                    if rec: recs.append(rec)
                if recs:
                    jnlfilename = 'hindawi%s.%s' % (ordner3, stampoftoday)
                    #closing of files and printing
                    xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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

#cleanup
for datei in todo:
    os.system('mv %s/%s %s/done/' % (feeddir, datei, feeddir))
    os.system('rm -rf %s/tmp/*/' % (feeddir))




