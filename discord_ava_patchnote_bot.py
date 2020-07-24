import discord
import asyncio

import os
from dotenv import load_dotenv

import time
import requests
from bs4 import BeautifulSoup

load_dotenv(encoding="utf_8")
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')
CHECK_INTERVAL = os.getenv('AVA_CHECK_INTERVAL_IN_MINUTES')

ava_url = "https://ava.mangot5.com"
latest_notice_title = "none"
hello_world = False
check_interval = int(CHECK_INTERVAL) * 60

client = discord.Client()
curr_guild = None
channel = None
log_count = 0

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
		
	msg = "This guild will now receive AVA news"
	if hello_world == False:
		await channel.send(msg)
		hello_world = True
		print("Bot is ready")


@client.event
async def checking():
	global ava_url, latest_notice_title, check_interval, log_count
	
	while(True):
		res = requests.get(ava_url + "/game/ava/notice")
		soup = BeautifulSoup(res.text, 'html.parser')

		try:
			list_of_notices = soup.find("tbody").find_all("a")

			#The latest notice is changed?
			if latest_notice_title != list_of_notices[0].text.strip():

				#Extracting url of notice (notice_url)
				notice_url = ava_url + list_of_notices[0]["href"]
		
				#Extracting title (latest_notice_title)
				latest_notice_title = list_of_notices[0].text.strip()
		
				#Extracting content of notice (Date: notice_post_date, Content: notice_content)
				notice_res = requests.get(notice_url)
				notice_soup = BeautifulSoup(notice_res.text, 'html.parser')
				notice_content = notice_soup.find("div", {"class": "view_contents"}).text.strip()
				notice_post_date = notice_soup.find("dl", {"class": "fR"}).dd.text.strip()
			
				curr_guild = discord.utils.get(client.guilds, name=GUILD)
				channel = discord.utils.get(curr_guild.text_channels, name=CHANNEL)
				message = latest_notice_title + "\n\n" + notice_post_date + "\n\n" + str(notice_url) + "\n\n\n" + str(notice_content)
				await channel.send(message)
			
				f = open("log.txt","a")
				f.write("[Log] " + time.asctime(time.localtime(time.time())) +  ": Posted \"" + latest_notice_title + "\"\n")
				print("[Log] " + time.asctime(time.localtime(time.time())) +  ": Posted \"" + latest_notice_title + "\"")
				f.close()
				
			else:
				if log_count == 0:
					f = open("log.txt","a")
					f.write("[Log] " + time.asctime(time.localtime(time.time())) +  ": No update, latest notice title: " + latest_notice_title + "\n")
					print("[Log] " + time.asctime(time.localtime(time.time())) +  ": No update, latest notice title: " + latest_notice_title)
					f.close()
				log_count = log_count + 1
				if log_count == 5:
					log_count = 0
				await asyncio.sleep(check_interval)
		
		except AttributeError:
			retry_time = 10
			f = open("log.txt","a")
			f.write("[Error] " + time.asctime(time.localtime(time.time())) +  ": Error in AVA website server, re-try in " + str(retry_time) + " seconds...\n")
			print("[Error] " + time.asctime(time.localtime(time.time())) +  ": Error in AVA website server, re-try in " + str(retry_time) + " seconds...")
			f.close()
			await asyncio.sleep(retry_time)

client.loop.create_task(checking())
client.run(TOKEN)