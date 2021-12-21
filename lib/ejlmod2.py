# -*- coding: utf-8 -*-
import xml.dom.minidom
import re
import os
import subprocess
import datetime
import platform
import unicodedata
import unidecode
import codecs

from collclean_lib import coll_cleanforthe
from collclean_lib import coll_clean710
from collclean_lib import coll_split
from inspire_utils.date import normalize_date

try:
    # needed to remove the print-commands from /usr/lib/python2.6/site-packages/refextract/references/engine.py
    from refextract import  extract_references_from_string
except:
    #for running on PubDB
    print 'could not import extract_references_from_string'

#QIS bibclassify
qisbibclassifycommand = "python /afs/desy.de/user/l/library/proc/bibclassify/bibclassify_cli.py  -k /afs/desy.de/user/l/library/akw/QIS_TEST.rdf -n 10"
absdir = '/afs/desy.de/group/library/publisherdata/abs'
tmpdir = '/afs/desy.de/user/l/library/tmp'


#from collclean import clean710

#mappings for refferences in JSON to MARC 
mappings = {'doi' : 'a',
            'hdl' : 'a', 
            'collaborations' : 'c',
            'document_type' : 'd',
            'author' : 'h',
            'isbn' : 'i',
            'texkey' : 'k',
            'misc' : 'm',
            'journal_issue' : 'n',
            'label' : 'o',
            'linemarker' : 'o',
            'reportnumber' : 'r',
            'journal_reference' : 's',
            'title' : 't',
            'urls' : 'u',
            'raw_ref' : 'x',
            'year' : 'y'}

#find additional reportnumbers
repreprints = re.compile('.*Preprint:? ([A-Z0-9\-\/, ]+).*')
repreprint = re.compile('^[A-Z0-9\-\/ ]+$')
#split keywords
rekeywsplit1 =  re.compile(', .*, ')
rekeywsplit2 =  re.compile('; .*; ')

#valid arXiv numbers
rearxivold = re.compile('^[a-z\-]+\/\d{7}$')
rearxivnew = re.compile('^ar[xX]iv:\d{4}\.\d{4,5}')
#valid ORCID
reorcid = re.compile('^ORCID:\d{4}\-\d{4}\-\d{4}\-\d{3}[0-9X]$')

#list of lists to automatically suggest fieldcodes based on journalname
#(can also handle mutiple FCs like 'ai' or so)
#from inspirelibrarylabs import fcjournalliste
fcjournalliste = [('b', ['IEEE Trans.Appl.Supercond.', 'Supercond.Sci.Technol.']),
                  ('m', ['Abstr.Appl.Anal.', 'Acta Appl.Math.', 'Adv.Appl.Clifford Algebras', 'Adv.Math.', 'Adv.Math.Phys.', 'Afr.Math.', 'Alg.Anal.', 'Algebr.Geom.Topol.', 'Alg.Groups Geom.', 'Alg.Logika', 'Anal.Math.Phys.', 'Anal.Part.Diff.Eq.', 'Annals Probab.', 'Ann.Inst.H.Poincare Probab.Statist.', 'Ann.Math.Sci.Appl.', 'Ann.PDE', 'Arab.J.Math.', 'Asian J.Math.', 'Axioms', 'Bayesian Anal.', 'Braz.J.Probab.Statist.', 'Bull.Am.Math.Soc.', 'Bull.Austral.Math.Soc.', 'Cahiers Topo.Geom.Diff.', 'Calc.Var.Part.Differ.Equ', 'Can.J.Math.', 'Commun.Anal.Geom.', 'Commun.Math.Phys.', 'Commun.Math.Sci.', 'Commun.Pure Appl.Math.', 'Compos.Math.', 'Compt.Rend.Math.', 'Conform.Geom.Dyn.', 'Contemp.Math.', 'Duke Math.J.', 'Eur.J.Combinatorics', 'Exper.Math.', 'Forum Math.Pi', 'Forum Math.Sigma', 'Fractals', 'Geom.Topol.', 'Geom.Topol.Monographs', 'Glasgow Math.J.', 'Hokkaido Math.J.', 'Int.Math.Res.Not.', 'Invent.Math.', 'Inverse Prob.', 'Izv.Vuz.Mat.', 'J.Alg.Geom.', 'J.Am.Math.Soc.', 'J.Appl.Math.', 'J.Appl.Math.Mech.', 'J.Austral.Math.Soc.', 'J.Diff.Geom.', 'J.Geom.Anal.', 'J.Geom.Symmetry Phys.', 'J.Inst.Math.Jussieu', 'J.Integrab.Syst.', 'J.Korean Math.Soc.', 'J.Math.Phys.', 'J.Math.Res.', 'J.Math.Sci.', 'J.Math.Soc.Jap.', 'J.Part.Diff.Eq.', 'Lect.Notes Math.', 'Lett.Math.Phys.', 'Manuscr.Math.', 'Math.Comput.', 'Mathematics', 'Math.Methods Appl.Sci.', 'Math.Nachr.', 'Math.Notes', 'Math.Phys.Anal.Geom.', 'Math.Phys.Stud.', 'Math.Proc.Cambridge Phil.Soc.', 'Math.Res.Lett.', 'Mat.Sbornik', 'Mat.Zametki', 'Moscow Math.J.', 'Pacific J.Math.', 'p Adic Ultra.Anal.Appl.', 'Proc.Am.Math.Soc.', 'Proc.Am.Math.Soc.Ser.B', 'Proc.Geom.Int.Quant.', 'Prog.Math.Phys.', 'Rept.Math.Phys.', 'Russ.J.Math.Phys.', 'Russ.Math.Surveys', 'Springer Proc.Math.Stat.', 'Tokyo J.Math.', 'Trans.Am.Math.Soc.', 'Trans.Am.Math.Soc.Ser.B', 'Trans.Moscow Math.Soc.', 'Turk.J.Math.', 'Ukr.Math.J.', 'J.Reine Angew.Math.', 'Arch.Ration.Mech.Anal.', 'Acta Math.Vietnamica', 'Quart.J.Math.Oxford Ser.', 'Int.J.Math.', 'Integral Transform.Spec.Funct.', 'Commun.Contemp.Math.', 'Selecta Math.']),
                  ('q', ['ACS Photonics', 'Atoms', 'J.Chem.Phys.', 'J.Chem.Theor.Comput.', 'J.Mod.Opt.', 'J.Molec.Struc.', 'J.Opt.', 'J.Opt.Soc.Am. A', 'J.Opt.Soc.Am. B', 'Mater.Chem.Phys.', 'Nano Lett.', 'Nanotechnol.', 'Nature Photon.']),
                  ('k', ['ACM Trans.Quant.Comput.', 'Quant.Inf.Proc.', 'Quantum Eng.', 'Quantum Rep.', 'Quantum Sci.Technol.', 'Quantum', 'AVS Quantum Sci.', 'Adv.Quantum Technol.']),
                  ('f', ['Adv.Cond.Mat.Phys.', 'Ann.Rev.Condensed Matter Phys.', 'Condens.Mat.', 'J.Noncryst.Solids', 'J.Phys.Chem.Solids', 'J.Phys.Condens.Matter', 'Solid State Commun.', 'Sov.Phys.Solid State', 'Condensed Matter Phys.', 'Phys.Status Solidi']),
                  ('a', ['Ann.Rev.Astron.Astrophys.', 'Acta Astron.', 'Acta Astron.Sin.', 'Adv.Astron.', 'Astron.Astrophys.', 'Astron.Astrophys.Lib.', 'Astron.Astrophys.Rev.', 'Astron.Geophys.', 'Astron.J.', 'Astron.Lett.', 'Astron.Nachr.', 'Astron.Rep.', 'Astrophys.Bull.', 'Astrophysics', 'Astrophys.J.', 'Astrophys.J.Lett.', 'Astrophys.J.Supp.', 'Astrophys.Space Sci.', 'Astrophys.Space Sci.Libr.', 'Astrophys.Space Sci.Proc.', 'Chin.Astron.Astrophys.', 'Exper.Astron.', 'Front.Astron.Space Sci.', 'Int.J.Astrobiol.', 'J.Astron.Space Sci.', 'J.Astrophys.Astron.', 'J.Atmos.Sol.Terr.Phys.', 'JCAP', 'J.Korean Astron.Soc.', 'Mon.Not.Roy.Astron.Soc.', 'Nat.Astron.', 'New Astron.', 'Open Astron.', 'Publ.Astron.Soc.Austral.', 'Publ.Astron.Soc.Jap.', 'Publ.Astron.Soc.Pac.', 'Res.Astron.Astrophys.', 'Res.Notes AAS', 'Rev.Mex.Astron.Astrofis.', 'Space Sci.Rev.', 'Nature Astron.', 'Galaxies']),
                  ('g', ['Class.Quant.Grav.', 'Gen.Rel.Grav.', 'Living Rev.Rel.']),
                  ('c', ['Comput.Softw.Big Sci.', 'J.Grid Comput.', 'J.Open Source Softw.', 'SoftwareX']),
                  ('i', ['IEEE Instrum.Measur.Mag.', 'IEEE Sensors J.', 'IEEE Trans.Circuits Theor.', 'IEEE Trans.Instrum.Measur.', 'Instruments', 'Instrum.Exp.Tech.', 'JINST', 'Meas.Tech.', 'Measur.Sci.Tech.', 'Metrologia', 'Microscopy Microanal.', 'Rad.Det.Tech.Meth.', 'Rev.Sci.Instrum.', 'Sensors', 'J.Astron.Telesc.Instrum.Syst.', 'EPJ Tech.Instrum.'])]
#rearrange the lists into a dictionary
jnltofc = {}
for (fc, jnllist) in fcjournalliste:
    for jnl in jnllist:
        jnltofc[jnl] = fc

#auxiliary function to strip lines
def tgstrip(x): return x.strip()

def kapitalisiere(string):
    if re.search('[a-z]', string):
        return string
    elif re.search('[A-Z]', string):
        acronyms = ['LHC', 'CFT', 'QCD', 'QED', 'QFT', 'ABJM', 'NLO', 'LO', 'NNLO', 'IIB', 'IIA', 'MSSM', 'NMSSM', 'SYM', 'WIMP', 'ATLAS', 'CMS', 'ALICE', 'RHIC', 'DESY', 'HERA', 'CDF', 'D0', 'BELLE', 'BABAR', 'BFKL', 'DGLAP', 'SUSY', 'QM', 'UV', 'IR', 'BRST', 'PET', 'GPS', 'NMR', 'XXZ', 'CMB', 'LISA', 'CPT', 'KEK', 'TRIUMF', 'PHENIX', 'VLBI', 'NGC', 'SNR', 'HESS', 'AKARI', 'GALEX', 'ESO', 'J-PARC', 'CERN', 'XFEL', 'FAIUR', 'ILC', 'CLIC', 'SPS', 'BNL', 'CEBAF', 'SRF', 'LINAC', 'HERMES', 'ZEUS', 'H1', 'GRB', 'GSI']
        word_list = re.split(' +', string)
        final = [word_list[0].capitalize()]
        for word in word_list[1:]:
            if word.upper() in acronyms:
                final.append(word.upper())
            elif len(word) > 3:
                final.append(word.capitalize())
            else:
                final.append(word.lower())
        return " ".join(final)
    else:
        return string

#FS: try to get arXiv-number from ADS for some journals
def arXivfromADS(rec):
    adslink = 'http://adsabs.harvard.edu/doi/' + rec['doi']
    print 'try '+adslink+' to get arXiv-number'
    for adsline in os.popen("lynx -source \"%s\"|grep citation_arxiv_id" % (adslink)).readlines():
        if re.search('arxiv',adsline):
            rec['arxiv'] = re.sub('.*content="(.*)".*', r'\1', adsline).strip()
            print '---[ ADS: %s -> %s ]---' % (rec['doi'], rec['arxiv'])
            if rec.has_key('note'):
                if type(rec['note']) == type(['Liste']):
                    rec['note'].append('arXiv number from ADS (not from publisher!)')
                else:
                    rec['note'] = [rec['note'],'arXiv number from ADS (not from publisher!)']
            else:
                rec['note'] = ['arXiv number from ADS (not from publisher!)']
    return

#find collaborations in authorfield
refcauthor = re.compile(' *([A-Z].*? [A-Z][a-z]+ .*?) FFF ')
refcsplitter1 = re.compile('( |^)[fF]or [Tt]he ')
refcsplitter2 = re.compile('( |^)[oO]n [bB]ehalf [oO]f [Tt]he ')
refcsplitter3 = re.compile('( |^)[fF]or ')
refcsplitter4 = re.compile('( |^)[oO]n [bB]ehalf [oO]f ')
def findcollaborations(authorfield):
    if re.search('Collaboration', authorfield):
        aft = re.sub('^ *\( *(.*) *\) *$', r'\1', authorfield)
        aft = refcsplitter1.sub(' FFF ', aft)
        aft = refcsplitter2.sub(' FFF ', aft)
        aft = refcsplitter3.sub(' FFF ', aft)
        aft = refcsplitter4.sub(' FFF ', aft)
        author = False
        if refcauthor.search(aft):
            author = refcauthor.sub(r'\1', aft)
        collaborations = re.sub('.*FFF ', '', aft)
        collaborations = re.sub('^ *(.*) Collaborations.*', '', collaborations)
        colparts = re.split(' *, *', re.sub(' [aA]nd ', ', ', collaborations))
        return (author, colparts)
    else:
        return (authorfield, False)
            


#FS:
#add experiment line for existing collaboration
#and try to find experiment in title
colexpdictfilename = '/afs/desy.de/user/l/library/lists/expcolFS'
colexpdictfile = open(colexpdictfilename,'r')
colexpdict = {}
expexpdict = {}
for colexpline in colexpdictfile.readlines():
    parts = re.split(';',colexpline.strip())
    colexpdict[re.sub(' *Collabo.*','',parts[0]).upper()] = parts[1:]
    if not re.search(' and ',parts[0]):
        expexpdict[re.sub(' *Collabo.*','',parts[0])] = re.sub(' *experiment.*','',parts[1])
colexpdictfile.close()

def findexperiment(rec):
    if rec.has_key('col'):
        #print "COL=",rec['col']
        collaboration = re.sub(' *Collabo.*','',rec['col']).upper()
        if colexpdict.has_key(collaboration):
            rec['exp'] = colexpdict[collaboration]
            #print "EXP=",rec['exp']
    else:
        experiments = []
        for exp in expexpdict.keys():
            if re.search('(\W|^)'+exp+'($|\W)',rec['tit']):
            #if (exp != 'DO') and re.search(exp,rec['tit']):
                experiments.append(expexpdict[exp] + '')
        if len(experiments) > 0:
            rec['exp'] = experiments
            print "EXP=",rec['exp']
    return


#FS:
#get abstract from arXiv (e.g. Intl. Press;)
def getabsfromarxiv(rec):
    absdir = '/afs/desy.de/group/library/publisherdata/abs/'
    bull = re.sub('.*\: ','',rec['arxiv'])
    print " get abstract for %s from arXiv" % (bull)
    arxivpage = os.popen("lynx -source \"http://export.arxiv.org/abs/%s\"" % (bull)).read().replace('\n',' ')
    abstract = re.sub('.*<span class=\"descriptor\">Abstract\:<\/span> *(.*) *<\/blockquote>.*',r'\1',arxivpage )
    abstract = re.sub('  +',' ',abstract)
    rec['abs'] = re.sub(';',',',abstract)
    return



#new stuff: writeXML
inspirefc = {'e':'Experiment-HEP', 'i':'Instrumentation', 
             'b':'Accelerators', 'x':'Experiment-Nucl', 
             'n':'Theory-Nucl', 'c':'Computing', 
             'a':'Astrophysics', 'p':'Phenomenology-HEP', 
             'o':'General Physics', 'g':'Gravitation and Cosmology', 
             'l':'Lattice', 'm':'Math and Math Physics', 
             'o':'Other', 'q':'General Physics',
             'f':'Condensed Matter', 'k':'Quantum Physics',
             's' : 'Data Analysis and Statistics', 't':'Theory-HEP'}
inspiretc = {'P':'Published', 'C':'ConferencePaper', 
             'R':'Review', 'T':'Thesis', 
             'B':'Book', 'S': 'BookChapter', 
             'K': 'Proceedings', 'O': 'Note', 
             'L' : 'Lectures', 'I':'Introductory'}


#translating HTML entities
htmlentity = re.compile(r'&#x.*?;')
def lam(x):                                                
    x  = x.group()
    return unichr(int(x[3:-1], 16))

#we can not install the latest refextractor :(
#here are some "manual" journal normalizations
renjwas = [(re.compile('Journal of Physics G.? Nuclear and Particle Physics, *'), 'J.Phys.,G'),
           (re.compile('Journal of Physics A.? General Physics, *'), 'J.Phys.,A'),
           (re.compile('Advances in High Energy Physics, *'), 'AHEP, '),
           (re.compile('Physical Review A.? Atomic, Molecular and Optical Physics, *'), 'Phys.Rev.,A'),
           (re.compile('Physical Review B.? Condensed Matter and Materials Physics, *'), 'Phys.Rev.,B'),
           (re.compile('Physical Review E.? Statistical, Nonlinear, and Soft Matter Physics, *'), 'Phys.Rev.,E'),
           (re.compile('Progress of Theoretical and Experimental Physics, *'), 'PTEP, '),
           (re.compile('Fortschritte der Physik.Progress of Physics, *'), 'Fortsch.Phys., '),
           (re.compile('Electronic Journal of Theoretical Physics, *'), 'Electron.J.Theor.Phys. , '),
           (re.compile('Journal of Modern Physics, *'), 'J.Mod.Phys., '),
           (re.compile('Physica Scripta. An International Journal for Experimental and Theoretical Physics, *'), 'Phys.Scripta, '),
           (re.compile('Results in Physics, *'), 'Results Phys., '),
           (re.compile('Computational Mathematics and Mathematical Physics, *'), 'Comput.Math.Math.Phys., '),
           (re.compile('Journal of Nonlinear Mathematical Physics, *'), 'J.Nonlin.Mathematical Phys., '),
           (re.compile('Journal of Geophysical Research.? .?Space Physics.?, *'), 'J.Geophys.Res.Space Phys., '),
           (re.compile('J. Geophys. Res. Space Physics, *'), 'J.Geophys.Res.Space Phys., '),
           (re.compile('Journal of Atmospheric and Solar..?.?Terrestrial Physics, *'), 'J.Atmos.Sol.Terr.Phys., '),
           (re.compile('International Journal Geometrical Methods in Modern Physics, *'), 'Int.J.Geom.Meth.Mod.Phys., '),
           (re.compile('Advances in Mathematical Physics, *'), 'Adv.Math.Phys., '),
           (re.compile('SciPost Physics, *'), 'SciPost Phys., '),
           (re.compile('Studies in History and Philosophy of Science. Part B. Studies in History and Philosophy of Modern Physics, *'), 'Stud.Hist.Phil.Sci.,B'),
           (re.compile('Indian Journal of Radio ..?.?.?.? Space Physics, *'), 'Indian J.Radio Space Phys, '),
           (re.compile('Atmospheric Chemistry And Physics, *'), 'Atmos.Chem.Phys., '),
           (re.compile('Opt. Exp., *'), 'Opt.Express, '),
           (re.compile('Low Temperature Physics, *'), 'Low Temp.Phys., ')]


def normalizejournalsworkaround(rawref):
    for (renjwa, normalized) in renjwas:
        rawref = renjwa.sub(normalized, rawref)
    return rawref



def validxml(string):
    if type(string) == type(()):
        return tuple([validxml(part) for part in string])
    elif type(string) == type([]):
        return [validxml(part) for part in string]
    else:
        #print '--->',string
        string = htmlentity.sub(lam, string)
        string = re.sub('&','&amp;',string)
        string = re.sub('>','&gt;',string)
        string = re.sub('<','&lt;',string)
        string = re.sub('"','&quot;',string)
        string = re.sub('\'','&apos;',string)
        return re.sub('  +', ' ', string)


def marcxml(marc,liste):
    if len(marc) < 5: marc += ' '
    if len(marc) < 5: marc += ' '
    #print marc,liste
    xmlstring = ' <datafield tag="%s" ind1="%s" ind2="%s">\n' % (marc[:3],marc[3],marc[4])
    for tupel in liste:
        if tupel[1] is not None:
            if type(tupel[1]) == type([]):
                for element in tupel[1]:
                    if element != '':
                        xmlstring += '  <subfield code="%s">%s</subfield>\n' % (tupel[0], validxml(element).strip())
            else:
                if tupel[1] != '':
                    try:
                        xmlstring += '  <subfield code="%s">%s</subfield>\n' % (tupel[0],validxml(tupel[1]).strip())
                    except:
                        print 'ERROR in function "marcxml"'
                        print marc, liste
    xmlstring += ' </datafield>\n'
    #avoid empty xml entries
    if re.search('<subfield code="[a-z]">',xmlstring):
        return xmlstring
    else:
        return ''


#regular expressions to add field code based on rec['note']
refcmp = re.compile('Mathematical Phys')
refcp = re.compile('Phys')
refcm = re.compile('Math')
refcc = re.compile('Comp')
refca = re.compile('Astro')
refck = re.compile('[qQ]uantum.(Phys|phys|Infor|infor|Comp|comp|Tec|Com|Corr|Theor|Mech|Dynam|Opti|Elec)')
def writeXML(recs,dokfile,publisher):
    dokfile.write('<collection>\n')
    i = 0
    for rec in recs:
        recdate = False
        if rec['jnl'] in ['Astron.Astrophys.', 'Mon.Not.Roy.Astron.Soc.', 
                          'Astronom.J.', 'Adv.Astron.', 'Astron.Nachr.']:
            arXivfromADS(rec)
        liste = []
        i += 1
        if 'doi' in rec.keys():
            print rec['doi'], rec.keys()
        elif 'hdl' in rec.keys():
            print rec['hdl'], rec.keys()
        elif 'urn' in rec.keys():
            print rec['urn'], rec.keys()
        else:
            print 'no identifier?!       ', rec.keys()
        if rec.has_key('arxiv') and re.search('v[0-9]+$', rec['arxiv']):
            rec['arxiv'] = re.sub('v[0-9]+$', '', rec['arxiv'])
        xmlstring = '<record>\n'
        #direct marc first (retinspire takes the first DOI?)
        if rec.has_key('MARC'):
            for marc in rec['MARC']:
                xmlstring += marcxml(marc[0], marc[1])
        #TITLE
        if rec.has_key('tit'):
            xmlstring += marcxml('245',[('a',kapitalisiere(rec['tit'])), ('9',publisher)])
        if rec.has_key('otits'):
            for otit in rec['otits']:
                xmlstring += marcxml('246', [('a',kapitalisiere(otit)), ('9',publisher)])
        if rec.has_key('transtit'):
            xmlstring += marcxml('242',[('a',kapitalisiere(rec['transtit'])), ('9',publisher)])
        #LANGUAGE
        if rec.has_key('language'):
            #print rec
            xmlstring += marcxml('041', [('a', rec['language'])])
            xmlstring += marcxml('595', [('a', 'Text in %s' % (rec['language']))])
        #ABSTRACT
        if rec.has_key('abs'):
            if len(rec['abs']) > 5:
                try:
                    xmlstring += marcxml('520',[('a',rec['abs']), ('9',publisher)])
                except:
                    #xmlstring += marcxml('595', [('a', 'could not write abstract!')])
                    xmlstring += marcxml('520', [('a', unidecode.unidecode(rec['abs'])), ('9', publisher)])
            else:
                print 'abstract "%s" too short' % (rec['abs'])
        #DATE
        if 'date' in rec.keys():
            try:
                #recdate = rec['date']
                recdate = normalize_date(rec['date'])
            except:
                recdate = False
                print ' !! invalid date "%s"' % (rec['date'])
                del(rec['date'])
        if not 'date' in rec.keys() and 'year' in rec.keys():
            rec['date'] = rec['year']
            recdate = rec['year']
        if 'date' in rec.keys():
            try:
                if 'B' in rec['tc']:
                    xmlstring += marcxml('260', [('c', recdate), ('t', 'published'), ('b', publisher)])
                else:
                    xmlstring += marcxml('260', [('c', recdate), ('t', 'published')])
            except:
                try:
                    xmlstring += marcxml('260', [('c', rec['year']), ('t', 'published')])
                except:
                    print '{DATE}', recdate,  rec
                    xmlstring += marcxml('599', [('a', 'date missing?!')])
        #KEYWORDS
        if rec.has_key('keyw'):
            if len(rec['keyw']) == 1:
                if rekeywsplit1.search(rec['keyw'][0]):
                    keywords = re.split(', ', rec['keyw'][0])
                    xmlstring += marcxml('595', [('a', 'Keywords split: "%s"' % (rec['keyw'][0]))])
                elif rekeywsplit2.search(rec['keyw'][0]):
                    keywords = re.split('; ', rec['keyw'][0])
                    xmlstring += marcxml('595', [('a', 'Keywords split: "%s"' % (rec['keyw'][0]))])
                else:
                    keywords = rec['keyw']
            else:
                keywords = rec['keyw']
            for kw in rec['keyw']:
                #xmlstring += marcxml('6531',[('a',kw), ('9','publisher')])
                if kw.strip(): 
                    try:
                        xmlstring += marcxml('6531',[('a',kw), ('9','author')])
                    except:
                        if unidecode.unidecode(kw).strip():
                            xmlstring += marcxml('6531', [('a', unidecode.unidecode(kw)), ('9','author')])
        if rec.has_key('authorkeyw'):
            for kw in rec['authorkeyw']:
                if kw:
                    xmlstring += marcxml('6531',[('a',kw), ('9','author')])
        #PUBNOTE
        if rec.has_key('jnl'):
            liste = [('p',rec['jnl'])]
            if rec.has_key('year'):
                liste.append(('y',rec['year']))
            elif rec.has_key('date'):
                liste.append(('y',re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])))
            if rec.has_key('p1'):
                if rec.has_key('p2'):
                    if rec['p1'] != rec['p2']:
                        liste.append(('c',rec['p1']+'-'+rec['p2']))
                    else:
                        liste.append(('c',rec['p1']))
                    if not rec.has_key('pages'):
                        try:
                            if rec['p1'] != rec['p2']:
                                xmlstring += marcxml('300',[('a',str(int(rec['p2'])-int(rec['p1'])+1))])
                        except:
                            pass
                else:
                    liste.append(('c',rec['p1']))
            elif rec.has_key('seq'):
                liste.append(('c',rec['seq']))
            elif rec.has_key('wsp_seq'):
                liste.append(('c',rec['wsp_seq']))
            elif rec.has_key('artnum'):
                liste.append(('c',rec['artnum']))
            if rec.has_key('vol'): liste.append(('v',rec['vol']))
            if rec.has_key('pbnrep'): liste.append(('r',rec['pbnrep']))
            if rec.has_key('issue'): liste.append(('n',rec['issue']))
            if rec.has_key('cnum'): liste.append(('w',rec['cnum']))
            if rec.has_key('motherisbn'): liste.append(('z',rec['motherisbn']))
            xmlstring += marcxml('773',liste)
        if 'alternatejnl' in rec.keys():
            alternateliste = [('p', rec['alternatejnl'])]
            for tup in liste:
                if tup[0] == 'v':
                    if 'alternatevol' in rec.keys():
                        alternateliste.append(('v', rec['alternatevol']))
                    else:
                        alternateliste.append(tup)
                elif tup[0] == 'c':
                    if 'alternatep1' in rec.keys():
                        if rec.has_key('alternatep2'):
                            if rec['alternatep1'] != rec['alternatep2']:
                                alternateliste.append(('c',rec['alternatep1']+'-'+rec['alternatep2']))
                            else:
                                alternateliste.append(('c',rec['alternatep1']))
                    else:
                        alternateliste.append(tup)
                elif tup[0] == 'n':
                    if 'alternateissue' in rec.keys():
                        alternateliste.append(('n', rec['alternateissue']))
                    else:
                        alternateliste.append(tup)
                elif tup[0] != 'p':
                    alternateliste.append(tup)
            xmlstring += marcxml('7731', alternateliste)
        if rec.has_key('jnl2') and rec.has_key('vol2'):
            liste = [('p',rec['jnl2'])]
            if rec.has_key('year2'):
                liste.append(('y',rec['year2']))
            elif rec.has_key('date'):
                liste.append(('y',re.sub('.*([12]\d\d\d.*', r'\1', rec['date'])))
            if rec.has_key('p1p22'):
                rec['p1p22'] = re.sub('–', '-', rec['p1p22'])
                liste.append(('c',rec['p1p22']))
            if rec.has_key('vol2'): liste.append(('v',rec['vol2']))
            if rec.has_key('issue2'): liste.append(('n',rec['issue2']))
            if rec.has_key('cnum'): liste.append(('w',rec['cnum']))
            xmlstring += marcxml('773',liste)
        #BOOK SERIES
        if rec.has_key('bookseries'):
            xmlstring += marcxml('490', rec['bookseries'])
        #ISBN
        if rec.has_key('isbns'):
            for isbn in rec['isbns']:
                xmlstring += marcxml('020', isbn)
        elif rec.has_key('isbn'):
            xmlstring += marcxml('020',[('a', re.sub('\-', '', rec['isbn']))])
        #DOI
        if rec.has_key('doi'):
            xmlstring += marcxml('0247',[('a',rec['doi']), ('2','DOI'), ('9',publisher)])
            #special euclid:
            if re.search('^20.2000\/euclid\.', rec['doi']):
                xmlstring += marcxml('035', [('9', 'EUCLID'), ('a', rec['doi'][8:])])
        #HDL
        if rec.has_key('hdl'):
            xmlstring += marcxml('0247',[('a',rec['hdl']), ('2','HDL'), ('9',publisher)])
        #URN
        if rec.has_key('urn'):
            xmlstring += marcxml('0247',[('a',rec['urn']), ('2','URN'), ('9',publisher)])
        elif not 'doi' in rec.keys() and not 'hdl' in rec.keys():
            if len(liste) > 2 or rec.has_key('isbn') or rec.has_key('isbns'):
                pseudodoi = '20.2000/'+re.sub(' ','_','-'.join([tup[1] for tup in liste]))
                if rec.has_key('isbn'):
                    pseudodoi += '_' + rec['isbn']
                elif rec.has_key('isbns'):
                    for tupel in rec['isbns'][0]:
                        if tupel[0] == 'a':
                            pseudodoi += '_' + tupel[1]
                xmlstring += marcxml('0247',[('a',pseudodoi), ('2','NODOI'), ('9',publisher)])
            elif 'tit' in rec.keys():
                pseudodoi = '30.3000/' + re.sub('\W', '', rec['tit'])
                if 'auts' in rec.keys() and rec['auts']:
                    pseudodoi += '/' + re.sub('\W', '', rec['auts'][0])
                elif 'autaff' in rec.keys() and rec['autaff'] and rec['autaff'][0]:
                    pseudodoi += '/' + re.sub('\W', '', rec['autaff'][0][0])
                xmlstring += marcxml('0247',[('a',pseudodoi), ('2','NODOI'), ('9',publisher)])
        #NUMBER OF PAGES
        if rec.has_key('pages'):
            if rec['pages']:
                if type(rec['pages']) == type('999'):
                    xmlstring += marcxml('300',[('a',rec['pages'])])
                elif type(rec['pages']) == type(u'999'):
                    xmlstring += marcxml('300',[('a',rec['pages'])])
                elif type(rec['pages']) == type(999):
                    xmlstring += marcxml('300',[('a',str(rec['pages']))])
        #TYPE CODE
        if rec.has_key('tc'):
            for tc in rec['tc']:
                if tc != '':
                    xmlstring += marcxml('980',[('a',inspiretc[tc])])
        #PACS
        if rec.has_key('pacs'):
            for pacs in rec['pacs']:
                xmlstring += marcxml('084',[('a',pacs), ('2','PACS')])
        #COLLABRATION
        if rec.has_key('col'):
            if type(rec['col']) != type([]):
                rec['col'] = [rec['col']]
            newcolls = []
            for col in rec['col']:
                for original in coll_split(col):
                    (coll, author) = coll_cleanforthe(original)
                    coll = coll_clean710(coll)
                    newcolls.append(coll)
                    if author:
                        try:
                            print 'found author %s in collaboration string %s' % (author, original)
                        except:
                            print 'found author in collaboration string'
            for col in newcolls:
                xmlstring += marcxml('710',[('g',col)])
                if not rec.has_key('exp') and colexpdict.has_key(col):
                    xmlstring += marcxml('693',[('e',colexpdict[col])])
        #arXiv NUMBER
        if rec.has_key('arxiv'):
            if re.search('^[0-9]',rec['arxiv']):
                rec['arxiv'] = 'arXiv:'+rec['arxiv']
            if rearxivnew.search(rec['arxiv']) or rearxivold.search(rec['arxiv']):
                xmlstring += marcxml('037',[('a',rec['arxiv']),('9','arXiv')])
            else:
                xmlstring += marcxml('037',[('a',rec['arxiv'])])
        #REPORT NUMBER
        if rec.has_key('rn'):
            for rn in rec['rn']:
                #check for OSTI
                if re.search('^OSTI\-', rn):
                    xmlstring += marcxml('035', [('9', 'OSTI'), ('a', rn[5:])])
                else:
                    xmlstring += marcxml('037', [('a', rn)])
        #EXPERIMENT
        if rec.has_key('exp'):
            xmlstring += marcxml('693',[('e',rec['exp'])])
        #PDF LINK
        if 'pdf' in rec.keys():
            if re.search('^http', rec['pdf']):
                xmlstring += marcxml('8564',[('u',rec['pdf']), ('y','Fulltext')])
            else:
                xmlstring += marcxml('595', [('a', 'invalid link "%s"' % (rec['pdf']))])
        #FULLTEXT
        if 'FFT' in rec.keys():
            if re.search('^http', rec['FFT']) or re.search('^\/afs\/cern', rec['FFT']):
                xmlstring += marcxml('FFT',[('a',rec['FFT']), ('d','Fulltext'), ('t','INSPIRE-PUBLIC')])
            else:
                xmlstring += marcxml('595', [('a', 'invalid link "%s"' % (rec['FFT']))])
        elif 'fft' in rec.keys():
            if re.search('^http', rec['fft']) or re.search('^\/afs\/cern', rec['fft']):
                xmlstring += marcxml('FFT',[('a',rec['fft']), ('d','Fulltext'), ('t','INSPIRE-PUBLIC')])
            else:
                xmlstring += marcxml('595', [('a', 'invalid link "%s"' % (rec['fft']))])
        elif 'hidden' in rec.keys():
            if re.search('^http', rec['hidden']) or re.search('^\/afs\/cern', rec['hidden']):
                xmlstring += marcxml('FFT',[('a',rec['hidden']), ('d','Fulltext'), ('o', 'HIDDEN')])
            else:
                xmlstring += marcxml('595', [('a', 'invalid link "%s"' % (rec['hidden']))])
        #LINK
        if 'link' in rec.keys():
            if re.search('^http', rec['link']):
                xmlstring += marcxml('8564',[('u', rec['link'])])
            else:
                xmlstring += marcxml('595', [('a', 'invalid link "%s"' % (rec['link']))])
        #LICENSE
        if 'license' in rec.keys() and not 'licence' in rec.keys():
            rec['licence'] = rec['license']
        if rec.has_key('licence'):
            entry = []
            if rec['licence'].has_key('statement'):
                entry.append(('a',rec['licence']['statement']))
            elif rec['licence'].has_key('url') and re.search('creativecommons.org', rec['licence']['url']):
                if re.search('\/zero\/', rec['licence']['url'].lower()):
                    statement = 'CC-0'
                else:
                    statement = re.sub('.*licen[cs]es', 'CC', rec['licence']['url']).upper()
                    statement = re.sub('.LEGALCODE', '', statement)
                    statement = re.sub('.DEED...', '', statement)
                entry.append(('a', re.sub('\/', '-', re.sub('\/$', '', statement))))
            if rec['licence'].has_key('url'):
                entry.append(('u',rec['licence']['url']))
            if rec['licence'].has_key('organization'):
                entry.append(('b',rec['licence']['organization']))
            elif entry:
                entry.append(('b', publisher))
            if rec['licence'].has_key('material'):
                entry.append(('3',rec['licence']['material']))
            try:
                xmlstring += marcxml('540', entry)
            except:
                xmlstring += marcxml(marc, [(tup[0], unidecode.unidecode(tup[1])) for tup in entry])
        #SUPERVISOR
        if rec.has_key('supervisor'):
            marc = '701'
            for autaff in rec['supervisor']:
                autlist = [('a',shapeaut(autaff[0]))]
                for aff in autaff[1:]:
                    if re.search('ORCID', aff):
                        aff = re.sub('\s+', '', aff)
                        if reorcid.search(aff):
                            autlist.append(('j', aff))
                        else:
                            print ' "%s" is not a valid ORCID' % (aff)                        
                    elif re.search('EMAIL', aff):
                        if re.search('@', aff):
                            autlist.append(('m', re.sub('EMAIL:', '', aff)))
                    else:
                        autlist.append(('v', aff))
                try:
                    xmlstring += marcxml(marc, autlist)
                except:
                    autlist2 = [(tup[0], unidecode.unidecode(tup[1])) for tup in autlist]
                    xmlstring += marcxml(marc, autlist2)
        #AUTHORS
        if rec.has_key('autaff'):
            marc = '100'
            for autaff in rec['autaff']:
                grids = []
                #check for collaborations
                if re.search('Collaboration', autaff[0], re.IGNORECASE):
                    newcolls = []
                    (coll, author) = coll_cleanforthe(autaff[0])
                    for scoll in coll_split(coll):
                        newcolls.append(re.sub('^the ', '', coll_clean710(scoll), re.IGNORECASE))
                    for col in newcolls:
                        xmlstring += marcxml('710',[('g',col)])
                        if not rec.has_key('exp') and colexpdict.has_key(col):
                            xmlstring += marcxml('693',[('e',colexpdict[col])])
                    if author:
                        autaff[0] = author
                    else:
                        continue
                if re.search('\([eE]d\.\)', autaff[0]):
                    autlist = [('a', shapeaut(re.sub(' *\([eE]d\.\) *','',autaff[0]))), ('e','ed.')]
                else:
                    autlist = [('a',shapeaut(autaff[0]))]
                for aff in autaff[1:]:
                    if re.search('ORCID', aff):
                        if reorcid.search(aff):
                            autlist.append(('j', aff))
                        else:
                            print ' "%s" is not a valid ORCID' % (aff)    
                    elif re.search('EMAIL', aff):
                        if re.search('@', aff):
                            autlist.append(('m', re.sub('EMAIL:', '', aff)))
                    else:
                        #GRID hier
                        if re.search(', GRID:', aff):
                            autlist.append(('v',  re.sub(', GRID:.*', '', aff)))
                            grid = re.sub('.*, GRID:', 'GRID:', aff)
                            if not grid in grids:
                                autlist.append(('t', grid))
                                grids.append(grid)
                        else:
                            autlist.append(('v', aff))
                try:
                    xmlstring += marcxml(marc, autlist)
                except:
                    print rec['link']
                    print autlist
                    autlist2 = [(tup[0], unidecode.unidecode(tup[1])) for tup in autlist]
                    xmlstring += marcxml(marc, autlist2)
                marc = '700'
        elif rec.has_key('auts'):
            affdict = {}
            tempaffs = []
            if rec.has_key('aff'):
                for aff in rec['aff']:
                    if re.search('=',aff):
                        parts = re.split('= *',aff)
                        affdict[parts[0]] = parts[1]
                    else:
                        tempaffs.append(('v',aff))
            #print affdict
            longauts = []
            rec['auts'].reverse()
            preventry = ' '
            for entry in rec['auts']:
                if entry == '':
                    continue
                #print '--', entry
                if entry[0] == '=':
                    if preventry[0] != '=':
                        tempaffs = []
                    affs = re.split('; ',entry)
                    affs.reverse()
                    for aff in affs:
                        if affdict.has_key(aff[1:]):
                            tempaffs.insert(0,('v',affdict[aff[1:]]))
                    #print tempaffs
                else:
                    #check for collaborations
                    if re.search('Collaboration', entry, re.IGNORECASE):
                        newcolls = []
                        (coll, author) = coll_cleanforthe(entry)
                        coll = re.sub(', ORCID.*', '', coll)
                        for scoll in coll_split(coll):
                            newcolls.append(re.sub('^the ', '', coll_clean710(scoll), re.IGNORECASE))
                        for col in newcolls:
                            if not re.search('(CHINESENAME|ORCID|EMAIL)', col):
                                xmlstring += marcxml('710',[('g',col)])
                                if not rec.has_key('exp') and colexpdict.has_key(col):
                                    xmlstring += marcxml('693',[('e',colexpdict[col])])
                        if author:
                            entry = author
                        else:
                            continue
                    if re.search('\([eE]d\.\)',entry):
                        aut = [('a', shapeaut(re.sub(' *\([eE]d\.\) *','',entry))), ('e','ed.')]
                    else:
                        author = entry
                        aut = []
                        if re.search('CHINESENAME', author):
                            aut.append(('q', re.sub('.*, CHINESENAME: ', '', author)))
                            author = re.sub(' *, CHINESENAME.*', '', author)
                        if re.search('ORCID', author):
                            orcid = re.sub(' ', '', re.sub('\.$', '', re.sub('.*, ORCID',  'ORCID', author)))
                            if reorcid.search(orcid):
                                aut.append(('j', orcid))
                            else:
                                print ' "%s" is not a valid ORCID' % (orcid)    
                            author = re.sub(' *, ORCID.*', '', author)
                        if re.search('EMAIL', author):
                            if re.search('@', author):
                                aut.append(('m', re.sub('.*, EMAIL:',  '', author)))
                            author = re.sub(', EMAIL.*', '', author)
                        aut.append(('a', shapeaut(author)))
                    if (len(tempaffs) == 0) and (len(affdict) > 0):
                        tempaffs = [('v',affdict[affdict.keys()[0]])]
                    #GRID hier
                    ntempaffs = []
                    grids = []
                    for ta in tempaffs:
                        if re.search(', GRID:', ta[1]):
                            ntempaffs.append(('v', re.sub(', GRID:.*', '', ta[1])))
                            grid = re.sub('.*, GRID:', 'GRID:', ta[1])
                            if not grid in grids:
                                ntempaffs.append(('t', grid))
                                grids.append(grid)
                        else:
                            ntempaffs.append(ta)
                    longauts.insert(0,aut+ntempaffs)
                preventry = entry
            marc = '100'
            for aut in longauts:
                xmlstring += marcxml(marc,aut)
                marc = '700'
        #REFERENCES
        if rec.has_key('refs'):
            print ' extracting %i refs for record %i of %i' % (len(rec['refs']),i,len(recs))
            for ref in rec['refs']:
                #print '  ->  ', ref
                if len(ref) == 1 and ref[0][0] == 'x':
                    rawref = re.sub('Google ?Scholar', '', ref[0][1])
                    rawref = re.sub('[cC]ross[rR]ef', '', rawref)
                    rawref = re.sub('[\n\t\r]', ' ', rawref)
                    rawref = re.sub('  +', ' ', rawref)
                    rawref = normalizejournalsworkaround(rawref)
                    rawref = re.sub('\xc2\xa0', ' ', rawref)
                    rawref = re.sub('\xa0', ' ', rawref)
                    try:
                        extractedrefs = extract_references_from_string(rawref, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}")
                        for ref2 in extractedrefs:
                            #find additional reportnumbers
                            additionalreportnumbers = []
                            if 'misc' in ref2.keys():
                                for misc in ref2['misc']:
                                    if repreprints.search(misc):
                                        for preprint in re.split(', ', repreprints.sub(r'\1', misc)):
                                            if repreprint.search(preprint):
                                                additionalreportnumbers.append(('r', re.sub('[\/ ]', '-', preprint)))
                            #translate refeextract output                                          
                            entryaslist = [('9','refextract')]
                            for key in ref2.keys():
                                if key in mappings.keys():
                                    for entry in ref2[key]:
                                        entryaslist.append((mappings[key], entry))
                            if len(extractedrefs) == 1:
                                if re.search('inspirehep.net\/record\/\d+', rawref):
                                    entryaslist.append(('0', re.sub('.*inspirehep.net\/record\/(\d+).*', r'\1',  rawref)))
                            xmlstring += marcxml('999C5', entryaslist + additionalreportnumbers)
                    except:
                        print 'UTF8 Problem in Referenzen'
                        try:
                            ref01 = unicode(unicodedata.normalize('NFKD', re.sub(u'ß', u'ss', rawref)).encode('ascii', 'ignore'), 'utf-8')
                            extractedrefs = extract_references_from_string(ref01, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}")                            
                            for ref2 in extractedrefs:
                                #find additional reportnumbers
                                additionalreportnumbers = []
                                if 'misc' in ref2.keys():
                                    for misc in ref2['misc']:
                                        if repreprints.search(misc):
                                            for preprint in re.split(', ', repreprints.sub(r'\1', misc)):
                                                if repreprint.search(preprint):
                                                    additionalreportnumbers.append(('r', re.sub('[\/ ]', '-', preprint)))
                                #translate refeextract output                                          
                                entryaslist = [('9','refextract')]
                                for key in ref2.keys():
                                    if key in mappings.keys():
                                        for entry in ref2[key]:
                                            entryaslist.append((mappings[key], entry))
                                if len(extractedrefs) == 1:
                                    if re.search('inspirehep.net\/record\/\d+', rawref):
                                        entryaslist.append(('0', re.sub('.*inspirehep.net\/record\/(\d+).*', r'\1',  rawref)))
                                xmlstring += marcxml('999C5', entryaslist + additionalreportnumbers)
                        except:
                            print 'real UTF8 Problem in Referenzen'
                            xmlstring += marcxml('595', [('a', 'real UTF8 Problem in Referenzen')])
                else:
                    xmlstring += marcxml('999C5',ref)
        xmlstring += marcxml('980',[('a','HEP')])
        #COMMENTS
        #temporary informations used for selection process
        if rec.has_key('comments'):
            for comment in rec['comments']:
                xmlstring += marcxml('595',[('a',comment)])
        if rec.has_key('note'):
            if not 'fc' in rec.keys():
                for comment in rec['note']:
                    if refcmp.search(comment):
                        rec['fc'] = 'm'
                        rec['note'].append('added fieldcode by note')
                    elif refcp.search(comment):
                        pass # ignore things like 'School of Mathematics and Physics'
                    elif refcm.search(comment):
                        rec['fc'] = 'm'
                        rec['note'].append('added fieldcode by note')
                    elif refca.search(comment):
                        rec['fc'] = 'a'
                        rec['note'].append('added fieldcode by note')
                    elif refck.search(comment):
                        rec['fc'] = 'k'
                        rec['note'].append('added fieldcode by note')
                    elif refcc.search(comment):
                        rec['fc'] = 'c'
                        rec['note'].append('added fieldcode by note')                    
            for comment in rec['note']:
                try: 
                    xmlstring += marcxml('595', [('a', comment)])
                except:
                    xmlstring += marcxml('595', [('a', unidecode.unidecode(comment))])
        if rec.has_key('typ'):
            xmlstring += marcxml('595',[('a',rec['typ'])])
        #FIELD CODE
        if rec['jnl'] in jnltofc.keys():
            for fc in jnltofc[rec['jnl']]:
                print '  FC:', rec['jnl'], fc
                if 'fc' in rec.keys():
                    rec['fc'] += fc
                else:
                    rec['fc'] = fc
        if rec.has_key('fc'):
            for fc in rec['fc']:
                xmlstring += marcxml('65017',[('a',inspirefc[fc]),('2','INSPIRE')])
        #THESIS PUBNOTE
        if 'T' in rec['tc'] and not re.search('"502"', xmlstring):
            thesispbn = [('b', 'PhD')]
            if 'autaff' in rec.keys() and len(rec['autaff'][0]) > 1:
                for aff in rec['autaff'][0][1:]:
                    if not re.search('EMAIL', aff) and not re.search('ORCID', aff):
                        thesispbn.append(('c', aff))
            elif 'aff' in rec.keys() and rec['aff']:
                thesispbn.append(('c', rec['aff'][0]))
            if 'date' in rec.keys():
                thesispbn.append(('d', re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])))
            xmlstring += marcxml('502', thesispbn)
        xmlstring += '</record>\n'
        try:
            dokfile.write(xmlstring)
        except:
            dokfile.write(xmlstring.encode("utf8", "ignore"))
    dokfile.write('</collection>\n')
    return


rebindestrich = re.compile('([A-Z] ?\.)[ \-]([A-Z] ?\.?)')
revan1a = re.compile('(.*) (van den|van der|van de|de la) (.*)')
revan2a = re.compile('(.*) (van|van|de|von|del|du) (.*)')
revan1b = re.compile('(.*) (van den|van der|van de|de la)$')
revan2b = re.compile('(.*) (van|van|de|von|del|du)$')
reswap = re.compile('(.*) (.*)')
def shapeaut(author):
    author = re.sub('\&nbps;', ' ', author)
    author = re.sub('\xa0', ' ', author)
    if re.search(' ',  author):
        if not re.search(',', author):
            if revan1a.search(author):
                author = revan1a.sub(r'\2 \3, \1',author).strip()
            elif revan2a.search(author):
                author = revan2a.sub(r'\2 \3, \1',author).strip()
            else:
                author = reswap.sub(r'\2, \1',author).strip()
        else:
            author = revan1b.sub(r'\2 \1', author)
            author = revan2b.sub(r'\2 \1', author)
    author = re.sub(' ([A-Z]) ',r' \1. ', author)
    author = rebindestrich.sub(r'\1\2', author)
    author = re.sub(', *', ', ', author.strip())
    if not re.search('[a-z]', author):
        author = author.title()
    author = re.sub('([A-Z])$',r'\1.', author)
    return author


reqis = re.compile('^\d+ *')
def writenewXML(recs, dokfile, publisher, dokifilename):
    for rec in recs:
        #add doki file name
        if 'note' in rec.keys():
            rec['note'].append('DOKIFILE:'+dokifilename)
        else:
            rec['note'] = ['DOKIFILE:'+dokifilename]
        #QIS keywords
        doi1 = False 
        if 'doi' in rec.keys():
            doi1 = re.sub('[\(\)\/]', '_', rec['doi'])
        elif 'hdl' in rec.keys():
            doi1 = re.sub('[\(\)\/]', '_', rec['hdl'])
        elif 'urn' in rec.keys():
            doi1 = re.sub('[\(\)\/]', '_', rec['urn'])
        print '>>', doi1
        if doi1:
            absfilename = os.path.join(absdir, doi1)
            bibfilename = os.path.join(tmpdir, doi1+'.qis.bib')
            if not os.path.isfile(absfilename):                
                absfile = codecs.EncodedFile(codecs.open(absfilename, mode='wb'), 'utf8')
                try:
                    if 'tit' in rec.keys():
                        try:
                            absfile.write(rec['tit'] + '\n\n')
                        except:
                            absfile.write(unidecode.unidecode(rec['tit']) + '\n\n')
                    if 'abs' in rec.keys():
                        try:
                            absfile.write(rec['abs'] + '\n\n')
                        except:
                            absfile.write(unidecode.unidecode(rec['abs']) + '\n\n')
                    if 'keyw' in rec.keys():
                        for kw in rec['keyw']:
                            try:
                                absfile.write(kw + '\n')
                            except:
                                absfile.write(unidecode.unidecode(kw) + '\n')
                except:
                    print '   could not write abstract to file'
                absfile.close()
            if not os.path.isfile(bibfilename):
                print ' >bibclassify %s' % (doi1)
                os.system('%s %s > %s' % (qisbibclassifycommand, absfilename, bibfilename))
            absbib = open(bibfilename, 'r')
            lines = absbib.readlines()
            qiskws = []
            for line in lines:
                if reqis.search(line):
                    qiskws.append('[QIS] ' + line.strip())
            absbib.close()
            if qiskws:
                if not 'note' in rec.keys():
                    rec['note'] = []
                rec['note'].append('%i QIS keywords found' % (len(qiskws)))
                print '   %i QIS keywords found' % (len(qiskws))
                for qiskw in qiskws:
                    rec['note'].append(qiskw)
                if 'fc' in rec.keys():
                    if not 'k' in rec['fc']:
                        rec['fc'] += 'k'
                else:    
                    rec['fc'] = 'k'
    writeXML(recs, dokfile, publisher)
    return
