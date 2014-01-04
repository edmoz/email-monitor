import base64
import datetime
import json
import os
import sys
import urllib2

if "SL_USERNAME" not in os.environ or \
        "SL_PASSWORD" not in os.environ or \
        "SL_SERVERID" not in os.environ:
    print "SL_USERNAME or SL_PASSWORD env vars not set"
    sys.exit(1)

SL_API_URL = "https://api.socketlabs.com/v1"
SL_USERNAME = os.environ['SL_USERNAME']
SL_PASSWORD = os.environ['SL_PASSWORD']
SL_SERVERID = os.environ['SL_SERVERID']
Q_DELTA = 5
Q_ALERT = 20

now = str(datetime.datetime.utcnow() - datetime.timedelta(minutes=Q_DELTA))
q_range = now[:now.index(".")].replace(' ', '%20')

method = "messagesQueued"
qs = "serverId=%s&getTotals=true&" % SL_SERVERID
qs += "startDate=%s&" % q_range
qs += "count=0"

def getData(method, params):
    url = "%s/%s?%s" % (SL_API_URL, method, params)
    print 'fetching: ', url
    request = urllib2.Request(url)
    base64string = base64.encodestring('%s:%s' \
        % (SL_USERNAME, SL_PASSWORD)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    return json.loads(result.read())

queued = getData("messagesQueued", qs)
sent = getData("messagesProcessed", qs)
failed = getData("messagesFailed", qs)

print 'queued count: ', queued['totalCount']
print 'sent count: ', sent['totalCount']
print 'failed count: ', failed['totalCount']

totalOut = int(failed['totalCount']) + int(sent['totalCount'])
q_pending = int(queued['totalCount']) - totalOut
print 'pending',  q_pending

if q_pending > Q_ALERT:
    print 'Exceeded queue limit sending email alert'
    # TODO: send email

