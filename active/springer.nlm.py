# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to convert Springer xml files (JATS) into doki format
# FS 2019-11-28
#
#Russian Journals missing
#
#

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
from invenio.search_engine import search_pattern


sprdir = '/afs/desy.de/group/library/publisherdata/springer'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'Springer'

#current timestamp (or other unique mark)
cday = sys.argv[1]

# uninteresting journals:
juninteresting = ['00153', '11105', '00426', '00477']

#dictionary of journal names
# springer journal id : [file name, INPIRE journal name, letter for volume, russian journal name, type code, book series]
jc = {'00006': ['aaca', 'Adv.Appl.Clifford Algebras', '', '', 'P'],
      '00016': ['pip', 'Phys.Perspect.', '', '', 'P'],
      '00023': ['ahp', 'Annales Henri Poincare', '', '', 'P'],
      '00159': ['aar', 'Astron.Astrophys.Rev.', '', '', 'P'],
      '00220': ['cmp', 'Commun.Math.Phys.', '', '', 'P'],
      '00339': ['apa', 'Appl.Phys.', 'A', '', 'P'], #HAL
      '00340': ['apb', 'Appl.Phys.', 'B', '', 'P'], #HAL
      '00601': ['fbs', 'Few Body Syst.', '', '', 'P'],
      '10050': ['epja', 'Eur.Phys.J.', 'A', '', 'P'],
      '10051': ['epjb', 'Eur.Phys.J.', 'B', '', 'P'],
      '10052': ['epjc', 'Eur.Phys.J.', 'C', '', 'P'],
      '10053': ['epjd', 'Eur.Phys.J.', 'D', '', 'P'],
      '10509': ['ass', 'Astrophys.Space Sci.', '', '', 'P'],
      '10511': ['ast', 'Astrophysics', '', '', 'P'],
      '10582': ['czjp', 'Czech.J.Phys.', '', '', 'P'], # stopped 2006
      '10686': ['ea', 'Exper.Astron.', '', '', 'P'],
      '10701': ['fp', 'Found.Phys.', '', '', 'P'],
      '10702': ['fpl', 'Found.Phys.Lett.', '', '', 'P'], # stopped 2006
      '10714': ['grg', 'Gen.Rel.Grav.', '', '', 'P'],
      '10723': ['jgc', 'J.Grid Comput.', '', '', 'P'],
      '10740': ['hite', 'High Temperature', '', 'Teplofizika Vysokikh Temperatur', 'P'],
      '10751': ['hypfin', 'Hyperfine Interact.', '', '', 'P'],
      '10773': ['ijtp', 'Int.J.Theor.Phys.', '', '', 'P'],
      '10781': ['fias', 'FIAS Interdisc.Sci.Ser.', '', '', 'P'],
      '10786': ['iet', 'Instrum.Exp.Tech.', '', '', 'P'],
      '10853': ['jmsme', 'J.Mater.Sci.', '', '', 'P'],
      '10909': ['jltp', 'J.Low.Temp.Phys.', '', '', 'P'],
      '10955': ['jstatphys', 'J.Statist.Phys.', '', '', 'P'],
      '10958': ['jms', 'J.Math.Sci.', 'Zap.Nauchn.Semin.', '', '', 'P'],
      '10967': ['jrnc', 'J.Radioanal.Nucl.Chem.', '', '', 'P'],
      '11005': ['lmp', 'Lett.Math.Phys.', '', '', 'P'],
      '11006': ['matnot', 'Math.Notes', '', '', 'P'],
      '11018': ['mt', 'Meas.Tech.', '', '', 'P'],
      '11040': ['mpag', 'Math.Phys.Anal.Geom.', '', '', 'P'],
      '11139': ['ramanujan', 'Ramanujan J.', '', '', 'P'],
      '11182': ['rpj', 'Russ.Phys.J.', '', 'Izv.Vuz.Fiz.', 'P'],
      '11207': ['soph', 'Solar Phys.', '', '', 'P'],#HAL
      '11214': ['ssr', 'Space Sci.Rev.', '', '', 'P'],
      '11232': ['tmp', 'Theor.Math.Phys.', '', 'Teor.Mat.Fiz.', 'P'],
      '11425': ['sica', 'Sci.China Math.', '', '', 'P'],
      '11433': ['sicg', 'Sci.China Phys.Mech.Astron.', '', '', 'P'],
      '11434': ['csb', 'Chin.Sci.Bull.', '', '', 'P'],
      '11443': ['al', 'Astron.Lett.', '', '', 'P'],
      '11444': ['ar', 'Astron.Rep.', '', '', 'P'],
      '11446': ['dok', 'Dokl.Phys.', '', '', 'P'],
      '11447': ['jetp', 'J.Exp.Theor.Phys.', '', 'Zh.Eksp.Teor.Fiz.', 'P'],
      '11448': ['jtpl', 'JETP Lett.', '', 'Pisma Zh.Eksp.Teor.Fiz.', 'P'],
      '11450': ['pan', 'Phys.At.Nucl.', '', 'Yad.Fiz.', 'P'],
      '11451': ['ptss', 'Sov.Phys.Solid State', '', 'Fiz.Tverd.Tela', 'P'],
      '11452': ['plpr', 'Plasma Phys.Rep.', '', 'Fiz.Plasmy', 'P'],
      '11454': ['tp', 'Tech.Phys.', '', '', 'P'],
      '11455': ['tpl', 'Tech.Phys.Lett.', '', '', 'P'],
      '11467': ['fpc', 'Front.Phys.(Beijing)', '', '', 'P'],
      '11470': ['cmmp', 'Comput.Math., Math.Phys.', '', '', 'P'],
      '11490': ['lasp', 'Laser Phys.', '', '', 'P'], # stopped 2012
      '11496': ['ppn', 'Phys.Part.Nucl.', '', 'Fiz.Elem.Chast.Atom.Yadra', 'P'],
      '11497': ['ppnl', 'Phys.Part.Nucl.Lett.', '', 'Pisma Fiz.Elem.Chast.Atom.Yadra', 'P'],
      '11503': ['rjmp', 'Russ.J.Math.Phys.', '', '', 'P'],
      '11534': ['cejp', 'Central Eur.J.Phys.', '', '', 'P'], # stopped 2014
      '11734': ['epjst', 'Eur.Phys.J.ST', '', '', 'P'],
      '11755': ['ab', 'Astrophys.Bull.', '', '', 'P'],
      '11953': ['blpi', 'Bull.Lebedev Phys.Inst.', '', '', 'P'],
      '11954': ['brasp', 'Bull.Russ.Acad.Sci.Phys.', '', 'Izv.Ross.Akad.Nauk Ser.Fiz.', 'P'],
      '11958': ['jocoph', 'J.Contemp.Phys.', '', 'Izv.Akad.Nauk Arm.SSR Fiz.', 'P'],
      '11972': ['mupb', 'Moscow Univ.Phys.Bull.', '', '', 'P'],
      '12036': ['jasas', 'J.Astrophys.Astron.', '', '', 'P'],
      '12043': ['pramana', 'Pramana', '', '', 'P'],
      '12267': ['gc', 'Grav.Cosmol.', '', '', 'P'],
      '12648': ['ijp', 'Indian J.Phys.', '', '', 'P'],
      '13129': ['epjh', 'Eur.Phys.J.', 'H', '', 'P'],
      '13130': ['jhep', 'JHEP', '', '', 'P'],
      '13324': ['anmp', 'Anal.Math.Phys.', '', '', 'P'],
      '13360': ['epjp', 'Eur.Phys.J.Plus', '', '', 'P'],
      '13538': ['bjp', 'Braz.J.Phys.', '', '', 'P'],
      '40010': ['pnisia', 'Proc.Nat.Inst.Sci.India (Pt.A Phys.Sci.)', '', '', 'P'],
      '40042': ['jkps', 'J.Korean Phys.Soc.', '', '', 'P'],
      '40065': ['arjoma', 'Arab.J.Math.', '', '', 'P'],
      '40485': ['epjti', 'EPJ Tech.Instrum.', '', '', 'P'],
      '40509': ['qsmf', 'Quant.Stud.Math.Found.', '', '', 'P'],
      '40623': ['eaplsc', 'Earth Planets Space', '', '', 'P'],
      '40766': ['rnc', 'Riv.Nuovo Cim.', '', '', 'PR'],
      '40995': ['ijsta', 'Iran.J.Sci.Technol.A', '', '', 'P'],
      '41114': ['lrr', 'Living Rev.Rel.', '', '', 'R'],
      '41365': ['nst', 'Nucl.Sci.Tech.', '', '', 'P'],
      '41467': ['natcomm', 'Nature Commun.', '', '', 'P'],
      '41550': ['natastr', 'Nat.Astron.', '', '', 'P'],
      '41566': ['natphoton', 'Nature Photon.', '', '', 'P'],
      '41567': ['natphys', 'Nature Phys.', '', '', 'P'],
      '41586': ['nature', 'Nature', '', '', 'P'],
      '41598': ['scirep', 'Sci.Rep.', '', '', 'P'],
      '41605': ['rdtm', 'Rad.Det.Tech.Meth.', '', '', 'P'],
      '41781': ['csbg', 'Comput.Softw.Big Sci.', '', '', 'P'],
      '42254': ['natrp', 'Nature Rev.Phys.', '', '', 'P'],
#Books
       '0304': ['lnm', 'Lect.Notes Math.', '', '', 'PS', ''],
       '0361': ['spprph', 'Springer Proc.Phys.', '', '', 'C', ''],
       '0426': ['stmp', 'Springer Tracts Mod.Phys.', '', '', 'S', ''],
       '0720': ['thmaph', 'Theor.Math.Phys.', '', '', 'S', ''], #???
       '0840': ['grtecoph', 'Graduate Texts Contemp.Phys.', '', '', 'S', ''], # stopped 2005
       '0848': ['asasli', 'Astron.Astrophys.Lib.', '', '', 'S', ''],
       '3052': ['acph', 'Accel.Phys.', '', '', 'S', ''], # stopped 1998
       '4308': ['adteph', 'Adv.Texts Phys.', '', '', 'S', ''], # stopped 2007
       '4813': ['prmaph', 'Prog.Math.Phys.', '', '', 'S', ''],
       '4890': ['eist', 'Einstein Studies', '', '', 'S', ''], #stopped 2012
       '5267': ['paacde', 'Part.Accel.Detect.', '', '', 'S', ''],
       '5304': ['lnp', 'Lect.Notes Phys.', '', '', 'PS', ''],
       '5664': ['assl', 'Astrophys.Space Sci.Libr.', '', '', 'S', ''],
       '6001': ['futhph', 'Fundam.Theor.Phys.', '', '', 'S', ''],
       '6316': ['mpstud', 'Math.Phys.Stud.', '', '', 'S', ''],
       '7395': ['assp', 'Astrophys.Space Sci.Proc.', '', '', 'C', ''],


       '5584': ['aemb', 'BOOK', '', '', 'S', 'Advances in Experimental Medicine and Biology'], #whole book
       '4848': ['pim', 'Progress in Mathematics' , '', '', 'S', ''], #whole book (327)
      '15602': ['sscml', 'BOOK', '', '', 'S', 'The Springer Series on Challenges in Machine Learning'], #Einzelaufnah
      '15585': ['icme', 'BOOK', '', '', 'C', ''], #einzelaufnahmen


       '8389': ['nophsc', 'Nonlin.Phys.Sci.', '', '', 'S', ''], # stopped 2013?
       '8431': ['gtip', 'BOOK', '', '', 'S', 'Grad.Texts Math.'],
       '8790': ['sprthe', 'BOOK', '', '', 'T', 'Springer Theses'], #Springer Theses
       '8806': ['spprma', 'Springer Proc.Math.', '', '', 'C', ''], #discontinued
       '8902': ['sprbip', 'BOOK', '', '', 'S', 'SpringerBriefs in Physics'],
      '10502': ['fimono', 'Fields Inst.Monogr.', '', '', 'S', ''], #Fields Institute Monographs
      '10503': ['ficomm', 'Fields Inst.Commun.', '', '', 'S']} #Fields Institute Communications

#known conferences
confdict = {'Proceedings of the 7th International Conference on Trapped Charged Particles and Fundamental Physics (TCP 2018), Traverse City, Michigan, USA, 30 September-5 October 2018' : 'C18-09-30'}


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
        (lt, refno) = ('', '')
        for label in ref.find_all('label'):
            lt = label.text.strip()
            if re.search('\[', lt):
                refno = '%s ' % (label.text.strip())
            else:
                refno = '[%s] ' % (label.text.strip())
        #journal
        for mc in ref.find_all('mixed-citation', attrs = {'publication-type' : 'journal'}):
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
            #DOI
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'doi'}):
                doi = pi.text.strip()
            #all together            
            if doi:
                reference = [('x', refno + '%s: %s, %s, DOI: %s' % (', '.join(authors), title, pbn, doi))]
                reference.append(('a', 'doi:'+doi))
                if lt: reference.append(('o', re.sub('\D', '', lt)))
            else:
                reference = [('x', refno + '%s: %s, %s' % (', '.join(authors), title, pbn))]
            refs.append(reference)
        #book
        for mc in ref.find_all('mixed-citation', attrs = {'publication-type' : ['confproc', 'book']}):
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
                refs.append([('x', refno + '%s: %s, pages %s in: %s: %s, %s' % (', '.join(authors), atitle, pbn, ', '.join(editors), btitle, bpbn))])
            else:
                refs.append([('x', refno + '%s: %s, %s' % (', '.join(authors), btitle, bpbn))])
        #other
        for mc in ref.find_all('mixed-citation', attrs = {'publication-type' : 'other'}):
            (doi, recid, arxiv) = ('', '', '')
            #INSPIRE links
            inspirelink = ''
            for el in mc.find_all('ext-link', attrs = {'ext-link-type' : 'uri'}):
                if el.has_attr('xlink:href'):
                    link = el['xlink:href']
                    if re.search('inspirehep.net.*IRN', link):
                        irn = re.sub('.*\D', '', link)
                        for recid in search_pattern(p='970__a:SPIRES-' + irn):
                            inspirelink += ', https://inspirehep.net/record/%i' % (recid)
                        el.decompose()
                    elif re.search('inspirehep.net.*recid', link):
                        recid = re.sub('.*\D', '', link)
                        inspirelink += ', https://inspirehep.net/record/%s' % (recid)
                        el.decompose()
                    elif re.search('inspirehep.net', link):
                        el.decompose()
                    elif re.search('arxiv.org', link):
                        arxiv = el.text.strip()
            #DOI
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'doi'}):
                doi = pi.text.strip()
                pi.replace_with(', DOI: %s' % (doi))
            #all together
            reference = [('x', refno + cleanformulas(mc))]
            if doi:
                reference.append(('a', 'doi:'+doi))
                if lt: reference.append(('o', re.sub('\D', '', lt)))
            if recid:
                reference.append(('0', str(recid)))
                if lt: reference.append(('o', re.sub('\D', '', lt)))
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
    if contlevel == 'article':
        metas = article.find_all('article-meta')
    elif contlevel == 'chapter':
        metas = article.find_all('book-part-meta')
    elif contlevel == 'book':
        metas = article.find_all('book-meta')
    for meta in metas:
        #DOI
        if contlevel == 'article':
            for aid in meta.find_all('article-id', attrs = {'pub-id-type' : 'doi'}):
                rec['doi'] = aid.text.strip()
        elif contlevel == 'chapter':
            for bpid in meta.find_all('book-part-id', attrs = {'book-part-id-type' : 'doi'}):
                rec['doi'] = bpid.text.strip()
        elif contlevel == 'book':
            for bid in meta.find_all('book-id', attrs = {'book-id-type' : 'doi'}):
                rec['doi'] = bid.text.strip()
        #bookseries as bookseries
        if len(jc[journalnumber]) > 5 and jc[journalnumber][5]:
            series = [('a', jc[journalnumber][5])]
            for bvn in article.find_all('book-volume-number'):
                series.append(('v', bvn.text.strip()))
            rec['bookseries'] = series
        #bookseries as journal
        else:
            for bvn in article.find_all('book-volume-number'):
                if jc[journalnumber][1] != 'BOOK':
                    rec['vol'] =  bvn.text.strip()
        #isbn
        if contlevel == 'book':
            rec['isbns'] = []
            for isbn in meta.find_all('isbn'):
                if isbn.has_attr('content-type'):
                    if isbn['content-type'] == 'ppub':
                        rec['isbns'].append([('b', 'Print'), ('a', re.sub('\D', '', isbn.text.strip()))])
                    elif isbn['content-type'] == 'epub':
                        rec['isbns'].append([('b', 'Online'), ('a', re.sub('\D', '', isbn.text.strip()))])
                    else:
                        rec['isbns'].append([('a', re.sub('\D', isbn.text.strip()))])
        #arXiv number
        for aid in meta.find_all('article-id', attrs = {'pub-id-type' : 'arxiv'}):
            rec['arxiv'] = aid.text.strip()
        #article type
        for ac in meta.find_all('article-categories'):
            for subj in ac.find_all('subject'):
                subjt = subj.text.strip()
                if re.search('[a-zA-Z]', subjt):
                    rec['note'].append(subjt)
                if subjt in ['Review', 'Review Article', 'Review Paper', 'Short Review', 'Systematic Review']:
                    if not 'R' in rec['tc']:
                        rec['tc'] += 'R'
                elif subjt in ['Editorial', 'News Q&A', 'Correspondence', 'News And Views', 'Career Q&A',
                               'Career News', 'Outlook', 'Technology Feature', 'Book Review', 'Obituary', 'News',
                               'Books And Arts', 'World View', 'Seven Days', 'Career Column', 'Career Brief',
                               'Futures']:
                    return {}
                #check whether article in fact is part of proceedings
                elif re.search('Proceedings of ', subjt) and 'P' in rec['tc']:
                    rec['tc'] = 'C'
                    if subjt in confdict.keys():
                        rec['cnum'] = confdict[subjt]
        #title # xml:lang="en" ?
        for tg in meta.find_all('title-group'): 
            for at in tg.find_all(['article-title', 'title']):
                rec['tit'] = cleanformulas(at)
            for st in tg.find_all('subtitle'):
                rec['tit'] += ': %s' % (cleanformulas(st))
            if at.has_attr('xml:lang') and at['xml:lang'] != 'en':
                #language
                if at['xml:lang'] == 'de':
                    rec['language'] = 'german'
                elif at['xml:lang'] == 'fr':
                    rec['language'] = 'french'
                #translated title
                for ttg in meta.find_all('trans-title-group'):
                    for tt in ttg.find_all('trans-title', attrs = {'xml:lang' : 'en'}):
                        rec['transtit'] = cleanformulas(tt)
                    for st in ttg.find_all('subtitle', attrs = {'xml:lang' : 'en'}):
                        rec['transtit'] += ': %s' % (cleanformulas(st))
        #year
        for pd in meta.find_all('pub-date', attrs = {'date-type' : 'collection'}):
            for year in pd.find_all('year'):
                rec['year'] = year.text.strip()
        #date
        for pd in meta.find_all('pub-date', attrs = {'date-type' : 'epub'}):
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
        #special case JHEP
            if journalnumber in ['13130']:
                rec['vol'] = '%s%02i' % (rec['year'][2:],int(rec['issue']))
                del rec['issue']
        #first page
        for p1 in meta.find_all('fpage'):
            rec['p1'] = p1.text.strip()
        #last page
        for p2 in meta.find_all('lpage'):
            rec['p2'] = p2.text.strip()
        #article ID
        for eid in meta.find_all('elocation-id'):
            if journalnumber == '13130':
                rec['p1'] = '%03i' % (int(eid.text.strip()))
            else:
                rec['p1'] = eid.text.strip()
            #remove pagination information if there is an article ID
            if 'p2' in rec.keys():
                del rec['p2']            
        #abstract
        abstracts = meta.find_all('abstract', attrs = {'xml:lang' : 'en'})
        if not abstracts:
            abstracts = meta.find_all('abstract')
        for abstract in abstracts:
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
            rec['note'].append(conf.text.strip())
        #PACS
        for kwg in meta.find_all('kwd-group'):
            for title in kwg.find_all('title'):
                if re.search('PACS', title.text):
                    rec['pacs'] = []
                    for kw in kwg.find_all('kwd'):
                        rec['pacs'].append(kw.text.strip())
        #keywords
        kwgs = meta.find_all('kwd-group', attrs = {'xml:lang' : 'en'})
        if not kwgs:
            kwgs = meta.find_all('kwd-group')            
        for kwg in kwgs:
            if kwg.has_attr('xml:lang'):
                rec['keyw'] = []
                for kw in kwg.find_all('kwd'):
                    rec['keyw'].append(kw.text.strip())
        #corrected article
        for ra in meta.find_all('related-article', attrs = {'related-article-type' : 'corrected-article'}):
            if ra.has_attr('xlink:href'):
                rec['tit'] += ' [doi: %s]' % (ra['xlink:href'])            
        #emails
        emails = {}
        for an in meta.find_all('author-notes'):
            for cor in an.find_all('corresp'):
                for email in cor.find_all('email'):
                    emails[cor['id']] = email.text.strip()
        for cg in meta.find_all('contrib-group'):            
            #affiliations
            for aff in cg.find_all('aff'):
                afftext = ''
                #Division
                for od in aff.find_all('institution', attrs = {'content-type' : 'org-division'}):
                    afftext += od.text.strip() + ', '
                #University
                for on in aff.find_all('institution', attrs = {'content-type' : 'org-name'}):
                    afftext += on.text.strip() + ', '
                #Postbox
                for postbox in aff.find_all('addr-line', attrs = {'content-type' : 'postbox'}):
                    afftext += postbox.text.strip() + ', '
                #Street
                for street in aff.find_all('addr-line', attrs = {'content-type' : 'street'}):
                    afftext += street.text.strip() + ', '
                #Postal Code
                for pc in aff.find_all('addr-line', attrs = {'content-type' : 'postcode'}):
                    afftext += pc.text.strip() + ' '
                #City
                for city in aff.find_all('addr-line', attrs = {'content-type' : 'city'}):
                    afftext += city.text.strip() + ', '
                #State
                for state in aff.find_all('addr-line', attrs = {'content-type' : 'state'}):
                    afftext += state.text.strip() + ', '
                #Country
                for country in aff.find_all('country'):
                    afftext += country.text.strip()
                #GRID
                for grid in aff.find_all('institution-id', attrs = {'institution-id-type' : 'GRID'}):
                    afftext += ', GRID:%s' % (grid.text.strip())
                rec['aff'].append('%s= %s' % (aff['id'], afftext))
        #check for editor
        authortype = 'author'
        if contlevel == 'book':
            if meta.find_all('contrib', attrs = {'contrib-type' : 'editor'}):
                authortype = 'editor'
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
                    for xref in contrib.find_all('xref', attrs = {'ref-type' : 'corresp'}):
                        if xref['rid'] in emails.keys():
                            authorname += ', EMAIL:' + emails[xref['rid']]
                    if not re.search('EMAIL:', authorname):
                        for adr in contrib.find_all('address'):
                            for email in adr.find_all('email'):
                                authorname += ', EMAIL:' + email.text.strip()
                rec['auts'].append(authorname)
                #Affiliation
                for xref in contrib.find_all('xref', attrs = {'ref-type' : 'aff'}):
                    rec['auts'].append('=%s' % (xref['rid']))
            #collaboration
            for coll in contrib.find_all('collab'):
                for email in coll.find_all('email'):
                    email.decompose()
                rec['col'].append(coll.text.strip())
    #references
    for rl in article.find_all('ref-list', attrs = {'id' : 'Bib1'}):
        rec['refs'] = get_references(rl)
    return rec

###go through book directory, collect records; create HA
def convertbook(journalnumber, dirname):
    isbn = re.sub('\D', '', re.sub('.*\/', '', dirname))
    recs = []
    #get structure
    front = ''
    back = ''
    chapters = []
    for chpdir in os.listdir(dirname):
        chpdirfullpath = os.path.join(dirname, chpdir)
        if re.search('^BFM', chpdir):
            for filename in os.listdir(chpdirfullpath):
                if re.search('Meta$', filename):
                    front = os.path.join(chpdirfullpath, filename)
        #elif re.search('^BBM', chpdir):
        #    for filename in os.listdir(chpdirfullpath):
        #        if re.search('Meta$', filename):
        #            back = os.path.join(chpdirfullpath, filename)
        elif re.search('^CHP', chpdir):
            for filename in os.listdir(chpdirfullpath):
                if re.search('Meta$', filename):
                    chapters.append(os.path.join(chpdirfullpath, filename))
        elif re.search('^PRT', chpdir):
            for chp2dir in os.listdir(chpdirfullpath):
                chp2dirfullpath = os.path.join(chpdirfullpath, chp2dir)
                for filename in os.listdir(chp2dirfullpath):
                    if re.search('Meta$', filename):
                        chapters.append(os.path.join(chp2dirfullpath, filename))
    #get Hauptaufnahme
    if front:
        ha = convertarticle(journalnumber, front, 'book')
        ha['p1'] = 'pp.'
        if not 'vol' in ha.keys():
            ha['vol'] = isbn
    #get chapters
    crecs = []
    for chapter in chapters:
        rec = convertarticle(journalnumber, chapter, 'chapter')
        rec['motherisbn'] = isbn
        if not 'vol' in rec.keys():
            rec['vol'] = isbn
        crecs.append(rec)
    #copy date to HA
    if front:
        if not 'date' in ha.keys() and 'date' in rec.keys():
            ha['date'] = rec['date']
    #combine
    if front:
        if rec['tc'] == 'C':            
            ha['tc'] = 'K'
        elif rec['tc'] == 'S':
            ha['tc'] = 'B'
        elif rec['tc'] == 'T':
            ha['tc'] = 'T'
        recs = [ha]
        #print '--HA--'
        #print ha['auts']
    else:
        recs = []    
    if front:
        if re.search('\(ed\.\)', ha['auts'][0]):
            recs += crecs
    else:
        recs += crecs
    #return
    if recs:
        jnlfilename = '%s%s.%s' % (jc[journalnumber][0], isbn, cday)
        return (jnlfilename, recs)
    else:
        return ('', [])
    
###go through issue directory, collect records
def convertissue(journalnumber, dirname):
    recs = []
    for artdir in os.listdir(dirname):
        artdirfullpath = os.path.join(dirname, artdir)
        if os.path.isdir(artdirfullpath):
            for filename in os.listdir(artdirfullpath):
                if re.search('Meta$', filename):
                    fullfilename = os.path.join(artdirfullpath, filename)
                    rec = convertarticle(journalnumber, fullfilename, 'article')
                    if rec: recs.append(rec)
    if recs:
        if 'vol' in rec.keys():
            if 'issue' in rec.keys():
                jnlfilename = '%s%s.%s.%s' % (jc[journalnumber][0], rec['vol'], rec['issue'], cday)
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
            ejlmod2.writeXML(recs, xmlfile, publisher)
            xmlfile.close()
            #retrival
            retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
            retfiles_text = open(retfiles_path, "r").read()
            line = jnlfilename+'.xml'+ "\n"
#            if not line in retfiles_text:
#                retfiles = open(retfiles_path, "a")
#                retfiles.write(line)
#                retfiles.close()
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
                    ejlmod2.writeXML(recs, xmlfile, publisher)
                    xmlfile.close()
                    #retrival
                    retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
                    retfiles_text = open(retfiles_path, "r").read()
                    line = jnlfilename+'.xml'+ "\n"
                    if not line in retfiles_text:
                        retfiles = open(retfiles_path, "a")
                        retfiles.write(line)
                        retfiles.close()



