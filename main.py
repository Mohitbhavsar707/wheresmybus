# importing dependencies
import os
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from pprint import pprint
import vonage
import requests
import os
from dotenv import load_dotenv

# Preparing Flask environment
load_dotenv()
app = Flask(__name__)

# Assigning environment variables to constants
DATABASE_URI=os.getenv('DATABASE_URI')
VONAGE_KEY=os.getenv('VONAGE_KEY')
VONAGE_SECRET=os.getenv('VONAGE_SECRET')
VONAGE_NUMBER_FROM=os.getenv('VONAGE_NUMBER_FROM')
VONAGE_NUMBER_TO = os.getenv('VONAGE_NUMBER_TO')


#-------------------------------------------------------------------------------
# Twilio
#--------------------------------------------------------------------------------

# Twilio challenge
@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    incoming_msg = request.values.get('Body', '').lower()
    print(incoming_msg)

    # Start our TwiML response
    resp = MessagingResponse()

    # Add a message
    resp.message(incoming_msg[::-1])

    return str(resp)



#-------------------------------------------------------------------------------
# Vonage
#--------------------------------------------------------------------------------

# Beginning vonage client instance
client = vonage.Client(key=VONAGE_KEY, secret=VONAGE_SECRET)
sms = vonage.Sms(client)

# Hangles Vonage inbound sms GET request
@app.route('/webhooks/inbound-sms', methods=['GET', 'POST'])
def inbound_sms():
    # Parses data depending on format
    if request.is_json:
        pprint(request.get_json())
    else:
        data = dict(request.args)
        pprint(data['text'])
    
    # Toronto Transit Commision - Stop predictions URL
    URL_REQUEST = "http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&a=ttc&stopId=" + data['text']
    
    # Fetches data from url and stores it in variable res
    res = requests.get(URL_REQUEST)

    # Parses raw data in res into JSON format
    resJson = res.json()

    # Variable for filtering key data from resJson
    busSchedule = {}
    
    # Filteres data in resJson to be meaningful
    for i in range(0, len(resJson['predictions']['direction']['prediction'])):
        busSchedule[resJson['predictions']['direction']['prediction'][i]['vehicle']] = resJson['predictions']['direction']['prediction'][i]['minutes']

    # Generates response for user depending on bus data
    userResponse = "Bus Stop: {0} \n".format(data['text'])
    for item in busSchedule:
        userResponse += "Bus: {0} | Time: {1} minutes \n".format(item, busSchedule[item])
    userResponse += "|"

    # Sends response with bus information to user
    responseData = sms.send_message(
        {
            "from": VONAGE_NUMBER_FROM,
            "to": VONAGE_NUMBER_TO,
            "text": userResponse,
        }
    )

    # Confirms if message was sent successfully or not
    if responseData["messages"][0]["status"] == "0":
        print("Message sent successfully.")
    else:
        print(f"Message failed with error: {responseData['messages'][0]['error-text']}")

    return ('', 204)

# Runs instance of Flack app
if __name__ == "__main__":
    app.run(debug=True)
