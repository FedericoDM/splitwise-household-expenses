"""
This file sends alerts when the budget is exceeded.
"""
from datetime import datetime

# Global imports
import pytz
import sendgrid
from sendgrid.helpers.mail import Content, Mail

from keys import email_keys

# Local imports
from splitwise import Splitwise

# Global variables
recipients = ["yourmail@gmail.com", "othermail@gmail.com"]


def send_email_html(recipient, alert_subject, html):
    """
    Sends email with html body:
        -recipient: string con el correo del recipiente
        -alert_subject: string con el subject del correo
        -html: body del correo
    """
    api_key = email_keys["api_key"]
    sg = sendgrid.SendGridAPIClient(api_key)

    from_email = "somemail@outlook.com"
    to_email = recipient
    subject = alert_subject

    # Add Intro
    html_text = "<html>" + html + "</html>"
    content = Content("text/html", html)

    mail = Mail(from_email, to_email, subject, content)
    sg.send(mail)

    print(f"email sent: {recipient}")


def alert_handler(event, context):
    # Get date
    today = datetime.now(pytz.timezone("US/Central")).strftime("%Y-%m-%d")

    # Get expenses
    splitwise = Splitwise()
    expenses = splitwise.get_expenses()
    print(expenses)
    print(splitwise.remaining_budget)
    print(splitwise.total_expenses)

    # Send email
    subject = f"Household Expenses - {today}"

    html = f"""
    <p>Hello,</p>
    <p>This is the expense summary for {today}:</p>

    <p><b>Total Expenses</b></p>
    <p>We have spent a total of ${splitwise.total_expenses} USD.</p>
    <p>The total budget is {splitwise.OVERALL_BUDGET} USD, so there are around {round(splitwise.OVERALL_BUDGET - splitwise.total_expenses, 2)} USD left.</p>

    <p><b>Food Expenses</b></p>
    <p>We have spent a total of ${splitwise.remaining_budget.loc[splitwise.remaining_budget.loc[:, "category"] == "Dining out", "cost"].values[0]} USD. </p>
    <p>The food budget is {splitwise.FOOD_BUDGET} USD, so we have {splitwise.remaining_budget.loc[splitwise.remaining_budget.loc[:, "category"] == "Dining out", "remaining_budget"].values[0]} USD left.</p>

    <p><b>Groceries Expenses</b></p>
    <p>We have spent a total of ${splitwise.remaining_budget.loc[splitwise.remaining_budget.loc[:, "category"] == "Groceries", "cost"].values[0]} USD. </p>
    <p>The groceries budget is {splitwise.GROCERIES_BUDGET} USD, so we have {splitwise.remaining_budget.loc[splitwise.remaining_budget.loc[:, "category"] == "Groceries", "remaining_budget"].values[0]} USD left.</p>

    <p><b>Transportation Expenses</b></p>
    <p>We have spent a total of ${splitwise.remaining_budget.loc[splitwise.remaining_budget.loc[:, "category"] == "Taxi", "cost"].values[0]} USD. </p>
    <p>The transportation budget is {splitwise.TRANSPORTATION_BUDGET} USD, so we have {splitwise.remaining_budget.loc[splitwise.remaining_budget.loc[:, "category"] == "Taxi", "remaining_budget"].values[0]} USD left.</p>

    <p>Have a great day!</p>
    """  # noqa: E501

    # Send email
    for recipient in recipients:
        send_email_html(recipient, subject, html)
