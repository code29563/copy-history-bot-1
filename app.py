from dotenv import load_dotenv
import logging
import os
import ast
from pyrogram import Client,errors
from datetime import datetime
import signal
import sys
import time
import asyncio

logging.basicConfig(format='[%(asctime)s --- %(filename)s line %(lineno)d --- %(levelname)s] --- %(message)s', level=logging.INFO) #for detailed logging

load_dotenv() #loading environment variables from .env file

str1 = os.environ.get("STREAMS") #loading the environment variable "STREAMS" to a variable str1
str2 = str1.split(";") #splitting at the semi-colons ; which is used as the separator between different streams
str3 = ["[" + x + "]" for x in str2] #enclosing each of the streams in square brackets
str4 = ','.join(str3) #joining the streams together, separated by commas
str5 = "[" + str4 + "]" #enclosing the entire thing in square brackets, which is relevant for correct recognition as a list of a list when there is only one stream
cs = ast.literal_eval(str5) #converting the string into an array
#print(cs)

str1 = os.environ.get("BOT_TOKENS")
str2 = str1.replace("\n","") #remove any line breaks
bts = str2.split(",") #bot tokens are separated from each other by a comma
#print(bts)

apiid = os.environ.get("API_ID")
apihash = os.environ.get("API_HASH")

l = list(range(len(bts))) #just to give it the right size
for b in l:
    l[b] = Client(":memory:",apiid,apihash,bot_token=bts[b],sleep_threshold=0) #sleep_threshold=0 so it doesn't automatically sleep for any floodwait errors

def copy_message(message,to):
    '''copy the given message to the destination with the appropriate added text/caption'''
    string = '\n\nchat_ID: ' + str(message.chat.id) + '\nmessage_ID: ' + str(message.message_id) #initialising the string to be added to the text/caption of the copied message
    if message.edit_date: #if the message is a previous message edited, then edit_date is the date of the most recent edit, which is what I want to output
        date = datetime.utcfromtimestamp(message.edit_date).strftime('%Y-%m-%d %H:%M:%S UTC') #converts the date from UNIX time to a more readable format
        string += ' (a_previous_message_edited)' + '\ndate: ' + date
    else: #i.e. if the message is brand new
        date = datetime.utcfromtimestamp(message.date).strftime('%Y-%m-%d %H:%M:%S UTC')
        string += '\ndate: ' + date
    if message.reply_to_message:
        string += '\nin_reply_to_message_ID: ' + str(message.reply_to_message.message_id)
    if message.forward_date: #if this property exists, it indicates the message is forwarded
        fdate = datetime.utcfromtimestamp(message.forward_date).strftime('%Y-%m-%d %H:%M:%S UTC')
        if message.forward_from_chat: #if this property exists, then what appears in the 'Forwarded from:' tag seems to be either a channel or an anonymous group admin
            if message.forward_from_chat.type == 'supergroup':
                string += '\nforwarded_from_chat_ID: ' + str(message.forward_from_chat.id) + ' (supergroup)\nforwarded_from_message_date: ' + fdate #it seems the message is forwarded from an anonymous group admin
            elif message.forward_from_message_id: #in which case I think it is a channel, in which case the ID of the original message is also accessible
                string += '\nforwarded_from_chat_ID: ' + str(message.forward_from_chat.id) + '\nforwarded_from_message_ID: ' + str(message.forward_from_message_id) + '\nforwarded_from_message_date: ' + fdate
        elif message.forward_sender_name: #in which case I think the 'Forwarded from:' tag contains a user's name (even if their original message was sent in a group rather than a private chat) and in this case the user didn't allow linking to their account when forwarding their messages
            string += '\nforwarded_from_user_name: ' + str(message.forward_sender_name) + '\nforwarded_from_message_date: ' + fdate
        elif message.forward_from.id: #in which case I think the 'Forwarded from:' tag contains a user's or bot's name (even if their original message was sent in a group rather than a private chat) and if it's a user then they have allowed linking to their account when forwarding their messages
            string += '\nforwarded_from_user_ID: ' + str(message.forward_from.id) + '\nforwarded_from_message_date: ' + fdate
        else:
            logging.info("This message has the `.forward_date attribute` but none of `.forward_from_chat`, `.forward_sender_name` or `.forward_from.id` attributes. I'm not adding the 'Forwarded from:' part of the caption to it; look into it. Here it is printed out:")
            print(message)
    if message.media:
        if message.text: #I did find a message with media type MessageMediaWebPage (in Telethon) because of a hyperlink therein, hence this
            if len(message.text + string) <= 4096: #to ensure it doesn't go above the limit for text messages, which I think is 4096 characters
                message.text += string #adding the above string to the text of the message
                message.copy(to) #copy the message (not forward) to the destination chat
            else: #if the combined string would be over the limit for text messages, send the message without the added string and send the string as a reply to it
                a = message.copy(to)
                a.reply_text(string[2:],quote=True) #remove the line breaks at the beginning of the above string, as it's not being added to previously existing text so nothing to separate it from
        elif message.caption: #media that already has a caption
            if len(message.caption + string) <= 1024: #to ensure it doesn't go above the limit for captions on media messages, which I think is 1024 characters
                message.caption += string #adding the above string to the caption
                message.copy(to)
            else:
                a = message.copy(to)
                a.reply_text(string[2:],quote=True)
        else: #if the media doesn't already have a caption
            cap = string[2:]
            message.copy(to,cap) #copy the message with this caption
    else:
        if len(message.text + string) <= 4096:
            message.text += string
            message.copy(to)
        else:
            a = message.copy(to)
            a.reply_text(string[2:],quote=True)

#now proceed with the process:

li = []
async def start_clients():
    for bot in l: #starting all bots concurrently
        a = asyncio.create_task(bot.start())
        li.append(a)
    for task in li: #wait until all the clients have finished starting
        await task
l[0].run(start_clients())

def move(x,d,w,f=False):
    """To move to the next bot in line
    set f=True if the move is triggered by a floodwait, otherwise leave as false if triggered by the counter maxxing out"""
    if f:
         logging.info('FloodWait error of {0} seconds encountered on bot {1}'.format(w[x][0],x+1))
    if len(d) == 1: #if there's only 1 bot, then there are no other bots to switch to
        if f:
            logging.info('Waiting {0} seconds to finish its floodwait'.format(w[x][0]))
            time.sleep(w[x][0])
    else:
        if x == d[-1]: #change the value of x to access the next bot in line
            x = 0
        else:
            x += 1
        p = w[x][0] - (time.time() - w[x][1]) #the remaining floodwait of the next bot
        if p > 0: #i.e.if the time passed since the next bot received its floodwait error is less than the time it was required to wait ...
            logging.info('Waiting {0} seconds before switiching to bot {1}, to finish its floodwait'.format(p,x+1))
            time.sleep(p) #... then sleep the remaining amount of time before moving onto the next bot
        elif f: #no need to sleep
            logging.info('Switching to bot {0}'.format(x+1))
    return x

def copy(p2f):
    d = list(range(len(l))) #a list of the indices of l (see below)
    x = 0 #to start the process with the first bot listed in l
    w = [[0,0] for i in d] #initialising w as such to suitably handle the first round of floodwaits, when the next bot in line hasn't had any floodwaits
    c = 1 #initialise the counter at 1
    #to handle cases where the script is cancelled before finishing with all messages:
    lid = 0 #the id of the last message copied (or zero when no messages have yet been copied)
    def cancel(sig,frame):
        logging.info('ID of last copied message = {}'.format(lid))
        sys.exit(0)
    signal.signal(signal.SIGINT, cancel)
    for s in cs: #copying the streams successively, one after the other, in the order given in the environment variable
        fro,sid,eid,to = [*s] #the chat from which messages are being copied, the ID of the first message to be copied, the ID of the last message to be copied, and the chat to which messages are to be copied
        for i in range(sid,eid+1): #looping over all the message IDs of the messages to be copied
            while True: #infinite looping; this is to try again for this message with the next bot if the current bot receives a floodwait error
                msg = l[x].get_messages(fro,i) #retrieve the message
                if not msg.empty and not msg.service: #to ensure the message with ID i wasn’t deleted, and that it isn't a service message (which can't be copied)
                    try:
                        copy_message(msg,to) #copying the message to the destination chat
                        lid = msg.message_id #if the message was copied without error, this line runs to update the ID of the last copied message
                        #logging.info('{0} bot {1}'.format(msg.message_id,x+1))
                    except errors.FloodWait as e:
                        t = time.time() #the current time at which the floodwait has occurred
                        wait = e.x #the required wait time
                        w[x] = [wait,t]
                        x = move(x,d,w,True)
                        c = 1 #reset the counter for the next bot
                        continue #continue to the next iteration of the while loop
                break #either the message is one that's not to be copied, or the 'try:' statement executed successfully, so the while loop needs to be brokem manually
            if p2f:
                print('',file=file) #a blank line
                print(msg,file=file)
            if c == 5: #so that each bot sends 5 messages at a time, then move onto the next bot
                x = move(x,d,w)
                c = 1
            else:
                c += 1 #changing c here rather than right after copying because I think you can still encounter floodwaits from get_messages
            #time.sleep(1)

if os.environ.get("PRINT_TO_FILE") == '1':
    with open('msgs.txt','a+',encoding='utf-8') as file:
        copy(True)
else:
    copy(False)

for bot in l:
    bot.stop()