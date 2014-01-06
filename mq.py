import base64
import datetime
import json
import os
import sys
import urllib2
import smtplib

if "SL_USERNAME" not in os.environ or \
        "SL_PASSWORD" not in os.environ or \
        "SL_SERVERID" not in os.environ:
    print "SL_USERNAME or SL_PASSWORD or SL_SERVERID=env vars not set"
    sys.exit(1)

SL_API_URL = "https://api.socketlabs.com/v1"
SL_PORT = 25
SL_USERNAME = os.environ['SL_USERNAME']
SL_PASSWORD = os.environ['SL_PASSWORD']
SL_SERVERID = os.environ['SL_SERVERID']
SAMPLE_TIME = 60
PENDING_LIMIT = 20
FAIL_PERCENT_LIMIT = 30
ALERT_MIN = 10

SL_SMTP = "smtp.socketlabs.com"
FROM_ADDR = "no-reply@persona.org"
TO_ADDR = ["ewong@mozilla.com"]
SUBJECT = "[socketlabs-mq] Auto Alert"

try:
    SL_SMTP_USERNAME = os.environ['SL_SMTP_USERNAME']
    SL_SMTP_PASSWORD = os.environ['SL_SMTP_PASSWORD']
    smtp_enabled = True
except:
    smtp_enabled = False
    print 'send email alert not enabled'

now = str(datetime.datetime.utcnow() - datetime.timedelta(minutes=SAMPLE_TIME))
now_sample = now[:now.index(".")].replace(' ', '%20')

method = "messagesQueued"
qs = "serverId=%s&getTotals=true&" % SL_SERVERID
qs += "startDate=%s&" % now_sample
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

def send_email(msg_body, from_addr, to_addr, subject):
    msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
           % (from_addr, ", ".join(to_addr), subject) )
    msg += "%s\r\n" % msg_body

    s = smtplib.SMTP(SL_SMTP, SL_PORT)
    s.ehlo()
    s.set_debuglevel(1)
    s.ehlo()
    s.login(SL_SMTP_USERNAME, SL_SMTP_PASSWORD)
    s.sendmail(from_addr, to_addr, msg)
    s.quit()

queued = getData("messagesQueued", qs)
sent = getData("messagesProcessed", qs)
failed = getData("messagesFailed", qs)

queue_ct = int(queued['totalCount'])
sent_ct = int(sent['totalCount'])
fail_ct = int(failed['totalCount'])

msg_body = "Socketlabs email status as of %s: \n" % now
msg_body +=  'Counts: queue=%s, sent=%s, fail=%s\n' % (queue_ct, sent_ct, fail_ct)

totalOut = sent_ct + fail_ct
pending = queue_ct - totalOut
if sent_ct == 0:
    sent_ct = 1
fail_percent = (float(fail_ct)/sent_ct) * 100
msg_body += 'Pending: %s\n' %  pending
msg_body += 'Fail Percentage: %s%%\n' % fail_percent

print 
print msg_body

if fail_ct > ALERT_MIN and pending > PENDING_LIMIT or fail_percent > FAIL_PERCENT_LIMIT:
    print 'Exceeded queue limit sending email alert'
    if smtp_enabled:
        send_email(msg_body, FROM_ADDR, TO_ADDR, SUBJECT)

