import time # For adding delays during scraping
import pandas as pd # For handling data and reading/writing CSV files
from selenium import webdriver # For controlling the Chrome browser via Selenium
from selenium.webdriver.chrome.options import Options # To configure Chrome
from selenium.webdriver.support.ui import WebDriverWait # For waiting until certain conditions are met
from selenium.webdriver.support import expected_conditions as EC # For defining wait conditions
from selenium.webdriver.common.by import By # For locating elements on the webpage
from bs4 import BeautifulSoup # For parsing HTML content and extracting data
from concurrent.futures import ThreadPoolExecutor, as_completed # For running scraping tasks concurrently


# ----------------------------- #
#     SCRAPE DYNAMIC FIELDS     #
# ----------------------------- #

# Initializes and returns a Selenium WebDriver instance for Google Chrome.
def get_chrome_driver():
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options) # Launch a new Chrome browser instance with the given options
    print("Initializing driver...")
    return driver

# Scrolls through the Y Combinator companies page to dynamically load startup cards.
# Stops when the specified number of unique cards is reached or no more content loads.
def scroll(driver, target_count=500):
    last_height = driver.execute_script('return document.body.scrollHeight')
    startup_cards = set()

    while len(startup_cards) < target_count:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll to the bottom of the page
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select("a._company_i9oky_355")  # Select all visible startup card elements
        startup_cards.update(cards)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # If no change in height, stop scrolling
            break
        last_height = new_height # Update scroll height tracker for the next iteration

    return driver.find_elements(By.CSS_SELECTOR, "a._company_i9oky_355") # Return all loaded startup card elements

# Scrapes company name, batch, description, and detail URL from the Y Combinator companies page
def scrape_dynamic_fields():
    driver = get_chrome_driver()
    driver.get("https://www.ycombinator.com/companies") # Open YC companies listing page
    time.sleep(3)

    cards = scroll(driver, target_count=500)
    data = [] # List to store extracted company data

    for i, card in enumerate(cards[:500]):
        try:

            card_html = card.get_attribute("outerHTML") # Get the outer HTML of the card
            soup = BeautifulSoup(card_html, "html.parser")

            name_tag = soup.find('span', class_='_coName_i9oky_470').text.strip()  # Extract company name
            batch_tag = batch_tag = soup.find('span', class_='pill _pill_i9oky_33').text.strip() # Extract batch
            description_tag = soup.find('span', class_='_coDescription_i9oky_495').text.strip() # Extract short description
            url = card.get_attribute("href") # Extract detail page URL

            # Add extracted data to the list
            data.append({
                "Company Name": name_tag,
                "Batch": batch_tag,
                "Short Description": description_tag,
                "Detail URL": url
            })

            print(f"[{i+1}/500] Scraped: {name_tag}")
        except Exception as e:
            print(f"[{i+1}] Error: {e}")
            continue # Skip to next card if an error occurs
    driver.quit() # Close the browser after scraping is complete

    # Save to CSV
    df = pd.DataFrame(data) # Convert the list of dictionaries into a pandas DataFrame
    df.to_csv("yc_dynamic_data.csv", index=False) # Save the DataFrame to a CSV file without row indices
    print("Saved to yc_dynamic_data.csv!")





# ----------------------------- #
#    SCRAPE STATIC FIELDS       #
# ----------------------------- #


def fetch_static_data_with_index(i, row):
    url = row["Detail URL"] # Extract company detail page URL from the row
    company_name = row["Company Name"] # Extract company name from the row

    driver = get_chrome_driver()
    founders, linkedin_urls = "", "" # Initialize placeholders for scraped data

    try:
        driver.get(url)  # Navigate to the company’s detail page
        WebDriverWait(driver, 8).until( # Wait until founder info block is loaded
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.text-xl.font-bold"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        founder_names = [] # List to store founder names
        linkedin_links = [] # List to store LinkedIn profile links


        founder_blocks = soup.select("div.min-w-0.flex-1") # Select blocks potentially containing founder info

        # Loop through each founder block
        for block in founder_blocks:
            name_tag = block.find("div", class_="text-xl font-bold")
            link_tag = block.find("a", href=True)

            if name_tag:
                name = name_tag.get_text(strip=True) # Clean and extract name text
                if name:
                    founder_names.append(name)

            if link_tag:
                href = link_tag["href"]
                if "linkedin.com" in href and "school/y-combinator" not in href: # Filter out non-profile links
                    if href.startswith("/"): # Convert relative links to absolute
                        href = "https://www.ycombinator.com" + href
                    linkedin_links.append(href)

        # If no names found in standard layout, try fallback
        if not founder_names:
            fallback_blocks = soup.select("div.flex.flex-row.items-center.justify-between div")
            for block in fallback_blocks:
                if "Founder" in block.get_text(strip=True):
                    maybe_name = block.find_previous_sibling("div")
                    if maybe_name:
                        founder_names.append(maybe_name.get_text(strip=True))

        # Fallback: Search entire page for valid LinkedIn profile links
        if not linkedin_links:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "linkedin.com/in/" in href and "school/y-combinator" not in href:
                    if href.startswith("/"):
                        href = "https://www.ycombinator.com" + href
                    linkedin_links.append(href)

        # Clean whitespace and remove duplicates while preserving order
        founder_names = list(dict.fromkeys([f.strip() for f in founder_names if f.strip()]))
        linkedin_links = list(dict.fromkeys([l.strip() for l in linkedin_links if l.strip()]))

        # Log if no data found
        if not founder_names:
            print(f"[{i+1}/500] No founder names found at {url}")
        if not linkedin_links:
            print(f"[{i+1}/500] No LinkedIn links found at {url}")

        founders = ", ".join(founder_names) # Combine names into single string
        linkedin_urls = ", ".join(linkedin_links) # Combine URLs into single string

        # Log scraping details
        print(f"[{i+1}/500] Scraped: {company_name} -> Founders: {founders}")
    except Exception as e:
        print(f"[{i+1}/500] Error at {url}: {e}")
    finally:
        driver.quit() # Ensure the browser is closed

    # Return index and scraped data for merging into DataFrame
    return i, {
        "Founder Name(s)": founders,
        "Founder LinkedIn URL(s)": linkedin_urls
    }

# Scrapes founder names and LinkedIn URLs using multithreading
def scrape_static_fields_concurrently(max_workers=10):
    df = pd.read_csv("yc_dynamic_data.csv") # Load the previously scraped dynamic data from CSV
    results = {}

    # Create a thread pool executor for concurrent scraping
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit a scraping task for each row in the DataFrame and map futures to row indices
        future_to_index = {
            executor.submit(fetch_static_data_with_index, i, row): i
            for i, row in df.iterrows()
        }

        # Collect results as threads complete
        for future in as_completed(future_to_index):
            try:
                # Get the result and store it using the correct index
                i, result = future.result()
                results[i] = result
            except Exception as e:
                # Handle errors and store empty data for failed rows
                i = future_to_index[future]
                print(f"Thread error at index {i}: {e}")
                results[i] = {
                    "Founder Name(s)": "",
                    "Founder LinkedIn URL(s)": ""
                }
    # Update the DataFrame with the scraped founder names and LinkedIn URLs for each company
    for i, data in results.items():
        df.at[i, "Founder Name(s)"] = data["Founder Name(s)"] # Set founder names for row i
        df.at[i, "Founder LinkedIn URL(s)"] = data["Founder LinkedIn URL(s)"] # Set LinkedIn URLs for row i

    # Export the final dataset to CSV after dropping the 'Detail URL' column
    df.drop(columns=["Detail URL"]).to_csv("yc_full_data.csv", index=False)
    print("Saved full dataset to yc_full_data.csv!")


# --------------------------------- #
#           Run Both Parts          #
# --------------------------------- #
if __name__ == "__main__":
    scrape_dynamic_fields()
    scrape_static_fields_concurrently(max_workers=10)