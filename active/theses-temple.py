# -*- coding: utf-8 -*-
#harvest theses from U. Temple
#JH: 2022-03-13


from urllib import urlopen
from time import sleep
from bs4 import BeautifulSoup
from json import loads
from base64 import b64encode
import datetime
import os
import codecs
import ejlmod2
import re

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Temple U. (main)'
jnlfilename = 'THESES-TEMPLE-%s' % (stampoftoday)

recs = []

def get_sub_side(url, fc, aff):
	print "[%s] --> Harversting Data" % url

	data = loads(urlopen(url).read())

	rec = {'jnl': 'BOOK', 'tc': 'T', 'fc': fc}

	# Generate the link
	link = "https://digital.library.temple.edu/digital/collection/%s/id/%s" % (data.get('collectionAlias'), data.get('requestedId'))
	rec['link'] = link

	# Get the pdf link
	pdf_link = "https://digital.library.temple.edu/%s" % data.get('downloadParentUri')
	rec['hidden'] = pdf_link

	# Generate fake DOI
	doi = "20.2000/Temple/%s" % b64encode(url.decode('utf-8'))
	rec['doi'] = doi

	if data.get('parent') is None:
		data = data.get('fields')
	else:
		data = data.get('parent').get('fields')

	for field in data:
		key = field.get('key')
		label = field.get('label')
		value = field.get('value')

		if key == "creato" and label == 'Author':
			# Get the author

			rec['autaff'] = [[value, aff]]
		elif key == 'title':
			# Get the title

			rec['tit'] = value
		elif key == 'date':
			# Get the date

			rec['date'] = value
		elif key == 'degree':
			# Check if the degree in a PhD

			if value != 'Ph.D.':
				print "NOT A DOCTORAL THESES! %s" % field.get('value')
				return None
		elif key == 'abstra':
			# Get the abstract

			rec['abs'] = value
		elif key == "contri" and label == 'Advisor':
			# Get the Advisors

			advisors = []
			# Check if multiple advisors
			splitted = value.split(';')
			if len(splitted) == 2 and splitted[-1] == []:
				advisors.append([splitted[0]])
			else:
				for advisor in splitted[0:len(splitted)-1]:
					advisors.append([advisor])
				# Check if rec['supervisor'] already exists
			if "supervisor" in rec.keys():
				for member in advisors:
					rec['supervisor'].append(member)
			else:
				rec['supervisor'] = advisors
		#elif key == 'audien' and label == 'Committee Members':
		#	# Get the Committee members
		#	committee_members = []
		#	# Check if multiple committee members
                #        splitted = value.split(';')
		#	if len(splitted) == 2 and splitted[-1] == []:
		#		committee_members.append([splitted[0]])
		#	else:
		#		for committee_member in splitted[0:len(splitted)-1]:
		#			committee_members.append([committee_member])
		#	# Check if rec['supervisor'] already exists
		#	if "supervisor" in rec.keys():
		#		for com_member in committee_members:
		#			rec['supervisor'].append(com_member)
		#	else:
		#		rec['supervisor'] = committee_members
		elif key == 'covera' and label == 'Keywords':
			# Get the keywords

			keywords = field.get('value').split('; ')
			rec['keyw'] = keywords
		elif key == 'relati' and label == 'Number of Pages':
			# Get the number of pages

			pages = value
                        if re.search('^\d+$', pages):
			        rec['pages'] = pages
		elif key == 'langua' and field.get('label') == 'Language':
			# Get the language

			lang = value

			rec['lang'] = lang

	#for i in rec.keys():
	#	print "[%s] :\n%s" %(i, rec.get(i))
        print '  ', rec.keys()

	print "-----------------------------------------------------------------------------------------------"

	recs.append(rec)

for (dep, fc, aff) in [('Physics', '', 'Temple U.'), ('Mathematics', 'm', 'Temple U. (main)')]:
        # Get the number of records
        total_results = loads(urlopen("https://digital.library.temple.edu/digital/api/search/collection/p245801coll10/searchterm/" + dep +"!ph.d./field/descri!degree/mode/exact!exact/conn/and!and/page/1/maxRecords/10").read()).get('totalResults')
        sleep(2)

        # Get the articles
        articles = loads(urlopen("https://digital.library.temple.edu/digital/api/search/collection/p245801coll10/searchterm/" + dep +"!ph.d./field/descri!degree/mode/exact!exact/conn/and!and/order/date/ad/desc!and/page/1/maxRecords/%i" % total_results).read()).get('items')

        i = 0 
        for item in articles:
                i += 1
                print '---{ %s %i/%i }---' % (dep, i, len(articles))
                year = 9999
                for entry in item.get('metadataFields'):
                        if entry['field'] == 'date':
                                year = int(entry['value'])
                if now.year - year < 3:
	                item_id = item.get('itemId')
	                coll_alias = item.get('collectionAlias')
                
	                item_link = "https://digital.library.temple.edu/digital/api/collections/%s/items/%s/false" % (coll_alias, item_id)
	                #get_sub_side(item_link, 'm', 'Temple U.')
	                get_sub_side(item_link, fc, aff)

	                sleep(3)


#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
