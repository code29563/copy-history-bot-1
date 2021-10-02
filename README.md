# Copy-history-bot 1

This script is intended for copying messages from public channels, or private channels to which you have the ability to add bots as admins. For private channels to which you don't have the ability to add bots as admins, use [my other script](https://github.com/code29563/copy-history-bot-2).


- [Features](#Features)
- [Getting started](#Getting-started)
- [How it works](#How-it-works)
  - [Switching between clients and handling floodwaits](#Switching-between-clients-and-handling-floodwaits)
- [Importance of using multiple clients](#Importance-of-using-multiple-clients)
- [The caption added to messages](#The-caption-added-to-messages)
- [Other notes](#Other-notes)

# Features

- Messages are copied to the destination channel without the 'Forwarded from:' tag
- Copy multiple streams without having to manually re-run the script and adjust the environment variables each time
- Dynamically switching between bots when encountering floodwaits, to avoid having to wait them out and increase the average rate at which messages are sent
- Adds a detailed caption to copied messages, giving various details about the original message
- The script doesn't terminate when it gets disconnected from the internet – it just attempts to reconnect until the connection is restored and then resumes working. Likewise when the system goes to sleep, it resumes when it wakes up and reconnects to the internet.
- Option to print each successfully copied message to a file

# Getting started
The environment variables are to be given in a .env file. An example is shown in example.env.

1. Make an app with the Telegram API: [https://my.telegram.org/apps](https://my.telegram.org/apps) and fill in the API\_ID and API\_HASH environment variables in the .env file with the App api\_id and App api\_hash respectively.
2. Fill in the BOT\_TOKENS environment variable with the bot tokens of the bots that you want to use to copy messages (you can make bots using @BotFather), comma-separated. You can split them onto multiple lines if you want. Ensure you don't put a comma on the end of the last session string listed.

	I recommend using around 17 bots, which should be enough to completely avoid unnecessary floodwaits. To make this many bots, you might have to stagger it over a few days as @BotFather could limit the number of bots you make in a single day.

	The bots don't have to be made with the account with which the API ID and Hash were obtained, or with any of the accounts that you're using with their session strings in this script.

	The minimum number of bot tokens required is 1.
	
3. Fill in the STREAMS environment variable, which gives the details of the messages to be copied and where to copy them to. A single stream contains 4 comma-separated elements which are (in order): the 'identifier' (see below) of the source channel from which messages are to be copied, the ID of the message from which to start copying (which becomes the first message to be copied), the ID of the message at which to finish copying (which becomes the last message to be copied), and the ID of the destination channel to which to copy those messages. You can list multiple streams in the STREAMS environment variable, separated from each other by semi-colons, and if you want you can split them onto multiple lines and leave spaces between the elements and the commas/semi-colons. The streams are copied successively, one after the other, in the order you list them in the environment variable.

	The 'identifier' of the source channel is its ID if it's a channel in which your bots are admins, or the username of the channel if it's a public channel. If it's a public channel in which your bots are admins, it can be either. If using a username, don't include the @ at the beginning, and enclose it in single quotes.

	The channel IDs and message IDs can simply be obtained by right-clicking a message in the Telegram app and copying it's link, then paste it somewhere. The number after the final forward slash is the message ID, and the number before it is the channel ID, but append -100 to it before inserting it in STREAMS. You can also find the channel ID through other means like with @username\_to\_id\_bot, or exporting your Telegram data from the app as 'Machine-readable JSON' where you can find the IDs of channels you're subcribed to in results.json.

4. Make sure all the bots are admins in the destination channel, and if using an ID for the source channel make sure they are admins there too.
5. If you want to print the Message object of each successfully copied message to a file, set the PRINT_TO_FILE environment variable to "1". The printed object contains various details of the message not present in the (already detailed) caption.
6. Run the script using 'python app.py'.

# How it works
For each stream, the script iterates through all numbers from the ID of the first message to be copied to the ID of the last message to be copied. For each number, the currently-used bot retrieves the message with ID equal to that number, then after confirming it's not the ID of a deleted message or a service message that can't be copied, an attempt is made to copy it with the caption.

## Switching between clients and handling floodwaits

The API method used when retrieving messages is messages.GetMessages, and the method used when sending messages is messages.sendMessage for text messages or messages.sendMedia for media messages.

A bot may receive a 420 FLOOD (floodwait) error if it makes a request with a particular method more than a particular number of times within some timeframe. The error includes a time the bot is required to wait before it can successfully send another request with that method.

When a bot encounters a floodwait whilst attempting to send a message, the script switches to a different bot to send that message and subsequent messages. This allows the process of copying messages to continue, whilst the bot that encountered the floodwait waits it out, rather than waiting for that bot to finish its floodwait before copying further messages.

The bots are used in the order or their bot tokens in the BOT_TOKENS environment variable. When a bot encounters a floodwait, the script switches to the next bot in line, and if the bot that encountered the floodwait is the final bot, it moves back to the first bot.

As bots continue to encounter floodwaits and the script continues to switch to the next bot in line, all the bots may at some point have encountered a floodwait. The time when the bot encountered the floodwait and the required waiting time are both recorded. When a switch is made to the next bot in line, the time passed since that bot encountered its most recent floodwait is calculated and subtracted from the time it was required to wait. The result is the remaining floodwait that bot is required to wait. If it's zero or negative, then that bot has already finished waiting out its floodwait and it can now be used to copy messages again. Otherwise, the script waits the remaining time until that bot finishes its floodwait, before using it to copy messages.

The exact numbers for how many requests of a method can be sent in what timeframe seems to be information Telegram hasn't made public, but some insight can be gained from testing and from the experiences of other users.

It seems a bot can send up to 5 messages in a timeframe of about 5 seconds before receiving a floodwait of 3-4 seconds. It also seems to be limited to sending 20 messages per minute, after which it receives a floodwait requiring it to wait until the minute has passed.

These are general patterns I've noticed and these limits for bots seem to be generally stable.

To avoid wasting any time sending requests only for them to fail and receive a floodwait back, when it could reasonably have been predicted based on the above experimentally-deduced numbers, I've implemented a variable to act as a counter for the number of messages a client has sent, its value being increased by 1 every time the client sends a message, until it reaches 5, at which point the script switches to the next bot in line to send the next message.

The counter is reset every time the script switches to the next bot, including when the switch is due to encountering a floodwait.

# Importance of using multiple bots

Switching between bots to avoid waiting out floodwaits is the main point of using multiple clients in the script. For every extra bot you use, the average rate at which messages get copied increases, until if you have enough bots, the script never has to remain idle waiting out a floodwait. From experience, the rate at this point could reach around 300 messages per minute, and this point could be reached with about 17 bots.

If you have one bot, the average rate at which messages are sent is 20 per minute because that's its limit, but the time spent sending those messages is just a few seconds, with the rest of the minute spend waiting idly. If you add another bot, the rate increases to 40 messages per minute and the time spend waiting idly decreases. If you add a third, the rate increases to 60 messages per minute and the 'idle time' decreases further, until when you have enough bots, there is no idle time.

At this point, it may seem like adding more bots is superfluous. This may be true for bots, as their limits seem to be generally stable at 20 messages per minute, which a bot can send in about 4 seconds overall split up over the minute into batches of 5 messages, so accounting for minor variations in this, I've found 17 bot to be sufficient from experience. There's no significant disadvantage to adding more bots though to account for unforeseen changes in the limits, besides using up more of a user's quota of 20 bots per account, but if you have multiple accounts this shouldn't be an issue.

# The caption added to messages

Not all messages accept a text component, but those that do include text messages (obviously), videos, photos, documents. The script adds a caption to whichever message can have a text component. The caption consists of the following components:

- For every message, the first line of the caption is 'chat\_ID: ' followed by the ID of the source channel from which the message has been copied
- The second line is 'message\_ID: ' followed by the ID of the message in the source channel. If the message in the source chanel has been edited since it was first sent there, this is followed by ' (a\_previous\_message\_edited)'.
- The third line is 'date: ' followed by the date and time at which the message was sent in the source channel, except if the message has been edited since it was first sent, in which case it's the date and time at which the message was last edited instead of that at which it was first sent. The format of the date in both cases is 'YYYY-MM-DD hh:mm:ss UTC' with the time being given in UTC.
- If the message is a reply to a previous message, the next line is 'in\_reply\_to\_message\_ID: ' followed by the ID of the message to which it was a reply.
- If the message in the source channel had been forwarded from somewhere else, such that it had a 'Forwarded from: ' tag, then:
  - If the message was forwarded from an anonymous group admin, the next line is 'forwarded\_from\_chat\_ID: {ID} (supergroup)' where {ID} is the ID of the group from which it was forwarded
  - If the message was forwarded from a channel, the next line is 'forwarded\_from\_chat\_ID: ' followed by the ID of that channel, and the line after that is 'forwarded\_from\_message\_ID: ' followed by the ID of the original message in that channel
  - If the message is forwarded from an individual user/bot, even if that original message was sent in a group rather than a private chat, then:
    - If it's a bot, or a user that allowed linking to their account in messages forwarded from them, the next line is 'forwarded\_from\_user\_ID: ' followed by the ID of the user/bot
    - Otherwise, if it's a user that didn't allow linking to their account in messages forwarded from them, the next line is 'forwarded\_from\_user\_name: ' followed by the name of the user, as it appears in the 'Forwarded from: ' tag
	
  The next line is then 'forwarded\_from\_message\_date: ' followed by the date and time at which the original message was sent in the chat from which it was forwarded to the source channel. The format of the date is likewise 'YYYY-MM-DD hh:mm:ss UTC' with the time being given in UTC.

The issue of the attributes of the Message object of a forwarded message is still somewhat vague, so if none of the attributes exist which are used to determine which of the above cases applies, the message is copied without this part of the caption, and a message is printed to the terminal which should provide relevant details to look into it if you wish.

If the message already has text, then two line breaks are inserted at the end, followed by the above caption. If the message doesn't already have text (e.g. a document with no caption), then the caption is inserted without being preceded by two line breaks.

This applies if the text a message already contains wouldn't exceed the limit if the caption was added to it. The limit is 4096 characters for text messages and 1024 characters for the caption of media messages. If it would exceed the limit, the message is instead copied without a caption added to it, and the caption is sent in a new message in reply to the copied message immediately afterwards.

# Other notes

If you cancel the script whilst it's running (e.g. using Ctrl+C), a message is output to the terminal giving the ID of the last copied message of the stream that was being copied at the time. Depending on when exactly you cancel the script, is a possibility that another message has successfully been copied, such that the ID output to the terminal is actually the ID of the penultimate message to have been copied, so you may want to confirm this yourself before using the ID output to the terminal to e.g. update the STREAMS environment variable for the next time you manually run the script to pick up where it left off.