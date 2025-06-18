# Web Scrapper Assignment - Zyner.io

## Overview

This project scrapes startup data from the [Y Combinator](https://www.ycombinator.com/companies) website using Python. It extracts both dynamic fields (company name, batch, short description) and static fields (founder names, LinkedIn URLs).

## Approach

- Used **Selenium** and **BeautifulSoup** in Python to scrape dynamic company data and static founder details.
- Leveraged **ThreadPoolExecutor** for concurrent scraping to improve speed and efficiency.
- Implemented fallback parsing logic to ensure robustness against HTML variations.

## Tech Stack

- Python  
- Selenium  
- BeautifulSoup  
- pandas  
- concurrent.futures (ThreadPoolExecutor)

## References
- [BeautifulSoup Web Scraping Full Course (freeCodeCamp)](https://youtu.be/XVv6mJpFOb0?si=pQbPLTdTaUGL3EHK)
- [Selenium Course for Beginners (freeCodeCamp)](https://youtu.be/j7VZsCCnptM?si=DpfO9lGYg5vMv3dk)
- [Multithreading with ThreadPoolExecutor (Corey Schafer)](https://youtu.be/IEEhzQoKtQU?si=ih0Pnj6Jqr0ZqVwd)  
- [Python Selenium for Beginners (The PyCoach)](https://youtu.be/UOsRrxMKJYk?si=C3UlK-OQhfH1WAB9)  


## Output

- `yc_dynamic_data.csv`: Contains scraped dynamic fields  
- `yc_full_data.csv`: Contains dynamic + static fields  



