import os
from dotenv import load_dotenv

import time
import requests
from bs4 import BeautifulSoup

load_dotenv(encoding="utf_8")
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')

ava_url = "https://ava.mangot5.com"
latest_notice_title = None

res = requests.get(ava_url + "/game/ava/notice")
soup = BeautifulSoup(res.text, 'html.parser')


try:
	list_of_notices = soup.find("tbody").find_all("a")
	
	#The latest notice is changed?
	if latest_notice_title != list_of_notices[0].text.strip():
	
		#Extracting url of notice
		notice_url = ava_url + list_of_notices[0]["href"]
		print("[**DEBUG**] URL: " + notice_url)
		
		#Extracting title
		latest_notice_title = list_of_notices[0].text.strip()
		print("[**DEBUG**] Title: " + latest_notice_title)
		
		#Extracting content of notice
		notice_res = requests.get(notice_url)
		notice_soup = BeautifulSoup(notice_res.text, 'html.parser')
		notice_content = notice_soup.find("div", {"class": "view_contents"}).text.strip()
		notice_post_date = notice_soup.find("dl", {"class": "fR"}).dd.text.strip()
		print("[**DEBUG**] Post Date: " + notice_post_date)
		print("[**DEBUG**] Content: " + notice_content)
		
	else:
		print("No update")
		
except AttributeError:
	print("Error in AVA website side, re-try in 1 minute...")