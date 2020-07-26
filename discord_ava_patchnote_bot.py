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

client = discord.Client()
curr_guild = None
channel = None

def write_to_log(msg):
	f = open("log.txt","a")
	f.write(msg + "\n")
	print(msg)
	f.close()

@client.event
async def on_ready():
	global hello_world, curr_guild, channel

	curr_guild = discord.utils.get(client.guilds, name=GUILD)
	if curr_guild is None:
		print("Guild \"" + GUILD + "\" not found")
		return
		
	channel = discord.utils.get(curr_guild.text_channels, name=CHANNEL)
	if channel is None:
		print("In guild: \"" + GUILD +  "\", text channel \"" + CHANNEL + "\" not found")
		return
		
	msg = "This channel will now receive AVA TW/HK news"
	if hello_world == False:
		#await channel.send(msg) #Please remove the comment symbol (#) if you are running this the first time
		hello_world = True
		write_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": Bot is online")

@client.event
async def checking():
	AVA_URL = "https://ava.mangot5.com"
	RETRY_TIME = 10
	NO_UPDATE_LOG_OCCURANCE = 10
	CHECK_INTERVAL_IN_SEC = int(CHECK_INTERVAL) * 60
	
	global latest_notice_title, log_count
	
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
					write_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": Posted in discord: '" + latest_notice_title + "'")
					log_count = 0
					await asyncio.sleep(CHECK_INTERVAL_IN_SEC)
				
			else: #No update
				if log_count == 0:
					write_to_log("[Log] " + time.asctime(time.localtime(time.time())) +  ": No update, latest: '" + latest_notice_title + "'")
				log_count = log_count + 1
				if log_count == NO_UPDATE_LOG_OCCURANCE:
					log_count = 0
				await asyncio.sleep(CHECK_INTERVAL_IN_SEC)
		
		except Exception as e: #AVA Server error
			tb = traceback.format_exc()
			write_to_log("[Error] " + time.asctime(time.localtime(time.time())) +  ": Error in AVA website server, re-try in " + str(RETRY_TIME) + " seconds.\n"+ str(tb))
			log_count = 0
			await asyncio.sleep(RETRY_TIME)
		
client.loop.create_task(checking())
client.run(TOKEN)
