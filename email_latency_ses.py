import datetime
import json
import os
import sys
import time
import urllib2
import smtplib

PORT = 25
RESTMAIL_ACCT = "latencyTest-ses@restmail.net"
LATENCY_LIMIT = 18
SMTP_URL = "email-smtp.us-east-1.amazonaws.com"
RESTMAIL_URL = "http://restmail.net/mail/%s" % RESTMAIL_ACCT
ALERT_LIST = ["ewong@mozilla.com"]
FROM_ADDR = "no-reply@lcip.org"
TO_ADDR = [RESTMAIL_ACCT]
latency = 0

try:
    SMTP_USERNAME = os.environ['SMTP_USERNAME']
    SMTP_PROD_PW = os.environ['SMTP_PROD_PW']
except:
    print 'No username pw env set'
    sys.exit(1)

print 'UTCNOW:', datetime.datetime.utcnow()
epoch_time = int(time.mktime(datetime.datetime.utcnow().timetuple()))
SUBJECT = epoch_time

def send_email(msg_body, from_addr, to_addr, subject):
    msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
           % (from_addr, ", ".join(to_addr), subject) )
    msg += "%s\r\n" % msg_body

    s = smtplib.SMTP(SMTP_URL, PORT)
    s.ehlo()
    # s.set_debuglevel(1)
    s.starttls()
    s.ehlo()
    s.login(SMTP_USERNAME, SMTP_PROD_PW)
    s.sendmail(from_addr, to_addr, msg)
    s.quit()

def get_mail():
    try:
        response = urllib2.urlopen(RESTMAIL_URL)
        data = json.load(response)
        return data
    except:
        print "can't load from restmail.net"
        sys.exit(0)

def compare_date(sent_epoch, rec_date):
    rec_date = rec_date[:rec_date.index('.')]
    pattern = '%Y-%m-%dT%H:%M:%S'
    rec_epoch = int((time.mktime(datetime.datetime.strptime(rec_date, pattern).timetuple())))
    print 'recieved: %s, send: %s' % (rec_epoch, sent_epoch)
    return rec_epoch - int(sent_epoch)

def checkLatency():
    mail_data =  get_mail()
    if mail_data:
        latency = compare_date(mail_data[-1]["subject"], mail_data[-1]["receivedAt"])
        print 'Fetching last email latency:\n%s s' % latency

    if latency > LATENCY_LIMIT:
        print "Latency over limit sending alert"
        msg =  "Send email latency is \n%ss" % latency
        send_email(msg, 
                   FROM_ADDR,
                   ALERT_LIST,
                   "Email latency alert")

checkLatency()
print 'sending latency mail'
send_email(epoch_time, FROM_ADDR, TO_ADDR, SUBJECT)


