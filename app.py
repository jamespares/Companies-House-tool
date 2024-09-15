from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sqlite3
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from utils import fetch_and_store

# Use a non-interactive backend for Matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

DB_PATH = os.path.join('data', 'companies.db')


def get_company_from_db(company_number):
    """
    Retrieves company profile from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM companies WHERE company_number = ?', (company_number,))
    result = cursor.fetchone()
    conn.close()
    if result:
        keys = ['company_number', 'company_name', 'company_status', 'incorporation_date']
        return dict(zip(keys, result))
    return None


def get_officers_from_db(company_number):
    """
    Retrieves officers data from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name, role, appointed_on, resigned_on FROM officers WHERE company_number = ?', (company_number,))
    results = cursor.fetchall()
    conn.close()
    officers = []
    for row in results:
        officers.append({
            'name': row[0],
            'role': row[1],
            'appointed_on': row[2],
            'resigned_on': row[3]
        })
    return officers


def get_filings_from_db(company_number):
    """
    Retrieves filings data from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT category, date FROM filings WHERE company_number = ?', (company_number,))
    results = cursor.fetchall()
    conn.close()
    filings = []
    for row in results:
        filings.append({
            'category': row[0],
            'date': row[1]
        })
    return filings


def create_filing_plot(filings):
    """
    Creates a bar plot of number of filings per year.
    Returns the plot as a base64-encoded string.
    """
    if not filings:
        return None

    df = pd.DataFrame(filings)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    filings_per_year = df.groupby('year').size().reset_index(name='count')

    plt.figure(figsize=(10,6))
    sns.barplot(data=filings_per_year, x='year', y='count', palette='viridis')
    plt.title('Number of Filings Per Year')
    plt.xlabel('Year')
    plt.ylabel('Number of Filings')
    plt.xticks(rotation=45)

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        company_number = request.form.get('company_number').strip()
        if not company_number:
            flash('Please enter a company number.', 'warning')
            return redirect(url_for('index'))
        
        # Fetch data and store in DB
        try:
            fetch_and_store(company_number)
            return redirect(url_for('report', company_number=company_number))
        except Exception as e:
            flash(f'Error fetching data: {e}', 'danger')
            return redirect(url_for('index'))
    return render_template('index.html')


@app.route('/report/<company_number>')
def report(company_number):
    company = get_company_from_db(company_number)
    if not company:
        flash('Company not found in the database.', 'warning')
        return redirect(url_for('index'))
    
    officers = get_officers_from_db(company_number)
    filings = get_filings_from_db(company_number)
    plot = create_filing_plot(filings)

    return render_template('report.html', company=company, officers=officers, plot=plot)


if __name__ == '__main__':
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)
