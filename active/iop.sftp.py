# -*- coding: UTF-8 -*-
# checks for new sftp-feeds from IOP and converts them
# FS 2021-11-01

import os
import sys
import re
import time
import datetime
import codecs
from bs4 import BeautifulSoup
import urllib2
import urlparse
import ejlmod2
import shutil
import pysftp

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'
iopdirtmp = '/afs/desy.de/group/library/publisherdata/iop/tmp'
iopdirraw = '/afs/desy.de/group/library/publisherdata/iop/raw'
iopdirdone = '/afs/desy.de/group/library/publisherdata/iop/done'
iopdirarchive = []
pdfdir = '/afs/desy.de/group/library/publisherdata/pdf'
publisher = 'IOP'
ftpdir = "/afs/desy.de/group/library/preprints/incoming/IOP"
from refextract import extract_references_from_string

#ISSN to journal name
jnl = {'1538-3881': ['Astron.J.', '', '', 'P'],
       '0004-637X': ['Astrophys.J.', '', '', 'P'],
       '1538-4357': ['Astrophys.J.Lett.', 'Astrophys.J.', '', 'P'],
       '2041-8205': ['Astrophys.J.Lett.', 'Astrophys.J.', '', 'P'],
       '0067-0049': ['Astrophys.J.Supp.', '', '', 'P'],
       '1009-9271': ['Chin.J.Astron.Astrophys.', '', '', 'P'],
       '1009-1963': ['Chin.Phys.', '', '', 'P'],
       '1674-1056': ['Chin.Phys.', '', 'B', 'P'],
       '1674-1137': ['Chin.Phys.', '', 'C', 'P'],
       '0256-307X': ['Chin.Phys.Lett.', '', '', 'P'],
       '0264-9381': ['Class.Quant.Grav.', '', '', 'P'],
       '0253-6102': ['Commun.Theor.Phys.', '', '', 'P'],
       '0143-0807': ['Eur.J.Phys.', '', '', 'P'],
       '0295-5075': ['EPL', '', '', 'P'],
       '1757-899X': ['IOP Conf.Ser.Mater.Sci.Eng.', '', '', 'C'],
       '1751-8121': ['J.Phys.', '', 'A', 'P'],
       '0953-4075': ['J.Phys.', '', 'B', 'P'],
       '2399-6528': ['J.Phys.Comm.', '', '', 'P'],
       '0953-8984': ['J.Phys.Condens.Matter', '', '', 'P'],
       '1742-6596': ['J.Phys.Conf.Ser.', '', '', 'C'],
       '0954-3899': ['J.Phys.', '', 'G', 'P'],
       '1475-7516': ['JCAP', '', '', 'P'],
       '1126-6708': ['JHEP', '', '', 'P'],
       '1748-0221': ['JINST', '', '', 'P'],
       '1742-5468': ['JSTAT', '', '', 'P'],
       '0957-0233': ['Measur.Sci.Tech.', '', '', 'P'],
       '0026-1394': ['Metrologia', '', '', 'P'],
       '1367-2630': ['New J.Phys.', '', '', 'P'],
       '0951-7715': ['Nonlinearity', '', '', 'P'],
       '0031-9120': ['Phys.Educ.', '', '', 'P'],
       '0031-9155': ['Phys.Med.Biol.', '', '', 'P'],
       '1402-4896': ['Phys.Scripta', '', '', 'P'],
       '1063-7869': ['Phys.Usp.', '', '', 'P'],
       '0741-3335': ['Plasma Phys.Control.Fusion', '', '', 'P'],
       '1538-3873': ['Publ.Astron.Soc.Pac.', '', '', 'P'],
       '0034-4885': ['Rept.Prog.Phys.', '', '', 'PR'],
       '1361-6633': ['Rept.Prog.Phys.', '', '', 'PR'],
       '1674-4527': ['Res.Astron.Astrophys.', '', '', 'P'],
       '0036-0279': ['Russ.Math.Surveys', '', '', 'P'],
       '0953-2048': ['Supercond.Sci.Technol.', '', '', 'P']}
jnl['2516-1067'] = ['Plasma Res.Express', '', '', 'P'] #Plasma Research Express#yepp
jnl['2632-2153'] = ['Mach.Learn.Sci.Tech.', '', '', 'P'] #Machine Learning: Science and Technology#yepp
jnl['2058-9565'] = ['Quantum Sci.Technol.', '', '', 'P'] #Quantum Science and Technology  (quanth-ph)#yepp
jnl['1674-4527'] = ['Res.Astron.Astrophys.', '', '', 'P'] #Research in Astronomy and Astrophysics#yepp
jnl['0266-5611'] = ['Inverse Prob.', '', '', 'P'] #Inverse Problems#yepp
jnl['0957-4484'] = ['Nanotechnol.', '', '', 'P'] #Nanotechnology#yepp
jnl['0253-6102'] = ['Commun.Theor.Phys.', '', '', 'P'] #Communications in Theoretical Physics#yepp
jnl['0004-6256'] = ['Nucl.Fusion', '', '', 'P'] #Nuclear Fusion#yepp
jnl['0029-5515'] = ['Nucl.Fusion', '', '', 'P'] #Nuclear Fusion#yepp
jnl['2040-8986'] = ['J.Opt.', '', '', 'P'] #Journal of Optics#yepp
jnl['1749-4699'] = ['Comput.Sci.Dis.', '', '', 'P'] #Computational Science & Discovery
jnl['1555-6611'] = ['Laser Phys.', '', '', 'P'] #Laser Physics#yepp
jnl['1612-202X'] = ['Laser Phys.Lett.', '', '', 'P'] #Laser Physics Letters #yepp
jnl['2515-5172'] = ['Res.Notes AAS', '', '', 'P']
jnl['1347-4065'] = ['Jap.J.Appl.Phys.', '', '', 'P']
##

#identify PACS
repacs = re.compile('^\d\d\.\d\d...$')

#uninteresting journals in feed
jnlskip = {'2058-8585' : 'Flexible and Printed Electronics'}

#CNUMs for conferences in JINST
confdict = {'12th Workshop on Resistive Plate Chambers and Related Detectors (RPC2014)': 'C14-02-23.2',
            '12th Workshop on Resistive Plate Chambers and Related Detectors': 'C14-02-23.2',
            'International Conference on Instrumentation for Colliding Beam Physics (INSTR14)': 'C14-02-24',
            'Topical Workshop on Electronics for Particle Physics 2013 (TWEPP-13)': 'C13-09-23',
            '13th Topical Seminar on Innovative Particle and Radiation Detectors (IPRD13)': 'C13-10-07',
            'Precision Astronomy with Fully Depleted CCDS (PACCD2013)': 'C13-11-18.1',
            '10th International Conference on Position Sensitive Detectors (PSD10)': 'C14-09-07',
            '10th International Conference on Position Sensitive Detectors': 'C14-09-07',
            'Workshop on Intelligent Trackers (WIT2014)': 'C14-05-14',
            'TWEPP2014': 'C14-09-22.7',
            '7th International Workshop on Semiconductor Pixel Detectors for Particles and Imaging': 'C14-09-01.3',
            '16th International Workshop on Radiation Imaging Detectors': 'C14-06-22.3',
            'Precision Astronomy with Fully Depleted CCDS(2014)': 'C14-12-04.1',
            '2nd International Summer School on Intelligent Signal Processing for Frontier Research and Industry': 'C14-07-15',
            '17th International Workshop on Radiation Imaging Detectors': 'C15-06-28.1',
            'Light Detection in Noble Elements (LIDINE 2015)': 'C15-08-28',
            '13th Workshop on Resistive Plate Chambers and Related Detectors (RPC2016)': 'C16-02-22.3',
            '17th International Symposium on Laser-Aided Plasma Diagnostics (LAPD17)' : 'C15-09-27.1',
            'TWEPP2015': 'C15-09-28',
            'International Workshop on Fast Cherenkov Detectors - Photon detection, DIRC design and DAQ (DIRC2015)' : 'C15-11-11.2',
            '4th International Conference Frontiers in Diagnostics Fix Technologies (ICFDT4)': 'C16-03-30.5',
            '18th International Workshop on Radiation Imaging Detectors (IWORID2016)' : 'C16-07-03.1',
            '14th Topical Seminar on Innovative Particle and Radiation Detectors' : 'C16-10-03',
            'International Workshop on Semiconductor Pixel Detectors for Particles and Imaging (Pixel 2016)' : 'C16-09-05.3',
            '14th Topical Seminar on Innovative Particle and Radiation Detectors (IPRD16)' : 'C16-10-03',
            'Topical Workshop on Electronics for Particle Physics (TWEPP2016)' : 'C16-09-26.4',
            'International Conference on Instrumentation for Colliding Beam Physics (INSTR17)' : 'C17-02-27',
            'Precision Astronomy with Fully Depleted CCDS (PACCD2016)' : 'C16-12-01.1',
            '19th International Workshop on Radiation Imaging Detectors (IWORID2017)' : 'C17-07-02.5',
            '11th International Conference on Position Sensitive Detectors (PSD11)' : 'C17-09-03.2',
            'Calorimetry for the High Energy Frontier (CHEF2017)' : 'C17-10-02.3',
            'XII International Symposium on Radiation from Relativistic Electrons in Periodic Structures (RREPS-17)' : 'C17-09-18.6',
            'International Workshop on Fast Cherenkov Detectors - Photon detection, DIRC design and DAQ (DIRC2017)' : 'C17-08-07.6',
            'Light Detection in Noble Elements (LIDINE2017)' : 'C17-09-22',
            'XII International Symposium on Radiation from Relativistic Electrons in Periodic Structures (RREPS-17)' : 'C17-09-18.6',
            '24th International congress on x-ray optics and microanalysis (ICXOM24)' : 'C17-09-25.6',
            '20th International Workshop On Radiation Imaging Detectors' : 'C18-06-24.2',
            '5th International Conference Frontiers in Diagnostcs Technologies (ICFDT)' : 'C18-10-03.1',
            'The 9th International Workshop on Semiconductor Pixel Detectors for Particles and Imaging' : 'C18-12-10',
            '14th Workshop on Resistive Plate Chambers and Related Detectors (RPC2018)' : 'C18-02-19.3',
            'RPC2018' : 'C18-02-19.3',
            'PIXEL2018' : 'C18-12-10',
            '3rd European Conference on Plasma Diagnostics (ECPD2019)' : 'C19-05-06.5',
            'ECPD2019' : 'C19-05-06.5',
            '20th International Workshop On Radiation Imaging Detectors' : 'C18-06-24.2',
            'LAPD19' : 'C19-09-22.5',
            'IWORID2019' : 'C19-07-07.2',
            'RREPS-19' : 'C19-09-16.8',
            'IPRD19' : 'C19-10-14.1',
            'DIRC2019' : 'C19-09-11.1',
            'INFIERI 2019' : 'C19-05-12.3',
            'LIDINE2019' : 'C19-08-28',
            'RPC2018' : 'C18-02-19.3',
            'CHEF2019' : 'C19-11-25.3',
            'The International Conference Instrumentation for Colliding Beam Physics (INSTR2020)' : 'C20-02-24',
            'RREPS-19' : 'C19-09-16.8',
            'XV Workshop on Resistive Plate Chambers and Related Detectors (RPC2020)' : 'C20-02-10.1'}

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d-%02d-%02d' % (now.year, now.month, now.day, now.hour, now.minute)

#check for new sftp-feeds
todo = []
done = os.listdir(iopdirdone)
for directory in iopdirarchive:
    done += os.listdir(directory)

srv = pysftp.Connection(host="collection-service.iop.org", username="inspire_hep", private_key="/afs/desy.de/user/l/library/.ssh/iop/id_rsa")
for datei in srv.listdir():
    if datei in done:
        print '%s already in done' % (datei)
    else:
        todo.append(datei)
        print 'downloading %s ...' % (datei)
        srv.get(datei, os.path.join(iopdirraw, datei))

print '%i packages to do: %s' % (len(todo), ', '.join(todo))
if not todo:
    sys.exit(0)
if not os.path.isdir(iopdirtmp):
    os.system('mkdir %s' % (iopdirtmp))

#extract the feeds:
for datei in todo:
    print 'extracting %s' % (os.path.join(iopdirraw, datei))
    os.system('cd %s && unzip -q -d %s -o %s' % (iopdirraw, iopdirtmp, datei))

#create base name
iopftrunc = stampoftoday


collapseWs = re.compile('[\n \t]+')
#initialBlank = re.compile('([A-Z]) ')
initialEnd = re.compile(r'([A-Z])\b')
#convert xml-tags to LaTex-style        
def fsunwrap(tag):
    try: 
        for sup in tag.find_all('SUP'):
            cont = sup.string
            sup.replace_with('^'+cont)
    except:
        print 'fsunwrap-sup-problem'
    try: 
        for sub in tag.find_all('SUB'):
            cont = sub.string
            sub.replace_with('_'+cont)
    except:
        print 'fsunwrap-sub-problem'
    return tag


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
            for fpage in mc.find_all('elocation-id'):
                pbn += ' ' + fpage.text.strip()
            #refextract on pbn to normalize it
            repbn = extract_references_from_string(pbn, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}")
            if repbn:
                if 'journal_reference' in repbn[0].keys():
                    #print ' [refextract] normalize "%s" to "%s"' % (pbn, repbn[0]['journal_reference'])
                    pbn = repbn[0]['journal_reference']
            else:
                for comment in mc.find_all('comment'):
                    pbn = comment.text.strip()                    
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
                #atitle = at.text.strip()
            #book title
            for source in mc.find_all('source'):
                btitle = cleanformulas(source)
                #btitle = source.text.strip()
            for source in mc.find_all('conf-name'):
                btitle += ' '+cleanformulas(source)
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
                        #inspire2 for recid in search_pattern(p='970__a:SPIRES-' + irn):
                        #inspire2    inspirelink += ', https://old.inspirehep.net/record/%i' % (recid)
                        #inspire2 el.decompose()
                    elif re.search('inspirehep.net.*recid', link):
                        recid = re.sub('.*\D', '', link)
                        inspirelink += ', https://old.inspirehep.net/record/%s' % (recid)
                        el.decompose()
                    elif re.search('inspirehep.net', link):
                        el.decompose()
                    elif re.search('arxiv.org', link):
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
            reference = [('x', refno + cleanformulas(mc))]
            #reference = [('x', refno + mc.text.strip())]
            if doi:
                reference.append(('a', 'doi:'+doi))
            if recid:
                reference.append(('0', str(recid)))
            if arxiv:
                reference.append(('r', arxiv))
            if doi or recid or arxiv:
                if lt: reference.append(('o', re.sub('\D', '', lt)))
            refs.append(reference)
    return refs




#convert individual article        
def convertarticle(issn, vol, isu, artid):
    if issn in jnl.keys():
        rec = {'jnl' : jnl[issn][0], 'note' : [], 'keyw' : [], 'aff' : [], 'refs' : [],
               'auts' : [], 'col' : []}
        if jnl[issn][1]:
            rec['alternatejnl'] = jnl[issn][1]
        tc = jnl[issn][3]
    elif issn in jnlskip.keys():
        print 'skip journal "%s"' % (jnlskip[issn])
        return []
    else:
        print 'do not know journal with ISSN:%s' % (issn)
        sys.exit(0)
        rec = {'jnl' : issn, 'note' : [], 'keyw' : [], 'aff' : [], 'refs' : []}
    ###read metadata
    for datei in os.listdir(os.path.join(iopdirtmp, issn, vol, isu, artid)):
        if re.search('xml$', datei):
            inf = open(os.path.join(iopdirtmp, issn, vol, isu, artid, datei), 'r')
            article = BeautifulSoup(''.join(inf.readlines()), features="lxml")
            inf.close()
            contlevel = 'article'
            if contlevel == 'article':
                metas = article.find_all('article-meta')
            elif contlevel == 'chapter':
                metas = article.find_all('book-part-meta')
            elif contlevel == 'book':
                metas = article.find_all('book-meta')
    if not metas:
        return {}
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
        #arXiv number
        for cm in  meta.find_all('custom-meta'):
            for mn in cm.find_all('meta-name'):
                if mn.text.strip() == 'arxivppt':
                    for mv in cm.find_all('meta-value'):
                        rec['arxiv'] = mv.text.strip()
        #article type
        for ac in meta.find_all('article-categories'):
            for subj in ac.find_all('subject'):
                subjt = subj.text.strip()
                if re.search('[a-zA-Z]', subjt):
                    rec['note'].append(subjt)
                if subjt in ['Review']:
                    tc += 'R'
                elif re.search('Special Issue.*Conference', subjt):
                    tc = 'C'
        #title
        for tg in meta.find_all('title-group'): 
            for at in tg.find_all(['article-title', 'title']):
                #rec['tit'] = at.text.strip()
                for fn in at.find_all('fn'):
                    rec['note'].append(fn.text.strip())
                    fn.decompose()
                rec['tit'] = re.sub('[\n\t\r]', ' ', cleanformulas(at))
            for st in tg.find_all('subtitle'):
                #rec['tit'] += ': %s' % (st.text.strip())
                rec['tit'] += ': %s' % (cleanformulas(st))
        #year
        pds = meta.find_all('pub-date', attrs = {'pub-type' : 'ppub'})
        for pd in pds:
            for year in pd.find_all('year'):
                rec['year'] = year.text.strip()
        #date
        pds = meta.find_all('pub-date', attrs = {'pub-type' : 'epub'})
        if not pds:
            pds = meta.find_all('pub-date', attrs = {'pub-type' : 'pub', 'publication-format' : 'electronic'})
        for pd in pds:
            for year in pd.find_all('year'):
                rec['date'] = year.text.strip()
            for month in pd.find_all('month'):
                rec['date'] += '-' + month.text.strip()
            for day in pd.find_all('day'):
                rec['date'] += '-' + day.text.strip()
        #volume
        for voltag in meta.find_all('volume'):
            rec['vol'] = jnl[issn][2] + voltag.text.strip()        
        #issue
        for iss in meta.find_all('issue'):
            rec['issue'] = iss.text.strip()              
        #first page
        for p1 in meta.find_all('fpage'):
            rec['p1'] = p1.text.strip()
        #last page
        for p2 in meta.find_all('lpage'):
            rec['p2'] = p2.text.strip()
        #article ID
        for eid in meta.find_all('elocation-id'):
            rec['p1'] = eid.text.strip()
            #remove pagination information if there is an article ID
            if 'p2' in rec.keys():
                del rec['p2']
        #pages
        for pc in meta.find_all('page-count'):
            rec['pages'] = pc['count']
        #abstract
        abstracts = meta.find_all('abstract', attrs = {'xml:lang' : 'en'})
        if not abstracts:
            abstracts = meta.find_all('abstract')
        for abstract in abstracts:
            rec['abs'] = ''
            for p in abstract.find_all('p'):
                #rec['abs'] += p.text.strip()
                rec['abs'] += cleanformulas(p)
        #license
        for permissions in meta.find_all('permissions'):
            for licence in permissions.find_all('license'):
                if licence.has_attr('license-type'):
                    if licence['license-type'] in ['cc-by']:
                        if licence.has_attr('xlink:href'):
                            if re.search('creativecommons.org', licence['xlink:href']):
                                rec['license'] = {'url' : licence['xlink:href']}
                    elif not licence['license-type'] in ['iop-standard']:
                        rec['note'].append('license: ' + licence['license-type'])   
        #keywords
        kwgs = meta.find_all('kwd-group')            
        rec['keyw'] = []
        for kwg in kwgs:
            for kw in kwg.find_all('kwd'):
                kwdt = kw.text.strip()
                if repacs.search(kwdt):
                    if 'pacs' in rec.keys():
                        rec['pacs'].append(kwdt)
                    else:
                        rec['pacs'] = [kwdt]
                else:
                    rec['keyw'].append(kwdt)
        #affiliations
        for cg in meta.find_all('contrib-group'):            
            for aff in cg.find_all('aff'):
                for label in aff.find_all('label'):
                    label.decompose()
                afftext = aff.text.strip()
                rec['aff'].append('%s= %s' % (aff['id'], re.sub('[\n\t\r]', ' ', afftext)))
        #check for editor
        authortype = 'author'
        if contlevel == 'book':
            if meta.find_all('contrib', attrs = {'contrib-type' : 'editor'}):
                authortype = 'editor'
        for contrib in meta.find_all('contrib', attrs = {'contrib-type' : authortype}):
            #authors
            for name in contrib.find_all('name', attrs = {'name-style' : 'western'}):
                for sn in name.find_all('surname'):
                    authorname = sn.text.strip()
                for gn in name.find_all('given-names'):
                    authorname += ', %s' % (gn.text.strip())
                #editor
                if authortype == 'editor':
                    authorname += ' (ed.)'
                #ORCID
                for cid in contrib.find_all('contrib-id', attrs = {'contrib-id-type' : 'orcid'}):
                    authorname += ', ORCID:' + cid.text.strip()
                #Email
                if not re.search('ORCID:', authorname):
                    for email in contrib.find_all('email'):
                        authorname += ', EMAIL:' + email.text.strip()
                #Chineses name
                for cname in contrib.find_all('name', attrs = {'name-style' : 'eastern'}):
                    for csn in cname.find_all('surname'):
                        chineseauthorname = csn.text
                    for cgn in name.find_all('given-names'):
                        chineseauthorname += cgn.text
                rec['auts'].append(authorname)
                #Affiliation
                for xref in contrib.find_all('xref', attrs = {'ref-type' : 'aff'}):
                    rec['auts'].append('=%s' % (xref['rid']))                
            #collaboration
            for coll in contrib.find_all('collab'):
                #safety check if authors are under collaboration
                authorsundercoll = False
                for bla in coll.find_all('contrib', attrs = {'contrib-type' : 'author'}):
                    authorsundercoll = True
                if authorsundercoll:
                    for inst in coll.find_all('institution'):
                        rec['col'].append(inst.text.strip())
                else:
                    for email in coll.find_all('email'):
                        email.decompose()
                    rec['col'].append(coll.text.strip())
    #references
    for rl in article.find_all('ref-list'):
        rec['refs'] = get_references(rl)
    for note in rec['note']:
        if note in confdict.keys():
            rec['cnum'] = confdict[note]
            rec['tc'] = 'C'
            rec['note'].append('added cnum:%s' % (rec['cnum']))




            

    #from stacks-code
    if 1 > 0:
        #JCAP special case
        if rec['jnl'] in ['JCAP', 'JHEP', 'JSTAT']:
            rec['vol'] = '%s%02i' % (rec['year'][2:4], int(rec['issue']))
            if 'issue' in rec.keys():
                del rec['issue']
        #issue
        for issuenode in article.find_all('issue'):
            issue = issuenode.text.strip()
            if issn == '1402-4896' and issue[0] == 'T':
                rec['vol'] = issue
            else:
                rec['issue'] = issue
                if issue.startswith("S"): #we have a supplememnt 
                    rec['jnl'] += " Suppl."
        #fulltext
        if 'license' in rec.keys():
            rec['FFT'] = 'http://iopscience.iop.org/article/%s/pdf' % (rec['doi'])
        #typecode
        rec['tc'] = tc
        try:
            if issn == '1748-0221' and rec['p1'][0] == 'C':
                rec['tc'] = ['C']
        except:
            pass
        print ' .', rec['doi'], rec.keys()        
        ###check for fulltext
        for datei in os.listdir(os.path.join(iopdirtmp, issn, vol, isu, artid)):
            if re.search('\.pdf$', datei):
                pdfsrc = os.path.join(iopdirtmp, issn, vol, isu, artid, datei)
                pdfdst = os.path.join(pdfdir, re.sub('\/.*', '', rec['doi']), re.sub('[\/\(\)]', '_', rec['doi']) + '.pdf')
                if os.path.isfile(pdfdst):
                    print '   fulltext found but no need to copy'
                else:
                   try:
                       shutil.copy(pdfsrc, pdfdst)
                       print '     fulltext found and copied'
                   except:
                       print '     fulltext found but not copied!'
                       print pdfsrc
                       print pdfdst
    #non-articles
    if not rec['auts'] and rec['tit'] in ['Preface', 'Peer review declaration', 'Statement of Peer Review',
                                          'Peer Review Declaration', 'Committee', 'Preface']:
        print '   skip non-article'
    else:
        return rec

        
#scan extracted directories
for issn in os.listdir(iopdirtmp):
    if issn in jnl.keys():
        print '\n======{ %s }======' % (jnl[issn][0])
    if re.search('\d\d\d\d\-\d\d\d[\dX]', issn):
        for vol in os.listdir(os.path.join(iopdirtmp, issn)):
            if re.search('\d', vol):
                recs = []
                issues = []
                for isu in os.listdir(os.path.join(iopdirtmp, issn, vol)):
                    if re.search('\d', isu):
                        print '------{ ISSN:%s VOL:%s ISU:%s}------' % (issn, vol, isu)
                        issues.append(re.sub('.*_', '', isu))
                        for artid in os.listdir(os.path.join(iopdirtmp, issn, vol, isu)):
                            if re.search('\d', artid):
                                rec = convertarticle(issn, vol, isu, artid)
                                if rec: recs.append(rec)
                if recs:
                    if issn in jnl.keys():
                        if 'vol' in recs[0].keys():
                            iopf = 'iop-%s-%s%s_%s' % (iopftrunc, re.sub(' ', '', jnl[issn][0]), recs[0]['vol'], '.'.join(issues))
                        else:
                            iopf = 'iop-%s-%s%s_%s' % (iopftrunc, re.sub(' ', '', jnl[issn][0]), vol, '.'.join(issues))                 
                    else:
                        iopf = 'iop-%s-%s%s_%s' % (iopftrunc,
                                                   re.sub(' ', '', issn), vol, '.'.join(issues))
                    print ' '
                    if not issn in jnlskip.keys():
                        xmlf = os.path.join(xmldir, iopf+'.xml')
                        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
                        ejlmod2.writenewXML(recs ,xmlfile, 'IOP', iopf)
                        xmlfile.close()
                  
                        #retrival
                        retfiles_text = open(retfiles_path,"r").read()
                        line = iopf+'.xml'+ "\n"
                        if not line in retfiles_text: 
                            retfiles = open(retfiles_path,"a")
                            retfiles.write(line)
                            retfiles.close()
                print '\n   %s with %i records\n' % (iopf, len(recs))

    
#if everything went fine, move the files to done
for datei in todo:
    os.system('mv %s/%s %s/%s' % (iopdirraw, datei, iopdirdone, datei))
shutil.rmtree(iopdirtmp)
print 'done :-)'
    
