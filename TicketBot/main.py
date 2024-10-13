#Import
import time
startupTime_start = time.time()
import asyncio
import datetime
import discord
import json
import jsonschema
import os
import platform
import psutil
import sentry_sdk
import signal
import sys
import sqlite3
import random
from CustomModules.app_translation import Translator as CustomTranslator
from CustomModules.ticket import TicketHTML as TicketSystem
from CustomModules import log_handler
from dotenv import load_dotenv
from typing import Optional, Any
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile

discord.VoiceClient.warn_nacl = False
load_dotenv()
APP_FOLDER_NAME = 'ticketbot'
BOT_NAME = 'Ticketbot'
os.makedirs(f'{APP_FOLDER_NAME}//Logs', exist_ok=True)
os.makedirs(f'{APP_FOLDER_NAME}//Buffer', exist_ok=True)
LOG_FOLDER = f'{APP_FOLDER_NAME}//Logs//'
BUFFER_FOLDER = f'{APP_FOLDER_NAME}//Buffer//'
ACTIVITY_FILE = f'{APP_FOLDER_NAME}//activity.json'
SQL_FILE = os.path.join(APP_FOLDER_NAME, f'{APP_FOLDER_NAME}.db')
BOT_VERSION = "1.0.0"
FOOTER_TEXT = 'Ticketbot'
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production',
    release=f'{BOT_NAME}@{BOT_VERSION}'
)

TOKEN = os.getenv('TOKEN')
OWNERID = os.getenv('OWNER_ID')
LOG_LEVEL = os.getenv('LOG_LEVEL')

log_manager = log_handler.LogManager(LOG_FOLDER, BOT_NAME, LOG_LEVEL)
discord_logger = log_manager.get_logger('discord')
program_logger = log_manager.get_logger('Program')
program_logger.info('Starting System...')

class JSONValidator:
    schema = {
        "type" : "object",
        "properties" : {
            "activity_type" : {
                "type" : "string",
                "enum" : ["Playing", "Streaming", "Listening", "Watching", "Competing"]
            },
            "activity_title" : {"type" : "string"},
            "activity_url" : {"type" : "string"},
            "status" : {
                "type" : "string",
                "enum" : ["online", "idle", "dnd", "invisible"]
            },
        },
    }

    default_content = {
        "activity_type": "Playing",
        "activity_title": "Ticketsystem",
        "activity_url": "https://github.com/Zaross/TicketBot",
        "status": "online"
    }

    def __init__(self, file_path):
        self.file_path = file_path

    def validate_and_fix_json(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                try:
                    data = json.load(file)
                    jsonschema.validate(instance=data, schema=self.schema)
                except (jsonschema.exceptions.ValidationError, json.decoder.JSONDecodeError) as e:
                    program_logger.error(f'ValidationError: {e}')
                    self.write_default_content()
        else:
            self.write_default_content()

    def write_default_content(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.default_content, file, indent=4)
validator = JSONValidator(ACTIVITY_FILE)
validator.validate_and_fix_json()


class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()
        intents.guild_messages = True
        intents.members = True

        super().__init__(owner_id = OWNERID,
                              intents = intents,
                              status = discord.Status.invisible,
                              auto_reconnect = True
                        )
        self.synced = False
        self.initialized = False


    class Presence():
        @staticmethod
        def get_activity() -> discord.Activity:
            with open(ACTIVITY_FILE) as f:
                data = json.load(f)
                activity_type = data['activity_type']
                activity_title = data['activity_title']
                activity_url = data['activity_url']
            if activity_type == 'Playing':
                return discord.Game(name=activity_title)
            elif activity_type == 'Streaming':
                return discord.Streaming(name=activity_title, url=activity_url)
            elif activity_type == 'Listening':
                return discord.Activity(type=discord.ActivityType.listening, name=activity_title)
            elif activity_type == 'Watching':
                return discord.Activity(type=discord.ActivityType.watching, name=activity_title)
            elif activity_type == 'Competing':
                return discord.Activity(type=discord.ActivityType.competing, name=activity_title)

        @staticmethod
        def get_status() -> discord.Status:
            with open(ACTIVITY_FILE) as f:
                data = json.load(f)
                status = data['status']
            if status == 'online':
                return discord.Status.online
            elif status == 'idle':
                return discord.Status.idle
            elif status == 'dnd':
                return discord.Status.dnd
            elif status == 'invisible':
                return discord.Status.invisible
            
    async def setup_database(self):
         c.executescript('''
         CREATE TABLE IF NOT EXISTS "TICKET_SYSTEM" (
            "ID"	        INTEGER,
            "GUILD_ID"	    INTEGER NOT NULL,
            "CHANNEL"	    INTEGER NOT NULL,
            "EMBED_ID"      INTEGER,
            "SUPPORT_ROLE"  INTEGER,
            PRIMARY KEY("ID" AUTOINCREMENT)
         );
         CREATE TABLE IF NOT EXISTS "CREATED_TICKETS" (
            "ID"            INTEGER,
            "USER_ID"       INTEGER NOT NULL,
            "CHANNEL_ID"    INTEGER NOT NULL,
            "GUILD_ID"      INTEGER NOT NULL,
            "CATEGORY"      TEXT NOT NULL,
            PRIMARY KEY("ID" AUTOINCREMENT)            
        )
         ''')
         
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            class AddUserModal(discord.ui.Modal):
                def __init__(self, channel):
                    super().__init__(title="Add user to ticket")
                    self.channel = channel

                    self.user_id_input = discord.ui.TextInput(
                        label='User-ID',
                        placeholder='User-ID',
                        min_length=17,
                        max_length=21
                    )
                    self.add_item(self.user_id_input)
                
                async def on_submit(self, interaction: discord.Interaction):
                    user = self.user_id_input.value
                    try:
                        user = await Functions.get_or_fetch('user', int(user))
                        await self.channel.set_permissions(user, read_messages=True, send_messages=True, read_message_history=True)
                        await interaction.response.send_message(f'{user.mention} has been added to the ticket.', ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f'Error while adding {user.mention}: {e}', ephemeral=True)
                        
            class RemoveUserModal(discord.ui.Modal):
                def __init__(self, channel):
                    super().__init__(title="Remove user from the ticket")
                    self.channel = channel

                    self.user_id_input = discord.ui.TextInput(
                        label='User-ID',
                        placeholder='User-ID',
                        min_length=17,
                        max_length=21
                    )
                    self.add_item(self.user_id_input)
                
                async def on_submit(self, interaction: discord.Interaction):
                    user = self.user_id_input.value
                    try:
                        user = await Functions.get_or_fetch('user', int(user))
                        if user == interaction.user:
                            await interaction.response.send_message(f'You cant remove yourself.', ephemeral=True)
                            return
                        await self.channel.set_permissions(user, read_messages=False, send_messages=False, read_message_history=False)
                        await interaction.response.send_message(f'{user.mention} wurde vom Ticket entfernt.', ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f'Error while adding {user.mention} to the ticket: {e}', ephemeral=True)

            class TicketModal(discord.ui.Modal):
                def __init__(self, category, user):
                    super().__init__(title='Create a Ticket')
                    self.category = category
                    self.user = user

                    self.title_input = discord.ui.TextInput(
                        label='Titel',
                        placeholder='Titel of the Ticket'
                    )
                    self.add_item(self.title_input)

                    self.description_input = discord.ui.TextInput(
                        label='Description',
                        placeholder='Describe the Ticket',
                        style=discord.TextStyle.paragraph
                    )
                    self.add_item(self.description_input)

                async def on_submit(self, interaction: discord.Interaction):
                    title = self.title_input.value
                    description = self.description_input.value
                    category = discord.utils.get(interaction.guild.categories, name='Ticket-Support')

                    if category is None:
                        category = await interaction.guild.create_category('Ticket-Support')

                    overwrites = {
                        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                        self.user: discord.PermissionOverwrite(read_messages=True)
                    }


                    channel_name = f"⚠ ticket-{self.user.name}-{random.randint(1, 9999)}"
                    ticket_channel = await interaction.guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
                    
                    ticket_embed = discord.Embed(
                       title=title,
                       description=description,
                       color=discord.Color.blue(),
                       timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    ticket_embed.set_footer(text=f"Ticket created by {self.user}", icon_url=self.user.avatar.url if self.user.avatar else '')

                    admin_embed = discord.Embed(
                        title="Admincommands",
                        description="These are the admin commands for the ticket system.",
                        color=discord.Color.dark_green(),
                        timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    admin_embed.set_footer(text=FOOTER_TEXT, icon_url=bot.user.avatar.url if bot.user.avatar else '')

                    close_button = discord.ui.Button(label="✅ Close", style=discord.ButtonStyle.blurple, custom_id="close_ticket")
                    add_button = discord.ui.Button(label="➕ Add", style=discord.ButtonStyle.green, custom_id="add_ticket")
                    remove_button = discord.ui.Button(label="➖ Remove", style=discord.ButtonStyle.red, custom_id="remove_ticket")
                
                    admin_view = discord.ui.View()
                    admin_view.add_item(close_button)
                    admin_view.add_item(add_button)
                    admin_view.add_item(remove_button)
                    

                    await ticket_channel.send(embed=admin_embed, view=admin_view)
                    await ticket_channel.send(embed=ticket_embed)
                    try:
                        c.execute('INSERT INTO CREATED_TICKETS (USER_ID, CHANNEL_ID, GUILD_ID, CATEGORY) VALUES (?, ?, ?, ?)', (self.user.id, ticket_channel.id, interaction.guild.id, self.category))
                        conn.commit()
                        program_logger.debug(f'Ticket was succesfully created ({self.user.id}, {ticket_channel.id}, {interaction.guild.id}, {self.category}).')
                    except Exception as e:
                        program_logger.error(f'Error while inserting in the database: {e}')
                    await interaction.response.send_message(f'Your ticket was succesfully created: {ticket_channel.mention}', ephemeral=True)

            class TicketDropdown(discord.ui.Select):
                def __init__(self):
                    options = [
                        discord.SelectOption(label="Discord", description="For general help in the Discord"),
                        discord.SelectOption(label="Report", description="Report a user on the Discord"),
                        discord.SelectOption(label="Support", description="For technical assistance"),
                        discord.SelectOption(label="Bug", description="If you have found a bug"),
                        discord.SelectOption(label="Feedback", description="If you have feedback to the Discord"),
                        discord.SelectOption(label="Other", description="For everything else"),
                    ]
                    super().__init__(placeholder="Select a ticket topic.", options=options, min_values=1, max_values=1, custom_id="support_menu")

                async def callback(self, interaction: discord.Interaction):
                    category = self.values[0]
                    modal = TicketModal(category, interaction.user)
                    await interaction.response.send_modal(modal)

            class TicketDropdownView(discord.ui.View):
                def __init__(self):
                    super().__init__()
                    self.add_item(TicketDropdown())
                    if not self.initialized:
                        return

            if interaction.data and interaction.data.get('component_type') == 3: #3 ist Dropdown
                button_id = interaction.data.get('custom_id')
                if button_id == ("support_menu"):
                    selected_value = interaction.data.get('values', [None])[0]
                    program_logger.debug(f"Support Menu gewählt: {selected_value}")
                    category = selected_value
                    modal = TicketModal(category, interaction.user)
                    await interaction.response.send_modal(modal)
                        
            elif interaction.data and interaction.data.get('component_type') == 2: #2 ist Button
                button_id = interaction.data.get('custom_id')
                if button_id == ("close_ticket"):
                   channel = interaction.channel
                   c.execute('SELECT * FROM CREATED_TICKETS WHERE CHANNEL_ID = ?', (channel.id,))
                   data = c.fetchone()
                   if data is None:
                       return
                   await interaction.response.defer(ephemeral=True)
                   await TicketSystem.create_ticket(bot, interaction.channel.id, data[1])
                   for user in interaction.channel.members:
                       with open(f'{BUFFER_FOLDER}ticket-{interaction.channel.id}.html', 'r') as f:
                            if user == bot.user:
                                continue
                            if user.bot:
                                continue
                            try:
                                 await user.send(file=discord.File(f'{BUFFER_FOLDER}ticket-{interaction.channel.id}.html'))
                            except Exception as e:
                                program_logger.error(f'Fehler beim senden der Nachricht an {user}\n Fehler: {e}')   
                   await asyncio.sleep(5)
                   os.remove(f'{BUFFER_FOLDER}ticket-{interaction.channel.id}.html')
                   c.execute('DELETE FROM CREATED_TICKETS WHERE CHANNEL_ID = ?', (channel.id,))
                   conn.commit()
                   await channel.delete()
                   
                elif button_id == ("add_ticket"):
                    channel = interaction.channel
                    modal = AddUserModal(channel)
                    await interaction.response.send_modal(modal)
                elif button_id == ("remove_ticket"):
                    channel = interaction.channel
                    modal = RemoveUserModal(channel)
                    await interaction.response.send_modal(modal)


    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        options = interaction.data.get("options")
        option_values = ""
        if options:
            for option in options:
                option_values += f"{option['name']}: {option['value']}"
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'This command is on cooldown.\nTime left: `{str(datetime.timedelta(seconds=int(error.retry_after)))}`', ephemeral=True)
        else:
            try:
                try:
                    await interaction.response.send_message(f"Error! Try again.", ephemeral=True)
                except:
                    try:
                        await interaction.followup.send(f"Error! Try again.", ephemeral=True)
                    except:
                        pass
            except discord.Forbidden:
                try:
                    await interaction.followup.send(f"{error}\n\n{option_values}", ephemeral=True)
                except discord.NotFound:
                    try:
                        await interaction.response.send_message(f"{error}\n\n{option_values}", ephemeral=True)
                    except discord.NotFound:
                        pass
                except Exception as e:
                    discord_logger.warning(f"Unexpected error while sending message: {e}")
            finally:
                try:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) @ {interaction.guild.name} ({interaction.guild.id}) with Language {interaction.locale[1]}")
                except AttributeError:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) with Language {interaction.locale[1]}")
                sentry_sdk.capture_exception(error)

    async def on_guild_join(self, guild):
        if not self.synced:
            return
        discord_logger.info(f'I joined {guild}. (ID: {guild.id})')

    async def on_message(self, message):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'Commands:\n'
                                       'help - Shows this message\n'
                                       'log - Get the log\n'
                                       'activity - Set the activity of the bot\n'
                                       'status - Set the status of the bot\n'
                                       'shutdown - Shutdown the bot\n'
                                       '```')

        if message.guild is None and message.author.id == int(OWNERID):
            args = message.content.split(' ')
            program_logger.debug(args)
            command, *args = args
            if command == 'help':
                await __wrong_selection()
                return
            elif command == 'log':
                await Owner.log(message, args)
                return
            elif command == 'activity':
                await Owner.activity(message, args)
                return
            elif command == 'status':
                await Owner.status(message, args)
                return
            elif command == 'shutdown':
                await Owner.shutdown(message)
                return
            else:
                await __wrong_selection()

    async def on_guild_remove(self, guild):
        if not self.synced:
            return
        program_logger.info(f'I got kicked from {guild}. (ID: {guild.id})')

    async def setup_hook(self):
        global owner, shutdown, conn, c
        shutdown = False
        try:
            conn = sqlite3.connect(SQL_FILE)
            c = conn.cursor()
            await self.setup_database()
            owner = await self.fetch_user(OWNERID)
            if owner is None:
                program_logger.critical(f"Invalid ownerID: {OWNERID}")
                sys.exit(f"Invalid ownerID: {OWNERID}")
        except discord.HTTPException as e:
            program_logger.critical(f"Error fetching owner user: {e}")
            sys.exit(f"Error fetching owner user: {e}")
        discord_logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        discord_logger.info('Syncing...')
        await tree.set_translator(CustomTranslator())
        await tree.sync()
        discord_logger.info('Synced.')
        self.synced = True

    async def on_ready(self):
        await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
        if self.initialized:
            return
        global start_time
        start_time = datetime.datetime.now(datetime.UTC)
        program_logger.info(f"Initialization completed in {time.time() - startupTime_start} seconds.")
        self.initialized = True
        
bot = aclient()
tree = discord.app_commands.CommandTree(bot)
tree.on_error = bot.on_app_command_error

class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        program_logger.info('Received signal to shutdown...')
        bot.loop.create_task(Owner.shutdown(owner))

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Functions():
    def format_seconds(seconds):
        years, remainder = divmod(seconds, 31536000)
        days, remainder = divmod(remainder, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if years:
            parts.append(f"{years}y")
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds:
            parts.append(f"{seconds}s")

        return " ".join(parts)

    async def get_or_fetch(item: str, item_id: int) -> Optional[Any]:
        """
        Attempts to retrieve an object using the 'get_<item>' method of the bot class, and
        if not found, attempts to retrieve it using the 'fetch_<item>' method.

        :param item: Name of the object to retrieve
        :param item_id: ID of the object to retrieve
        :return: Object if found, else None
        :raises AttributeError: If the required methods are not found in the bot class
        """
        get_method_name = f'get_{item}'
        fetch_method_name = f'fetch_{item}'

        get_method = getattr(bot, get_method_name, None)
        fetch_method = getattr(bot, fetch_method_name, None)

        if get_method is None or fetch_method is None:
            raise AttributeError(f"Methods {get_method_name} or {fetch_method_name} not found on bot object.")

        item_object = get_method(item_id)
        if item_object is None:
            try:
                item_object = await fetch_method(item_id)
            except discord.NotFound:
                pass
        return item_object

class Owner():
    async def log(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'log [current/folder/lines] (Replace lines with a positive number, if you only want lines.) - Get the log\n'
                                       '```')
        if args == []:
            await __wrong_selection()
            return
        if args[0] == 'current':
            try:
                await message.channel.send(file=discord.File(f'{LOG_FOLDER}{BOT_NAME}.log'))
            except discord.HTTPException as err:
                if err.status == 413:
                    with ZipFile(f'{BUFFER_FOLDER}Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                        f.write(f'{LOG_FOLDER}{BOT_NAME}.log')
                    try:
                        await message.channel.send(file=discord.File(f'{BUFFER_FOLDER}Logs.zip'))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await message.channel.send("The log is too big to be sent directly.\nYou have to look at the log in your server (VPS).")
                    os.remove(f'{BUFFER_FOLDER}Logs.zip')
                    return
        elif args[0] == 'folder':
            if os.path.exists(f'{BUFFER_FOLDER}Logs.zip'):
                os.remove(f'{BUFFER_FOLDER}Logs.zip')
            with ZipFile(f'{BUFFER_FOLDER}Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                for file in os.listdir(LOG_FOLDER):
                    if file.endswith(".zip"):
                        continue
                    f.write(f'{LOG_FOLDER}{file}')
            try:
                await message.channel.send(file=discord.File(f'{BUFFER_FOLDER}Logs.zip'))
            except discord.HTTPException as err:
                if err.status == 413:
                    await message.channel.send("The folder is too big to be sent directly.\nPlease get the current file or the last X lines.")
            os.remove(f'{BUFFER_FOLDER}Logs.zip')
            return
        else:
            try:
                if int(args[0]) < 1:
                    await __wrong_selection()
                    return
                else:
                    lines = int(args[0])
            except ValueError:
                await __wrong_selection()
                return
            with open(f'{LOG_FOLDER}{BOT_NAME}.log', 'r', encoding='utf8') as f:
                with open(f'{BUFFER_FOLDER}log-lines.txt', 'w', encoding='utf8') as f2:
                    count = 0
                    for line in (f.readlines()[-lines:]):
                        f2.write(line)
                        count += 1
            await message.channel.send(content=f'Here are the last {count} lines of the current logfile:', file=discord.File(f'{BUFFER_FOLDER}log-lines.txt'))
            if os.path.exists(f'{BUFFER_FOLDER}log-lines.txt'):
                os.remove(f'{BUFFER_FOLDER}log-lines.txt')
            return

    async def activity(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'activity [playing/streaming/listening/watching/competing] [title] (url) - Set the activity of the bot\n'
                                       '```')
        def isURL(zeichenkette):
            try:
                ergebnis = urlparse(zeichenkette)
                return all([ergebnis.scheme, ergebnis.netloc])
            except:
                return False

        def remove_and_save(liste):
            if liste and isURL(liste[-1]):
                return liste.pop()
            else:
                return None

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        url = remove_and_save(args[1:])
        title = ' '.join(args[1:])
        program_logger.debug(title)
        program_logger.debug(url)
        with open(ACTIVITY_FILE, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'playing':
            data['activity_type'] = 'Playing'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'streaming':
            data['activity_type'] = 'Streaming'
            data['activity_title'] = title
            data['activity_url'] = url
        elif action == 'listening':
            data['activity_type'] = 'Listening'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'watching':
            data['activity_type'] = 'Watching'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'competing':
            data['activity_type'] = 'Competing'
            data['activity_title'] = title
            data['activity_url'] = ''
        else:
            await __wrong_selection()
            return
        with open(ACTIVITY_FILE, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Activity set to {action} {title}{" " + url if url else ""}.')

    async def status(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'status [online/idle/dnd/invisible] - Set the status of the bot\n'
                                       '```')

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        with open(ACTIVITY_FILE, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'online':
            data['status'] = 'online'
        elif action == 'idle':
            data['status'] = 'idle'
        elif action == 'dnd':
            data['status'] = 'dnd'
        elif action == 'invisible':
            data['status'] = 'invisible'
        else:
            await __wrong_selection()
            return
        with open(ACTIVITY_FILE, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Status set to {action}.')

    async def shutdown(message):
        global shutdown
        _message = 'Engine powering down...'
        program_logger.info(_message)
        try:
            await message.channel.send(_message)
        except:
            await owner.send(_message)
        await bot.change_presence(status=discord.Status.invisible)
        shutdown = True

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        await bot.close()

@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
@discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! \nCommand execution time: `{int(ping)}ms`\nPing to gateway: `{int(bot.latency * 1000)}ms`')

@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    member_count = sum(guild.member_count for guild in bot.guilds)

    embed = discord.Embed(
        title=f"Informationen about {bot.user.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else '')

    embed.add_field(name="Created at", value=bot.user.created_at.strftime("%d.%m.%Y, %H:%M:%S"), inline=True)
    embed.add_field(name="Bot-Version", value=BOT_VERSION, inline=True)
    embed.add_field(name="Uptime", value=str(datetime.timedelta(seconds=int((datetime.datetime.now(datetime.UTC) - start_time).total_seconds()))), inline=True)
    embed.add_field(name="Bot-Owner", value=f"<@!{OWNERID}>", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Server", value=f"{len(bot.guilds)}", inline=True)
    embed.add_field(name="Member count", value=str(member_count), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Shards", value=f"{bot.shard_count}", inline=True)
    embed.add_field(name="Shard ID", value=f"{interaction.guild.shard_id if interaction.guild else 'N/A'}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Python-Version", value=f"{platform.python_version()}", inline=True)
    embed.add_field(name="discord.py-Version", value=f"{discord.__version__}", inline=True)
    embed.add_field(name="Sentry-Version", value=f"{sentry_sdk.consts.VERSION}", inline=True)
    embed.add_field(name="Invite", value=f"[Invite me](https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot)", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    if interaction.user.id == int(OWNERID):
        process = psutil.Process(os.getpid())
        cpu_usage = process.cpu_percent()
        ram_usage = round(process.memory_percent(), 2)
        ram_real = round(process.memory_info().rss / (1024 ** 2), 2)
        embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{ram_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{ram_real} MB", inline=True)
    await interaction.response.send_message(embed=embed)

@tree.command(name = 'change_nickname', description = 'Change the nickname of the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(manage_nicknames = True)
@discord.app_commands.describe(nick='New nickname for me.')
async def self(interaction: discord.Interaction, nick: str):
    await interaction.guild.me.edit(nick=nick)
    await interaction.response.send_message(f'My new nickname is now **{nick}**.', ephemeral=True)
    

class TicketDropdown(discord.ui.Select):
        def __init__(self):
            options = [
                 discord.SelectOption(label="Discord", description="For general help in the Discord"),
                 discord.SelectOption(label="Report", description="Report a user on the Discord"),
                 discord.SelectOption(label="Support", description="For technical assistance"),
                 discord.SelectOption(label="Bug", description="If you have found a bug"),
                 discord.SelectOption(label="Feedback", description="If you have feedback to the Discord"),
                 discord.SelectOption(label="Other", description="For everything else"),
            ]
            super().__init__(placeholder="Select a ticket topic.", options=options, min_values=1, max_values=1, custom_id="support_menu")

        async def callback(self, interaction: discord.Interaction):
            category = self.values[0]
            modal = TicketModal(category, interaction.user)
            await interaction.response.send_modal(modal)

class TicketSystemView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.add_item(TicketDropdown())

class TicketModal(discord.ui.Modal):
        def __init__(self, category, user):
            super().__init__(title='Create a Ticket')
            self.category = category
            self.user = user

            self.title_input = discord.ui.TextInput(
                label='Titel',
                placeholder='Titel of the Ticket'
            )
            self.add_item(self.title_input)

            self.description_input = discord.ui.TextInput(
                label='Description',
                placeholder='Describe the Ticket',
                style=discord.TextStyle.paragraph
            )
            self.add_item(self.description_input)

        async def on_submit(self, interaction: discord.Interaction):
            title = self.title_input.value
            description = self.description_input.value
            category = discord.utils.get(interaction.guild.categories, name='Ticket-Support')

            if category is None:
                category = await interaction.guild.create_category('Ticket-Support')
            
            c.execute('SELECT * FROM TICKET_SYSTEM WHERE GUILD_ID = ?', (interaction.guild_id,))
            ticketsystem = c.fetchone()
            if ticketsystem is None:
                return
            admin_role = Functions.get_or_fetch('role', ticketsystem[4])
            if admin_role is None:
                return

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                self.user: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True, manage_channels=True) 
            }

            channel_name = f"⚠ ticket-{self.user.name}-{random.randint(1, 9999)}"
            ticket_channel = await interaction.guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

            ticket_embed = discord.Embed(
               title=title,
               description=description,
               color=discord.Color.blue(),
               timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            ticket_embed.set_footer(text=f"Ticket created by {self.user}", icon_url=self.user.avatar.url if self.user.avatar else '')

            admin_embed = discord.Embed(
                title="Admincommands",
                description="These are the admin commands for the ticket system.",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            admin_embed.set_footer(text=FOOTER_TEXT, icon_url=bot.user.avatar.url if bot.user.avatar else '')

            close_button = discord.ui.Button(label="✅ Close", style=discord.ButtonStyle.blurple, custom_id="close_ticket")
            add_button = discord.ui.Button(label="➕ Add", style=discord.ButtonStyle.green, custom_id="add_ticket")
            remove_button = discord.ui.Button(label="➖ Remove", style=discord.ButtonStyle.red, custom_id="remove_ticket")
            
            admin_view = discord.ui.View()
            admin_view.add_item(close_button)
            admin_view.add_item(add_button)
            admin_view.add_item(remove_button)

            try:
                c.execute('INSERT INTO CREATED_TICKETS (USER_ID, CHANNEL_ID, GUILD_ID, CATEGORY) VALUES (?, ?, ?, ?)', (self.user.id, ticket_channel.id, interaction.guild.id, self.category))
                conn.commit()
                program_logger.debug(f'Ticket was succesfully created ({self.user.id}, {ticket_channel.id}, {interaction.guild.id}, {self.category}).')
            except Exception as e:
                program_logger.error(f'Error while inserting in the database: {e}')
            await ticket_channel.send(embed=admin_embed, view=admin_view)
            await ticket_channel.send(embed=ticket_embed)
            await interaction.response.send_message(f'Your ticket was succesfully created: {ticket_channel.mention}', ephemeral=True)

@tree.command(name='create_ticketsystem', description='creates the ticketsystem.')
@discord.app_commands.checks.cooldown(1, 2, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.describe(channel='In which channel the ticketsystem should be.')
async def self(interaction: discord.Interaction, channel: discord.TextChannel, supportrole: discord.Role):
    bot_avatar = bot.user.avatar.url if bot.user.avatar else ''
    ticketsystem_embed = discord.Embed(
    title='Ticket System',
    description='You can create a ticket here. Select a category below.',
    color=discord.Color.gold(),
    )
    ticketsystem_embed.set_footer(text='Ticketbot', icon_url=bot_avatar)

    c.execute('SELECT * FROM TICKET_SYSTEM WHERE GUILD_ID = ?', (interaction.guild_id,))
    ticketsystem = c.fetchone()
    if ticketsystem:
        emb = discord.Embed(
            title='Ticketsystem',
            description='A ticket system already exists on this server. If you want to change it, react to the tick at the end of the message',
            color=discord.Color.dark_gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
        emb.add_field(name='Channel:', value=f'<#{ticketsystem[2]}>', inline=False)
        emb.set_footer(text=FOOTER_TEXT, icon_url=bot_avatar)
        msg = await interaction.channel.send(embed=emb)
        await msg.add_reaction('✅')
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) == '✅' and reaction.message.id == msg.id
        try:
            reaction, user = await interaction.client.wait_for('reaction_add', timeout=60.0, check=check)
            if reaction.emoji == '✅':
                c.execute('UPDATE TICKET_SYSTEM SET CHANNEL = ?, SUPPORT_ROLE = ? WHERE GUILD_ID = ?', (channel.id, supportrole.id ,interaction.guild_id))
                conn.commit()
                await interaction.channel.send('✅ Ticketchannel changed succesfully.')
                await msg.delete()
                await channel.send(embed=ticketsystem_embed, view=TicketSystemView())
        except asyncio.TimeoutError:
            await interaction.channel.send('❌ Time is up.')
    else:
        c.execute('UPDATE TICKET_SYSTEM SET CHANNEL = ?, SUPPORT_ROLE = ? WHERE GUILD_ID = ?', (channel.id, supportrole.id ,interaction.guild_id))
        conn.commit()
        await channel.send(embed=ticketsystem_embed, view=TicketSystemView())
        await interaction.response.send_message(content=f'Ticketsystem wurde erfolgreich erstellt.', ephemeral=True)

if __name__ == '__main__':
    if sys.version_info < (3, 11):
        program_logger.critical('Python 3.11 or higher is required.')
        sys.exit(1)
    if not TOKEN:
        program_logger.critical('Missing token. Please check your .env file.')
        sys.exit()
    else:
        SignalHandler()
        try:
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            program_logger.critical('Invalid token. Please check your .env file.')
            sys.exit()
        except asyncio.CancelledError:
            if shutdown:
                pass
