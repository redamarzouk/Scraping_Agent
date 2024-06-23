from firecrawl import FirecrawlApp
from openai import OpenAI
from dotenv import load_dotenv
import os 
import json 
import pandas as pd 
from datetime import datetime


def scrape_data(url):
    load_dotenv()
    # Initialize the FirecrawlApp with your API key
    app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))
    
    # Scrape a single URL
    scraped_data = app.scrape_url(url,{'pageOptions':{'onlyMainContent': True}})
    
    # Check if 'markdown' key exists in the scraped data
    if 'markdown' in scraped_data:
        return scraped_data['markdown']
    else:
        raise KeyError("The key 'markdown' does not exist in the scraped data.")
    
def save_raw_data(raw_data, timestamp, output_folder='output'):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Save the raw markdown data with timestamp in filename
    raw_output_path = os.path.join(output_folder, f'rawData_{timestamp}.md')
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_data)
    print(f"Raw data saved to {raw_output_path}")

def format_data(data, fields=None):
    load_dotenv()
    # Instantiate the OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Assign default fields if not provided
    if fields is None:
        fields = ["Address", "Real Estate Agency", "Price", "Beds", "Baths", "Sqft", "Home Type", "Listing Age", "Picture of home URL", "Listing URL"]

    # Define system message content
    system_message = f"""You are an intelligent text extraction and conversion assistant. Your task is to extract structured information 
                        from the given text and convert it into a pure JSON format. The JSON should contain only the structured data extracted from the text, 
                        with no additional commentary, explanations, or extraneous information. 
                        You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
                        Please process the following text and provide the output in pure JSON format with no words before or after the JSON:"""

    # Define user message content
    user_message = f"Extract the following information from the provided text:\nPage content:\n\n{data}\n\nInformation to extract: {fields}"


    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    # Check if the response contains the expected data
    if response and response.choices:
        formatted_data = response.choices[0].message.content.strip()
        print(f"Formatted data received from API: {formatted_data}")

        try:
            parsed_json = json.loads(formatted_data)
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            print(f"Formatted data that caused the error: {formatted_data}")
            raise ValueError("The formatted data could not be decoded into JSON.")
        
        return parsed_json
    else:
        raise ValueError("The OpenAI API response did not contain the expected choices data.")
    

def save_formatted_data(formatted_data, timestamp, output_folder='output'):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Save the formatted data as JSON with timestamp in filename
    output_path = os.path.join(output_folder, f'sorted_data_{timestamp}.json')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, indent=4)
    print(f"Formatted data saved to {output_path}")

    # Check if data is a dictionary and contains exactly one key
    if isinstance(formatted_data, dict) and len(formatted_data) == 1:
        key = next(iter(formatted_data))  # Get the single key
        formatted_data = formatted_data[key]

    
    # Convert the formatted data to a pandas DataFrame
    df = pd.DataFrame(formatted_data)

    # Convert the formatted data to a pandas DataFrame
    if isinstance(formatted_data, dict):
        formatted_data = [formatted_data]

    df = pd.DataFrame(formatted_data)

    # Save the DataFrame to an Excel file
    excel_output_path = os.path.join(output_folder, f'sorted_data_{timestamp}.xlsx')
    df.to_excel(excel_output_path, index=False)
    print(f"Formatted data saved to Excel at {excel_output_path}")

if __name__ == "__main__":
    # Scrape a single URL
    #url = 'https://www.zillow.com/salt-lake-city-ut/'
    url = 'https://www.trulia.com/CA/San_Francisco/'
    #url = 'https://www.seloger.com/immobilier/achat/immo-lyon-69/'
    
    try:
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Scrape data
        raw_data = scrape_data(url)
        
        # Save raw data
        save_raw_data(raw_data, timestamp)
        
        # Format data
        formatted_data = format_data(raw_data)
        
        # Save formatted data
        save_formatted_data(formatted_data, timestamp)
    except Exception as e:
        print(f"An error occurred: {e}")
