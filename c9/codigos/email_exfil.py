import smtplib
import time
import win32com.client

smtp_server = 'smtp.mail.com'
smtp_port = 587 # TLS
smtp_acc = 'asdas@mail.com'
smtp_pass = 'senha'
tgt_accs= ['asdas@mail.com']

def plain_email(subject, contents):
    message = f'Assunto: {subject}\n De: {smtp_acc}'
    message += f'Para: {tgt_accs}\n\n{contents.decode()}'
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_acc, smtp_pass)
    
    server.set_debuglevel(1)
    server.sendmail(smtp_acc, tgt_accs, message)
    time.sleep(1)
    server.quit()
    
def outlook(subject, contents):
    outlook = win32com.client.Dispatch('Outlook.Application')
    message = outlook.CreateItem(0)
    message.DeleteAfterSubmit = True
    message.Subject = subject
    message.Body = contents.decode()
    message.To = tgt_accs[0]
    message.Send()
    
if __name__ == '__main__':
    plain_email('test_message a', b'asdsadasd')