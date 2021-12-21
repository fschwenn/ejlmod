# -*- coding: utf-8 -*- 
#harvest theses from Brussels
#JH: 2021-12-20

from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.common.by import By
import re
import unicodedata


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
	print "["+url+"] --> Harvesting data"

	rec = {}

	rec['supervisor'] = []
	rec['notes'] = []
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
						rec['tit'] = convert_string(title[0].text)
				elif caption.text.find('Author') != -1:

					# Get the author of the article
					author = tr.find_all('td', attrs={'id': 'value'})
					if len(author) == 1:
						rec['autaff'] = [convert_string(author[0].text)]
				elif caption.text.find('Director') != -1:

					# Add the director to the comittee members
					director = tr.find_all('td', attrs={'id': 'value'})
					if len(director) == 1:
						rec["supervisor"].append([convert_string(director[0].text)])
				elif caption.text.find('Committee member') != -1:

					# Add the committee members
					committee_members_section = tr.find_all('td', attrs={'id': 'value'})
					if len(committee_members_section) == 1:
						committee_members = committee_members_section[0].text.split(';')
						for member in committee_members:
							rec['supervisor'].append([convert_string(member)])
				elif caption.text.find('Defense date') != -1:

					# Get the publication date
					publication_date = tr.find_all('td', attrs={'id': 'value'})
					if len(publication_date) == 1:
						rec['date'] = publication_date[0].text.replace('-', '/')
				elif caption.text.find('CREF') != -1:

					# Get the CREFs and add it the the notes
					crefs = []
					crefs.append(tr.find_all('td', attrs={'id': 'value'})[0])

					# Run this loop as long as needed to catch all of the entries under this point
					i = 1
					while True:
						if record_details[0].find_all('tr')[counter+i].find_all('td', attrs={'id': 'caption'})[0].text != "":
							break

						crefs.append(record_details[0].find_all('tr')[counter+i].find_all('td', attrs={'id': 'value'})[0].text)

						i += 1
					rec['notes'].append(crefs)
				elif caption.text.find('Keywords') != -1:

					# Get the keywords
					# In case they are in an enumeration split it, otherwise Run a loop till all of them  are caught
					keywords_section = tr.find_all('td', attrs={'id': 'value'})
					if keywords_section[0].text.find(',') != -1:
						keywords = keywords_section[0].text.split(', ')
						for keyword in keywords:
							rec['keyw'] = convert_string(keyword)
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
						rec['notes'].append(degree_section[0])
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
	print rec
	recs.append(rec)
	

pages = 464
for page in range(1, pages+1):
	print "--- OPEN PAGE " + str(page) + " ---"
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
	sleep(10)
