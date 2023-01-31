import os 
import json
import requests

from flask import Flask
from flask_cors import CORS
from flask import Flask, request
from flask import jsonify

PAGE_ACCESS_TOKEN = "EAAFdOotTChsBAJIBAy0L8UxtRRQhWIscKhuKL2thruZCd1iCo9DE0ZAY6kd8ckv9V1UaR0ZBMSe5JfQLIHTzGgt5Sm3sZBrbJrogxDUm28Bp56cf6gSDV7KkaZAVQPPqQYlXwkSe6hKuncLv9mDvI4ZB4VtMOHemiYSlARGVUAg8W3c5LXjX1ZB"
#for prod
# from .config import *

app = Flask(__name__)
cors = CORS(app)

app.config['CORS_HEADERS'] = 'Content-Type'

chatbot_base_url = os.getenv("CHAT_BASE_URL", "http://127.0.0.1:6055/webhooks/rest/webhook")

# chatbot_base_url = "http://127.0.0.1:6055/webhooks/rest/webhook"

TOKEN = "rasa-bot"
TIMEOUT = 15

HEADERS = {'Content-Type': 'application/json'}

FACEBOOK_SEND_API = "https://graph.facebook.com/v10.0/me/messages?access_token={}"
FACEBOOK_MESSENGER_PROFILE_API = "https://graph.facebook.com/v2.6/me/messenger_profile?access_token={}"

# RML_BASE_URL = "http://127.0.0.1:8000"
RML_BASE_URL = "https://clap-centralsystem.rmlconnect.net/"
# RML_CONVERSATION_API_BASE_URL = "http://0.0.0.0:5101"
RML_CONVERSATION_API_BASE_URL = "https://clap-managechat.rmlconnect.net/"

HANDOVER_API = RML_CONVERSATION_API_BASE_URL + "/handover-v2/"
CHECK_HANDOVER_API = RML_CONVERSATION_API_BASE_URL + "/check_handover/"

CHAT_WITH_LIVE_AGENT = RML_BASE_URL + "/user/chat_with_live_agent/"

VENDOR_NAME = "transfashionlive"
# VENDOR_NAME = "tvs"

SAVE_CHAT_CONVERSATION = RML_BASE_URL + "/chatbot/save_chatbot_conversation/"

def get_started_button():
    url = FACEBOOK_MESSENGER_PROFILE_API.format(PAGE_ACCESS_TOKEN)
    print(url)
    payload = {"get_started": {"payload": "Hello world messenger"}}
    
    response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    print(response.status_code)
    print(response.text)

    print("GET started successfully")

def callSendAPI(senderPsid, response):

    """
        To send back the message to the enduser using SEND api
    """
    text = response.get("text")

    payload = {
    'recipient': {'id': senderPsid},
    'message': {"text":text},
    'messaging_type': 'RESPONSE'
    }
    headers = HEADERS

    url = FACEBOOK_SEND_API.format(PAGE_ACCESS_TOKEN)
    r = requests.post(url, json=payload, headers=headers)
    print(r.text)
    print(senderPsid)



#Function for handling a message from MESSENGER
def handleMessage(senderPsid, receivedMessage):
    #check if received message contains text
    try:
        print("handleMessage")
        print(receivedMessage)
        print(type(receivedMessage))
        for msg in receivedMessage:

            response = {"recipient_id":senderPsid, "text": msg["text"]}
            print("response-----------",response)
            callSendAPI(senderPsid, response)
            save_chatbot_conversation_bot(senderPsid, response)
        
    except Exception as ex:
        print(ex)
        callSendAPI(senderPsid, response)
        return False



@app.route('/webhook', methods=["GET", "POST"])
def chat_interface_app():
    try:
        """
            facebook verifies the webhook by hitting a get request on the endpoint
        """
        if request.method == 'GET':
           
            if 'hub.mode' in request.args:
                mode = request.args.get('hub.mode')
                print(mode)
            if 'hub.verify_token' in request.args:
                token = request.args.get('hub.verify_token')
                print(token)
            if 'hub.challenge' in request.args:
                challenge = request.args.get('hub.challenge')
                print(challenge)

            if 'hub.mode' in request.args and 'hub.verify_token' in request.args:
                mode = request.args.get('hub.mode')
                token = request.args.get('hub.verify_token')

                if mode == 'subscribe' and token == TOKEN:
                    # get_started_button()
                    print('WEBHOOK VERIFIED')

                    challenge = request.args.get('hub.challenge')

                    return challenge, 200
                else:
                    return 'ERROR', 403

            return 'SOMETHING', 200

        """
            facebook returns the unique id of app as well as enduser's PSID
        """

        if request.method == 'POST':
            
            
            if 'hub.mode' in request.args:
                mode = request.args.get('hub.mode')
                print("hub.mode----------------",mode)
            if 'hub.verify_token' in request.args:
                token = request.args.get('hub.verify_token')
                print("hub.verify_token-------------------------",token)
            if 'hub.challenge' in request.args:
                challenge = request.args.get('hub.challenge')
                print("hub.challenge---------------------------",challenge)

            if 'hub.mode' in request.args and 'hub.verify_token' in request.args:
                mode = request.args.get('hub.mode')
                token = request.args.get('hub.verify_token')

                if mode == 'subscribe' and token == TOKEN:
                    print('WEBHOOK VERIFIED')

                    challenge = request.args.get('hub.challenge')

                    return challenge, 200
                else:
                    return 'ERROR', 403


            data = request.data
            body = json.loads(data.decode('utf-8'))


            print("BODY OF REQUEST-------------------------",body, "\n\n\n")


            if 'object' in body and body['object'] == 'instagram':
                entries = body['entry']
                for entry in entries:
                    webhookEvent = entry['messaging'][0]
                    print("MESSAGE PAYLOAD-------------------",webhookEvent)

                    senderPsid = webhookEvent['sender']['id']
                    print('Sender PSID: {}'.format(senderPsid))

                    handover_to = check_handover(senderPsid)
                    print("handover_to-----------", handover_to)

                    if handover_to == "chatbot":
                        if "message" in webhookEvent.keys():
                            if "quick_reply" in webhookEvent["message"]: 
                                message = webhookEvent["message"]["quick_reply"].get("payload")
                            # To verify that the user has sent text and not any attachments
                            elif "attachments" not in webhookEvent['message']:
                                message = webhookEvent['message'].get("text")
                            else:
                                message = json.dumps(body)

                        # If we use postback button in interactive list and replies
                        elif "postback" in webhookEvent: 
                            message = webhookEvent['postback'].get("payload")

                        # To send all the attachment like image video location etc.
                        else:
                            message = json.dumps(body)
                        
                        payload = {
                            "sender": senderPsid,
                            "message": message
                        }
                        save_chatbot_conversation_user(senderPsid, body)
                        print("payload----------------",payload)
                        response = requests.post(chatbot_base_url, data = json.dumps(payload),timeout = TIMEOUT)
                        json_response_msg = json.loads(response.text)

                        handleMessage(senderPsid, json_response_msg)

                    else:
                        print("Calling live agent api")
                        chat_with_live_agent_api(senderPsid, body)
                        
                    return 'EVENT_RECEIVED', 200
            else:
                return 'ERROR', 404

    except Exception as ex:
        print('Exception', ex)
        response_data = {
            "exception": ex
        }
    return jsonify(response_data), 500



def save_chatbot_conversation_bot(customer_identifier, body):
    try:
        payload = {
            "customer_identifier": str(customer_identifier),
            "vendor": VENDOR_NAME,
            "user_input": "",
            "chatbot_response": [body],
            "service_type":"facebook"
        }
        response = requests.post(url = SAVE_CHAT_CONVERSATION, headers = HEADERS, data=json.dumps(payload))
        print("save_chatbot_conversation---------------------",response.text)
    except Exception as ex:

        print(ex)


def save_chatbot_conversation_user(customer_identifier, body):
    try:
        payload = {
            "customer_identifier": str(customer_identifier),
            "vendor": VENDOR_NAME,
            "user_input": body,
            "chatbot_response": [],
            "service_type":"facebook"
        }
        response = requests.post(url = SAVE_CHAT_CONVERSATION, headers = HEADERS, data=json.dumps(payload))
        print("save_chatbot_conversation_user---------------------",response.text)
    except Exception as ex:

        print(ex)


def check_handover(customer_identifier):
    try:

        payload = {
            "customer_identifier": customer_identifier,
            "vendor": VENDOR_NAME,
            "service_type":"facebook"
        }
        response = requests.post(url=CHECK_HANDOVER_API, data=json.dumps(payload), headers=HEADERS, timeout=TIMEOUT)
        return response.text

    except Exception as ex:
        print(ex)
        return False


def chat_with_live_agent_api(customer_identifier, user_input_payload):
    payload = {
        "customer_identifier": customer_identifier,
        "vendor": VENDOR_NAME,
        "chatbot_response":  [],
        "service_type": "facebook",
        "user_message": user_input_payload
    }
    response = requests.post(url=CHAT_WITH_LIVE_AGENT, data=json.dumps(payload), headers=HEADERS, timeout=TIMEOUT)
    print("chat with live agent---------", response.text)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9033)