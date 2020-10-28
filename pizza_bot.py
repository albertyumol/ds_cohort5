import logging
import sys
import spacy
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def extract_intent(doc):
    nlp = spacy.load('en_core_web_sm')
    #doc = nlp(doc)
    verbList = [('order', 'want', 'give', 'make'), ('show', 'find')]
    dobjList = [('pizza', 'pie', 'dish'), ('cola', 'soda')]
    substitutes = ('one', 'it', 'same', 'more')
    intent = {'verb':'', 'dobj': ''}
    for sent in doc.sents:
        for token in sent:
            if token.dep_ == 'dobj':
                verbSyns = [item for item in verbList if token.head.text in item]
                dobjSyns = [item for item in dobjList if token.text in item]
                substitute = [item for item in substitutes if token.text in item]
                if (dobjSyns != [] or substitute != []) and verbSyns != []:
                    intent['verb'] = verbSyns[0][0]
                if dobjSyns != []:
                    intent['dobj'] = dobjSyns[0][0]
    intentStr = intent['verb'] + intent['dobj'].capitalize()
    return intentStr
    
def details_to_str(user_data):
    details = list()
    for key, value in user_data.items():
        details.append('{} - {}'.format(key, value))
    return "\n".join(details).join(['\n', '\n'])
    
def start(update, context):
    update.message.reply_text("Hi! This is a pizza ordering app. Do you want to order something?")
    return 'ORDERING'
    
def intent_ext(update, context):
    msg = update.message.text
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(msg)
    for token in doc:
        if token.dep_ == 'dobj':
            intent = extract_intent(doc)
            if intent == 'orderPizza':
                context.user_data['product'] = 'pizza'
                update.message.reply_text("We need some more information to place your order. What type of pizza do you want?")
                return 'ADD_INFO'
            else:
                update.message.reply_text("Your intent is not recognized. Please rephrase your request.")
                return 'ORDERING'
    update.message.reply_text("Please rephrase your request. Be as specific as possible!")
    
def add_info(update, context):
    msg = update.message.text
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(msg)
    for token in doc:
        if token.dep_ == 'dobj':
            dobj = token
            for child in dobj.lefts:
                if child.dep_ == 'amod' or child.dep_ == 'compound':
                    context.user_data['type'] = child.text
                    user_data = context.user_data
                    update.message.reply_text("Your order has been placed." "{}" \
                                             "Have a nice day!".format(details_to_str(user_data)))
                    return ConversationHandler.END
    update.message.reply_text("Cannot extract necessary info. Please try again.")
    return 'ADD_INFO'
    
def cancel(update, context):
    update.message.reply_text("Have a nice day!")
    return ConversationHandler.END
    
def main():
    updater = Updater("TOKEN", use_context = True)
    disp = updater.dispatcher
    conv_handler = ConversationHandler(
    entry_points = [CommandHandler('start', start)],
    states = {
        'ORDERING':[MessageHandler(Filters.text, intent_ext)],
        'ADD_INFO':[MessageHandler(Filters.text, add_info)],
    },
    fallbacks = [CommandHandler('cancel', cancel)]
    )
    disp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
if __name__ == '__main__':
    main()
