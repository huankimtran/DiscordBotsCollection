# bot.py
import threading
from SeleniumBots.walgreen_bot import WallGreenBot
import os

import discord
import json
import random
import time
from SeleniumBots.walgreen_bot import *

"""
    Requirement:
    There needs to be a discord_config.json file in this folder.
    The JSON file contains the structure below. User needs to fill in the field
    {
        "DISCORD_VACCINE_TRACKER_BOT_API": "BOT_API_HERE",
        "DISCORD_SERVER_NAME": "SERVER_NAME_HERE, it should be Julius's Broadcaster"
        "DISCORD_COVID_VACCINE_TRACKER_CHANNEL_ID": "The sequence when you type \#channel_name in the channel"
    }
"""

def load_config(config_file_name):
    try:
        with open(config_file_name) as f:
            return json.loads(f.read())
    except Exception as e:
        print('Error openning discord config file!')
        return None

def run_availability_checker_bot(discord_bot):
    #  Wait until the discord_bot ready
    while not discord_bot.ready:
        time.sleep(0.1)

    while True:
        for bot in discord_bot.checker_bot_map.values():
            try:
                bot.run()
            except Exception as e:
                print(f'Error running bot {e}')
            # Pause before next bot
            time.sleep(1)
            

class DiscordVaccineTrackerBot:
    def __init__(self) -> None:
        self.ready = False
        # Load discord config file
        self.ENV = load_config('discord_config.json')
        if self.ENV == None:
            print('Terminating bot due to no config file found')
            exit(0)
        # Extrect bot api
        self.BOT_API = self.ENV['DISCORD_VACCINE_TRACKER_BOT_API']
        # bot subscribe command prompt
        self.SUBSCRIBE_CMD_PROMPT = """ The command syntax is
                /subscribe_zip [list of zip seperated by , or zipcode range seperated by a hyphen]
                For example:

                /subscribe_zip 55737, 77433

                Or using range, from 75513 to 75515

                /subscribe_zip 75513-75515"""
        self.UNSUBSCRIBE_CMD_PROMPT = """ The command syntax is
                /unsubscribe_zip [list of zip seperated by , or zipcode range seperated by a hyphen]
                For example:

                /unsubscribe_zip 55737, 77433

                Or using range, from 75513 to 75515

                /unsubscribe_zip 75513-75515"""
        # Generate the discord bot
        self.bot = client = discord.Client()
        # =========================================DiscordBotDefinition=============================================
        @client.event
        async def on_ready():
            # Get channel to post on
            self.channel = client.get_channel(int(self.ENV['DISCORD_COVID_VACCINE_TRACKER_CHANNEL_ID']))
            await self.channel.send('Bot ready!')
            # Initialize the checker bot map
            self.checker_bot_map = {
                'walgreen' : WallGreenBot(self)
            }

            print(f'{client.user.name} has connected to Discord!')
            self.ready = True

        @client.event
        async def on_message(message):
            # Preventing bot from responding to itself
            if message.author == client.user:
                return
            
            # Only responds to channel covid-vaccine-tracker
            if str(message.channel) != 'covid-vaccine-tracker':
                return
            
            # Track user command
            if self.parse_subscribe_zip(message.author.mention, message.content):
                await message.channel.send("Subscribed")
            elif self.parse_unsubscribe_zip(message.author.mention, message.content):
                await message.channel.send("Unsubscribed")
        # =========================================EndDiscordBotDefinition=============================================

        # Create thread to run availability checker bots
        threading.Thread(target=run_availability_checker_bot, args=(self, )).start()

    def send_msg_to_channel(self, msg):
        self.bot.loop.create_task(self.channel.send(msg))

    def run(self):
        self.bot.run(self.BOT_API)

    def parse_subscribe_zip(self, user_name, full_msg) -> bool:
        """
            Track the command to add a user to a list of zipcode
            The command syntax is
            /subscribe_zip [list of zip seperated by , or zipcode range seperated by a hyphen]
            For example:

            /subscribe_zip 55737, 77433

            Or using range, from 75513 to 75515

            /subscribe_zip 75513-75515
            Return False if cannot find the command or command does not follow
            the correct syntax
        """
        # Remove redundant spaces
        full_msg = full_msg.strip()
        full_msg = ' '.join(full_msg.split())

        # Check if message contains this command
        if full_msg.find('/subscribe_zip') == -1:
            return False
       
        # Extract arguments
        arg_raw = full_msg[len('/subscribe_zip '):]

        # range or list ?
        if '-' in arg_raw:
            try:
                para = [int(p) for p in arg_raw.split('-')]
            except Exception as e:
                print(f'Unable to parse command arguments in message {full_msg} due to {str(e)}')
                print(self.SUBSCRIBE_CMD_PROMPT)
                return False

            # Get list of zip code
            low = min(para)
            high = max(para)
            zipcode_list = list(range(low, high+1))
        else:
            try:
                zipcode_list = [int(z) for z in arg_raw.split(',')]
            except Exception as e:
                print(f'Unable to parse command arguments in message {full_msg} due to {str(e)}')
                print(self.SUBSCRIBE_CMD_PROMPT)
                return False

        # subscribe user to the zipcode
        try:
            for bot in self.checker_bot_map.values():
                bot.subscribe_user_to_zipcode(user_name, zipcode_list)
        except Exception as e:
            print(f'Unable to subscribe user {user_name} to zipcode {zipcode_list} due to error {str(e)}')
            return False
        return True

    def parse_unsubscribe_zip(self, user_name, full_msg) -> bool:
        """
            Track the command to add a user to a list of zipcode
            The command syntax is
            /unsubscribe_zip [list of zip seperated by , or zipcode range seperated by a hyphen]
            For example:

            /unsubscribe_zip 55737, 77433

            Or using range, from 75513 to 75515

            /unsubscribe_zip 75513-75515
            Return False if cannot find the command or command does not follow
            the correct syntax
        """
        # Remove redundant spaces
        full_msg = full_msg.strip()
        full_msg = ' '.join(full_msg.split())

        # Check if message contains this command
        if full_msg.find('/unsubscribe_zip') == -1:
            return False

       
        # Extract arguments
        arg_raw = full_msg[len('/unsubscribe_zip '):]

        # range or list ?
        if '-' in arg_raw:
            try:
                para = [int(p) for p in arg_raw.split('-')]
            except Exception as e:
                print(f'Unable to parse command arguments in message {full_msg} due to {str(e)}')
                print(self.SUBSCRIBE_CMD_PROMPT)
                return False

            # Get list of zip code
            low = min(para)
            high = max(para)
            zipcode_list = list(range(low, high+1))
        else:
            try:
                zipcode_list = [int(z) for z in arg_raw.split(',')]
            except Exception as e:
                print(f'Unable to parse command arguments in message {full_msg} due to {str(e)}')
                print(self.SUBSCRIBE_CMD_PROMPT)
                return False

        # unsubscribe user from the zipcode
        try:
            for bot in self.checker_bot_map.values():
                bot.unsubscribe_user_from_zipcode(user_name, zipcode_list)
        except Exception as e:
            print(f'Unable to unsubscribe user {user_name} from zipcode {zipcode_list} due to error {str(e)}')
            return False
        return True

DiscordVaccineTrackerBot().run()