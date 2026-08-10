import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# Email Configuration — do not store credentials in source; read from environment
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# Twilio Configuration — read from environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')


def send_registration_email(recipient_email, user_name, role):
    """Send a welcome email to the newly registered user"""
    try:
        subject = f"Welcome to Alumni Management System - {role.title()} Account"
        
        # Create email body based on user role
        if role == 'alumni':
            body = f"""
Dear {user_name},

Welcome to the Alumni Management System!

Your alumni account has been successfully created. You can now:
- Build and update your professional profile
- Connect with fellow alumni
- Post and view job opportunities
- Participate in alumni events
- Make donations to support the institution

To log in to your account, please visit: http://localhost:5000/alumni/login
Or use your email: {recipient_email}

If you did not create this account, please contact our support team immediately.

Best regards,
Alumni Management Team
            """
        elif role == 'student':
            body = f"""
Dear {user_name},

Welcome to the Alumni Management System - Student Portal!

Your student account has been successfully created. You can now:
- View internship and job opportunities
- Connect with alumni mentors
- Attend alumni events and webinars
- Access career development resources
- Participate in the student community

To log in to your account, please visit: http://localhost:5000/student/login
Or use your email: {recipient_email}

If you did not create this account, please contact our support team immediately.

Best regards,
Alumni Management Team
            """
        elif role == 'staff':
            body = f"""
Dear {user_name},

Welcome to the Alumni Management System - Staff Portal!

Your staff account has been successfully created. You can now:
- Manage alumni records and events
- Post job opportunities and news
- Track donations and allocations
- Manage staff team members
- Access administrative features

To log in to your account, please visit: http://localhost:5000/staff/login
Or use your email: {recipient_email}

If you did not create this account, please contact our support team immediately.

Best regards,
Alumni Management Team
            """
        else:
            body = f"""
Dear {user_name},

Welcome to the Alumni Management System!

Your account has been successfully created. Please log in to access your profile and available features.

If you did not create this account, please contact our support team immediately.

Best regards,
Alumni Management Team
            """
        
        # Create message
        message = MIMEMultipart()
        message['From'] = EMAIL_ADDRESS
        message['To'] = recipient_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)
        server.quit()
        
        print(f"Registration email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send registration email to {recipient_email}: {str(e)}")
        return False


def send_email(recipient_email, subject, body):
    """Send a generic email"""
    try:
        message = MIMEMultipart()
        message['From'] = EMAIL_ADDRESS
        message['To'] = recipient_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)
        server.quit()
        
        print(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {str(e)}")
        return False


def send_registration_sms(phone_number, user_name, role):
    """Send a welcome SMS to the newly registered user"""
    try:
        # Create SMS body based on user role
        if role == 'alumni':
            message_body = f"Welcome {user_name}! Your Alumni account has been created. Log in at http://localhost:5000/alumni/login. You can now connect with alumni, view jobs, and support the institution."
        elif role == 'student':
            message_body = f"Welcome {user_name}! Your Student account has been created. Log in at http://localhost:5000/student/login. Access internships, connect with mentors, and explore opportunities."
        elif role == 'staff':
            message_body = f"Welcome {user_name}! Your Staff account has been created. Log in at http://localhost:5000/staff/login. Manage alumni records, post jobs, and access admin features."
        else:
            message_body = f"Welcome {user_name}! Your account has been created successfully. Please log in to access your profile."
        
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        print(f"Registration SMS sent successfully to {phone_number}")
        return True
        
    except Exception as e:
        print(f"Failed to send registration SMS to {phone_number}: {str(e)}")
        return False


def send_sms(phone_number, message_body):
    """Send a generic SMS"""
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        print(f"SMS sent successfully to {phone_number}")
        return True
        
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {str(e)}")
        return False
