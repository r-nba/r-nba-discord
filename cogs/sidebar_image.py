import requests
from PIL import Image
from io import BytesIO
import praw
import os
from db import SidebarImages, Base, Session, engine
import datetime
import config
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

import discord
from discord.ext import commands


class sidebar_image:

    def __init__(self, bot):
        self.bot = bot

        # Creates SQL Tables
        Base.metadata.create_all(engine,checkfirst=True)

        self.reddit = praw.Reddit(
            client_id = config.client_id,
            client_secret = config.client_secret,
            refresh_token = config.refresh_token,
            user_agent='r/nba sidebar bot v0.0.1 by /u/brexbre')

        self.load_settings()

    def load_settings(self):
        self.subreddit = self.reddit.subreddit('nbadev')
        self.server_id = 229123661624377345

        self.image_reactions = ['\U0001F4F7', '\u270F', '\U0001F4AF', '\u2705','\U0001F6AB'] # Emoji Python Codes
        self.update_content = []
        self.active_updates = []
        self.image_file = ''

    def image_resize(self, url):

        self.response = requests.get(url)
        self.image = Image.open(BytesIO(self.response.content))

        if self.image.size > (312,468):
            coord = requests.get('https://api.imagga.com/v1/croppings?url=' + url + '&resolution=312x468&no_scaling=0',
                             auth=(config.img_key, config.img_secret)).json()['results'][0]['croppings'][0]

            self.image = self.image.crop((coord['x1'], coord['y1'], coord['x2'], coord['y2']))
            self.image.thumbnail((312,468), Image.ANTIALIAS)
            self.image.save('image.png')
        else:
            self.image.thumbnail((312,468), Image.ANTIALIAS)
            self.image.save('image.png')

        return self.image

    def embed_message(self, title, description, caption, stats):

        self.embed = discord.Embed(title=title, description=description, color=16753920)
        self.embed.add_field(name="Sidebar caption:", value=caption, inline=False)
        self.embed.add_field(name="Sidebar stats:", value=stats, inline=False)
        self.embed.add_field(name="To edit or confirm your changes", value=":camera: to edit the image\n:pencil2: to edit the caption\n:100: to edit the stats\n:white_check_mark:  to confirm your final changes\n:no_entry_sign: to cancel the update", inline=False)

        return self.embed

    @commands.command(name='image', aliases=['img'])
    @commands.guild_only()
    async def image(self, ctx, url, cap, stats):
        if ctx.guild.id == 229123661624377345:
            await ctx.message.delete()

            self.image_resize(url)
            self.embed_message('Sidebar Image Update','Are you sure you want to set this as the sidebar?',cap,stats.upper())

            with open('image.png', 'rb') as f:
                self.update = await ctx.send(embed=self.embed, file=discord.File(f))

            for emoji in self.image_reactions:
                await self.update.add_reaction(emoji)

            self.update_content = [self.update.id,url,cap,stats.upper(),self.update]
            self.active_updates.append(self.update.id)
            self.image_file = self.image

    async def on_reaction_add(self, reaction, user):

        author = reaction.message.author

        if reaction.message.id in self.active_updates and reaction.emoji in self.image_reactions and user != self.bot.user:

            if reaction.emoji == '\U0001F4F7':
                await self.update_content[4].delete()
                self.new_url_info = await reaction.message.channel.send('Okay, what\'s the new image url?')

                def check(m):
                    return m.content.startswith('http') and m.author == user

                self.msg = await self.bot.wait_for('message', check=check)

                await self.new_url_info.delete()
                await self.msg.delete()

                self.image = self.image_resize(self.msg.content)
                self.embed = self.embed_message('Image has been changed','Are you sure you want to change the image to this?',self.update_content[2],self.update_content[3])

                with open('image.png', 'rb') as f:
                    self.new_url_msg = await self.msg.channel.send(embed=self.embed, file=discord.File(f))

                for emoji in self.image_reactions:
                    await self.new_url_msg.add_reaction(emoji)

                self.update_content = [self.new_url_msg.id,self.msg.content,self.update_content[2],self.update_content[3],self.new_url_msg]
                self.active_updates.append(self.new_url_msg.id)

            elif reaction.emoji == '\u270F':
                await self.update_content[4].delete()
                self.new_cap_info = await reaction.message.channel.send('Okay, what\'s the new caption?')

                def check(m):
                    return m.author == user

                self.msg = await self.bot.wait_for('message', check=check)

                await self.new_cap_info.delete()
                await self.msg.delete()

                self.image = self.image_resize(self.update_content[1])
                self.embed = self.embed_message('Caption has been changed','Are you sure you want to change the caption to this?',self.msg.content,self.update_content[3])

                with open('image.png', 'rb') as f:
                    self.new_cap_msg = await self.msg.channel.send(embed=self.embed, file=discord.File(f))

                for emoji in self.image_reactions:
                    await self.new_cap_msg.add_reaction(emoji)

                self.update_content = [self.new_cap_msg.id,self.update_content[1],self.msg.content,self.update_content[3],self.new_cap_msg]
                self.active_updates.append(self.new_cap_msg.id)

            elif reaction.emoji == '\U0001F4AF':
                await self.update_content[4].delete()
                self.new_stats_info = await reaction.message.channel.send('Okay, what are the new stats?')

                def check(m):
                    self.content = m.content[0]
                    return self.content[0].isdigit() and m.author == user

                self.msg = await self.bot.wait_for('message', check=check)

                await self.new_stats_info.delete()
                await self.msg.delete()

                self.image = self.image_resize(self.update_content[1])
                self.embed = self.embed_message('Stats have been changed','Are you sure you want to change the stats to this?',self.update_content[2],self.msg.content.upper())

                with open('image.png', 'rb') as f:
                    self.new_stats_msg = await self.msg.channel.send(embed=self.embed, file=discord.File(f))

                for emoji in self.image_reactions:
                    await self.new_stats_msg.add_reaction(emoji)

                self.update_content = [self.new_stats_msg.id,self.update_content[1],self.update_content[2],self.msg.content.upper(),self.new_stats_msg]
                self.active_updates.append(self.new_stats_msg.id)

            elif reaction.emoji == '\u2705':
                await self.update_content[4].delete()
                self.new_confirm_info = await reaction.message.channel.send('Okay, updating now!')

                self.image = self.image_resize(self.update_content[1])
                self.embed = discord.Embed(title='Sidebar Image Updated', description='[Click here to view your changes!](http://reddit.com/r/nba)', color=16753920)
                self.embed.add_field(name="Sidebar caption:", value=self.update_content[2], inline=False)
                self.embed.add_field(name="Sidebar stats:", value=self.update_content[3], inline=False)
                self.embed.add_field(name='Command Invoker', value=user.mention)

                #Update Sidebar Image Code

                stylesheet = self.subreddit.stylesheet
                stylesheet.upload('sb','image.png')

                # Update Sidebar Caption Code

                stylesheet = self.subreddit.wiki['config/stylesheet'].content_md
                lines = stylesheet.splitlines()

                if self.update_content[3] == 'none':
                    stats = []
                else:
                    stats = self.update_content[3].upper().split(' ')
                    stats = [" ".join(stats[i:i+2]) for i in range(0, len(stats), 2)]
                    offset = (4-len(stats))+1
                
                if stats:
                    for index,stat in enumerate(stats):
                        for i,line in enumerate(lines):
                            if line.startswith('.side a[href^="/stat'+str(index+offset)+'"]:before {'):
                                lines[i] = '.side a[href^="/stat'+str(index+offset)+'"]:before { content: "'+stat+'"; }'

                for i,v in enumerate(lines):
                    # Caption
                    if v.startswith('.side .spacer:nth-of-type(1):before'):
                        lines[i+1] = '    content: "'+self.update_content[2]+'";'

                    # Hide/Show stat boxes
                    if v.startswith('.side a[href^="/stat1"] {'):
                        if len(stats) <= 3:
                            lines[i+1] = '    display: none;'
                        elif len(stats) > 3:
                            lines[i+1] = '    display: inline-block;'

                    if v.startswith('.side a[href^="/stat2"] {'):
                        if len(stats) <= 2:
                            lines[i+1] = '    display: none;'
                        elif len(stats) > 2:
                            lines[i+1] = '    display: inline-block;'

                    if v.startswith('.side a[href^="/stat3"] {'):
                        if len(stats) <= 1:
                            lines[i+1] = '    display: none;'
                        elif len(stats) > 1:
                            lines[i+1] = '    display: inline-block;'

                    if v.startswith('.side a[href^="/stat4"] {'):
                        if len(stats) <= 0:
                            lines[i+1] = '    display: none;'
                        elif len(stats) > 0:
                            lines[i+1] = '    display: inline-block;'

                sheet = ""
                for line in lines:
                    sheet+=(line+'\n')

                self.subreddit.stylesheet.update(sheet)

                await self.new_confirm_info.delete()

                with open('image.png', 'rb') as f:
                    self.final_msg = await reaction.message.channel.send(embed=self.embed, file=discord.File(f))

                # Archive Sidebar Code
                # Move image to archive folder and add timestamp
                #filename = 'archive/image'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'.png'
                #os.rename('image.png',filename)
                #Create a new SQL object
                sb = SidebarImages(stats=self.update_content[3], caption=self.update_content[2],mod=user.name)
                session = Session()
                session.add(sb)
                session.commit()
                session.close()

                self.update_content = [self.final_msg.id,self.update_content[1],self.update_content[2],self.update_content[3],self.final_msg]
                self.active_updates.append(self.final_msg.id)

            elif reaction.emoji == '\U0001F6AB':
                await self.update_content[4].delete()
                self.new_cancel_info = await reaction.message.channel.send('Okay, cancelling the update.')

                self.embed = discord.Embed(title='Sidebar Image Update Cancelled', description='Type !image to try again.', color=16753920)
                self.embed.add_field(name='Command Invoker', value=user.mention)

                await self.new_cancel_info.delete()

                self.cancel_msg = await reaction.message.channel.send(embed=self.embed)

                self.update_content = [self.cancel_msg.id,self.update_content[1],self.update_content[2],self.update_content[3],self.cancel_msg]
                self.active_updates.append(self.cancel_msg.id)

def setup(bot):
    bot.add_cog(sidebar_image(bot))
