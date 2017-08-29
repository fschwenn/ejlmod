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




def spie(volume):
    jnlname = 'Proc.SPIE Int.Soc.Opt.Eng.'
    #jnlname = 'Proc.SPIE'
    urltrunc = "https://www.spiedigitallibrary.org"
    toclink = "%s/conference-proceedings-of-spie/%s.toc" % (urltrunc, volume)
    print 'open %s' % (toclink)
    page = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
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
                rec = {'keyw' : [], 'note' : [section, articletype], 'jnl' : jnlname, 'vol' : volume, 
                       'tc' : 'C', 'autaff' : [], 'refs' : []}
                for a in div.find_all('a', attrs = {'class' : 'TocLineItemAnchorText1'}):
                    rec['artlink'] = '%s%s' % (urltrunc, a['href'])
                    rec['tit'] = a.text.strip()
                    recs.append(rec)
    #get detailed informations from article pages
    i = 0
    for rec in recs:
        i += 1
        print '  open [%i/%i] %s' % (i, len(recs), rec['artlink'])
        try:
            time.sleep(20)
            articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=300))
        except:
            print 'retry %s in 5 minutes' % (urltrunc +link)
            time.sleep(300)
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
        #number of pages
        for div in articlepage.body.find_all('text', attrs = {'class' : 'ProceedingsArticleSmallFont'}):
            pages = re.split(' *', div.text.strip())
            if len(pages) == 2 and pages[1] in ['pages', 'PAGES']:
                rec['pages'] = pages[0]
        if len(args) > 1:
            rec['cnum'] = args[1]
        if rec.has_key('year'):
            print '  %s %s (%s) %s, %s' % (jnlname,volume,rec['year'],rec['p1'],rec['tit'])
        else:
            print '=== PROBLEM WITH RECORD ==='
            print rec
            print '==========================='
    return recs




if __name__ == '__main__':
    usage = """
        python spie_proc_crawler.py volume [cnum]
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        if len(args) > 2:
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
        outfile = 'spie%s_%s.xml' % (volume, cnum)
    else:
        outfile = 'spie%s.xml' % (volume)
    #dokf = codecs.EncodedFile(open(os.path.join(xmldir,outfile),mode='wb'),"utf8")
    dokf = open(os.path.join(xmldir,outfile),'w')
    ejlmod2.writeXML(recs,dokf,publisher)
    dokf.close()
    #retrival
    retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
    retfiles_text = open(retfiles_path,"r").read()
    line = outfile+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
