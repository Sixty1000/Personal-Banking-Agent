import os
import asyncio
from pathlib import Path

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions import kernel_function
from typing import Annotated
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from dotenv import find_dotenv, load_dotenv

import matplotlib.pyplot as plt
import numpy as np



async def main():
    os.system('cls' if os.name=='nt' else 'clear')

    script_dir = Path(__file__).parent
    file_path = script_dir / 'data.txt'
    with file_path.open('r') as file:
        data = file.read() + "\n"
    data = data.rstrip('\n')
    
    user_prompt = input(f"{data}\n\nWhat would you like me to do with your data?\n\n")
    await process_expenses_data (user_prompt, data)

async def process_expenses_data(prompt, expenses_data):
    load_dotenv()
    ai_agent_settings = AzureAIAgentSettings()

    temp_data_file = Path("temp_expenses_data.txt")
    with temp_data_file.open('w') as f:
        f.write(expenses_data)

    

    async with (
        DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True) as creds,
        AzureAIAgent.create_client(
            credential=creds
        ) as project_client
    ):
        banking_agent_def = await project_client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="banking_agent",
            instructions=""""You are an AI Agent tasked with calculating the user's total monthly expenses.
                            The user's expense data is stored in a file called 'temp_expenses_data.txt'.
                            The file format is: Date,Amount,Details.
                            When the user requests total monthly expenses:
                            Use the adder-plugin to sum the expenses.
                            Feed the result into the graph-plugin using the x and y parameters to create a visual representation.
                            Then:
                            Provide spending advice based on the individual monthly totals.
                            Include a breakdown of spending by category using keywords in the 'Details' field.
                            Categories: Transfers/Zelle, Investments, Subscriptions, Dining, Shopping, Transportation, Fees, Entertainment, Other.
                            Match keywords like 'ZELLE', 'ROBINHOOD', 'NETFLIX', 'STARBUCKS', etc., to assign each transaction to a category.
                            Sum all expenses per category and return them in descending order of total spending.
                            Important:
                            Do not pass the expense data inline to any function calls.
                            Always set the file_path parameter to 'temp_expenses_data.txt'."""
        )

        banking_agent = AzureAIAgent(
            client=project_client,
            definition=banking_agent_def,
            plugins=[GraphPlugin(), AdderPlugin(), CategorizerPlugin()]
        )

        thread: AzureAIAgentThread = AzureAIAgentThread(client=project_client)
        try:
            prompt_messages = [f"{prompt} - The data is stored in the file 'temp_expenses_data.txt'"]
            response = await banking_agent.get_response(thread_id=thread.id, messages=prompt_messages)
            print(f"\n# {response.name}:\n{response}")
        except Exception as e:
            print(e)
        finally:
            await thread.delete() if thread else None
            await project_client.agents.delete_agent(banking_agent.id)
            if temp_data_file.exists():
                temp_data_file.unlink()

class CategorizerPlugin:
    @kernel_function(description="Returns categorized expense totals from the expense data file.")
    def categorize(
        self,
        name: Annotated[str, "Path to file containing expense data"] = "temp_expenses_data.txt"
    ):
        category_keywords = {
            'Transfers/Zelle': ['ZELLE', 'TRANSFER'],
            'Investments': ['ROBINHOOD', 'WEBULL', 'STOCK'],
            'Subscriptions': ['NETFLIX', 'SPOTIFY', 'APPLE.COM', 'PRIME', 'YOUTUBE', 'HULU'],
            'Dining': ['RESTAURANT', 'STARBUCKS', 'FOOD', 'CHIPOTLE', 'DOMINOS'],
            'Shopping': ['AMAZON', 'TARGET', 'WALMART', 'SHOP'],
            'Transportation': ['UBER', 'GAS', 'SHELL', 'EXXON', 'TOLL'],
            'Fees': ['FEE', 'CHARGE'],
            'Entertainment': ['MOVIE', 'CINEMA', 'GAME'],
        }

        category_totals = {k: 0.0 for k in category_keywords}
        category_totals['Other'] = 0.0

        with open(name, 'r') as file:
            lines = file.readlines()

        for line in lines:
            try:
                date, amount, details = line.strip().split(",", 2)
                amount = float(amount)
                if amount >= 0:
                    continue  # Skip income or deposits
                details_upper = details.upper()
                matched = False
                for category, keywords in category_keywords.items():
                    if any(keyword in details_upper for keyword in keywords):
                        category_totals[category] += abs(amount)
                        matched = True
                        break
                if not matched:
                    category_totals['Other'] += abs(amount)
            except:
                continue  # Skip malformed lines

        # Sort by spending amount
        sorted_totals = dict(sorted(category_totals.items(), key=lambda item: item[1], reverse=True))
        return sorted_totals

class GraphPlugin:
    @kernel_function(description="Creates a bar graph that plots the total expenses for each month of the year.")
    def create_graph(self,
                   x: Annotated[list[str], "Months of the year"],
                   y: Annotated[list[int], "The total expenses for every month"]):
        plt.figure(figsize=(12, 8))
        plt.bar(x, y, color='skyblue', edgecolor='black')
        plt.title('Monthly Expenses', fontsize=16)
        plt.xlabel('Months', fontsize=14)
        plt.ylabel('$', fontsize=14)
        plt.show()

class AdderPlugin:
    def get_expense_list(self, data):
        expense_list = []
        data_lines = data.split("\n")

        for line in data_lines:
            items = line.split(",")
            date = items[0]
            try:
                month = int(date.split("/")[0])
                expense_str = items[1]
                if(expense_str[0] == '-'):
                    expense = float(expense_str[1:])
                    expense_list.append([month, expense])
                else:
                    expense_list.append([month, 0.0])
            except ValueError:
                print("", end="")
                break

        return expense_list
        
    @kernel_function(description="Returns total expenses for month given.")
    def add(self,
            name: Annotated[str, "Path to file containing expense data"]="temp_expenses_data.txt"):
        with open(name, 'r') as file:
            data = file.read() + "\n"
        data.rstrip("\n")
        expense_list = self.get_expense_list(data)
        total_expense_monthly = [0.0] * 12
        for expense in expense_list:
            total_expense_monthly[expense[0] - 1] += expense[1]
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        monthly_expense_list = []
        for i in range(len(total_expense_monthly)):
            monthly_expense_list.append([months[i], expense_list[i]])
        
        return months, total_expense_monthly

if __name__ == "__main__":
    asyncio.run(main())
