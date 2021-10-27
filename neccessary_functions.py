from datetime import datetime
import smtplib
import pytz

def get_current_time():
    timeZ_Kl = pytz.timezone('Asia/Kolkata')
    dt_Kl = datetime.now(timeZ_Kl)
    return (dt_Kl.strftime('%Y-%m-%d %H:%M:%S'))

def send_mail(gmail_id, gmail_password, subject, body, listofaddress):
    smtp_object = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_object.starttls()
    smtp_object.login(gmail_id, gmail_password)
    message = "Subject:{}\n\n{}".format(subject,body)
    listofaddress = listofaddress
    smtp_object.sendmail("libraryomni@gmail.com", listofaddress, message)
    smtp_object.quit()
    print("Message sent successfully!")