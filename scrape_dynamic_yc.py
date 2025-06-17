from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time


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


if __name__ == "__main__":
    driver = get_chrome_driver()
    driver.get("https://www.ycombinator.com/companies")
    time.sleep(3)

    print("📜 Scrolling to load startups...")
    cards = scroll(driver, target_count=100)  # Try with 100 first to test

    print(f"✅ Found {len(cards)} startup cards")

    # Print the first 5 names (if possible)
    for i, card in enumerate(cards[:5]):
        try:
            name = card.find_element(By.TAG_NAME, "h2").text
            print(f"{i+1}. {name}")
        except:
            print(f"{i+1}. ❌ Could not extract name")

    driver.quit()

# if __name__ == "__main__":
#     get_chrome_driver()
