import requests
import pandas as pd
import sqlite3
import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('COMPANIES_HOUSE_API_KEY')
print(f"Loaded Companies House API Key: {'***' if API_KEY else 'Not Loaded'}")  # Debug Statement

BASE_URL = 'https://api.company-information.service.gov.uk'

DB_PATH = os.path.join('data', 'companies.db')

def get_company_profile(company_number):
    """
    Fetches the company profile from Companies House API.
    """
    url = f"{BASE_URL}/company/{company_number}"
    response = requests.get(url, auth=(API_KEY, ''))
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_filing_history(company_number):
    """
    Fetches the filing history of the company from Companies House API.
    """
    url = f"{BASE_URL}/company/{company_number}/filing-history"
    response = requests.get(url, auth=(API_KEY, ''))
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_officers(company_number):
    """
    Fetches the current officers (directors) of the company from Companies House API.
    """
    url = f"{BASE_URL}/company/{company_number}/officers"
    response = requests.get(url, auth=(API_KEY, ''))
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def init_db():
    """
    Initializes the SQLite database with necessary tables.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create companies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            company_number TEXT PRIMARY KEY,
            company_name TEXT,
            company_status TEXT,
            incorporation_date TEXT
        )
    ''')

    # Create officers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_number TEXT,
            name TEXT,
            role TEXT,
            appointed_on TEXT,
            resigned_on TEXT,
            FOREIGN KEY(company_number) REFERENCES companies(company_number)
        )
    ''')

    # Create filings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_number TEXT,
            category TEXT,
            description TEXT,
            date TEXT,
            FOREIGN KEY(company_number) REFERENCES companies(company_number)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


def store_company_data(company_number, profile):
    """
    Stores company profile data into the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO companies (company_number, company_name, company_status, incorporation_date)
        VALUES (?, ?, ?, ?)
    ''', (
        company_number,
        profile.get('company_name'),
        profile.get('company_status'),
        profile.get('date_of_creation')
    ))

    conn.commit()
    conn.close()


def store_officers(company_number, officers_data):
    """
    Stores officers data into the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for officer in officers_data.get('items', []):
        cursor.execute('''
            INSERT INTO officers (company_number, name, role, appointed_on, resigned_on)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            company_number,
            officer.get('name'),
            officer.get('officer_role'),
            officer.get('appointed_on'),
            officer.get('resigned_on')
        ))

    conn.commit()
    conn.close()


def store_filings(company_number, filings_data):
    """
    Stores filings data into the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for filing in filings_data.get('items', []):
        cursor.execute('''
            INSERT INTO filings (company_number, category, description, date)
            VALUES (?, ?, ?, ?)
        ''', (
            company_number,
            filing.get('category'),
            filing.get('description'),
            filing.get('date')
        ))

    conn.commit()
    conn.close()


def fetch_and_store(company_number):
    """
    Fetches data from Companies House API and stores it in the database.
    """
    try:
        profile = get_company_profile(company_number)
        filing_history = get_filing_history(company_number)
        officers = get_officers(company_number)

        store_company_data(company_number, profile)
        store_filing_history_in_files(company_number, filing_history)  # Optional: Store filings as JSON
        store_officers(company_number, officers)
        store_filings(company_number, filing_history)

        print(f"Data for company {company_number} stored successfully.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")


def store_filing_history_in_files(company_number, filings_data):
    """
    (Optional) Stores filing history as JSON files for detailed analysis.
    """
    company_dir = os.path.join('data', company_number)
    os.makedirs(company_dir, exist_ok=True)
    filepath = os.path.join(company_dir, 'filing_history.json')
    with open(filepath, 'w') as f:
        json.dump(filings_data, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Companies House Tool Utility')
    parser.add_argument('--init-db', action='store_true', help='Initialize the SQLite database.')
    parser.add_argument('--fetch', type=str, help='Fetch and store data for the given company number.')

    args = parser.parse_args()

    if args.init_db:
        init_db()
    elif args.fetch:
        fetch_and_store(args.fetch)
    else:
        parser.print_help()
