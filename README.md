<div align="center" markdown>
<img src="https://github.com/iwatkot/affirmbot/assets/118521851/facdb0c2-2378-467d-9bce-0f42013195fa">

Completely free bot to automate the publication of user-suggested content in the Telegram channel.

<p align="center">
    <a href="#Overview">Overview</a> • 
    <a href="#Quick-Start">Quick Start</a> •
    <a href="#Step-by-step-guide">Step-by-step guide</a> • 
    <a href="#Custom-Templates">Custom templates</a> •
    <a href="#Entry-Types">Entry Types</a>
</p>
<p align="center">
    <a href="#Administration">Administration</a> •
    <a href="#How-to-use-the-bot">How to use the bot</a> •
    <a href="#Bugs-and-Feature-Requests">Bugs and Feature Requests</a> •
    <a href="#For-developers">For developers</a> •
    <a href="#Upcoming-Features">Upcoming Features</a>
</p>

![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/iwatkot/affirmbot)
![GitHub issues](https://img.shields.io/github/issues/iwatkot/affirmbot)
![Docker pulls](https://img.shields.io/docker/pulls/iwatkot/affirmbot)
[![Maintainability](https://api.codeclimate.com/v1/badges/b0be132e5bf9ec3fdb59/maintainability)](https://codeclimate.com/github/iwatkot/affirmbot/maintainability)

</div>

## Overview
This bot is designed to automate the publication of user-suggested content in the Telegram channel. It supports custom templates for users to fill in, accept and reject suggestions, and automatically publish them after approval.<br>
It's completely free and open-source, so you can host it yourself for your own needs without any restrictions, even for commercial purposes.<br>

## Quick Start
Long story short, you can run the bot with a single command (it will use default built-in templates):

```bash
docker run -e TOKEN="TELEGRAM_BOT_TOKEN" -e ADMINS="TELEGRAM_ID,TELEGRAM_ID" iwatkot/affirmbot
```

Or you can use your templates, in this case, you'll need to create a public GitHub repository with a `config.yml` file, containing your templates:

```bash
docker run -e TOKEN="TELEGRAM_BOT_TOKEN" -e ADMINS="TELEGRAM_ID,TELEGRAM_ID" -e CONFIG="github_username/repo_name" iwatkot/affirmbot
```

After the bot is started, remember to connect it to the channel where you want to publish the suggestions, you can learn how to do it in the [Channel](#Channel) section.<br>
If you ensured that the bot was added to the channel, you can add the environment variable `CHANNEL` with the channel ID to the `docker run` command. In this case, the bot will be connected to the channel from the start, but it won't check if it was added correctly.

```bash
docker run -e TOKEN="TELEGRAM_BOT_TOKEN" -e ADMINS="TELEGRAM_ID,TELEGRAM_ID" -e CHANNEL="CHANNEL_ID" iwatkot/affirmbot
```

Here's the full list of environment variables you can use:

|     Variable       |        Required         |                         Description                                             |
| :----------------: | :----------------------:|:------------------------------------------------------------------------------: |
|    TOKEN           |           ✅            | The token of your Telegram bot.                                                 |
|    ADMINS          |           ✅            | A list of admin Telegram IDs.                                                   |
|    CHANNEL         |           ❌            | The channel ID where the suggestions will be published.                         |
|    CONFIG          |           ❌            | The GitHub repository with the `config.yml` file.                               | 
|      ENV           |           ❌            | For developers only, if set to "DEV", the bot will run in the development mode. | 


## Step-by-step guide
If you're a rookie and don't know anything about Docker, GitHub, and all that stuff, this section is for you.

### Step 1: Create a Telegram bot
In this step, you need to create a Telegram bot and get its token. To do this, you need to talk to the [BotFather](https://t.me/botfather) and follow the instructions, it's very simple. After the bot is created, you will receive a token. Save it, you will need it later. Friendly reminder: don't share your token with anyone, it's a secret key to control your bot.<br>
The token looks like this: `1234567890:ABCdefGhIjKlmnOpqrStuVwXyz1234567890`.

### Step 2 (optional): Find a hosting
The bot needs to be hosted somewhere, but actually, you can run it on your local machine. This is why this step is optional. But if you rent a server, I suggest you deploy it on Ubuntu. And if you don't know what to do, and what is the hosting, you can use [DigitalOcean](https://www.digitalocean.com/) since it has detailed instructions and a simple interface. You even can connect to the console from a web browser to avoid learning some scary words like "SSH".

### Step 3: Install Docker
No matter where you host the bot, you need to install Docker. It's available for all popular operating systems, including Windows, macOS, and Linux.<br>
So, here are the links to the installation guides:
- [Windows](https://docs.docker.com/desktop/install/windows-install/)
- [macOS](https://docs.docker.com/desktop/install/mac-install/)
- [Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

If you decide to host the bot on Linux, you can copy-paste the following commands to install Docker:

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

```bash
# Install Docker:
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

```bash
# Test the installation:
sudo docker run hello-world
```

### Step 4: Obtain your Telegram ID
The bost must know who is the admin to accept or reject suggestions and must be started with the `ADMINS` environment variable. To get your Telegram ID, you can use the [userinfobot](https://t.me/userinfobot). Just start a chat with it and it will show you your ID.<br>
Note: I can't guarantee that this bot will work forever, but you can find a similar one by searching for `userinfo` in the Telegram search.<br>
You can start the bot with at least one admin ID and add others later, but also you can add multiple IDs at once while running the bot.

### Step 5 (optional): Add custom templates
To learn how to create custom templates, you can read the [Custom Templates](#Custom-templates) section. This step is optional, you can skip it and use the built-in templates.


### Step 6: Run the bot
Now, when you installed Docker, created a bot, and got your Telegram ID, you can run the bot with the following command:

```bash
docker run -e TOKEN="1234567890:ABCdefGhIjKlmnOpqrStuVwXyz1234567890" -e ADMINS="1234567890" iwatkot/affirmbot
```

to use it with built-in templates, or, if you prepared custom templates, you can run the bot with the following command:

```bash
docker run -e TOKEN="1234567890:ABCdefGhIjKlmnOpqrStuVwXyz1234567890" -e ADMINS="1234567890" -e CONFIG="github_username/repo_name" iwatkot/affirmbot
```

Friendly reminder: don't forget to replace `1234567890:ABCdefGhIjKlmnOpqrStuVwXyz1234567890` with your bot token and `1234567890` with your Telegram ID.

## Custom Templates
To use custom templates, you need to create a public GitHub repository with a `config.yml` file, containing your templates. The repository must be public, otherwise, the bot won't be able to access it.<br>
So, again step by step for those who are not familiar with GitHub:

### Step 1: Create a GitHub account
I assume this is an obvious step, which doesn't require any additional explanation.

### Step 2: Create a new repository or fork the existing one
If you don't want to dive into the details, you can fork the [example repository](https://github.com/iwatkot/affirmbot_config) and use it as a template. And if you want to create your repository, I assume you know how to do it.<br>
Just a tip: to fork the repository, you need to click the "Fork" button in the upper right corner of the repository page.
After you forked the repository, you can find it in your profile.

### Step 3: Edit the `config.yml` file
You can edit the file directly on the GitHub website, just click on it and then click the pencil icon in the upper right corner. Again, I won't describe how to edit the file locally and push it to the repository. <br>
Note: please pay attention to the file structure, it must be correct, otherwise, the bot won't be able to read it and will use the built-in templates.<br>
So, let's take a look at the example `config.yml` file:

```yaml
welcome: "Hello! With this bot, you can fill out the form, which will be posted to the channel, if admins accept it."
templates:
  - title: "Form for posting to channel"
    description: "This form will be posted to channel if accepted."
    toend: "Please, use the reactions so author will know that you're going to the event."
    complete: "Thank you for completing the form, the bot will notify you when it will be accepted or rejected."
    entries:
    - mode: "text"
      title: "Event title"
      incorrect: "You entered an incorrect title, please try again."
      description: "Please, enter the title for your event."
    - mode: "date"
      title: "Event Date"
      incorrect: "It was an incorrect date, please try again."
      skippable: true
      description: "Please enter the date in DD.MM.YYYY format (e.g. 31.05.2024)."
    - mode: "oneof"
      title: "Where will your event take place"
      incorrect: "Please, try again and use the buttons."
      description: "Please select the answer from one of the buttons."
      options:
        - "Outdoor"
        - "Indoor"
```
On the first level, there are two keys: `welcome`, which is a welcome message when the bot starts a conversation with a user, and `templates`, which is a list of templates.<br>

### Template structure

So here's a list of keys which represent the template:
  
|     Key name       |        Required         |                         Description                                        |
| :----------------: | :----------------------:|:-------------------------------------------------------------------------: |
|    `title`         |           ✅            | The title of the template, which will be shown to the user.                |
|    `description`   |           ❌            | The description of the template, which will be shown to the user.          |
|    `complete`      |           ✅            | The message that the user will receive after filling out the form.         |
|    `toend`         |           ✅            | The text that will be added to the end of the filled form.                 |
|    `entries`       |           ✅            | A list of entries that the user must fill out.                             |

✅ - required, must be entered in the yaml file.<br>
❌ - optional, can be omitted in the yaml file.

### Entry structure

There are several types of entries, learn more about them in the [Entry Types](#Entry-Types) section.<br>
But for most of them, you can use the following keys:

|     Key name       |        Required         |                         Description                                        |
| :----------------: | :----------------------:|:-------------------------------------------------------------------------: |
|    `mode`          |           ✅            | The type of entry, must be entered exactly as in documentation.            |
|    `title`         |           ✅            | The title of the entry, which will be shown to the user.                   |
|    `description`   |           ❌            | The description of the entry, which will be shown to the user.             |
|    `incorrect`     |           ✅            | The message that the user will receive if the entry is incorrect.          |
|    `skippable`     |           ❌            | A boolean value that allows the user to skip the entry.                    |
|    `options`       |           *️⃣            | A list of options that the user can choose from. Required for `oneof`.     |

✅ - required, must be entered in the yaml file.<br>
❌ - optional, can be omitted in the yaml file.<br>
*️⃣ - required for specific entry types, for others is optional.<br>

Some keys are optional for most entry types, but may be required for specific entry types. For example, the `oneof` entry type requires the `options` key, which is a list of options that the user can choose from. For other entry types, this key is optional and will add additional buttons to the message. In the next section, you can learn how to use different entry types. 

## Entry Types
Before we start talking about entry types, I beg you to NOT USE specific entry types (like `date`) if you don't need them. Let me explain to you why. Imagine that the user wants to suggest an event that will take place for example on Friday and enters something like 7 June. If you set the field to text, it would be okay, but if you set it to date, the bot will reject the answer because it doesn't understand the date since it waits for the date in popular formats like 07.06.2024. And it will tell the user that the date was incorrect again and again. So, please, be careful with the entry types you choose. And if you're not sure, just use the text entry type.

### Text
mode: `text`<br>
additional keys: none<br>
This is the simplest entry type, the user must enter any text. The bot doesn't check the correctness of the text, it just accepts it. Here is an example:

```yaml
- mode: "text"
  title: "Event title"
  incorrect: "You entered an incorrect title, please try again."
  description: "Please, enter the title for your event."
```

### Number
mode: `number`<br>
additional keys: none<br>
This entry type is used to enter the number. The bot checks the correctness of the number. Here is an example:

```yaml
- mode: "number"
  title: "Number of participants"
  incorrect: "You entered an incorrect number, please try again."
  description: "Please enter the number of participants."
```

### Date
mode: `date`<br>
additional keys: none<br>
Note: don't use this entry type if you don't need it.<br>
This entry type is used to enter the date. The bot checks the correctness of the date by several popular formats. Here is an example:

```yaml
- mode: "date"
  title: "Event Date"
  incorrect: "It was an incorrect date, please try again."
  description: "Please enter the date in DD.MM.YYYY format (e.g. 31.05.2024)."
```

### OneOf
mode: `oneof`<br>
additional keys: `options`<br>
This entry type is used to select one of the options. The user can choose the option by clicking on the button. All other answers will be rejected. Here is an example:

```yaml
- mode: "oneof"
  title: "Where will your event take place"
  skippable: true
  incorrect: "Please, try again and use the buttons."
  description: "Please select the answer from one of the buttons."
  options:
    - "Outdoor"
    - "Indoor"
```

### Url
mode: `url`<br>
additional keys: none<br>
This entry type is used to enter the URL. The bot checks the correctness of the URL. Here is an example:

```yaml
- mode: "url"
  title: "Event URL"
  incorrect: "You entered an incorrect URL, please try again."
  description: "Please enter the URL of the event."
```

### File
mode: `file`<br>
additional keys: none<br>
This entry type is used to upload the file. The bot doesn't check the correctness of the file, it just accepts it. Here is an example:

```yaml
- mode: "file"
  title: "Data archive"
  incorrect: "You uploaded an incorrect file, please try again."
  description: "Please upload the archive with the data."
```

## Administration
To change the bot's admin settings, click on the `Administration` button in the bot's menu.
### Channel
After you run the bot, first of all, you need to add the bot to the channel where you want to publish the suggestions. When the bot is added to the channel, go to the bot's `Administration` and click on the `Channel` button. In this menu, you can connect the bot to the channel or disconnect it. By the way, you'll need to know your channel ID. This can be done with one of the Telegram bots, for example, [GetTheirIdBot](https://t.me/GetTheirIDBot).<br>
Note: If this bot doesn't work, you can find a similar one by searching for `channel id` in the Telegram search.

### Team
In the `Team` menu, you can add or remove moderators and admins. The difference between them is that the admin can change the bot settings, and the moderator can only accept or reject suggestions. The moderators can't do anything else. Basically, moderators are ordinary users with the ability to accept or reject suggestions.

#### Admins
In the `Admins` menu, you can add or remove admins by their Telegram IDs. Just a tip: you can't remove yourself from the list of admins.

#### Moderators
In the `Moderators` menu, you can add or remove moderators by their Telegram IDs.

### Templates
In the `Templates` menu, you can enable or disable templates. The users will see only enabled templates.

### Config
In the `Config` menu, you can reload the configuration from the GitHub repository. This is useful if you made changes to the `config.yml` file and want to apply them without restarting the bot.

### Get Logs
If something goes wrong, you can click on the `Get Logs` button to get the logs from the bot. The bot will send you an archive with all logs and tracebacks. If you want to open an issue, please attach these logs, otherwise, I won't be able to help you.

### Settings menu
In the `Settings` menu, you can change different admin settings, like the number of approvals and rejections needed to publish or reject the suggestion, and also here you can backup and restore the settings.

#### Minimum approvals
This setting allows you to set the minimum number of approvals needed to publish the suggestion. For example, if you have 3 admins and set this value to 2, the suggestion will be published if at least 2 admins accept it. The default value is 1 and the maximum value is the number of admins.

#### Minimum rejections
This setting allows you to set the minimum number of rejections needed to reject the suggestion. For example, if you have 3 admins and set this value to 2, the suggestion will be rejected if at least 2 admins reject it. The default value is 1 and the maximum value is the number of admins.

#### Backup settings
After clicking on this button, the bot will send you a file with the settings. You can use it to restore the settings in case of redeploying the bot. Friendly reminder: if you won't clean the history of the chat, the file will always be available for you, so you don't need to save it on your device.

#### Restore settings
After clicking on this button, the bot will ask you to upload the file with the settings. After uploading the file, the bot will restore the settings from it. The file has a pretty simple JSON structure, so you can edit it manually if needed.<br>
Here's an example of the settings file:

```json
{
    "admins": [
        1234567890,
    ],
    "moderators": [
        1234567890,
    ],
    "channel": -1234567890,
    "active_templates": [
        0
    ],
    "inactive_templates": [],
    "min_approval": 1,
    "min_rejection": 1
}
```
|     Key name       |        Required         |                         Description                                        |
| :----------------: | :----------------------:|:-------------------------------------------------------------------------: |
|    `admins`        |           ✅            | A list of admin Telegram IDs.                                              |
|  `moderators`      |           ❌            | A list of moderator Telegram IDs.                                          |
|    `channel`       |           ✅            | The channel ID where the suggestions will be published.                    |
|  `active_templates`|           ❌            | A list of indexes of active templates.                                     |
|`inactive_templates`|           ❌            | A list of indexes of inactive templates.                                   |
|  `min_approval`    |           ✅            | The minimum number of approvals needed to publish the suggestion.          |
|  `min_rejection`   |           ✅            | The minimum number of rejections needed to reject the suggestion.          |

✅ - required, must be entered in the JSON file.<br>
❌ - optional, can be omitted in the JSON file.

## How to use the bot

### How users can suggest content
The users have only one button `Forms` which opens the list of active templates. The user can choose the template and fill it out. After filling out the form, the user will receive a message that the form has been sent for review. The admins will receive a notification about the new suggestion and can accept or reject it. If the suggestion is accepted, it will be published in the channel. If it is rejected, it won't. In both cases, the user will receive a notification about the decision.

### How admins can accept or reject suggestions
When the user sends a suggestion, each admin will receive a notification about the new suggestion with two buttons: `Accept` and `Reject`. By clicking on the button, the admin can accept or reject the suggestion.

## Bugs and Feature Requests
If you found a bug, please first save the logs, you can learn how to do it in the [Get Logs](#Get-Logs) section, and then open an issue. If you have a feature request, you can also open an issue or use the Discussions tab.<br>
Friendly reminder: this bot is free and open-source, so I can't guarantee that I will fix all bugs and implement all feature requests, but I will try to do my best. You can also contribute to the project by opening a pull request or forking the repository.<br>

## For developers
If you want to set the bot in development mode, you can add the `ENV` environment variable with the value `DEV`.<br>
In this mode:<br>
- All entry checks will be disabled and always return `True`.
- All errors will be raised without catching them.
If you don't want to change the core features, you can use the `src/event.py` file to easily add new buttons, callbacks and so on. It's designed in a very simple way, so mostly you just need to add a string for the event and implement the `process()` method, which will be called when the button or callback is clicked.<br>

## Upcoming Features
I can't guarantee that these features will be implemented, but I'm planning to add them in the future (or at least think about them):

- 🔳 Add more built-in templates for easy deployment.
- ☑️ (v0.0.4) Setting minimum approvals and rejections to publish or reject the suggestion. E.g. if you have multiple admins, you can set that the suggestion will be published only if at least 3 admins accept it. Same for rejections. It's already implemented in the code, but not in the UI.
- ☑️ (v0.0.5) Backing up the settings to the file and loading them back in case of redeploying the bot (starting a new container). It already works for stopping and ending the existing container, but not for creating a new one.
- ☑️ (v0.0.8) Add the `Moderator` role. This user won't be able to change the bot settings, only for accepting or rejecting suggestions.
- 🔳 Show the list of suggestions waiting for the decision for admin. 
- ☑️ (v0.0.5) New types of Entries (e.g. link, file).

## Wontfix

- ❌ Adding multiple languages support. Since the main interaction of a user happens with the template, you can create a template in any language you want. But for the menus and buttons, I'm not planning to add any other languages, since it's a lot of (useless) work. But if you want to add a new language, you can fork the repository and do it yourself.