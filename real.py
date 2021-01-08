#-*- encoding: utf-8 -*-

from bs4 import BeautifulSoup
from math import ceil
from optparse import OptionParser
import re
import os
import time
import sys
import requests
from fake_useragent import UserAgent
import telegram
import urllib.request
import json
from pyquery import PyQuery

#https://scrape.pastebin.com/api_scrape_item.php?i=

def get_timestamp():
	return time.strftime('%Y/%m/%d %H:%M:%S')

class Logger:

	def log (self, message, log_time = True):

		prefix = ''

		if log_time:
			prefix += '[{:s}] '.format(get_timestamp())

		message = prefix + message
		print(message)
		sys.stdout.flush()

	def error(self, err):
		self.log(err, True)

	def fatal_error(self, err):
		self.error(err)
		exit()

class Exceeded (Exception):
	def __init__(self):
		super().__init__(Logger().fatal_error('Malformed patterns file. Format: regex_pattern, URL logging file, directory logging file.'))
		


class Pastebin_Crawler:

	BASIC_URL = "https://pastebin.com/"
	PASTEBIN_URL = "https://scrape.pastebin.com/api_scraping.php"
	PASTEBINDATA_URL = "https://scrape.pastebin.com/api_scrape_item.php?i="
	PASTE_URL = PASTEBIN_URL + "/archive"
	patterns_file = 'patterns.txt'

	checked_id = []
	new_id = []
	suspicious_url = []

	SUCCESS = 0
	ACCESS_DENIED = -1
	NO_VALUE = -2

	ERR_MSG = "JSONDecodeError has occured"

	def read_patterns_file(self):
		try:
			f=open(self.patterns_file, 'r')
		except KeyboardInterrupt:
			raise
		except:
			Logger().fatal_error('{:s} not found or not acessible.'.format(self.patterns_file))
		try:
			self.patterns=[]
			for line in f.readlines():
				self.count=[]
				self.count.extend(line[:-1].split(','))
				if(len(self.count)==3):
					self.patterns += [self.count]
				else:
					raise Exceeded
		except KeyboardInterrupt:
			raise

	def __init__(self):
		self.read_patterns_file()

	def alert_error(self, errmsg):
		timestamp = get_timestamp()

		try:

			my_token = '1213099453:AAEwl1ZNFv6dIccexTUIhzvqbkTQIaU0T64'
			bot = telegram.Bot(token = my_token)
			updates = bot.getUpdates()

			chat_id = bot.getUpdates()[-1].message.chat.id 
		
			bot.sendMessage(chat_id = chat_id, text = errmsg )

		except OSError:
			pass
		except TimeoutError:
			pass
	
	def telegram_bot(self, filename):
		timestamp = get_timestamp()

		try:
			my_token = '1213099453:AAEwl1ZNFv6dIccexTUIhzvqbkTQIaU0T64'
			bot = telegram.Bot(token = my_token)
			updates = bot.getUpdates()

			chat_id = bot.getUpdates()[-1].message.chat.id
			bot.sendMessage(chat_id = chat_id, text = "["+timestamp+"]"+filename+" is saved\n")

		except OSError:
			pass
		except TimeoutError:
			pass


	def get_pastes_id(self):
		Logger().log('**Start Crawler**', True)
		pasteids = []

		try:
			ua = UserAgent()
			session = requests.Session()

			headers = {"User-Agent":str(ua.random)}
			#html = session.get(self.PASTEBIN_URL, headers=headers).content
			html = requests.get(self.PASTEBIN_URL).content
			soup = BeautifulSoup(html, 'html.parser')
			#page = PyQuery(html)
			#page_html = page.html()
			page_html = soup.prettify()

			f = open('list.txt','w+')
			f.write(page_html)
			f.close()

			fname = 'list.txt'
			json_data = json.loads(open(fname).read())
			

			#first = page_html.replace('\0','').strip("'<>() ").replace('\'', '\"')
			#jsondata = json.loads(page_html.replace('\\\\"','\\"'))
			#jsondata = json.loads(first)

			for n in range(0,50):
				pasteids.append(json_data[n]["key"])

		except ValueError:
			pass

		try:
			'''
			if re.findall(r'\bblocked\b|\bbanned\b', page_html, re.IGNORECASE):
				return self.ACCESS_DENIED, None
			'''
			if not pasteids:
				return self.NO_VALUE, pasteids
			else:
				return self.SUCCESS, pasteids #soup.find_all('table', 'maintable')
				'''
				if pasteids == NULL:
					return self.NO_VALUE, pasteids
				'''
		except KeyboardInterrupt:
			raise

#def error_ids():

	def check_paste(self, paste_id):

		paste_url = self.PASTEBINDATA_URL + paste_id
		basic_url = self.BASIC_URL + paste_id

		try:
			ua = UserAgent()
			session = requests.Session()
			headers = {"User-Agent":str(ua.random)}
			#html = session.get(paste_url, headers=headers).content
			html = requests.get(paste_url).content
			#page_html = PyQuery(html)
			page_html = str(html)
			soup = BeautifulSoup(html, 'html.parser')

			with urllib.request.urlopen(paste_url) as response:
				html = response.read()
				soup = BeautifulSoup(html,'html.parser')

			#paste_text = str(page_html)
			paste_text = soup.prettify()

			#paste_text = soup.find('pre','style').get_text()
			#print(type(paste_text))
			#paste_title = soup.find('h1').get_text()

			for pattern, urlfile, directory in self.patterns:
				if re.findall(pattern, paste_text, re.IGNORECASE):
					Logger().log('A pattern was found in the post content: ' + basic_url + '('+ urlfile+')', True)
					self.save_result(basic_url, paste_id, paste_text, urlfile, directory)
					return True
			Logger ().log('No pattern in the post content: ' + basic_url)

		except KeyboardInterrupt:
			raise

	def save_result(self, paste_url, paste_id, paste_text, urlfile, directory):
		timestamp = get_timestamp()
		#sendtext = ""
		with open(urlfile,'a') as matchingurl:
			matchingurl.write('['+ timestamp+'] ' + paste_url +'\n')

		try:
			os.mkdir(directory)
		except KeyboardInterrupt:
			raise
		except:
			pass

		with open(directory + '/' + timestamp.replace('/','-').replace(':','-').replace('','_')+'_'+paste_id+'.txt', mode = 'w',encoding="utf-8") as matchingtext:
			matchingtext.write(paste_text+'\n')
			#sendtext=str(matchingtext)
		self.telegram_bot(paste_url)

	def start(self, refresh_time = 15, delay = 1, ban_wait = 5, flush_after_x_refreshes=100, connection_timeout=60):

		count = 0

		while True:
			sys.setrecursionlimit(100000)
			state, pastes = self.get_pastes_id()
			start_time = time.time()

			if state == self.NO_VALUE:
				self.alert_error(self.ERR_MSG)
				count += 1
				elapsed_time = time.time() - start_time
				sleep_time = ceil(max(0, (refresh_time - elapsed_time)))

				if sleep_time > 0:
					Logger().log('Maybe JSONDecodeError has ocurred - Waiting {:d} secondes to refresh'.format(sleep_time), True)
					time.sleep(sleep_time)

			if state == self.SUCCESS:
				for paste in pastes:
					self.new_id.append(paste)
					if paste not in self.checked_id:
						self.check_paste(paste)
						time.sleep(delay)
					count += 1
					'''
					a_tag = paste.find_all("a")
					for href_tag in a_tag:
						if 'href' in href_tag.attrs:
							if "archive" in href_tag.attrs['href']:
								pass
							else:
								paste_id = href_tag.attrs['href']
								self.new_id.append(paste_id)
								if paste_id not in self.checked_id:
									self.check_paste(paste_id)
									time.sleep(delay)
								count += 1

					'''
				if count == flush_after_x_refreshes:
					self.checked_id = self.new_id
					count = 0
				else:
					self.checked_id += self.new_id
				self.new_id=[]

				elapsed_time = time.time() - start_time
				sleep_time = ceil(max(0, (refresh_time - elapsed_time)))

				if sleep_time > 0:
					Logger().log('Waiting {:d} seconds to refresh'.format(sleep_time), True)
					time.sleep(sleep_time)

			elif state == self.ACCESS_DENIED:
				Logger ().log('banned')
				for n in range(0, ban_wait):
					Logger().log('Wait ' + str(ban_wait - n ) + ' minute' + ('s' if (ban_wait - n) > 1 else ''))
					time.sleep(60)


if __name__ == '__main__':
	Pastebin_Crawler().start()

