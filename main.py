import pydsb
import urllib.request
import urllib.parse
import time
import telepot
from telepot.loop import MessageLoop
import re
import json
from bs4 import BeautifulSoup
import threading

nachricht = ""
global benutzer
benutzer = ""
passwort = ""
klasse = ""
baseUrl = "https://iphone.dsbcontrol.de/iPhoneService.svc/DSB"
content = {"klasse": ""}

def writesilas():
    global bot
    bot.sendMessage(790105337, "now")

def alletesten():
    global bot
    threading.Timer(1800, alletesten).start()
    json = getjson()
    for jeder in json:
        update(json[jeder]["klasse"], json[jeder]["user"], json[jeder]["password"], jeder, bot, json, False)



def strike(text):
  result = ''
  for c in text:
    result = result + '\u0336' + c
  return result


def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '   ', raw_html)
  return cleantext


def verschoenern(inhalt):
    alles = []
    stunden = []
    for einzeln in inhalt:
        einzelnstr = str(inhalt[einzeln]["inhalt"])
        stunden = einzelnstr.split("</tr>")
        for einzelstunde in stunden:
            seinzelstunde = cleanhtml(einzelstunde)
            alles.append(seinzelstunde)
    alles = filter(None, alles)
    alles = list(dict.fromkeys(alles))
    return alles

def getcontent(klassen, user, password):
    global baseUrl
    content = {}
    authUrl = baseUrl + "/authid/" + user + "/" + password
    dsb = pydsb.PyDSB(user, password)
    timetables=dsb.get_plans()
    if not timetables == "":
        for table in timetables:
            with urllib.request.urlopen(table["url"]) as f:
                timetabledata = f.read()  
            soup = BeautifulSoup(timetabledata, 'html.parser')
            tableInfo = soup.find('div', attrs={'class': 'mon_title'})
            tableInfo = "*" + tableInfo.text.strip() + "*:"
            tableInfo = re.sub('\([^)]+\)', " ", tableInfo)

            reineTabelle = soup.find('table', attrs={'class': 'mon_list'})
            reineTabellestr = reineTabelle.text.strip()

            for klasse in klassen:

                for einzeln in reineTabelle.findAll('td'):
                    if (klasse in str(einzeln)):
                        einzelTr = einzeln.find_parent('tr')
                        einzelTr = tableInfo + str(einzelTr)

                        find = re.search('\?[\S]+', einzelTr)
                        if not find == None:
                            searched = find.group().replace(" ", "")
                            searched = strike(searched.replace("?", ""))
                            einzelTr = re.sub('\?[\S]+', searched, einzelTr)
                                                        
                        einzelTr.encode('utf-8')
                        if klasse in content:
                            if not "inhalt" in content[klasse]:
                                content[klasse] = {"inhalt": einzelTr}
                            else:
                                contentact = str(content[klasse]['inhalt'])
                                content[klasse] = {"inhalt": contentact + str(einzelTr)}

                        else:
                            content[klasse] = {"inhalt": einzelTr}
    return content

def sendcontent(klassen, user, password, chat_id, bot, json):
    if ", " in klassen:
        klassen= klassen.split(", ")
    else:
        klassen = klassen.split(",")

    inhalt = getcontent(klassen, user, password)
    alles = verschoenern(inhalt)
    for stunde in alles:

        bot.sendMessage(chat_id, str(stunde), parse_mode= 'Markdown')


    json[str(chat_id)]["letzer"] = alles
    return json




def update(klassen, user, password, chat_id, bot, input, sendnonews):
    send = False
    up = True
    if ", " in klassen:
        klassen= klassen.split(", ")
    else:
        klassen = klassen.split(",")


    if not klassen == [""] and not user == "" and not password == "":
        inhalt = getcontent(klassen, user, password)
        alles = verschoenern(inhalt)
        for stunde in alles:
            if not stunde in input[str(chat_id)]["letzer"] and up:
                bot.sendMessage(chat_id, "*Update:*", parse_mode= 'Markdown')
                up = False


        for stunde in alles:
            if not stunde in input[str(chat_id)]["letzer"]:
                send = True
                bot.sendMessage(chat_id, str(stunde), parse_mode= 'Markdown')
        if not send and sendnonews:
            bot.sendMessage(chat_id, "*Es gibt seit der letzten Nachricht keine Veränderungen auf dem Vertretungsplan*", parse_mode='Markdown')

        input[str(chat_id)]["letzer"] = alles
        json.dump(input, open("/usr/local/DsbBot/config.json", "w"))
    return input





def getjson():
    input = json.load(open("/usr/local/DsbBot/config.json", "r"))
    return input

def resetjson(chat_id, chat_type):
    input = {
        str(chat_id): {
            "chatId": str(chat_id),
            "chatType": chat_type,
            "user": "",
            "password": "",
            "klasse": "",
            "letzer": ""}}
    json.dump(input, open("/usr/local/DsbBot/config.json", "w"))
    return input

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    global benutzer
    global passwort
    global klasse
    input = json.load(open("/usr/local/DsbBot/config.json", "r"))


    if not str(chat_id) in input:
        input[str(chat_id)] = {
                "chatId": str(chat_id),
                "chatType": chat_type,
                "user": "",
                "password": "",
                "klasse": "",
                "letzer": ""}


    if content_type == 'text':
        nachricht = msg["text"]
        if re.search("/user*", msg["text"]):
            if "/user" == msg['text']:
                bot.sendMessage(chat_id, "bitte gebe ein: /user _benutzername_ ein", parse_mode= 'Markdown')
            else:
                benutzer = nachricht[6:]
                bot.sendMessage(chat_id, "benutzername \"" + nachricht[6:] + "\" gespeichert")
                input[str(chat_id)]['user'] = benutzer
                input = update(input[str(chat_id)]['klasse'], input[str(chat_id)]['user'], input[str(chat_id)]['password'], chat_id, bot, input, True)


        elif re.search("/password*", msg["text"]):
            if "/password" == msg['text']:
                bot.sendMessage(chat_id, "bitte gebe ein: /password _passwort_ ein", parse_mode= 'Markdown')
            else:
                passwort = nachricht[10:]
                bot.sendMessage(chat_id, "benutzername \"" + nachricht[10:] + "\" gespeichert")
                input[str(chat_id)]['password'] = passwort
                input = update(input[str(chat_id)]['klasse'], input[str(chat_id)]['user'], input[str(chat_id)]['password'], chat_id, bot, input, True)

        elif re.search("/klassen*", msg["text"]):
            if "/klassen" == msg['text']:
                bot.sendMessage(chat_id, "bitte gebe ein: /klassen _klasse_ bzw. /klassen _klasse_, _klasse_ achte auf Groß und Kleinschreibung, gebe es genau so ein, wie es auf DSB angezeigt wird ein", parse_mode='Markdown')
            else:
                klasse = nachricht[9:]
                bot.sendMessage(chat_id, "klasse(n) \"" + nachricht[9:] + "\" gespeichert")
                input[str(chat_id)]['klasse'] = klasse
                input = update(input[str(chat_id)]['klasse'], input[str(chat_id)]['user'], input[str(chat_id)]['password'], chat_id, bot, input, True)


        elif "/news" == msg['text']:
            chat_idstr = str(chat_id)
            input = sendcontent(input[str(chat_id)]['klasse'], input[str(chat_id)]['user'], input[str(chat_id)]['password'], chat_id, bot, input)

        elif "/update" == msg['text']:
            input = update(input[str(chat_id)]['klasse'], input[str(chat_id)]['user'], input[str(chat_id)]['password'], chat_id, bot, input, True)

        elif "/test" == msg['text']:
            bot.sendMessage(chat_id, strike("test"), parse_mode= 'Markdown')

        elif "/test2" == msg['text']:
            test(input)

        elif "/testall" == msg['text']:
            alletesten()
        elif "/getinfo" == msg['text']:
            bot.sendMessage(chat_id, "DSB Benutzer:*" + input[str(chat_id)]['user'] + "*" , parse_mode='Markdown')
            bot.sendMessage(chat_id, "DSB Passwort:*" + input[str(chat_id)]['password'] + "*" , parse_mode='Markdown')
            bot.sendMessage(chat_id, "Klasse(n):*" + input[str(chat_id)]['klasse'] + "*" , parse_mode='Markdown')

        elif "/start" == msg['text']:
            bot.sendMessage(chat_id, "hallo _" + str(bot.getChat(chat_id)['first_name']) + "_, dies ist ein Bot der dir deine Vertretung für deine Klasse von DSB mobile ausließt und dir hier schickt." , parse_mode='Markdown')
            bot.sendMessage(chat_id, "Zum Anmelden verwende bitte die Befehle */user* _DSB Benutzername (deiner Schule)_ \n und */passwort* _DSB Passwort (deiner Schule)_,\n anschließend musst du eine oder mehrere Klassen hinterlegen, dies machst du mit */klassen* _Klasse(n) (bei mehreren mit Komma getrennt)_ wie zum Beispiel: */klassen* _11b, 11ethik_." , parse_mode='Markdown')
            bot.sendMessage(chat_id, "*Achtung! Achte bei allen Anmeldevorgängen auf Groß und Kleinschreibung und schreibe die Klassen genauso, wie sie auf dem Vertretungsplan zu finden wären*." , parse_mode='Markdown')
            bot.sendMessage(chat_id, "bist du an der Karl Kübel Schule oder an der Melibokusschule, so kannst du auch */kks* oder */meli* schreiben, um dich direkt mit den Zugangsdaten anzumelden\n mit */getinfo* werden dir alle Anmeldedaten, die du hinterlegt hast ausgegeben." , parse_mode='Markdown')
            bot.sendMessage(chat_id, "mit */update* kannst du die Aktuallisierung händisch aktivieren, ansonsten wird alle 30 min nach Änderungen auf dem Vertretungsplan gesucht.\n mit */news* erhälts du auch Invormationen, die dir bereits geschickt wurden." , parse_mode='Markdown')


        else:
            bot.sendMessage(chat_id,"Tut mir leid, leider kann ich damit nichts anfangen, für eine Übersicht was dieser Bot kann schreibe */start* \n ansonsten benutze die Befehle: */user*, */passwort*, */klassen*, */kks*, */meli*, */update*, */news* oder */getinfo*", parse_mode='Markdown')

    json.dump(input, open("/usr/local/DsbBot/config.json", "w"))

bot = telepot.Bot("BOT TOKEN")

MessageLoop(bot, handle).run_as_thread()

alletesten()
# Keep the program running
while 1:
    time.sleep(10)
