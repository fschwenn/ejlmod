#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import os
import sys
import getopt
import codecs
import urllib
from invenio.bibrecord import *
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_record
#from invenio.bibcheck_task import AmendableRecord
from invenio.bibrecord  import record_add_field
from clean_fulltext import clean_fulltext_jacow, clean_fulltext_moriond, clean_linebreaks, get_reference_section

##from correct_utf8 import check_record

## http://invenio-software.org/code-browser/invenio.bibrecord-module.html

tmppath = '/tmp/jacow/'
publisherdatapath = '/afs/desy.de/group/library/publisherdata/jacow/'
ejl = '/afs/desy.de/user/l/library/inspire/ejl/'
#ejl = '/afs/desy.de/user/s/sachs/inspire/jacow/'
#publisherdatapath = '/afs/desy.de/user/s/sachs/inspire/jacow/in/'
TRANSLATE ={"&uuml;":u"ü", "&auml;":u"ä", "&ouml;":u"ö", "&Auml;":u"Ä", 
    "&Ouml;":u"Ö", "&Uuml;":u"Ü", "&szlig;":u"ß", "&thinsp;":u" "}

re_number = re.compile(r'^\[(\d+)\]')
def by_number(a,b):
    '''
    sort references by number
    works only if one reference per line
    '''
    number_a = re_number.search(a)
    number_b = re_number.search(b)
    if number_a and number_b:
        return cmp(int(number_a.group(1)), int(number_b.group(1)))
    else:
        return 0


def get_references(url, clean='jacow'):
    from refextract import extract_references_from_string
    filename = url.split('/')[-1]
    if os.path.isfile('%s/%s_clean.txt' % (tmppath, filename[:-4])):
        controlfile = codecs.EncodedFile(codecs.open('%s/%s_clean.txt' % (tmppath, filename[:-4])),'utf8')
        fulltext = controlfile.read()
        controlfile.close()      
    else:
        if not os.path.isfile('%s/%s.txt' % (tmppath, filename[:-4])):
            if not os.path.isfile('%s/%s' % (tmppath, filename)):
                os.system('wget -q -O %s%s %s' % (tmppath, filename, url))
            os.system('/usr/bin/pdftotext %s%s' % (tmppath, filename))
    
        infile = codecs.EncodedFile(codecs.open('%s/%s.txt' % (tmppath, filename[:-4])),'utf8')
        fulltext = infile.readlines()
        if clean == 'jacow':
            fulltext = clean_fulltext_jacow(fulltext, verbose=1)
        elif clean == 'moriond':
            fulltext = clean_fulltext_moriond(fulltext)
        elif clean == 'linebreaks':
            fulltext = '\n'.join(fulltext)+'\n'
            fulltext = clean_linebreaks(fulltext)
        else:
            fulltext = '\n'.join(fulltext)+'\n'
        fulltext = get_reference_section(fulltext)
        infile.close()

        if '[2]' in fulltext:
            lines = fulltext.split('\n')
            lines.sort(cmp=by_number)
            fulltext = '\n'.join(lines)
            last_number = 0
            errors = ''
            for line in lines:
                number = re_number.search(line)
                if number:
                    this_number = int(number.group(1))
                    if not this_number - last_number == 1:
                        errors += '%s: [%s] followed by [%s]\n' % (filename[:-4], last_number, this_number)
                    last_number = this_number
                elif last_number:
                    errors += '%s: No number for %s\n' % (filename[:-4], line[:30])
            if errors:
                reflog_file = open('%s/%s.log' % (publisherdatapath, filename[:-4]), mode='wb')
                reflog_file.write(errors)
                reflog_file.close()

        controlfile = codecs.EncodedFile(codecs.open('%s/%s_clean.txt' % (tmppath, filename[:-4]), mode='wb'),'utf8')
        controlfile.write(fulltext)
        controlfile.close()      
    
    refs = extract_references_from_string(fulltext, is_only_references=False, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}")
    references = []
    
    #mappings for references in JSON to MARC
    mappings = {'doi': 'a',
                'collaborations': 'c',
                'document_type': 'd',
                'author': 'h',
                'isbn': 'i',
                'texkey': 'k',
                'misc': 'm',
                'journal_issue': 'n',
                'label': 'o',
                'linemarker': 'o',
                'reportnumber': 'r',
                'journal_reference': 's',
                'title': 't',
                'urls': 'u',
                'url': 'u',
                'raw_ref': 'x',
#                'journal_title': None,
#                'journal_volume': None,
#                'journal_page': None,
#                'journal_year': None,
#                'publisher': None,
                'year': 'y'}
    
    for ref in refs:
        entryaslist = [('9','refextract')]
        for key in ref.keys():
            if key in mappings:
                for entry in ref[key]:
                     entryaslist.append((mappings[key], entry))
#            else:
#                print 'no mapping for', key
        references.append(entryaslist)
    return references
    
def convertToInspire(argv):
    re_non_char = re.compile(r"[^\w',. -]", re.UNICODE)
    conf = ''
    cnum = ''
    first = True
    badcounter = 0

#    badpdf = ["MOPMB019" ,"MOPOW005" ,"MOPOY003" ,"MOPOY023" ,"MOPOY051" ,"TUPMR019" ,"TUPMW012" ,"TUPMW013" ,"TUPMW028" ,"TUPMY002" ,"TUPMY026" ,"TUPOW051" ,"TUPOW052" ,"TUPOW055" ,"TUPOY002" ,"WEPMB006" ,"WEPMW007" ,"WEPMW030" ,"WEPMW032" ,"WEPMY035" ,"WEPOY019" ,"WEPOY037" ,"WEPOY040" ,"WEPOY046" ,"WEPOY060" ,"WEXA01" ,"WEZA01" ,"THPMB039" ,"THPMB053" ,"THPMB055" ,"THPMR018" ,"THPMR037" ,"THPOR003" ,"THPOR004" ,"THPOR007" ,"THPOW021"]
    badpdf = []

    try:
        opts, args = getopt.getopt(argv,"hc:i:",["cnum=","conf="])
    except getopt.GetoptError:
        print 'Usage: jacow.py -c <cnum> -i <conf>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: jacow.py -c <cnum> -i <conf>'
            sys.exit()
        elif opt in ("-c", "--cnum"):
            cnum = arg
        elif opt in ("-i", "--conf"):
            conf = arg

    if conf == '' or cnum == '':
        print 'Usage: jacow.py -c <cnum> -i <conf>'
        sys.exit(2)
        
    confpath = publisherdatapath+conf+'.xml'
    if not os.path.isfile(confpath):
        confpath = publisherdatapath+'inspire-'+conf+'.xml'
        if not os.path.isfile(confpath):
            print conf, 'xml does not exist'
            sys.exit(2)
        
    
    infile = codecs.EncodedFile(codecs.open(confpath,'r'),'utf8')
    xmlrecords = infile.read()
    for html, utf in TRANSLATE.items():
        xmlrecords = xmlrecords.replace(html, utf)
    xmlrecords = xmlrecords.replace('&','&amp;')
    records = create_records(xmlrecords,verbose=1)
    infile.close()
      
    outfile = codecs.EncodedFile(codecs.open(ejl+'jacow.'+conf+'.xml',mode='wb'),'utf8')
    outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n')
        
#    authorproblems = codecs.EncodedFile(codecs.open(publisherdatapath+conf+'_author_problems.txt',mode='wb'),'utf8')
#    authorsfile = codecs.EncodedFile(codecs.open(ejl+'jacow.'+conf+'_authors.txt',mode='wb'),'utf8')
#    incompleteAuthorsfile = codecs.EncodedFile(codecs.open(ejl+'jacow.'+conf+'_incomplete_authors.txt',mode='wb'),'utf8')
 
 
    nrec = 0
    info = {}
    for recordtuple in records:
        if recordtuple[1] == '0':
            print recordtuple[2]
            print 'error in record'
            continue
        
        record = recordtuple[0]
        if not record:
            print 'no record'
            print recordtuple
            continue
        
##        record = AmendableRecord(record)
##        # try to fix UTF8 problems
##        message = check_record(record, ['100__a', '700__a'])
##        if message:
##            print message
            
        nrec +=1
        
        if record_get_field_value(record, '245', ' ', ' ', 'a').startswith('Proceedings'):
            proceedings = True
        else:
            proceedings = False
        
        # clean 980
        m980 = record_delete_fields(record, '980')
        tag980 = ['HEP',]
        if proceedings:
            tag980.append('Proceedings')
            
        if m980:
            for j in range(0, len(m980)):
                for i in range(0, len(m980[j][0])):
                    if m980[j][0][i][0] == 'a':
                        tag = m980[j][0][i][1]
                        if not tag980.count(tag):
                            tag980.append(tag)
        for t in tag980:  
            record_add_field(record,'980',' ',' ','',[('a',t)])
    
        #check for field 856 with ind1 = 4
        m856 = record_delete_fields(record, '856')
        urls = []

        if m856:
            for j in range(0, len(m856)):
                if m856[j][1] == '4':
                    for i in range(0, len(m856[j][0])):
                        if m856[j][0][i][0] == 'u':
                            urls.append(m856[j][0][i][1])
#                    m856[j][0].append(('y', 'JACOW'))
        else:
            #try a different version, perhaps a typing error
            urls = record_get_field_values(record, '8564', ' ', ' ', 'u')
            if len(urls) > 0:
                print 'wrong MARC field 8564 - use anyhow'
                record_delete_fields(record, '8564')
        
        # check the first URLs
        
        if urls > 0:
            url = urls[0]
            if url[-4:].lower() == '.pdf':
                if nrec < 10:
                    url_type = urllib.urlopen(url).info().gettype()
                    if not url_type == 'application/pdf':
                        if first:
                            print 'switch to accelconf'  
                            first = False
                        url = url.replace("http://jacow.org/", "http://accelconf.web.cern.ch/AccelConf/") 
                        url_type = urllib.urlopen(url).info().gettype()
                        if not url_type == 'application/pdf':
                            print 'still doesnt work:', url
                            url = None
                if url:
                    record_add_field(record,'856','4',' ','',[('u', url),('y', 'JACOW')])
                    artid = url.split('/')[-1].split('.')[0]
                    if artid.upper() in badpdf:
                        print 'No FFT for',url
                    else:
                        record_add_field(record,'FFT',' ',' ','',[('a', url),('y', 'Fulltext'),('t', 'INSPIRE-PUBLIC')])
                        #add references
                        references = get_references(url)
                        for ref in references:
                            record_add_field(record, '999', ind1='C', ind2='5', subfields=ref)
                else:
                    record_add_field(record,'856','4',' ','',[('u', urls[0]),('y', 'JACOW')])            
               
            else:
                record_add_field(record,'856','4',' ','',[('u', urls[0]),('y', 'JACOW')])            
           
        
        else:
            print 'No URL found!'
            print record

# delete link if DOI
        if record.has_key('024'):
            record_delete_fields(record, '856')
        
#       correct isbn
        m = record_delete_fields(record, '020')
        if m:
            for j in range(0, len(m)):
                for i in range(0, len(m[j][0])):
                    if m[j][0][i][0] == 'a':
                        m[j][0][i] = ('a',m[j][0][i][1].replace('-',''))
            record_add_fields(record, '020', m)

#       correct licence
        licence_a = 'CC-BY-3.0'
        licence_u = 'http://creativecommons.org/licenses/by/3.0/'
        licence= record_delete_fields(record, '540')
        if licence:
            for field in licence[0][0]:
                if field[0] == 'a':
                    if field[1] != licence_a and field[1] != 'Open Access':
                        print 'Licence different:', field[1]
                if field[0] == 'z':
                    if field[1] != licence_z:
                        print 'Licence different:', field[1]
        record_add_field(record,'540',' ',' ','',[('a',licence_a),('u',licence_u)])            
       
        dates = record.get('260',[])
        year = None
        for num, field in enumerate(dates):
            for date in field[0]:
                if date[0] == "c":
                    year = date[1][:4]

        #replace the conference CNUM with the input value
        m773 = record_delete_fields(record, '773')
        article_id = ""
#        conf_acronym = ""
        conf_acronym = conf
        m773w = 0
        m773y = 0
        if m773:
            for j in range(0, len(m773)):
                for i in range(0, len(m773[j][0])):
                    if m773[j][0][i][0] == 'c':
                        article_id = m773[j][0][i][1]
                    elif m773[j][0][i][0] == 'q':
                        conf_acronym = m773[j][0][i][1]
                    elif m773[j][0][i][0] == 'y':
                        m773y = 1
                    elif m773[j][0][i][0] == 'w':
                        m773w = 1
                        m773[j][0][i] = ('w', cnum)
                if not m773w:
                    m773[j][0].append(('w', cnum))
                if year and not m773y:
                    m773[j][0].append(('y', year))
            record_add_fields(record, '773', m773)
        else:
            m773 = [('w',cnum),('c',year)]
            record_add_field(record,'773',' ',' ','', m773)

        # add pseudo DOIconf_acronym if there is none
        if not record.has_key('024'):
            if proceedings:
                if conf_acronym:
                    nodoi = 'jacow.%s.proc' % (conf_acronym)
                else:
                    nodoi = 'jacow.%s.proc' % (cnum)
            else:
                nodoi = 'jacow.%s.%s' % (conf_acronym, article_id)
            record_add_field(record,'024','7',' ','',[('a',nodoi),('2','NODOI')])
        
#        m980__a = record_get_field_values(record, '980', ' ', ' ', 'a')
#        record_delete_fields(record, '980')            
#        doctyp = 'PROCEEDINGS'
#        for t in m980__a:
#            if t == 'Conference' or t == 'ConferencePaper':
#                doctyp = 'ConferencePaper'
#        record_add_field(record,'980',' ',' ','',[('a',doctyp)])
#        record_add_field(record,'980',' ',' ','',[('a','HEP')])
# 
   
##        #get authors and write them into the authors file
##        authors = record_get_field_instances(record, '100')
##        authors += record_get_field_instances(record, '700')
##        
##        for i in range(0, len(authors)):
##            name=''; aff=''; rawaff=''; email=''; aid=''
##            for line in authors[i][0]:
##                if line[0] == 'a':
##                    name = line[1]
##                if line[0] == 'u':
##                    rawaff = line[1] 
##                if line[0] == 'v':
##                    aff = line[1]
##                if line[0] == 'm':
##                    email = line[1]
##                if line[0] == 'j':
##                    aid = line[1]
##            
##
##            if email or aid:
##                afile = authorsfile
##            else:
##                badcounter += 1
##                if badcounter < 10:
##                    print 'Author informations not complete!  Writing them to '+conf+'_incomplete_authors.txt.'
##                elif badcounter == 10:
##                    print 'More authors fail'
##                afile = incompleteAuthorsfile
##            if name:
##                afile.write('NAME='+name+';\n')
##            if aff:
##                afile.write('AFFILIATION='+aff+';\n')
##            if rawaff:
##                afile.write('ADDRESS='+rawaff+';\n')
##            if email:
##                afile.write('EMAIL='+email+';\n')
##            if aid:
##                afile.write('ID='+aid+';\n')
##            afile.write(';\n')

        # delete wrong aff and move adress to v
        for marc in ['100','700']:
        # delete email
###            record_delete_subfield(record, marc, 'm')
        # delete wrong aff and move adress to v
###            record_delete_subfield(record, marc, 'v')
        # delete JACoW aff 
        # delete empty fields
            record_delete_subfield(record, marc, 'u')
            m = record_delete_fields(record, marc)
            for j in range(0, len(m)):
                empty_fields = []
                for i in range(0, len(m[j][0])):
#                    if m[j][0][i][0] == 'u':
#                        m[j][0][i] = ('v',m[j][0][i][1])
                    if m[j][0][i][0] == 'm': # delete email if wrong syntax
                        if not '@' in m[j][0][i][1]:
                            if m[j][0][i][1]:
                                print 'Wrong email:', m[j][0][i][1]
                            m[j][0][i] = ('m','')
                    if not m[j][0][i][1]:
                        empty_fields.append(i)
                    if m[j][0][i][0] == 'a':
                        if m[j][0][i][1].count('"'):
                            m[j][0][i] = ('a',m[j][0][i][1].replace('"',''))
                        if m[j][0][i][1] == 'Schaa, Volker RW':
                            m[j][0][i] = ('a','Schaa, Volker R.W.')
                empty_fields.reverse()
                for i in empty_fields:
                    m[j][0].pop(i)
            record_add_fields(record, marc, m)
        
        outfile.write(record_xml_output(record))
        
        # basic check for dublets
        titles = record_get_field_values(record,'245',' ',' ','a')
        art_ids = record_get_field_values(record,'773',' ',' ','c')
        if titles and art_ids:
            title = titles[0]
            if info.has_key(title):
                print 'same title in %s and' % art_ids
                print '              %s \n '% info[title]
                info[title] += art_ids
            else:
                info[title] = art_ids
    
    print 'created xml for %s records' % nrec

#    incompleteAuthorsfile.close()
#    authorsfile.close()
#    authorproblems.close()
    
    outfile.write('</collection>\n')
    outfile.close()


    print 'To remove fulltexts:   rm /tmp/jacow/*'
if __name__ == "__main__":
    convertToInspire(sys.argv[1:])
