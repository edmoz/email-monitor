import datetime
import json
import os
import sys
import time
import urllib2
import smtplib

PORT = 25
RESTMAIL_ACCT = "ses-monitor@restmail.net"
RESTMAIL_URL = "http://restmail.net/mail/%s" % RESTMAIL_ACCT
SMTP_URL = "email-smtp.us-east-1.amazonaws.com"

ALERT_LIST = ["services-alerts@mozilla.org"]
FROM_ADDR = "no-reply@lcip.org"
TO_ADDR = [RESTMAIL_ACCT]
LATENCY_LIMIT = 18
CHECK_NUM = 20 # checks for approximatly 60 seconds
CHECK_SLEEP = 3
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
    # Sends an email with utcnow in as the subject
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
    print 'check_mail'
    # if restmail is accessible at all
    try:
        response = urllib2.urlopen(RESTMAIL_URL)
        return json.load(response)
    except:
        print "can't load from restmail.net"
        return None

def poll_mail():
    check_count = 0
    data = ""
    while True:
        check_count += 1
        if check_count > CHECK_NUM:
            return None

        time.sleep(CHECK_SLEEP)
        data = get_mail()
        if data:
            return data

def delete_mail():
    # delete email from restmail
    print 'Deleting restmail'
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(RESTMAIL_URL)
    request.add_header('Content-Type', 'application/json')
    request.get_method = lambda: 'DELETE'
    return opener.open(request, data=None)

def compare_date(sent_epoch, rec_date):
    # returns the seconds delta between send and recieve
    rec_date = rec_date[:rec_date.index('.')]
    pattern = '%Y-%m-%dT%H:%M:%S'
    rec_epoch = int((time.mktime(datetime.datetime.strptime(rec_date, pattern).timetuple())))
    print 'recieved: %s, send: %s' % (rec_epoch, sent_epoch)
    return rec_epoch - int(sent_epoch)

def check_mail():
    # checks if mail was recieved, sends email if wasn't received or wasn't above latency limit
    mail_data =  poll_mail()
    print 'mail_data', mail_data
    if mail_data:
        latency = compare_date(mail_data[0]["subject"], mail_data[0]["receivedAt"])
        print 'Email latency:\n%s s' % latency
    else:
        msg  = 'Restmail did not recieve email from %s' % SMTP_URL
        send_email(msg, 
                   FROM_ADDR,
                   ALERT_LIST,
                   "SES email alert: restmail did not recieve email")
        print msg
        sys.exit(1)

    if latency > LATENCY_LIMIT:
        msg =  "Send email latency is \n%ss" % latency
        send_email(msg, 
                   FROM_ADDR,
                   ALERT_LIST,
                   "SES Email latency alert")
        print msg
        sys.exit(1)


send_email(epoch_time, FROM_ADDR, TO_ADDR, SUBJECT)
check_mail()
delete_mail()



