import re
from refextract import extract_references_from_string

verbose = False

def tryprint(string):
    if verbose:
        try:
            print string
        except:
            print '...'
    return


#handle nasty formatting
reclpbns = [(re.compile(', vol. '), ', '),
            (re.compile(', Article ID '), ', '),
            (re.compile('\| *'), ''),
            (re.compile('\| *'), ''),
            (re.compile(', article '), ', '),
            (re.compile(', aticle [Nn]o\. '), ', '),
            (re.compile('\. View at: , DOI:'), ', DOI:'),
            (re.compile('\. View at: *$'), ''),
            (re.compile('Zeitschrift f.r Physik C, '), 'Z.Phys., C'),
            (re.compile('Zeitschrift f.r Physik C Particles and Fields, '), 'Z.Phys., C'),
            (re.compile('Zeitschrift f.r Physik'), 'Z.Phys.'),
            (re.compile('Nuclear Physics. B. Theoretical, Phenomenological, and Experimental High Energy Physics. Quantum Field Theory and Statistical Systems, (\d+), [Nn]o. \d+, '), r'Nucl.Phys., B\1, '),
            (re.compile('Nuclear Physics. B. Theoretical, Phenomenological, and Experimental High Energy Physics. Quantum Field Theory and Statistical Systems, (\d+), [Nn]o. \d+.\d+, '), r'Nucl.Phys., B\1, '),
            (re.compile('Nuclear Physics. B. Theoretical, Phenomenological, and Experimental High Energy Physics. Quantum Field Theory and Statistical Systems, '), 'Nucl.Phys., B'),
            (re.compile('Physics Reports, (\d+), [Nn]o. \d+, '), r'Phys.Rept., \1, '),
            (re.compile('Physics Reports, (\d+), [Nn]o. \d+.\d+, '), r'Phys.Rept., \1, '),
            (re.compile('Nuclear Physics A, (\d+), [Nn]o. \d+, '), r'Nucl.Phys., A\1, '),
            (re.compile('Nuclear Physics A, (\d+), [Nn]o. \d+.\d+, '), r'Nucl.Phys., A\1, '),
            (re.compile('Nuclear Physics B, (\d+), [Nn]o. \d+, '), r'Nucl.Phys., B\1, '),
            (re.compile('Nuclear Physics B, (\d+), [Nn]o. \d+.\d+, '), r'Nucl.Phys., B\1, '),
            (re.compile('Physics Letters A, (\d+), [Nn]o. \d+, '), r'Phys.Lett., A\1, '),
            (re.compile('Physics Letters A, (\d+).\d+, [Nn]o. \d+, '), r'Phys.Lett., A\1, '),
            (re.compile('Physics Letters B, (\d+), [Nn]o. \d+, '), r'Phys.Lett., B\1, '),
            (re.compile('Physics Letters B, (\d+), [Nn]o. \d+.\d+, '), r'Phys.Lett., B\1, '),
            (re.compile('Physical Review ([ABCDEX]),? (\d{1,3}), (no\.|p\.) (\d{3,6})'), r'Phys.Rev., \1\2, \4'),
            (re.compile('Physics Letters B, B'), 'Phys.Lett., B'),
            (re.compile('Physics of the Dark Universe, '), 'Phys.Dark Univ., '),
            (re.compile('The European Physical Journal Plus, (\d+), p\. (\d+)'), r'Eur.Phys.J.Plus, \1, \2'),
            (re.compile('The European Physical Journal Plus, '), 'Eur.Phys.J.Plus, '),
            (re.compile('Journal of Physics A: Mathematical and General, '), 'J.Phys., A'),
            (re.compile('Physics Letters.? A. General, Atomic [aA]nd Solid State Physics, '), 'Phys.Lett., A'),
            (re.compile('Physics Letters. B. Particle Physics, Nuclear Physics,? [aA]nd Cosmology, '), 'Phys.Lett., B'),
            (re.compile('Physics Letters B. Particle Physics, Nuclear Physics,? [aA]nd Cosmology, '), 'Phys.Lett., B'),
            (re.compile('International Journal of Modern Physics A. Particles [aA]nd Fields. Gravitation. Cosmology. Nuclear Physics. '), 'Int.J.Mod.Phys., A'),
            (re.compile('International Journal of Modern Physics A. Particles [aA]nd Fields. Gravitation. Cosmology. '), 'Int.J.Mod.Phys., A'),
            (re.compile('International Journal of Modern Physics D. Gravitation, Astrophysics, Cosmology, '), 'Int.J.Mod.Phys., D'),
            (re.compile('Physical Review C *. [nN]uclear [pP]hysics, '), 'Phys.Rev., C'),
            (re.compile('Physical Review C *. Covering Nuclear Physics, '), 'Phys.Rev., C'),
            (re.compile('Physical Review D *. Covering Particles, Fields, Gravitation,? [aA]nd Cosmology, '), 'Phys.Rev., D'),
            (re.compile('Physical Review D *. Particles, Fields, Gravitation,? [aA]nd Cosmology, '), 'Phys.Rev., D'),
            (re.compile('Physics Letters, Section B: Nuclear, Elementary Particle and High-Energy Physics, '), 'Phys.Lett., B'),
            (re.compile('Astronomy & Astrophysics *, '), 'Astron.Astrophys., '),
            (re.compile('The Astrophysical Journal Letters, (\d+) , [Nn]o. L(\d+)'), r'Astrophys.J.Lett., \1, L\2'),
            (re.compile('European Physical Journal A: Hadrons and Nuclei '), 'Eur.Phys.J., A'),
            (re.compile('The European Physical Journal A, '), 'Eur.Phys.J., A'),
            (re.compile('The European Physical Journal B, '), 'Eur.Phys.J., B'),
            (re.compile('European Physical Journal C: Particles and Fields '), 'Eur.Phys.J., C'),
            (re.compile('The European Physical Journal C, '), 'Eur.Phys.J., C'),
            (re.compile('The European Physical Journal D, '), 'Eur.Phys.J., D'),
            (re.compile('The European Physical Journal E, '), 'Eur.Phys.J., E'),
            (re.compile('Journal of Physics A: Mathematical and General '), 'J.Phys.,A'),
            (re.compile('Journal of Physics: Conference Series, '), 'J.Phys.Conf.Ser. '),
            (re.compile('Journal of Cosmology and Astroparticle Physics'), 'JCAP'),
            (re.compile('Journal of High Energy Physics'), 'JHEP'),
            (re.compile('Nuclear Physics B.Proceedings Supplements, '), 'Nucl.Phys.Proc.Suppl., '),
            (re.compile('Advances in Theoretical and Mathematical Physics'), 'Adv.Theor.Math.Phys.'),
            (re.compile('Physics Letters, Section A: General, Atomic and Solid State Physics, '), 'Phys.Lett., A'),
            (re.compile('Nuclear Instruments and Methods in Physics Research Section A, '), 'Nucl.Instrum.Meth., A'),
            (re.compile('Nuclear Instruments and Methods in Physics Research Section B, '), 'Nucl.Instrum.Meth., B'),
            (re.compile('Nuclear Instruments and Methods in Physics Research Section A: Accelerators, Spectrometers, Detectors and Associated Equipment,? '), 'Nucl.Instrum.Meth., A'),
            (re.compile('^ARA&A '), 'Ann.Rev.Astron.Astrophys. '),
            (re.compile('^A\&A '), 'Astron.Astrophys. '),
            (re.compile('^A\&AS '), 'Astron.Astrophys.Suppl.Ser. '),
            (re.compile('^CSE (\d)'), r'Comput.Sci.Eng. \1'),
            (re.compile('^SoPh (\d)'), r'Solar Phys. \1'),
            (re.compile('^PhRvD (\d)'), r'Phys.Rev.D \1'),
            (re.compile('^PhRvL (\d)'), r'Phys.Rev.Lett. \1'),
            (re.compile('^PhLB (\d)'), r'Phys.Lett.B \1'),
            (re.compile('^NatMe (\d)'), r'Nature Meth. \1'),
            (re.compile('^NatAs (\d)'), r'Nature Astron. \1'),
            (re.compile('^AN (\d)'), r'Astron.Nachr. \1'),
            (re.compile('J. Phys.: Conf. Ser.'), r'J.Phys.Conf.Ser.'),
            (re.compile('J. Phys. A: Math. Theor.'), r'J.Phys.A'),
            (re.compile('^SCPMA '), 'Sci.China Phys.Mech.Astron. '),
            (re.compile(', pp. '), ', '),
            (re.compile(u'[\u201d\u201c]'), '"'),
            (re.compile(u'[\u2010\u2011\u2012\u2013\u2014\u2015]'), '-'),
            (re.compile(u'[\u2018\u2019]'), "'"),
            (re.compile(', [Nn]o. [0-9\-]+,? '), ', ')]
def cleanpubnote(lit):
    if type(lit) == type([]):
        lit = lit[0]
    for (regexp, replacement) in reclpbns:
        lit = regexp.sub(replacement, lit)
    return lit

###clean formulas in tag
recleandash = re.compile(u'[\u2010\u2011\u2012\u2013\u2014\u2015]')
recleansquot = re.compile(u'[\u2018\u2019]')
recleandquot = re.compile(u'[\u201d\u201c]')
recleandollar = re.compile('\$\$')
recleanbreak = re.compile('[\n\t\r]')
recleanspace = re.compile('  +')
recleanlatex = re.compile('.*begin.document..(.*)..end.document.*')
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
                tmt = recleanspace.sub(' ', recleanbreak.sub('', tm.text.strip()))
                tmt = recleanlatex.sub(r'\1', tmt)
                inlineformula.replace_with(tmt)
        else:
            tryprint('DECOMPOSE' + str(inlineformula))
            inlineformula.decompose()
    #insert spaces between tags befor textifying it
    for child in tag.find_all():
        children = child.find_all()
        if len(children) == 0:
            content = child.text
            child.replace_with(content + ' ')
    for child in tag.find_all():
        children = child.find_all()
        if len(children) == 0:
            content = child.text
            child.replace_with(content + ',')
    output = recleanspace.sub(' ', recleanbreak.sub(' ', tag.text.strip()))
    output = recleansquot.sub("'", recleandquot.sub('"', output))
    #unite subsequent LaTeX formulas
    output = recleandash.sub('-', recleandollar.sub('', output))
    return output

#extract JATS-references
#expects BeautifulSoup-object, checks by default <element-citation>'s
rehdl = re.compile('.*hdl.handle.net/(\d.*\/.*)')
redoi = re.compile('.*doi.org/(10\.\d+\/.*)')
rebadhdl = re.compile('123456789')
resqrbrckt = re.compile('\[')
repdf = re.compile('\.pdf$')
rearxivold = re.compile('ar[xX]iv\:[a-z\-]+\/\d')
rearxivnew = re.compile('^\d{4}.\d{4}')
rearxivhttp = re.compile('https?:.*arxiv.org\/[ap]..\/')
rearxivversion = re.compile('v\d+$')
rearxivdoi = re.compile('.*10.48550/arXiv.(\d{4}\.\d+).*')
rearxivrepo = re.compile(' \[[a-z].*')
reinspirehepold = re.compile('inspirehep.net.*IRN')
reinspirehepnew = re.compile('inspirehep.net.*recid')
renumber = re.compile('.*\D')
reisbn = re.compile('\-')
rehttp = re.compile('http')
def jatsreferences(soup, citationtag='element-citation'):
    refs =  []
    srefs = soup.find_all('ref')
    statistik = {'goodrefs' : {'sum' : 0}, 'badrefs' : {'sum' : 0}, 'dois' : 0, 'hdls' : 0, 'arxivs' : 0, 'recids' : 0}
    for ref in srefs:
        for mc in ref.find_all(citationtag):
            (btitle, bpbn, year, title, publishername) = ('', '', '', '', '')
            #check type of reference
            if mc.has_attr('publication-type'):
                publicationtype = mc['publication-type']
            else:
                publicationtype = ''
            tryprint( '\n  (mc|' + publicationtype + ')  '+str(mc))
            #check label
            (lt, refno) = ('', '')
            for label in ref.find_all('label'):
                lt = label.text.strip()
                lt = re.sub('\W', '', lt)
                if resqrbrckt.search(lt):
                    refno = '%s ' % (lt)
                else:
                    refno = '[%s] ' % (lt)
                label.decompose() 
            #title
            for at in mc.find_all('article-title'):
                title = cleanformulas(at)
                at.decompose()
            #authors/editors
            (authors, editors) = ([], [])
            for pg in mc.find_all('person-group'):
                for nametag in mc.find_all('name'):
                    name = ''
                    for gn in nametag.find_all('given-names'):
                        name = gn.text.strip()
                        if len(name) == 1: name += '.'
                    for sn in nametag.find_all('surname'):
                        name += ' ' + sn.text.strip()
                    if pg.has_attr('person-group-type'):
                        if pg['person-group-type'] == 'author':
                            authors.append(name)
                        elif pg['person-group-type'] == 'editor':
                            editors.append(name)
                    else:
                        authors.append(name)
                pg.decompose()
            #DOI/arXiv/HDL/link
            (doi, arxiv, link, hdl, recid) = ('', '', '', '', '')
            (journal, volume, page) = ('', '', '')
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'doi'}):
                doi = pi.text.strip()
                pi.replace_with(', DOI: %s' % (doi))
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'arxiv'}):
                arxiv = pi.text.strip()
                pi.replace_with(', arXiv: %s' % (arxiv))
            for el in mc.find_all('ext-link', attrs = {'ext-link-type' : 'arxiv'}):
                link = el['xlink:href']     
                if rearxivdoi.search(link):
                    arxiv = rearxivdoi.sub(r'arxiv:\1', link)
                    el.replace_with(', arXiv: %s' % (arxiv))
                elif redoi.search(link):
                    doi = redoi.sub(r'\1', link)
                    el.replace_with(', ' + link)
                else:
                    arxiv = rearxivversion.sub('', el.text.strip())
                    el.replace_with(', arXiv: %s' % (arxiv))
            for el in mc.find_all('ext-link', attrs = {'ext-link-type' : ['url', 'uri', 'simple', 'http', 'https']}):
                if el.has_attr('xlink:href'):
                    link = el['xlink:href']                    
                    if rehdl.search(link):
                        if not rebadhdl.search(link):
                            hdl = rehdl.sub(r'\1', link)
                            el.replace_with(', ' + link)
                    elif redoi.search(link):
                        doi = redoi.sub(r'\1', link)
                        el.replace_with(', ' + link)
                    elif re.search('arxiv.org', link) and not re.search('submit', link):
                        arxiv = rearxivversion.sub('', link)
                        el.replace_with(', ' + link)
                    elif reinspirehepold.search(link):
                        irn = renumber.sub('', link)
                    elif reinspirehepnew.search(link):
                        recid = renumber.sub('', link)
                        inspirelink = ', https://old.inspirehep.net/record/%s' % (recid)
                        el.decompose()
                    elif re.search('inspirehep.net', link):
                        el.decompose()
            for el in mc.find_all('ext-link', attrs = {'ext-link-type' : 'doi'}):
                if el.has_attr('xlink:href'):
                    link = el['xlink:href']
                    if re.search('arxiv.org', link):
                        arxiv = rearxivversion.sub('', link)
                        el.replace_with(', ' + link)
                    if redoi.search(link):
                        doi = redoi.sub(r'\1', link)
                        el.replace_with(', ' + link)
            #pubnote
            (isbn, pbn, cpbn) = ('', '', '')
            potentialpbndecompose = []
            pubness = 0
            for i in mc.find_all('isbn'):
                isbn = reisbn.sub('', i.text.strip())
                i.replace_with(', ISBN: %s' % (isbn))
            for source in mc.find_all('source'):
                jnl = source.text.strip()
                pbn = jnl
                pubness += 1
                potentialpbndecompose.append(source)
            for vol in mc.find_all('volume'):
                volume = vol.text.strip()
                pbn += ' ' + volume
                pubness += 1
                potentialpbndecompose.append(vol)
            for issue in mc.find_all('issue'):
                pbn += ', No. ' + issue.text.strip()
                potentialpbndecompose.append(issue)
            for y in mc.find_all('year'):
                year = y.text.strip()
                pbn += ' (%s) ' % (year)
                potentialpbndecompose.append(y)
            fps = mc.find_all('fpage')
            if fps:
                for fpage in fps:
                    page = fpage.text.strip()
                    pubness += 1
                    pbn += ' ' + page
                    for lpage in mc.find_all('lpage'):
                        pbn += '-' + lpage.text.strip()
                        potentialpbndecompose.append(lpage)
                    potentialpbndecompose.append(fpage)
            else:
                artnums = mc.find_all('artnum')
                if artnums:
                    for artnum in artnums:
                        page = artnum.text.strip()
                        pubness += 1
                        pbn += ' ' + artnum.text.strip()
                        potentialpbndecompose.append(artnum)
                else:
                    artnums = mc.find_all('elocation-id')
                    for artnum in artnums:
                        page = artnum.text.strip()
                        pubness += 1
                        pbn += ' ' + page
                        potentialpbndecompose.append(artnum)
                if not artnums:
                    artnums = mc.find_all('pub-id', attrs = {'pub-id-type' : 'publisher-id'})
                    for artnum in artnums:
                        page = artnum.text.strip()
                        pubness += 1
                        pbn += ' ' + page
                        potentialpbndecompose.append(artnum)                    
            tryprint('  (pbn)   '+ pbn)
            if pubness > 1:
                pbn = cleanpubnote(pbn)
                tryprint( '  (clpbn) '+ pbn)
                repbn = extract_references_from_string(pbn, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}")
                if 'journal_reference' in repbn[0].keys():
                    if 'Physics' in repbn[0]['journal_title']:
                        pbn = ''
                    else:
                        pbn = repbn[0]['journal_reference'][0]
                        tryprint('  (rpbn)  '+ pbn)
                        for tag in potentialpbndecompose: tag.decompose()
                else:
                    tryprint('  (pbn!)  '+ pbn + '  http://doi.org/'+doi)
                    if pubness < 3:
                        pbn = ''
                    elif publicationtype in ['journal']:
                        pbn = '%s,%s,%s' % (jnl,volume,page)
                        for tag in potentialpbndecompose: tag.decompose()
            else:
                pbn = ''
            #missing spaces?
            for bold in mc.find_all('bold'):
                bt = bold.text.strip()
                bold.replace_with(' %s ' % (bt))
            #recombine everything
            reference = []
            if publicationtype in ['journal', 'preprint']:
                if pbn:
                    if title:
                        if doi:
                            reference = [('x', refno + '%s, "%s", %s, DOI: %s' % (', '.join(authors[:4]), title, pbn, doi))]
                        else:
                            reference = [('x', refno + '%s, "%s", %s' % (', '.join(authors[:4]), title, pbn))]
                    else:
                        if doi:
                            reference = [('x', refno + '%s, %s, DOI: %s' % (', '.join(authors[:4]), pbn, doi))]
                        else:
                            reference = [('x', refno + '%s, %s' % (', '.join(authors[:4]), pbn))]
            elif publicationtype in ['confproc', 'book', 'thesis', 'conf']:
                if publicationtype == 'thesis':
                    prefix = 'Thesis: '
                else:
                    prefix = ''
                #book title
                for source in mc.find_all('source'):
                    btitle = cleanformulas(source)
                    source.decompose()
                for source in mc.find_all('conf-name'):
                    btitle += ' '+cleanformulas(source)
                    source.decompose()
                #book pubnote
                for pn in mc.find_all('publisher-name'):
                    publishername = pn.text.strip()
                    bpbn = publishername + ', '
                    pn.decompose()
                for publisherloc in mc.find_all('publisher-loc'):
                    bpbn += publisherloc.text.strip() + ', '
                    publisherloc.decompose()
                for institution in mc.find_all('institution'):
                    bpbn += institution.text.strip() + ', '
                    institution.decompose()
                if year:
                    bpbn += year
                #pubnote
                if not pbn:
                    for fpage in mc.find_all('fpage'):
                        cpbn = ' ' + fpage.text.strip()
                        if title:
                            fpage.decompose()
                    for lpage in mc.find_all('lpage'):
                        cpbn += '-' + lpage.text.strip()
                        if title:
                            lpage.decompose()
                else:
                    cpbn = pbn
                tryprint('    btitle:%s | title:%s |bpbn:%s | cpbn:%s' % (btitle, title, bpbn, cpbn))
                #all together
                if title:
                    reference = [('x', refno + '%s%s: %s, pages %s in: %s: %s, %s,   %s' % (prefix, ', '.join(authors), title, cpbn, ', '.join(editors), btitle, bpbn, cleanformulas(mc)))]
                elif btitle:
                    reference = [('x', refno + '%s%s: %s, %s,   %s' % (prefix, ', '.join(authors), btitle, bpbn, cleanformulas(mc)))]
            elif publicationtype in ['web', 'gov']:
                webref = ''
                for comment in mc.find_all('comment'):
                    if rehttp.search(comment.text):
                        link = comment.text
                        comment.decompose()
                if link:
                    reference = [('x', refno + '%s: %s, %s,   %s' % (', '.join(authors), title, year, cleanformulas(mc)))]
            elif publicationtype in ['commun']:
                reference = [('x', refno + '%s: %s, %s,   %s' % (', '.join(authors), title, year, cleanformulas(mc)))]
            tryprint( '  (rawreference) '+str(reference))
            #add other stuff
            #good reference
            if reference:
                bad = False
                statistik['goodrefs']['sum'] += 1
                if publicationtype in statistik['goodrefs']:
                    statistik['goodrefs'][publicationtype] += 1
                else:
                    statistik['goodrefs'][publicationtype] = 1
                for author in authors:
                    reference.append(('h', author))
                for editor in editors:
                    reference.append(('e', editor))
                if isbn:
                    reference.append(('i', isbn))
                if lt:
                    reference.append(('o', lt))
                if title:
                    reference.append(('t', title))
                    if btitle and (btitle != title):
                        reference.append(('q', btitle))
                elif btitle:
                    reference.append(('t', btitle))
                if pbn:
                    reference.append(('s', pbn))
                if link:
                    reference.append(('u', link))
                if year:
                    reference.append(('y', year))
                if publishername:
                    reference.append(('p', publishername))
            #bad reference
            else:
                bad = True
                statistik['badrefs']['sum'] += 1
                if publicationtype in statistik['badrefs']:
                    statistik['badrefs'][publicationtype] += 1
                else:
                    statistik['badrefs'][publicationtype] = 1
                if authors:
                    rawref = refno + '%s: %s' % (', '.join(authors), title)
                else:
                    rawref = refno + title
                if pbn:
                    rawref += ', %s' % (pbn)
                if year:
                    rawref += ', %s' % (year)
                reference = [('x', '%s,   %s' % (rawref, cleanformulas(mc)))]
            #add persistent identifiers in any case
            if doi:
                reference.append(('a', 'doi:'+doi))
                statistik['dois'] += 1
            if hdl:
                reference.append(('a', 'hdl:'+hdl))
                statistik['hdls'] += 1
            if arxiv:
                arxiv = rearxivrepo.sub('', arxiv)
                reference.append(('r', arxiv))
                statistik['arxivs'] += 1
            if recid:
                reference.append(('0', str(recid)))
                statistik['recids'] += 1
            refs.append(reference)
            if bad and not doi+hdl+arxiv+recid:
                tryprint('  (bad|%s) %s' % (publicationtype, str(reference)) )
    #reporting
    statistikgoodrefs = '|'.join('%s:%i' % (pt, statistik['goodrefs'][pt]) for pt in statistik['goodrefs'])
    statistikbadrefs = '|'.join('%s:%i' % (pt, statistik['badrefs'][pt]) for pt in statistik['badrefs'])
    pidreport = 'dois:%i, hdls:%i, arxivs:%i, recids:%i' % (statistik['dois'], statistik['hdls'], statistik['arxivs'], statistik['recids'])
    statistikline = '[jatsreferences] %i/%i: good=%i (%s), bad=%i (%s) | %s' % (len(refs), len(srefs), statistik['goodrefs']['sum'], statistikgoodrefs, statistik['badrefs']['sum'], statistikbadrefs, pidreport)
    if verbose: print statistikline
    return(refs)




