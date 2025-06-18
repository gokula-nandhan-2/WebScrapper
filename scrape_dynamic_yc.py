import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initializes and returns a headless Chrome browser using Selenium
def get_chrome_driver():
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    print("Initializing driver...")
    return driver

def scroll(driver, target_count=500):
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

    cards = scroll(driver, target_count=500)
    data = []

    for i, card in enumerate(cards[:500]):
        try:

            card_html = card.get_attribute("outerHTML")
            soup = BeautifulSoup(card_html, "html.parser")

            name_tag = soup.find('span', class_='_coName_i9oky_470').text.strip()
            batch_tag = batch_tag = soup.find('span', class_='pill _pill_i9oky_33').text.strip()
            description_tag = soup.find('span', class_='_coDescription_i9oky_495').text.strip()
            url = card.get_attribute("href")

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
    print("Saved to yc_dynamic_data.csv")

def fetch_static_data_with_index(i, row):
    url = row["Detail URL"]
    company_name = row["Company Name"]

    driver = get_chrome_driver()
    founders, linkedin_urls = "", ""

    try:
        driver.get(url)
        WebDriverWait(driver, 8).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.text-xl.font-bold"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        founder_names = []
        linkedin_links = []

        # ✅ Find all possible founder blocks
        founder_blocks = soup.select("div.min-w-0.flex-1")

        for block in founder_blocks:
            name_tag = block.find("div", class_="text-xl font-bold")
            link_tag = block.find("a", href=True)

            if name_tag:
                name = name_tag.get_text(strip=True)
                if name:
                    founder_names.append(name)

            if link_tag:
                href = link_tag["href"]
                if "linkedin.com" in href and "school/y-combinator" not in href:
                    if href.startswith("/"):
                        href = "https://www.ycombinator.com" + href
                    linkedin_links.append(href)

        # 🔄 Fallback if no names found
        if not founder_names:
            fallback_blocks = soup.select("div.flex.flex-row.items-center.justify-between div")
            for block in fallback_blocks:
                if "Founder" in block.get_text(strip=True):
                    maybe_name = block.find_previous_sibling("div")
                    if maybe_name:
                        founder_names.append(maybe_name.get_text(strip=True))

        # 🔍 Fallback for LinkedIn
        if not linkedin_links:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "linkedin.com/in/" in href and "school/y-combinator" not in href:
                    if href.startswith("/"):
                        href = "https://www.ycombinator.com" + href
                    linkedin_links.append(href)

        # 🧹 Clean and deduplicate
        founder_names = list(dict.fromkeys([f.strip() for f in founder_names if f.strip()]))
        linkedin_links = list(dict.fromkeys([l.strip() for l in linkedin_links if l.strip()]))

        if not founder_names:
            print(f"[{i+1}/500] No founder names found at {url}")
        if not linkedin_links:
            print(f"[{i+1}/500] No LinkedIn links found at {url}")

        founders = ", ".join(founder_names)
        linkedin_urls = ", ".join(linkedin_links)

        print(f"[{i+1}/500] Scraped: {company_name} -> Founders: {founders}")
    except Exception as e:
        print(f"[{i+1}/500] Error at {url}: {e}")
    finally:
        driver.quit()

    return i, {
        "Founder Name(s)": founders,
        "Founder LinkedIn URL(s)": linkedin_urls
    }


def scrape_static_fields_concurrently(max_workers=10):
    df = pd.read_csv("yc_dynamic_data.csv")
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(fetch_static_data_with_index, i, row): i
            for i, row in df.iterrows()
        }

        for future in as_completed(future_to_index):
            try:
                i, result = future.result()
                results[i] = result
            except Exception as e:
                i = future_to_index[future]
                print(f"Thread error at index {i}: {e}")
                results[i] = {
                    "Founder Name(s)": "",
                    "Founder LinkedIn URL(s)": ""
                }


    for i, data in results.items():
        df.at[i, "Founder Name(s)"] = data["Founder Name(s)"]
        df.at[i, "Founder LinkedIn URL(s)"] = data["Founder LinkedIn URL(s)"]


    df.drop(columns=["Detail URL"]).to_csv("yc_full_data.csv", index=False)
    print("Saved full dataset to yc_full_data.csv!")


# --------- Run Both Parts --------- #
if __name__ == "__main__":
    scrape_dynamic_fields()
    scrape_static_fields_concurrently(max_workers=10)