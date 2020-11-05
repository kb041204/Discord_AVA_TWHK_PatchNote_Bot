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

hello_world = False
log_count = 0
error_count = 0

last_update_or_error_time = time.time()
latest_notice_title = "none"
last_message = "none"
last_url = "none"

client = discord.Client(activity=discord.Activity(name="AVA web server", type=discord.ActivityType.listening))

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
	NO_UPDATE_LOG_OCCURANCE = 10 #How many consecutive no update log should not be recorded
	DAYS_WITHOUT_UPDATE_CLEAR_LOG = 1 #How many days should pass without any update to clear all previous logs
	RETRY_TIME_IN_SECONDS = 10 #How many seconds to wait until retry upon error
	ERROR_RETRY_ADJUSTMENT_COUNT = 10 #How many consecutive error it receives before adjusting the retry time
	ERROR_RETRY_ADJUSTMENT_LIMIT = int(int(CHECK_INTERVAL)*60/int(RETRY_TIME_IN_SECONDS)) #How many times the system is allowed to change its adjustment, default = max every check interval
	SLEEP_INTERVAL_IN_HOUR = 7
	
	AVA_URL = "https://ava.mangot5.com"
	CHECK_INTERVAL_IN_SEC = int(CHECK_INTERVAL) * 60
	SLEEP_INTERVAL_IN_SEC = SLEEP_INTERVAL_IN_HOUR*60*60

	global log_count, latest_notice_title, last_update_or_error_time, last_message, last_url
	
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
					message = discord.Embed(title=str(latest_notice_title), description=str(notice_content), url=str(notice_url), colour=discord.Color.teal())
					
					if last_url == notice_url: #Title changed but URL not changed
						await message_sent_to_discord.edit(embed=message, suppress=False)
						append_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": Edited post in discord: '" + str(latest_notice_title) + "'")
					else:
						message_sent_to_discord = await channel.send(embed=message)
						append_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": Posted in discord: '" + str(latest_notice_title) + "'")
					
					last_message = message
					last_url = notice_url
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
				if int(time.strftime("%H", time.localtime(time.time()))) == 16: #UTC 16:00/GMT+8 00:00
					message = "[Log] " + time.asctime(time.localtime(time.time())) +  ": No update, latest: '" + str(latest_notice_title) + "', BOT going to sleep mode for " + str(SLEEP_INTERVAL_IN_HOUR)  + " hours"
					append_to_log(message)
					log_count = 0
					await asyncio.sleep(SLEEP_INTERVAL_IN_SEC)
				else:
					await asyncio.sleep(CHECK_INTERVAL_IN_SEC)
		
			error_count = 0 #Previous post has no error
			
		except Exception as e: #AVA Server error
			tb = traceback.format_exc()
			error_count = error_count + 1 #Increase error count
			adjustment = int(error_count / ERROR_RETRY_ADJUSTMENT_COUNT) + 1
			if adjustment >= ERROR_RETRY_ADJUSTMENT_LIMIT:
				adjustment = ERROR_RETRY_ADJUSTMENT_LIMIT
			actual_retry_time = adjustment*RETRY_TIME_IN_SECONDS
			append_to_log("[Error] " + time.asctime(time.localtime(time.time())) +  ": Error in AVA website server, re-try in " + str(actual_retry_time) + " seconds.\n" + str(tb) + "\n")
			log_count = 0
			last_update_or_error_time = time.time()
			await asyncio.sleep(actual_retry_time)
		
client.loop.create_task(checking())
client.run(TOKEN)
