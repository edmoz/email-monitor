import base64
import datetime
import json
import os
import sys
import urllib2

if "SL_USERNAME" not in os.environ or \
        "SL_PASSWORD" not in os.environ or \
        "SL_SERVERID" not in os.environ:
    print "SL_USERNAME or SL_PASSWORD or SL_SERVERID=env vars not set"
    sys.exit(1)

SL_API_URL = "https://api.socketlabs.com/v1"
SL_USERNAME = os.environ['SL_USERNAME']
SL_PASSWORD = os.environ['SL_PASSWORD']
SL_SERVERID = os.environ['SL_SERVERID']
SAMPLE_TIME = 5
PENDING_LIMIT = 20
FAIL_PERCENT_LIMIT = 20


now = str(datetime.datetime.utcnow() - datetime.timedelta(minutes=SAMPLE_TIME))
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

queue_ct = int(queued['totalCount'])
sent_ct = int(sent['totalCount'])
fail_ct = int(failed['totalCount'])
print 
print 'Counts: queue=%s, sent=%s, fail=%s' % (queue_ct, sent_ct, fail_ct)

totalOut = sent_ct + fail_ct
pending = queue_ct - totalOut
fail_percent = (float(fail_ct)/sent_ct) * 100
print 'Pending: ',  pending
print 'Fail Percentage: %s%%' % fail_percent


if pending > PENDING_LIMIT or fail_percent > FAIL_PERCENT_LIMIT:
    print 'Exceeded queue limit sending email alert'
    # TODO: send email

