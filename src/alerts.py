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
recipients = ["yourmail@domain.com", "othermail@domain.com"]


def get_expenses_and_budget(splitwise, category):
    """
    Gets expenses and budget
    """

    budget_dict = {
        "Dining out": splitwise.FOOD_BUDGET,
        "Groceries": splitwise.GROCERIES_BUDGET,
        "Taxi": splitwise.TRANSPORTATION_BUDGET,
    }

    existing_categories = splitwise.remaining_budget.loc[:, "category"].values

    if category in existing_categories:
        expense = splitwise.remaining_budget.loc[
            splitwise.remaining_budget.loc[:, "category"] == category, "cost"
        ].values[0]

        remaining_budget = splitwise.remaining_budget.loc[
            splitwise.remaining_budget.loc[:, "category"] == category,
            "remaining_budget",
        ].values[0]

    else:
        expense = 0
        remaining_budget = budget_dict[category]

    return expense, remaining_budget


def send_email_html(recipient, alert_subject, html):
    """
    Sends email with html body:
        -recipient: string con el correo del recipiente
        -alert_subject: string con el subject del correo
        -html: body del correo
    """
    api_key = email_keys["api_key"]
    sg = sendgrid.SendGridAPIClient(api_key)

    from_email = "yourmail@domain.com"
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
    print(splitwise.remaining_budget)
    print(splitwise.total_expenses)

    REMAINING_BUDGET = round(splitwise.OVERALL_BUDGET - splitwise.total_expenses, 2)

    DINING_OUT_EXPENSES, REMAINING_DINING_OUT_BUDGET = get_expenses_and_budget(
        splitwise, "Dining out"
    )

    GROCERIES_EXPENSES, REMAINING_GROCERIES_BUDGET = get_expenses_and_budget(
        splitwise, "Groceries"
    )

    TRANSPORTATION_EXPENSES, REMAINING_TRANSPORTATION_BUDGET = get_expenses_and_budget(
        splitwise, "Taxi"
    )

    # Send email
    subject = f"Gastos Household - {today}"

    html = f"""
    <p>Hola,</p>
    <p>Este es el resumen semanal de los gastos del household al día de hoy, {today}:</p>
    
    
    <p><b>Gastos Totales</b></p>
    <p>Hemos gastado un total de ${splitwise.total_expenses} USD. </p> 
    <p>El presupuesto total es de {splitwise.OVERALL_BUDGET} USD, por lo que nos quedan {REMAINING_BUDGET} USD.</p>

    <p><b>Gastos en Comida (Salidas)</b></p>
    <p>Hemos gastado un total de ${DINING_OUT_EXPENSES} USD. </p>
    <p>El presupuesto de comida es de {splitwise.FOOD_BUDGET} USD, por lo que nos quedan {REMAINING_DINING_OUT_BUDGET} USD.</p>

    <p><b>Gastos en Groceries</b></p>
    <p>Hemos gastado un total de ${GROCERIES_EXPENSES} USD. </p>
    <p>El presupuesto de groceries es de {splitwise.GROCERIES_BUDGET} USD, por lo que nos quedan {REMAINING_GROCERIES_BUDGET} USD.</p>

    <p><b>Gastos en Transporte</b></p>
    <p>Hemos gastado un total de ${TRANSPORTATION_EXPENSES} USD. </p>
    <p>El presupuesto de transporte es de {splitwise.TRANSPORTATION_BUDGET} USD, por lo que nos quedan {REMAINING_TRANSPORTATION_BUDGET} USD.</p>

    <p>Que tengas un buen día!</p>
    <p>Saludos.</p> """  # noqa: E501

    # Send email
    for recipient in recipients:
        send_email_html(recipient, subject, html)

