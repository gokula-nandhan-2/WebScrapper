from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initializes and returns a headless Chrome browser using Selenium
def get_chrome_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    print("🚀 Initializing driver...")
    return driver

# Testing part of the get_chrome_Method
# driver = get_chrome_driver()
# driver.get("https://www.ycombinator.com/companies")
# time.sleep(10)

def scroll(driver, target_count=10):
    last_height = driver.execute_script('return document.body.scrollHeight')
    startup_cards = set()

    while len(startup_cards) < target_count:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select("a._company_i9oky_355")
        startup_cards.update(cards)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return driver.find_elements(By.CSS_SELECTOR, "a._company_i9oky_355")

def scrape_dynamic_fields():
    driver = get_chrome_driver()
    driver.get("https://www.ycombinator.com/companies")
    time.sleep(3)

    cards = scroll(driver, target_count=10)
    data = []

    for i, card in enumerate(cards[:10]):
        try:

            card_html = card.get_attribute("outerHTML")
            soup = BeautifulSoup(card_html, "html.parser")

            name_tag = soup.find('span', class_='_coName_i9oky_470').text.strip()
            batch_tag = soup.find('div', class_='_pillWrapper_i9oky_33').text.strip()
            description_tag = soup.find('span', class_='_coDescription_i9oky_495').text.strip()
            url = card.get_attribute("href")

            # name = card.find_element(By.TAG_NAME, "h2").text
            # batch = card.find_element(By.TAG_NAME, "div").text
            # description = card.find_element(By.TAG_NAME, "p").text
            # url = card.get_attribute("href")

            data.append({
                "Company Name": name_tag,
                "Batch": batch_tag,
                "Short Description": description_tag,
                "Detail URL": url
            })

            print(f"[{i+1}/500] Scraped: {name_tag}")
        except Exception as e:
            print(f"[{i+1}] Error: {e}")
            continue
    driver.quit()

    # Save to CSV
    df = pd.DataFrame(data)
    df.to_csv("yc_dynamic_data.csv", index=False)
    print("✅ Saved to yc_dynamic_data.csv")

#

def fetch_static_data_with_index(i, row):
    url = row["Detail URL"]
    name = row["Company Name"]

    driver = get_chrome_driver()
    founders, linkedin_urls = "", ""

    try:
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # links = soup.select("div[class*='FounderSection'] a")

        founder_tags = soup.select("div.text-xl.font-bold")
        founder_names = [tag.get_text(strip=True) for tag in founder_tags]

        # founder_names = []
        # linkedin_links = []

        # for link in links:
        #     href = link.get("href", "")
        #     if "linkedin.com" in href:
        #         founder_names.append(link.text.strip())
        #         linkedin_links.append(href)

        linkedin_links = [
            a.get("href", "") for a in soup.select("a[href*='linkedin.com']")
            if "school/y-combinator" not in a.get("href", "")
        ]

        founders = ', '.join(founder_names)
        linkedin_urls = ', '.join(linkedin_links)

        print(f"[{i+1}] ✅ Scraped: {name}")
    except Exception as e:
        print(f"[{i+1}] ❌ Error at {url}: {e}")
    finally:
        driver.quit()

    return {
        "Founder Name(s)": founders,
        "Founder LinkedIn URL(s)": linkedin_urls
    }


def scrape_static_fields_concurrently(max_workers=5):
    df = pd.read_csv("yc_dynamic_data.csv")
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(fetch_static_data_with_index, i, row): i
            for i, row in df.iterrows()
        }

        for future in as_completed(future_to_index):
            i = future_to_index[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Thread error at index {i}: {e}")
                results.append({
                    "Founder Name(s)": "",
                    "Founder LinkedIn URL(s)": ""
                })

    static_df = pd.DataFrame(results)
    final_df = pd.concat([df, static_df], axis=1)
    final_df.drop(columns=["Detail URL"]).to_csv("yc_full_data.csv", index=False)
    print("✅ Saved full dataset to yc_full_data.csv")



# --------- Run Both Parts --------- #
if __name__ == "__main__":
    scrape_dynamic_fields()
    scrape_static_fields_concurrently(max_workers=10)