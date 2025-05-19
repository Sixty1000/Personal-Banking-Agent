import os
import asyncio
from pathlib import Path


def get_expense_list(data):
        expense_list = []
        data_lines = data.split("\n")

        for line in data_lines:
            items = line.split(",")
            date = items[0]
            month = int(date.split("/")[0])
            expense_str = items[1]
            if(expense_str[0] == '-'):
                expense = float(expense_str[2:])
                expense_list.append([month, expense])
            else:
                expense_list.append([month, 0.0])

        return expense_list

def add(data):
        expense_list = get_expense_list(data)
        total_expense_monthly = [0.0] * 12
        for expense in expense_list:
            total_expense_monthly[expense[0] - 1] += expense[1]
        print(total_expense_monthly)

if "__main__" == __name__:
    os.system('cls' if os.name=='nt' else 'clear')

    script_dir = Path(__file__).parent
    file_path = script_dir / 'data.txt'

    with file_path.open('r') as file:
        data = file.read() + "\n"
    data = data.rstrip('\n')


    add(data)

