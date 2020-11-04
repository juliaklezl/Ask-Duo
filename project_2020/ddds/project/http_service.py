# -*- coding: utf-8 -*-

import json

from flask import Flask, request
from jinja2 import Environment
from urllib.request import Request, urlopen

import duolingo
lingo  = duolingo.Duolingo('Julia981676', 'xxx')
import datetime

user = 'Julia981676'

app = Flask(__name__)
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter

language = list(lingo.get_user_info()["language_data"].keys())[0]
llanguage = lingo.get_language_from_abbr(language)
words =  lingo.get_learned_skills(language)[-1]["words"]
languages = lingo.get_languages(abbreviations=False)


friends = ["Andrea613914", "Saga796697", "m2v9M6iB"]
friendsdict = {}
for friend in friends:
    lingo.set_username(friend)
    friendsdict[friend] = lingo.get_languages()

lingo.set_username(user)
cal = lingo.get_calendar()


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response
    
@app.route("/language_learned", methods=['POST'])
def language_learned():
    l = languages
    print(l)
    languagestring = ""
    if len(l) > 1:
        for i in range(len(l)-1):
            languagestring += l[i] + ", "
        languagestring += "and " + l[-1]
    else:
        languagestring = l[0]
    return query_response(value=None, grammar_entry=languagestring)
    
@app.route("/friends_number", methods=['POST'])
def friends_number():
    friends = lingo.get_friends()
    fnum = len(friends) - 1  # counts user as friend too
    return query_response(value=fnum, grammar_entry=None)
    
@app.route("/friends_names", methods=['POST'])
def friends_names():
    friends = lingo.get_friends()
    fnames = [f["username"] for f in friends if f["username"] != user]  # counts user as friend too
    fstring = ""
    for i in range(len(fnames)-1):
        fstring += fnames[i] + ", "
    fstring += "and " + fnames[-1]
    return query_response(value=fstring, grammar_entry=None)
    
@app.route("/last_activity", methods=['POST'])
def last_activity():
    payload = request.get_json()
    if "chosen_lesson_type" in payload["context"]["facts"]:
        ltype = payload["context"]["facts"]["chosen_lesson_type"]["grammar_entry"]
        lcal = [f for f in cal if f["event_type"] == ltype]
        if lcal != []:
            last = lcal[-1]["datetime"]
            last = datetime.datetime.fromtimestamp(last//1000.0)
            laststring = last.strftime('%Y-%m-%d %H:%M:%S')
        else:
            laststring = "you didn't do a " + ltype + " recently"
    else:
        last = cal[-1]["datetime"]
        last = datetime.datetime.fromtimestamp(last//1000.0)
        laststring = last.strftime('%Y-%m-%d %H:%M:%S')
    return query_response(value=laststring, grammar_entry=None)
    
@app.route("/streak", methods=['POST'])
def streak():
    streak = lingo.get_streak_info()["site_streak"]
    return query_response(value=streak, grammar_entry=None)

@app.route("/friend_languages", methods=['POST'])  # workaround
def friend_languages():
    payload = request.get_json()
    name = payload["context"]["facts"]["chosen_friend"]["value"]
    langs = friendsdict[name]
    languagestring = ""
    if len(langs) > 1:
        for i in range(len(langs)-1):
            languagestring += langs[i] + ", "
        languagestring += "and " + langs[-1]
    else:
        languagestring = langs[0]
    return query_response(value=None, grammar_entry=languagestring)
    
#@app.route("/friend_languages", methods=['POST'])
#def friend_languages():
#    payload = request.get_json()
#    name = payload["context"]["facts"]["chosen_friend"]["value"]
#    lingo.set_username(name)
#    langs = lingo.get_languages()
#    languagestring = ""
#    for i in range(len(langs)-1):
#        languagestring += langs[i] + ", "
#    languagestring += "and " + langs[-1]
#    return query_response(value=languagestring, grammar_entry=None)

@app.route("/leading_friend", methods=['POST'])
def leading_friend():
    payload = request.get_json()
    unit = payload["context"]["facts"]["chosen_unit"]["value"]
    lb = lingo.get_leaderboard(unit, "before")[0]
    lf = lb["username"]
    lp = lb["points"]
    response = lf + " made the most progress with " + str(lp) + " points"
    return query_response(value=None, grammar_entry=response)
    
@app.route("/topics_learned", methods=['POST'])
def topics_learned():
    payload = request.get_json()
    lang = language
    topics = lingo.get_known_topics(lang)
    topicstring = ""
    if len(topics) > 1:
        for i in range(len(topics)-1):
            topicstring += topics[i] + ", "
        topicstring += "and " + topics[-1]
    else:
        topicstring = topics[0]
    topicstring += " in " + llanguage
    return query_response(value=None, grammar_entry=topicstring)
    
@app.route("/current_language", methods=['POST'])
def current_language():
    l = list(lingo.get_user_info()["language_data"].keys())[0]
    return query_response(value=None, grammar_entry=l)
    
@app.route("/status", methods=['POST'])
def status():
    payload = request.get_json()
    lang = payload["context"]["facts"]["current_language"]["value"]
    word = payload["context"]["facts"]["word"]["value"]
    voc = lingo.get_known_words(lang)
    if word in voc:
        status = "have"
    else:
        status = "have not"
    return query_response(value=None, grammar_entry=status)

@app.route("/translation", methods=['POST'])
def translation():
    payload = request.get_json()
    word = payload["context"]["facts"]["word"]["value"]
    print(word)
    print(language)
    #print(lingo.get_translations([word], source=language, target='en'))
    trans = list(lingo.get_translations([word], source=language, target='en').values())[0][0]
    return query_response(value=None, grammar_entry=trans)

@app.route("/last_words", methods=['POST'])
def last_words():
    payload = request.get_json()
    lang = language
    wordslist = words
    wordstring = ""
    if len(words) > 1:
        for i in range(len(words)-1):
            wordstring += words[i] + ", "
        wordstring += "and " + words[-1]
    else:
        wordstring = words[0]
    return query_response(value=wordstring, grammar_entry=None)
