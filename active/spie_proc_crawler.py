# -*- coding: utf-8 -*-
#program to harvest SPIE Proceedings
# FS 2017-08-27

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

def spie(volume):
    jnlname = 'Proc.SPIE Int.Soc.Opt.Eng.'
    #jnlname = 'Proc.SPIE'
    urltrunc = "https://www.spiedigitallibrary.org"
    toclink = "%s/conference-proceedings-of-spie/%s.toc" % (urltrunc, volume)
    print 'open %s' % (toclink)
    page = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink), features="lxml")
    for text in page.body.find_all('text', attrs = {'class' : 'ProceedingsArticleVolTitleText'}):
        conftitle = text.text.strip()
    (section, articletype) = ('', '')
    recs = []
    for div in page.body.find_all('div'):
        if div.attrs.has_key('class'):
            if 'TOCLineItemSectionHeaderDiv' in div['class']:
                section = div.text.strip()
            elif 'articleType' in div['class']:
                articletype = div.find('a').string
            elif 'TOCLineItemRow1' in div['class'] and not re.search('^Front Matter', section):
                media = []
                for img in div.find_all('img'):
                    if img.has_attr('alt'):
                        media = re.split(' \+ ', img['alt'])
                if 'Paper' in media:
                    rec = {'keyw' : [], 'note' : [section, articletype], 'jnl' : jnlname, 'vol' : volume, 
                           'tc' : 'C', 'autaff' : [], 'refs' : []}
                    for a in div.find_all('a', attrs = {'class' : 'TocLineItemAnchorText1'}):
                        rec['artlink'] = '%s%s' % (urltrunc, a['href'])
                        rec['tit'] = a.text.strip()
                        if not rec['artlink'] in [r['artlink'] for r in recs]:
                            if not rec['artlink'] in ['https://www.spiedigitallibrary.org/conference-proceedings-of-spie/11364/113640I/High-speed-electronics-for-silicon-photonics-transceivers/10.1117/12.2558467.full',
                                                      'https://www.spiedigitallibrary.org/conference-proceedings-of-spie/11455/114556D/Photonic-generation-of-phase-coded-chirp-microwave-waveform-by-an/10.1117/12.2565263.full']:
                                recs.append(rec)
                else:
                    print '  skip', media        
    #get detailed article pages
    i = 0
    for rec in recs:
        i += 1
        print '  get [%i/%i] %s' % (i, len(recs), rec['artlink'])
        try:
            time.sleep(20)
            articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=400), features="lxml")
        except:
            print 'retry %s in 5 minutes' % (rec['artlink'])
            time.sleep(300)
            articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=400), features="lxml")
        for meta in articlepage.head.find_all('meta'):
            if meta.has_attr('name'):
                if meta['name'] == 'citation_author':
                    rec['articlepage'] = articlepage
                    print '    found proper articlepage'
                    break
    #get detailed informations from article pages
    i = 0
    for rec in recs:
        i += 1
        if rec.has_key('articlepage'):
            print '  open [%i/%i] %s' % (i, len(recs), 'use article page in cache')
            articlepage = rec['articlepage']
        else:
            print '  open [%i/%i] %s' % (i, len(recs), rec['artlink'])
            try:
                time.sleep(20)
                articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=400))
            except:
                print 'retry %s in 5 minutes' % (rec['artlink'])
                time.sleep(300)
                articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=400))
        autaff = []
        for meta in articlepage.head.find_all('meta'):
            if meta.has_attr('name'):
                if 'citation_firstpage' in meta['name']:
                    rec['p1'] = meta['content']
                elif 'citation_lastpage' in meta['name']:
                    rec['pages'] = re.sub('.*\-','',meta['content'])
                elif 'citation_doi' in meta['name']:
                    rec['doi'] = meta['content']
                elif 'citation_abstract' in meta['name']:
                    rec['abs'] = meta['content']
                elif 'citation_keyword' in meta['name']:
                    for keyw in re.split('; ', meta['content']):
                        if keyw: rec['keyw'].append(keyw)
                elif 'citation_publication_date' in meta['name']:
                    rec['date'] = meta['content']
                    rec['year'] = rec['date'][:4]
                elif 'pdf' in meta['name']:
                    for OA in articlepage.body.find_all('img', attrs = {'src' : "/Content/themes/SPIEImages/OpenAccessIcon.png"}):
                        rec['FFT'] = meta['content']
                elif meta['name'] == 'citation_author':
                    if autaff:
                        rec['autaff'].append(autaff)
                    autaff = [ meta['content'] ]
                elif meta['name'] == 'citation_author_institution':
                    autaff.append(meta['content'])
                elif meta['name'] == 'citation_author_orcid':
                    orcid = re.sub('.*\/', '', meta['content'])
                    autaff.append('ORCID:%s' % (orcid))
                elif meta['name'] == 'citation_author_email':
                    email = meta['content']
                    autaff.append('EMAIL:%s' % (email))   
        rec['autaff'].append(autaff)
        #presentation only
        for tag in articlepage.body.find_all('text', attrs = {'class' : 'ProceedingsArticleSmallFont'}):
            rec['note'].append(tag.text.strip())
        #number of pages
        for div in articlepage.body.find_all('text', attrs = {'class' : 'ProceedingsArticleSmallFont'}):
            pages = re.split(' *', div.text.strip())
            if len(pages) == 2 and pages[1] in ['pages', 'PAGES']:
                rec['pages'] = pages[0]
        #references
        for div in articlepage.body.find_all('div', attrs = {'class' : 'section ref-list'}):
            for div2 in div.find_all('div'):
                if div2.has_attr('class'):
                    if 'ref-content' in div2['class']:
                        rdoi = False
                        for a in div2.find_all('a'):
                            if a.has_attr('href') and re.search('doi.org.10', a['href']):
                                rdoi = re.sub('.*?(10\.\d+.*)', r'\1', a['href'])
                            a.replace_with('')
                        ref = div2.text.strip()
                        if reflabel:
                            ref = '[%s] %s' % (reflabel, ref)
                            rec['refs'].append([('x', ref)])
                        if rdoi:
                            ref = re.sub('\.? *$', ', DOI: %s' % (rdoi), ref)
                            rec['refs'].append([('x', ref), ('a', 'doi:%s' % (rdoi))])
                        reflabel = False
                    elif 'ref-label' in div2['class']:
                        reflabel = re.sub('.*?(\d+).*', r'\1', div2.text.strip())
        ###
        if rec['doi'] == '10.1117/12.2536012':
            rec['autaff'] = [['Schaefer, H.']]
        if not rec['autaff'][0]:
            rec['autaff'] = [['NONE']]
        if len(args) > 1:
            rec['cnum'] = args[1]
            if len(args) > 2:
                rec['fc'] = args[2]
        try:
            del rec['articlepage']
        except:
            pass
        if rec.has_key('year'):
            print '  %s %s (%s) %s' % (jnlname,volume,rec['year'],rec['p1'])
        else:
            print '=== PROBLEM WITH RECORD ==='
            print rec
            print '==========================='
            
    return recs

if __name__ == '__main__':
    usage = """
        python spie_proc_crawler.py volume [cnum] [fc]
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        if len(args) > 3:
            raise getopt.GetoptError("Too many arguments given!!!")
        elif not args:
            raise getopt.GetoptError("Missing mandatory argument volume")
    except getopt.GetoptError as err:
        print(str(err))  # will print something like "option -a not recognized"
        print(usage)
        sys.exit(2)
    volume = args[0]
    publisher = 'International Society for Optics and Photonics'
    recs = spie(volume)
    if len(args) > 1:
        cnum = args[1]
        if len(args) > 2: fc = args[2]
        outfile = 'spie%s_%s.xml' % (volume, cnum)
    else:
        outfile = 'spie%s.xml' % (volume)
    dokf = codecs.EncodedFile(open(os.path.join(xmldir,outfile),mode='wb'),"utf8")
    #dokf = open(os.path.join(xmldir,outfile),'w')
    ejlmod2.writenewXML(recs,dokf,publisher, outfile[:-4])
    dokf.close()
    #retrival
    retfiles_text = open(retfiles_path,"r").read()
    line = outfile+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
