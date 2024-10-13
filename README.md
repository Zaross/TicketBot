# 🎫 Discord Ticket Bot - Effortless Ticket Management for Your Server!

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/github/license/Zaross/TicketBot)](LICENSE)

### 📢 Welcome to the ultimate Discord Ticket Bot!
Say goodbye to chaotic support systems and hello to streamlined ticket management on your server! This bot is designed to make your life easier, providing your community with a sleek, efficient way to open and manage tickets. Plus, with a beautifully generated HTML summary after every ticket closure, you’ll have all the information at your fingertips.

---

### 🚀 Features

- **Dropdown Menu for Ticket Categories** – Choose from predefined ticket categories with a simple, intuitive dropdown.
- **Automated HTML Ticket Summary** – Once a ticket is closed, the bot generates a detailed HTML summary, including all relevant information and chat history.
- **Quick Setup** – With just **one command** and **two arguments**, you can have the bot running and customized for your server.
- **Admin-Friendly Controls** – Built-in admin tools for managing tickets, adding/removing users, and closing tickets.
- **Discord.py Powered** – Built using the reliable and flexible [discord.py](https://discordpy.readthedocs.io/) library.
- **Docker Ready** – Easily deployable on your server or local machine with Docker.

---

### 🛠️ How It Works

1. **Setup**: Run the `/create_ticketsystem` command followed by your category and support role to get started.
2. **Ticket Creation**: Users can open tickets with predefined categories via a dropdown menu.
3. **Admin Commands**: Admins can close tickets, add or remove users from the ticket, and manage ticket settings.
4. **HTML Summary**: After closing a ticket, a detailed HTML file summarizing the ticket is sent, perfect for keeping records.

---

### 📄Example Ticket Workflow:

- A user opens a ticket in the "Support" category.
- All Admins which has the support role, get added to the ticket.
- Once the ticket is closed, an HTML file with all the information is generated and sent for future reference.

---

### 🔧 Built With

**discord.py** – The Discord API wrapper that makes everything possible.

**Docker** – For easy deployment and portability.

---

### 🖥️ Setup Guide

Setting up the bot is incredibly simple and takes just a few minutes.

### 1. Clone the Repository

```bash
git clone https://github.com/Zaross/Ticketbot.git
cd Ticketbot
```

### 2. Creating the .env

```bash
mv .env.template .env
nano .env
```

Fill out the .env with your data.

### 3. Starting the bot

```bash
docker compose up --build -d
```

### 4. Bot is up and now switch to discord

If the bot is up and you want to setup the bot simple type:

`/create_ticketsystem <channel> <role>`

You are finished if the bot give you positive feedback.

---

### 🎯 Why You Should Use This Bot

**Simple Setup:** With minimal configuration, your server will be fully equipped with an advanced ticketing system.
**Automated Record Keeping:** Never lose track of any tickets again, thanks to the automated HTML generation.
**Customizable Ticket Categories:** Make the bot your own by easily defining ticket categories that match your community’s needs.
**Efficient Support Workflow:** Streamline the support process for your admins and users alike with easy-to-use admin tools.

---

### 🧑‍💻 Contributing

Contributions are welcome! Feel free to submit issues and pull requests.
