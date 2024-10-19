import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
from email.header import decode_header
import time

# Global variables to store the credentials
CREDENTIALS = {"email": None, "password": None}

def get_credentials():
    """Ask for credentials if not already provided."""
    if CREDENTIALS["email"] is None or CREDENTIALS["password"] is None:
        CREDENTIALS["email"] = input("Enter your Yahoo email: ")
        CREDENTIALS["password"] = input("Enter your email password (use app password if 2FA is enabled): ")

def send_email():
    # Get credentials if not already set
    get_credentials()
    sender_email = CREDENTIALS["email"]
    password = CREDENTIALS["password"]

    # Ask for email details
    recipient_email = input("Enter recipient's email: ")
    subject = input("Enter subject: ")
    message = input("Enter your message: ")

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Add the message body
    msg.attach(MIMEText(message, 'plain'))

    # Setup the SMTP server using TLS
    smtp_server = "smtp.mail.yahoo.com"
    smtp_port = 587

    try:
        # Establish connection with the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()  # Send EHLO command to the server
        server.starttls()  # Start TLS encryption
        time.sleep(1)  # Adding a small delay to avoid connection drop
        server.ehlo()  # Send EHLO again after starting TLS
        
        # Log in to the server
        server.login(sender_email, password)
        time.sleep(1)  # Add a small delay after login

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Email sent successfully!")

    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Check your email and password.")
    except smtplib.SMTPServerDisconnected:
        print("Connection closed unexpectedly.")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        try:
            server.quit()
        except:
            pass  # Ignore if the connection was already closed

def receive_emails():
    # Get credentials if not already set
    get_credentials()
    email_user = CREDENTIALS["email"]
    password = CREDENTIALS["password"]

    # Connect to the Yahoo IMAP server
    imap_server = "imap.mail.yahoo.com"
    imap_port = 993
    
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_user, password)

        # Select the inbox
        mail.select("inbox")

        # Search for all emails
        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()

        # Get the latest email
        latest_email_id = mail_ids[-1]

        # Fetch the email by ID
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        
        # Convert the raw email to a message object
        msg = email.message_from_bytes(raw_email)
        
        # Decode the email subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")
        
        # Print the subject and sender
        print(f"Subject: {subject}")
        print(f"From: {msg.get('From')}")
        
        # Print the email body if it is plain text
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8")
                    print(f"Body: {body}")
        else:
            body = msg.get_payload(decode=True).decode("utf-8")
            print(f"Body: {body}")

    except imaplib.IMAP4.error:
        print("Failed to login to IMAP server. Check your credentials.")
    except Exception as e:
        print(f"Failed to fetch email: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass  # Ignore if the connection was already closed

if __name__ == "__main__":
    option = input("Do you want to send or receive emails? (send/receive): ").strip().lower()
    if option == "send":
        send_email()
    elif option == "receive":
        receive_emails()
    else:
        print("Invalid option. Please choose either 'send' or 'receive'.")
