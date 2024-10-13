from datetime import datetime
import os
import asyncio

class TicketHTML:
    def __init__(self):
        print("TicketHTML initialized")

    async def create_ticket(bot, channel_id, creator):
                messages = []
                creatorname = await bot.fetch_user(creator)
                creator = creatorname.name
                channel = bot.get_channel(channel_id)
                ticket_id = channel_id
                ticket_name = channel.name
                creator_name = creator
                ticket_status = "Closed"
                closing_date = datetime.now().strftime("%d.%m.%Y | %H:%M:%S")

                async for message in channel.history(limit=None):
                    avatar_url = getattr(message.author.avatar, 'url', None)
                    if message.author.bot:
                         continue
                    if message.attachments:
                        continue
                    if avatar_url is None:
                        avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"
                    if message.author.avatar is None:
                        messages.append(f"""
                        <div class="message">
                        <div class='message-header'>                
                            <img src='{avatar_url}'>
                            {message.author.name}
                            {message.created_at.strftime('%d.%m.%Y - %H:%M')}
                        </div>
                            <p class="message-content">{message.content}</p>
                        </div>
                        """) 
                    else:
                        messages.append(f"""
                        <div class="message">
                        <div class='message-header'>                
                            <img src='{message.author.avatar.url}'>
                            {message.author.name}
                            {message.created_at.strftime('%d.%m.%Y - %H:%M')}
                        </div>
                            <p class="message-content">{message.content}</p>
                        </div>
                        """)
                        
                messages.reverse()
                
                messages = "".join(messages)

                html = f"""
                <!DOCTYPE html>
                <html lang="de">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Ticket #{ticket_id}</title>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
                
                        body {{
                            font-family: 'Roboto', sans-serif;
                            margin: 0;
                            padding: 0;
                            background-color: #313338;
                            color: #fff;
                            display: flex;
                            flex-direction: column;
                            min-height: 100vh;
                        }}
                
                        .header {{
                            position: fixed;
                            top: 0;
                            left: 0;
                            width: 100%;
                            background-color: #212121;
                            padding: 15px 30px;
                            z-index: 1000;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                            animation: slideInDown 0.6s ease-out;
                        }}
                
                        @keyframes slideInDown {{
                            from {{ transform: translateY(-100%); opacity: 0; }}
                            to {{ transform: translateY(0); opacity: 1; }}
                        }}
                
                        .header-left {{
                            display: flex;
                            align-items: center;
                        }}
                
                        .header img {{
                            width: 50px;
                            height: 50px;
                            margin-right: 15px;
                            transition: transform 0.3s ease;
                        }}
                
                        .header img:hover {{
                            transform: rotate(360deg);
                        }}
                
                        .header-text {{
                            font-size: 24px;
                            font-weight: 700;
                        }}
                
                        .ticket-id {{
                            font-size: 18px;
                            font-weight: 700;
                        }}
                
                        .content {{
                            padding: 100px 40px 40px 40px;
                            flex: 1;
                            animation: fadeIn 0.8s ease-in;
                        }}
                
                        @keyframes fadeIn {{
                            from {{ opacity: 0; }}
                            to {{ opacity: 1; }}
                        }}
                
                        .ticket-header {{
                            background-color: #444;
                            padding: 15px;
                            border-radius: 8px;
                            margin-bottom: 20px;
                            border-left: 4px solid #9900ff;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                        }}
                
                        .ticket-header h1 {{
                            margin: 0;
                        }}
                
                        .ticket-info h2 {{
                            margin-top: 0;
                        }}
                
                        .message {{
                            margin-bottom: 15px;
                            animation: bounceIn 0.6s ease;
                        }}
                
                        @keyframes bounceIn {{
                            from {{ transform: scale(0.8); opacity: 0; }}
                            to {{ transform: scale(1); opacity: 1; }}
                        }}
                
                        .message-header {{
                            display: flex;
                            align-items: center;
                            font-weight: bold;
                            margin-bottom: 10px;
                        }}
                
                        .message-header img {{
                            width: 50px;
                            height: 50px;
                            border-radius: 50%;
                            margin-right: 15px;
                            transition: transform 0.3s ease;
                        }}
                
                        .message-header img:hover {{
                            transform: scale(1.1);
                        }}
                
                        .message-content {{
                            background-color: #1b1b1b;
                            padding: 15px;
                            border-radius: 8px;
                            color: #fff;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                        }}
                
                        .footer {{
                            background-color: #212121;
                            padding: 15px 30px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            animation: slideInUp 0.6s ease-out;
                        }}
                
                        @keyframes slideInUp {{
                            from {{ transform: translateY(100%); opacity: 0; }}
                            to {{ transform: translateY(0); opacity: 1; }}
                        }}
                
                        .footer a {{
                            color: #fff;
                            text-decoration: none;
                            margin: 0 30px;
                            transition: color 0.3s ease;
                        }}
                
                        .footer a:hover {{
                            color: #07a66d;
                        }}
                
                        ::-webkit-scrollbar {{
                            width: 8px;
                        }}
                
                        ::-webkit-scrollbar-track {{
                            background: #1b1b1b;
                        }}
                
                        ::-webkit-scrollbar-thumb {{
                            background: #9900ff;
                            border-radius: 4px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="header-left">
                            <img src="https://cdn.discordapp.com/avatars/1244932312773431296/14777efbf888832a6566dd3eb6d96862.webp?size=4096" alt="Logo">
                            <span class="header-text">Ticketbot</span>
                        </div>
                        <div class="ticket-id">Ticket #{ticket_id}</div>
                    </div>
                
                    <div class="content">
                        <div class="ticket-header">
                            <h1>Ticket #{ticket_id}</h1>
                            <p>Closed at: {closing_date}</p>
                        </div>
                
                        <div class="ticket-info">
                            <h2>Ticket Informations</h2>
                            <p><strong>Ticket name:</strong> {ticket_name}</p>
                            <p><strong>Created by:</strong> {creator_name}</p>
                            <p><strong>Status:</strong> {ticket_status}</p>
                        </div>
                
                        <div class="ticket-messages">
                            <h2>Message history</h2>
                            {messages}
                        </div>
                    </div>
                
                    <div class="footer">
                        <a href="https://github.com/Zaross/Ticketbot" target="_blank">
                            <i class="fab fa-github"></i> Github
                        </a>
                    </div>
                </body>
                </html>
                """
                APP_FOLDER_NAME = 'Ticketbot'
                BUFFER_FOLDER = f'{APP_FOLDER_NAME}/Buffer/'
                ticket_path = f"{BUFFER_FOLDER}ticket-{channel_id}.html"
                with open(f"{ticket_path}", "w", encoding='utf-8') as file:
                    file.write(html)
                return f"{ticket_path}"
    
        

