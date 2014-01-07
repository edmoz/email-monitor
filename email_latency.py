import datetime
import json
import os
import sys
import urllib2
import smtplib

SL_API_URL = "https://api.socketlabs.com/v1"
SL_PORT = 25
RESTMAIL_URL = "http://restmail.net/mail/latencyTest@restmail.net"
LATENCY_LIMIT = 8

try:
    SL_SMTP_USERNAME = os.environ['SL_SMTP_USERNAME']
    SL_SMTP_PROD_PW = os.environ['SL_SMTP_PROD_PW']
    smtp_enabled = True
except:
    smtp_enabled = False
    print 'send email alert not enabled'

epoch_time = int((datetime.datetime.utcnow() -
                  datetime.datetime(1970,1,1)).total_seconds())
SL_SMTP = "smtp.socketlabs.com"
FROM_ADDR = "no-reply@persona.org"
TO_ADDR = ["latencyTest@restmail.net"]
SUBJECT = epoch_time

def send_email(msg_body, from_addr, to_addr, subject):
    msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
           % (from_addr, ", ".join(to_addr), subject) )
    msg += "%s\r\n" % msg_body

    s = smtplib.SMTP(SL_SMTP, SL_PORT)
    s.ehlo()
    # s.set_debuglevel(1)
    # s.ehlo()
    s.login(SL_SMTP_USERNAME, SL_SMTP_PROD_PW)
    s.sendmail(from_addr, to_addr, msg)
    s.quit()

def get_mail():
    try:
        response = urllib2.urlopen(RESTMAIL_URL)
        data = json.load(response)   
        return data
    except:
        print 'no restmail'
        sys.exit(0)

def compare_date(sent_epoch, rec_date):
    rec_date = rec_date[:rec_date.index('.')]
    pattern = '%Y-%m-%dT%H:%M:%S'
    rec_epoch = int((datetime.datetime.strptime(rec_date, pattern) - 
                     datetime.datetime(1970,1,1)).total_seconds())
    print 'recieved: %s, send: %s' % (rec_epoch, sent_epoch)
    return rec_epoch - int(sent_epoch)

mail_data =  get_mail()[-1]
latency = compare_date(mail_data["subject"], mail_data["receivedAt"])
print 'fetching last email latency:\n%s s' % latency
if latency > LATENCY_LIMIT:
    print "Latency over limit sending alert"
    msg =  "Send email latency is \n%ss" % latency
    send_email(msg, 
               FROM_ADDR,
               ["ewong@mozilla.com"],
               "Email latency alert")

print 'sending latency mail'
send_email(epoch_time, FROM_ADDR, TO_ADDR, SUBJECT)


