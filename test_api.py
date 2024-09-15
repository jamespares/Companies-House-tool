import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('COMPANIES_HOUSE_API_KEY')
COMPANY_NUMBER = '00000136'  # Replace with a valid company number if needed

def test_api_call(api_key, company_number):
    if not api_key:
        print("API key not found. Please check your .env file.")
        return

    url = f'https://api.company-information.service.gov.uk/company/{company_number}'
    try:
        response = requests.get(url, auth=(api_key, ''))
        if response.status_code == 200:
            print("API call successful. Company details:")
            print(response.json())
        elif response.status_code == 401:
            print("Unauthorized: Invalid API key.")
        elif response.status_code == 404:
            print(f"Company {company_number} not found.")
        else:
            print(f"Failed to retrieve company details. Status code: {response.status_code}")
            print("Response:", response.text)
    except Exception as e:
        print("An error occurred while making the API call:", e)

if __name__ == "__main__":
    test_api_call(API_KEY, COMPANY_NUMBER)
