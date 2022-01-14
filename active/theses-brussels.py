# -*- coding: utf-8 -*- 
#harvest theses from Brussels
#JH: 2021-12-20

from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.common.by import By
import re
import unicodedata
import ejlmod2
import datetime
import codecs
import os

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Brussels'
jnlfilename = 'THESES-BRUSSELS-%s' % (stampoftoday)

pages = 6
boring = ["Doctorat en Criminologie", u"Doctorat en Histoire, histoire de l'art et archéologie",
          "Doctorat en Philosophie", u"Doctorat en Sciences biomédicales et pharmaceutiques (Médecine)",
          u"Doctorat en Sciences biomédicales et pharmaceutiques (Pharmacie)", "Doctorat en Sciences juridiques",
          "Doctorat en Sciences politiques et sociales", u"Doctorat en Sciences psychologiques et de l'éducation",
          "Doctorat en Art et Sciences de l'Art", u"Doctorat en Histoire, art et archéologie",
          u"Doctorat en Sciences de la motricité", u"Doctorat en Sciences de la santé Publique",
          u"Doctorat en Art de bâtir et urbanisme (Polytechnique)",
          u"Doctorat en Langues, lettres et traductologie", "Doctorat en Sciences des religions",
          u"Doctorat en Sciences agronomiques et ingénierie biologique", u"Doctorat en Sciences médicales (Médecine)",
          u"Doctorat en Santé Publique", u"Doctorat en Sciences économiques et de gestion",
          u"Doctorat en Sciences de l'ingénieur et technologie", "Option Biologie des organismes du Doctorat en Sciences",
          u"Option Biologie moléculaire du Doctorat en Sciences", u"Option Géographie du Doctorat en Sciences",
          u"Doctorat en Sciences médicales (Santé Publique)",
          u"Option Gestion de l’environnement et d’aménagement du territoire du Doctorat en Sciences",
          u"Doctorat en Arts du spectacle et technique de diffusion et de communication",
          u"Doctorat en Langues et lettres", u"Doctorat en Information et communication",
          u"Doctorat en Art de bâtir et urbanisme (Architecture)", u"Doctorat en droit",
          u"Doctorat en environnement, Orientation gestion de l'environnement",
          u"Doctorat en philosophie et lettres, Orientation histoire de l'art et archéologie",
          u"Doctorat en philosophie et lettres, Orientation linguistique",
          u"Doctorat en sciences agronomiques et ingénierie biologique",
          u"Doctorat en sciences économiques, Orientation économie",
          u"Doctorat en sciences, Orientation statistique", u"Doctorat en sciences pharmaceutiques",
          u"Doctorat en sciences politiques", u"Doctorat en sciences psychologiques",
          u"Doctorat en sciences sociales, Orientation sociologie",
          u"Doctorat en sciences, Spécialisation chimie", u"Doctorat en sciences, Spécialisation géologie",
          u"Doctorat en Sciences dentaires", u"Doctorat en sciences médicales",
          u"Doctorat en Art de bâtir et urbanisme", u"Doctorat en Sciences de la santé publique",
          u"Doctorat en Sciences Psychologiques et de l'éducation", u"Doctorat en Sciences médicales",
          u"Doctorat en Sciences biomédicales et pharmaceutiques", u"Doctorat en Sciences de l'ingénieur",
          u"Doctorat en sciences sociales, Orientation sciences du travail",
          u"Doctorat en philosophie et lettres, Orientation langue et littérature",
          u"Doctorat en philosophie et lettres, Orientation histoire"]
boring += [u"Sciences sociales", u"Télédétection", u"Chimie des surfaces et des interfaces",
           u"Géologie", u"Ecologie", u"Géochimie", u"Océanographie physique et chimique", "Chimie",
           u"Biochimie", u"Biologie cellulaire", u"Urbanisme et architecture (aspect sociologique)",
           u"Informatique mathématique", u"Chimie organique", u"Biologie", u"Biologie moléculaire",
           u"Glaciologie", u"Géographie urbaine", u"Géographie humaine", u"Chimie analytique",
           u"Biologie théorique", u"Immunologie", u"Cancérologie", u"Architecture et art urbain",
           u"Santé publique", u"Psychologie", u"Sciences de l'ingénieur", u"Sciences pharmaceutiques",
           u"Disciplines biomédicales diverses", u"Médecine pathologie humaine", u"Langues et littératures",
           u"Sociologie du travail et de la technique", u"Urbanisme et architecture [génie civil]",
           u"Sciences humaines", u"Agronomie générale", u"Géographie physique", u"Aménagement du territoire"]
           
recs = []

# Initialize driver
driver = webdriver.PhantomJS()


def convert_string(string):
	string_list = list(string)

	for i in range(0,len(string_list)):
		try:
			string_list[i] = str(unicodedata.digit(string_list[i])).encode('utf-8')
		except ValueError:
			pass

	out = ""
       	for j in string_list:
		out += j

	return out



def get_sub_side(url):
	print " ["+url+"] --> Harvesting data"
        keepit = True
        
	rec = {'keyw' : []}

	rec['supervisor'] = []
	rec['note'] = []
	rec['tc'] = 'T'
	rec['jnl'] = 'BOOK'
	rec['link'] = url

	# Set the fake doi
	rec['doi'] = "20.2000/brussels/" + re.sub('\W', '', url) 

	driver.get(url)
	soup = BeautifulSoup(driver.page_source, 'lxml')

	# Get the main information table
	record_details = soup.find_all('table', attrs={'id': 'recorddetails'})
	if len(record_details) == 1:
		counter = 0
		for tr in record_details[0].find_all('tr'):
			for caption in tr.find_all('td', attrs={'id': 'caption'}):
				if caption.text.find('Title') != -1:

					# Get the title of the article
					title = tr.find_all('td',attrs={'id': 'value'})
					if len(title) == 1:
						rec['tit'] = convert_string(convert_string(title[0].text))
				elif caption.text.find('Author') != -1:

					# Get the author of the article
					author = tr.find_all('td', attrs={'id': 'value'})
					if len(author) == 1:
						rec['autaff'] = [[convert_string(author[0].text), publisher]]
				elif caption.text.find('Director') != -1:

					# Add the director to the comittee members
					director = tr.find_all('td', attrs={'id': 'value'})
					if len(director) == 1:
                                                for sv in re.split('; ', convert_string(director[0].text)):
						        rec["supervisor"].append([sv])
				elif caption.text.find('Co.Supervisor') != -1:

					# Add the director to the comittee members
					codirector = tr.find_all('td', attrs={'id': 'value'})
					if len(codirector) == 1:
                                                for sv in re.split('; ', convert_string(codirector[0].text)):
						        rec["supervisor"].append([sv])
				elif caption.text.find('Committee member') != -1:

					# Add the committee members
					committee_members_section = tr.find_all('td', attrs={'id': 'value'})
					if len(committee_members_section) == 1:
						committee_members = committee_members_section[0].text.split(';')
                                                #Committee Mebmbers do not count as supervisors
						#for member in committee_members:
						#    rec['supervisor'].append([convert_string(member)])
				elif caption.text.find('Physical description') != -1:

					# Add number of pages
				        pages = tr.find_all('td', attrs={'id': 'value'})
					if len(pages) == 1:
						pages = pages[0].text
                                                if re.search('\d+ p\.', pages):
                                                        rec['pages'] = re.sub('.*?(\d+) p\..*', r'\1', pages)
				elif caption.text.find('Defense date') != -1:

					# Get the publication date
					publication_date = tr.find_all('td', attrs={'id': 'value'})
					if len(publication_date) == 1:
						rec['date'] = publication_date[0].text.replace('-', '/')
				elif caption.text.find('CREF') != -1:

					# Get the CREFs and add it the the note
					crefs = []
					crefs.append(tr.find_all('td', attrs={'id': 'value'})[0].text)

					# Run this loop as long as needed to catch all of the entries under this point
					i = 1
					while True:
						if record_details[0].find_all('tr')[counter+i].find_all('td', attrs={'id': 'caption'})[0].text != "":
							break

						crefs.append(record_details[0].find_all('tr')[counter+i].find_all('td', attrs={'id': 'value'})[0].text)

                                                i += 1
					rec['note'] += crefs
                                        for cref in crefs:
                                                if cref in boring:
                                                        keepit = False
				elif caption.text.find('Keywords') != -1:

					# Get the keywords
					# In case they are in an enumeration split it, otherwise Run a loop till all of them  are caught
					keywords_section = tr.find_all('td', attrs={'id': 'value'})
					if keywords_section[0].text.find(',') != -1:
						keywords = keywords_section[0].text.split(', ')
						for keyword in keywords:
							rec['keyw'].append(convert_string(keyword))
					else:
						keywords = []
						keywords.append(convert_string(tr.find_all('td', attrs={'id': 'value'})[0].text))
						i = 1
                                        	while True:
                                                	if record_details[0].find_all('tr')[counter+i].find_all('td', attrs={'id': 'caption'})[0].text != "":
                                                        	break

	                                                keywords.append(convert_string(record_details[0].find_all('tr')[counter+i].find_all('td', attrs={'id': 'value'})[0].text))
	
        	                                        i += 1
						rec['keyw'] = keywords
				elif caption.text.find('Degree') != -1:

					# Get the degree
					degree_section = tr.find_all('td', attrs={'id': 'value'})
					if len(degree_section) == 1:
                                                degree = degree_section[0].text
                                                if degree in boring:
                                                        keepit = False
                                                else:
						        rec['note'].append(degree)
				elif caption.text.find('Language') != -1:

					# Get the language of the article
					language_section = tr.find_all('td', attrs={'id': 'value'})
					if len(language_section) == 1:
						if language_section[0].text.find('nglish') == -1:
							rec['language'] = language_section[0].text
			counter += 1


	# Get the abstract
	abstract_link_section = soup.find_all('a', attrs={'class': 'first'})
	for i in abstract_link_section:
		if i.text == "Content":
			driver.get(i.get('href'))
			break

	soup = BeautifulSoup(driver.page_source, 'lxml')
	abstract_section = soup.find_all('td', attrs={'id': 'abstractvalue'})
	if len(abstract_section) == 1:
		rec['abs'] = u''
		rec['abs'] = convert_string(abstract_section[0].text)
		#rec['abs'] = convert_string(rec['abs'])
        if keepit:
                #Fulltext
                sleep(2)
                holdingsurl = re.sub('Details', 'Holdings', url)
                driver.get(holdingsurl)
                holdingspage = BeautifulSoup(driver.page_source, features="lxml")
                for script in holdingspage.find_all('script', attrs = {'type' : 'text/javascript'}):
                        sstring = script.string
                        #JSON parsing does not work because of quotation marks mess
                        if sstring and re.search('\.pdf', sstring):
                                for part in re.split('"File" *:', sstring)[1:]:
                                        if re.search('(Full text|uvre compl).*Open access', part):
                                                #rec['note'].append(part)
                                                access = re.sub('.*(https.*?\.pdf).*', r'\1', part)
                                                rec['FFT'] = access
	        print '  ', rec.keys()
	        recs.append(rec)

	

for page in range(1, pages):
	print "--- OPEN PAGE %i OF %i  ---" % (page, pages)
	index_url = "https://difusion.ulb.ac.be/vufind//Search/Home?lookfor=&sort=pubdate+desc&submitButton=Recherche&type=general&filter[]=genreUlbStr:%22info:ulb-repo/semantics/doctoralThesis%22&page=" + str(page)
	driver.get(index_url)
	sleep(2)

	language_switch = driver.find_elements(By.ID, 'enLang')
	if len(language_switch) == 1:
		language_switch[0].click()
		sleep(5)
		for i in BeautifulSoup(driver.page_source, 'lxml').find_all('div', attrs={'id': 'resultItemLine1'}):
			link = i.find_all('a')
			if link[0].get('href') is not None:
				href = link[0].get('href').split('/')
				href[-1] = "Details"
				final_link = ""
				for part in href:
					final_link += "/" + part
				get_sub_side("https://difusion.ulb.ac.be" + final_link)
			sleep(10)
	sleep(5)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'),'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
