import pytz
import requests
import pandas as pd
from datetime import datetime

# URL
from keys import KEY

# Request to splitwise API


class Splitwise:
    FOOD_BUDGET = 250
    GROCERIES_BUDGET = 500
    TRANSPORTATION_BUDGET = 100
    OVERALL_BUDGET = 1110
    DESIRED_USER = "Lluvia"
    UNDESIRED_GROUPS = [50435769, 38405778]
    UNDESIRED_EXPENSES = ["Medicamento"]
    NUM_DECIMALS = 2

    def __init__(self):
        self.KEY = KEY
        self.num_expenses = 200
        # Get all groups
        self.groups_url = "https://secure.splitwise.com/api/v3.0/get_groups"

        # List last 100 expenses
        self.expenses_url = "https://secure.splitwise.com/api/v3.0/get_expenses/?limit={self.num_expenses}}"
        self.headers = {"Authorization": "Bearer " + self.KEY}

        # Get first day of the month

    def get_month_first_day(self):
        """
        Returns first day of the month
        """
        today = datetime.now(pytz.timezone("US/Central"))
        self.todays_month = today.month

    def filter_month_expenses(self, expenses_df):
        """
        Filters expenses that happened this month
        """
        self.get_month_first_day()
        expenses_df["date"] = pd.to_datetime(expenses_df["date"])
        # Get month column
        expenses_df["month"] = expenses_df["date"].dt.month
        expenses_df = expenses_df.loc[expenses_df["month"] == self.todays_month].copy()
        expenses_df.reset_index(inplace=True, drop=True)
        expenses_df.drop(columns=["month"], inplace=True)

        return expenses_df

    def group_by_category(self, expenses_df):
        """
        Groups expenses by category
        """
        category_expenses_df = (
            expenses_df.groupby(by="category").sum(numeric_only=True).reset_index()
        )

        # Round to two decimals
        category_expenses_df = category_expenses_df.round(self.NUM_DECIMALS)

        self.category_expenses_df = category_expenses_df

    def get_remaining_budget(self):
        """
        Creates a dataframe that has the remaining budget for the month
        """
        remaining_budget = pd.DataFrame(
            [
                ["Dining out", self.FOOD_BUDGET],
                ["Groceries", self.GROCERIES_BUDGET],
                ["Taxi", self.TRANSPORTATION_BUDGET],
                ["Overall", self.OVERALL_BUDGET],
            ],
            columns=["category", "budget"],
        )
        remaining_budget = remaining_budget.merge(
            self.category_expenses_df, on="category", how="inner"
        )
        remaining_budget["remaining_budget"] = (
            remaining_budget["budget"] - remaining_budget["cost"]
        )
        remaining_budget["remaining_budget"] = remaining_budget[
            "remaining_budget"
        ].astype(float)
        # Round to two decimals
        remaining_budget = remaining_budget.round(self.NUM_DECIMALS)

        self.remaining_budget = remaining_budget

    def get_expenses(self):
        """
        Gets expenses from splitwise API
        """
        response = requests.get(self.expenses_url, headers=self.headers)
        expenses = response.json()["expenses"]
        expense_dict_list = []
        for expense in expenses:
            expense_dict = {}
            expense_dict["description"] = expense["description"]
            expense_dict["cost"] = expense["cost"]
            expense_dict["category"] = expense["category"]["name"]
            expense_dict["date"] = expense["date"]

            users = expense["users"]
            user_names = [user["user"]["first_name"] for user in users]

            if expense["group_id"] in self.UNDESIRED_GROUPS:
                print("Skipping expense: ", expense_dict["description"])
                continue

            if self.DESIRED_USER not in user_names:
                print("Skipping expense: ", expense_dict["description"])
                continue

            if expense_dict["description"] in self.UNDESIRED_EXPENSES:
                print("Skipping expense: ", expense_dict["description"])
                continue

            expense_dict_list.append(expense_dict)
        expenses_df = pd.DataFrame.from_dict(expense_dict_list)

        # Filter by month
        expenses_df = self.filter_month_expenses(expenses_df)
        expenses_df["cost"] = expenses_df["cost"].astype(float)

        # Round cost to 2 decimals
        expenses_df.loc[:, "cost"] = expenses_df.loc[:, "cost"].round(self.NUM_DECIMALS)

        # Group by category
        self.group_by_category(expenses_df)

        # Get remaining budget
        self.get_remaining_budget()

        # Get total expenses
        self.total_expenses = expenses_df["cost"].sum()
        # Round to two decimals
        self.total_expenses = round(self.total_expenses, self.NUM_DECIMALS)

        return expenses_df
