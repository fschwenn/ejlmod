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


ejdir = '/afs/desy.de/user/l/library/dok/ejl'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
#xmldir = '/afs/desy.de/user/s/schwenn/inspire/ejl'




def spie(jnl, vol, iss):
    if jnl == 'jatis':
        jnlname = 'J.Astron.Telesc.Instrum.Syst.'
        jnlspiename = 'Journal-of-Astronomical-Telescopes-Instruments-and-Systems'
    else:
        print 'unknown journal "%s"' % (jnl)
    urltrunc = "https://www.spiedigitallibrary.org"
    toclink = "%s/journals/%s/volume-%s/issue-%02i" % (urltrunc, jnlspiename, vol, int(iss))
    print 'open %s' % (toclink)
    page = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
    (section, articletype) = ('', '')
    recs = []
    for div in page.body.find_all('div'):
        if div.attrs.has_key('class'):
            if 'TOCLineItemSectionHeaderDiv' in div['class']:
                section = div.text.strip()
            elif 'articleType' in div['class']:
                articletype = div.find('a').string
            elif 'TOCLineItemRow1' in div['class'] and not re.search('^Front Matter', section):
                rec = {'keyw' : [], 'note' : [section, articletype], 'jnl' : jnlname, 'vol' : vol, 'issue' : iss, 
                       'tc' : 'P', 'autaff' : [], 'refs' : []}
                for a in div.find_all('a', attrs = {'class' : 'TocLineItemAnchorText1'}):
                    rec['artlink'] = '%s%s' % (urltrunc, a['href'])
                    rec['tit'] = a.text.strip()
                    if re.search('List of Reviewers', rec['tit']):
                        continue
                    if not rec['artlink'] in [r['artlink'] for r in recs]:
                        recs.append(rec)
    #get detailed article pages
    i = 0
    for rec in recs:
        i += 1
        print '  get [%i/%i] %s' % (i, len(recs), rec['artlink'])
        try:
            time.sleep(20)
            articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=400))
        except:
            print 'retry %s in 5 minutes' % (rec['artlink'])
            time.sleep(300)
            articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=400))
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
                    rec['autaff'].append([ meta['content'] ])
                elif meta['name'] == 'citation_author_institution':
                    rec['autaff'][-1].append(meta['content'])
                elif meta['name'] == 'citation_author_orcid':
                    orcid = re.sub('.*\/', '', meta['content'])
                    rec['autaff'][-1].append('ORCID:%s' % (orcid))
                elif meta['name'] == 'citation_author_email':
                    email = meta['content']
                    rec['autaff'][-1].append('EMAIL:%s' % (email))   
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
            reflabel = False
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
#                    elif 'ref-label' in div2['class']:
#                        reflabel = re.sub('.*?(\d+).*', r'\1', div2.text.strip())
        try:
            del rec['articlepage']
        except:
            pass
        if rec.has_key('year'):
            #print '  %s %s.%s (%s) %s, %s' % (jnlname,vol, iss, rec['year'],rec['p1'],rec['tit'])
            print '  %s %s.%s (%s) %s' % (jnlname,vol, iss, rec['year'],rec['p1'])
        else:
            print '=== PROBLEM WITH RECORD ==='
            print rec
            print '==========================='
    return recs




if __name__ == '__main__':
    usage = """
        python spie_journal.py journal volume issue
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
    jnl = args[0]
    vol = args[1]
    iss = args[2]
    publisher = 'International Society for Optics and Photonics'
    recs = spie(jnl, vol, iss)
    outfile = 'spie_%s%s.%s.xml' % (jnl, vol, iss)
    #dokf = codecs.EncodedFile(open(os.path.join(xmldir,outfile),mode='wb'),"utf8")
    dokf = open(os.path.join(xmldir,outfile),'w')
    ejlmod2.writenewXML(recs,dokf,publisher, outfile[:-4])
    dokf.close()
    #retrival
    retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
    retfiles_text = open(retfiles_path,"r").read()
    line = outfile+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
