import discord
import asyncio

import os
from dotenv import load_dotenv

import time
import requests
from bs4 import BeautifulSoup
import traceback

load_dotenv(encoding="utf_8")
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')
CHECK_INTERVAL = os.getenv('AVA_CHECK_INTERVAL_IN_MINUTES')

latest_notice_title = "none"
hello_world = False
log_count = 0
last_update_or_error_time = 0

client = discord.Client()

class SettingError(Exception):
    pass

def append_to_log(msg): #Add a new line
	f = open("log.txt","a")
	f.write(msg + "\n")
	print(msg)
	f.close()

def write_to_log(msg): #Overwrite all the existing line
	f = open("log.txt","w")
	f.write(msg + "\n")
	print(msg)
	f.close()

@client.event
async def on_ready():
	global hello_world

	curr_guild = discord.utils.get(client.guilds, name=GUILD)
	if curr_guild is None:
		raise SettingError("Guild \"" + GUILD + "\" not found")
		
	channel = discord.utils.get(curr_guild.text_channels, name=CHANNEL)
	if channel is None:
		raise SettingError("In guild: \"" + GUILD +  "\", text channel \"" + CHANNEL + "\" not found")
		
	msg = "This channel will now receive AVA TW/HK news"
	if hello_world == False:
		#await channel.send(msg) #Please remove the comment symbol (#) if you are running this the first time
		hello_world = True
		append_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": Bot is online")

@client.event
async def checking():
	RETRY_TIME = 10
	NO_UPDATE_LOG_OCCURANCE = 10
	DAYS_WITHOUT_UPDATE_CLEAR_LOG = 1
	
	AVA_URL = "https://ava.mangot5.com"
	CHECK_INTERVAL_IN_SEC = int(CHECK_INTERVAL) * 60

	global latest_notice_title, log_count, last_update_or_error_time
	
	while(True):
		res = requests.get(AVA_URL + "/game/ava/notice")
		soup = BeautifulSoup(res.text, 'html.parser')

		try:
			list_of_notices = soup.find("tbody").find_all("a")

			#The latest notice is changed?
			if latest_notice_title != list_of_notices[0].text.strip():

				#Extracting url of notice (notice_url)
				notice_url = AVA_URL + list_of_notices[0]["href"]
		
				#Extracting title (latest_notice_title)
				latest_notice_title = list_of_notices[0].text.strip()
		
				#Extracting content of notice (Date: notice_post_date, Content: notice_content)
				notice_res = requests.get(notice_url)
				notice_soup = BeautifulSoup(notice_res.text, 'html.parser')
				notice_content = notice_soup.find("div", {"class": "view_contents"}).text.strip()
				notice_post_date = notice_soup.find("dl", {"class": "fR"}).dd.text.strip()
				
				#Send message and log
				curr_guild = discord.utils.get(client.guilds, name=GUILD)
				if curr_guild is not None:
					channel = discord.utils.get(curr_guild.text_channels, name=CHANNEL)
					message = str(latest_notice_title) + "\n\n" + str(notice_url) + "\n\n" + str(notice_content)
					await channel.send(message)
					append_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": Posted in discord: '" + str(latest_notice_title) + "'")
					log_count = 0
					last_update_or_error_time = time.time()
					await asyncio.sleep(CHECK_INTERVAL_IN_SEC)
				
			else: #No update
				if log_count == 0:
					message = "[Log] " + time.asctime(time.localtime(time.time())) +  ": No update, latest: '" + str(latest_notice_title) + "'"
					if (time.time() - last_update_or_error_time >= DAYS_WITHOUT_UPDATE_CLEAR_LOG*24*60*60): #If there's no updates in n day(s)
						write_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": " + str(DAYS_WITHOUT_UPDATE_CLEAR_LOG) + " day(s) without update, cleared previous logs")
						last_update_or_error_time = time.time()
					append_to_log(message)
				log_count = log_count + 1
				if log_count == NO_UPDATE_LOG_OCCURANCE:
					log_count = 0
				await asyncio.sleep(CHECK_INTERVAL_IN_SEC)
		
		except Exception as e: #AVA Server error
			tb = traceback.format_exc()
			append_to_log("[Error] " + time.asctime(time.localtime(time.time())) +  ": Error in AVA website server, re-try in " + str(RETRY_TIME) + " seconds.\n" + str(tb) + "\n")
			log_count = 0
			last_update_or_error_time = time.time()
			await asyncio.sleep(RETRY_TIME)
		
client.loop.create_task(checking())
client.run(TOKEN)
