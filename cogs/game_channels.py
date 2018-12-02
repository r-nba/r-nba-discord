from urllib.request import urlopen
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
import datetime
import calendar
import collections
import logging
import traceback
from dateutil import parser

import discord
from discord.ext import commands

class game_channels:

    def __init__(self, bot):
        self.bot = bot
        logging.basicConfig()
        self.logger = logging.getLogger('apscheduler')
        self.logger.setLevel(logging.ERROR)
        self.sched = AsyncIOScheduler()
        self.sched.add_job(self.update_games_daily, 'cron', hour=3)
        self.sched.add_job(self.create_game_threads, 'interval', minutes=1)
        self.sched.start()
        self.load_settings()

    def load_settings(self):
        self.server_id = 451446182515048448
        self.category_id = 495258425727385610

        # load team data
        self.load_teams()

        self.get_games()

    def load_teams(self):
        self.team_dict = {}
        self.team_dict_med_key = {}
        self.team_dict_short_key = {}
        with open("data/teams.csv", "r") as teamInfoFile:
            for teamInfoRow in teamInfoFile.read().split("\n"):
                teamInfo = teamInfoRow.split(',')
                tmp_team_dict = {
                    'long_name': teamInfo[0] + " " + teamInfo[1],
                    'med_name': teamInfo[1],
                    'short_name': teamInfo[2].upper()
                }
                self.team_dict[teamInfo[2].upper()] = tmp_team_dict
                self.team_dict_med_key[teamInfo[1]] = tmp_team_dict
                self.team_dict_short_key[teamInfo[2].upper()] = tmp_team_dict

    def get_games(self):
        self.games = []
        self.date = datetime.datetime.today()
        self.parameter = self.date.strftime('%Y%m%d')
        with urlopen('http://data.nba.com/prod/v2/' + self.parameter + '/scoreboard.json') as url:
            self.j = json.loads(url.read().decode())
            for game in self.j["games"]:
                self.gameDetails = {}
                self.gameDetails["time"] = parser.parse(game["startTimeEastern"])
                self.vTeam = game['vTeam']['triCode']
                self.hTeam = game['hTeam']['triCode']

                self.gameDetails["away"] = self.team_dict[self.vTeam]['med_name']
                self.gameDetails["home"] = self.team_dict[self.hTeam]['med_name']

                self.games.append(self.gameDetails)

        return self.games

    async def update_games_daily(self):
        self.guild = self.bot.get_guild(self.server_id)
        self.category = self.bot.get_channel(self.category_id)

        self.channels = []
        for channel in self.guild.text_channels:
            self.channel_info = {}
            self.channel_info['name'] = channel.name
            self.channel_info['object'] = channel
            
            self.channels.append(self.channel_info)
        
        for game in self.games:
            self.channel_name = game['away'] + '-at-' + game['home']
            self.channel_name = self.channel_name.lower().replace(" ", "-")
            
            for channel in self.channels:
                self.logger.error('channel[name]: '+channel['name'])
                self.logger.error('self.channel_name.lower(): '+self.channel_name.lower())
                if self.channel_name.lower() == channel['name']:
                    print('trying to delete ' + channel['name'])
                    try:
                        await channel['object'].delete()
                        
                    except Exception as e:
                        self.logger.critical(e)
                        traceback.print_exc()
        
        self.get_games()

    async def create_game_threads(self):
        self.guild = self.bot.get_guild(self.server_id)
        self.category = self.bot.get_channel(self.category_id)
        
        self.channels = []
        for channel in self.guild.text_channels:
            self.channels.append(channel.name)

        for game in self.games:
            if (datetime.datetime.now() + datetime.timedelta(hours=2)) > game['time']:
                self.channel_name = game['away'] + '-at-' + game['home']
                self.channel_name = self.channel_name.lower().replace(" ", "-")
                
                if self.channel_name not in self.channels:
                    print('creating game channel for ' + self.channel_name)
                    self.channel = await self.guild.create_text_channel(self.channel_name, category=self.category)
                else:
                    print('channel already created for ' + self.channel_name)

def setup(bot):
    bot.add_cog(game_channels(bot))
