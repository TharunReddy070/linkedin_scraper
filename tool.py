from playwright.sync_api import sync_playwright
from models import LinkedInProfile
import time
import os
from dotenv import load_dotenv
from typing import Optional, Any
from pydantic import Field
import logging
import pandas as pd
from datetime import datetime
import csv
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class LinkedInTool():
    def __init__(self):
        self.username = os.getenv('LINKEDIN_USERNAME')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    def scroll_smoothly(self):
        """Scroll the page smoothly to the bottom."""
        try:
            # Get initial scroll height
            last_height = self.page.evaluate('document.body.scrollHeight')
            current_position = 0
            step = 300  # Smaller step for smoother scrolling
            
            while current_position < last_height:
                # Scroll down smoothly
                current_position = min(current_position + step, last_height)
                self.page.evaluate(f'window.scrollTo(0, {current_position})')
                time.sleep(0.5)  # Add delay for smooth scrolling
                
                # Update scroll height
                new_height = self.page.evaluate('document.body.scrollHeight')
                if new_height > last_height:
                    last_height = new_height
                    
            # Scroll back to top smoothly
            while current_position > 0:
                current_position = max(current_position - step, 0)
                self.page.evaluate(f'window.scrollTo(0, {current_position})')
                time.sleep(0.3)  # Slightly faster scroll up
                
        except Exception as e:
            logger.error(f"Error during smooth scrolling: {str(e)}")
            
    def wait_for_element(self, selector, timeout=60000, state="visible"):
        try:
            self.page.wait_for_selector(selector, state=state, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Timeout waiting for selector {selector}: {str(e)}")
            return False
            
    def _run(self, keyword: str, limit: int = 5, location: str = "India") -> str:
        """Execute the LinkedIn search and scraping."""
        try:
            logger.info(f"Starting LinkedIn search for keyword: {keyword} with limit: {limit}")
            self.init_browser()
            self.login()
            results = self.search_and_scrape(keyword, location)
            
            if results:
                # Results are already dictionaries, no need for vars()
                df = pd.DataFrame(results)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"linkedin_results_{keyword}_{timestamp}.csv"
                df.to_csv(filename, index=False)
                logger.info(f"Results saved to {filename}")
                
            self.cleanup()
            return results
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            self.cleanup()
            return f"Error occurred: {str(e)}"
       
    def init_browser(self):
        logger.info("Initializing browser...")
        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.launch(
                headless=False,  # Set to True in production
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                logger.error("Browser executable not found. Installing browsers via 'playwright install'.")
                subprocess.run(["playwright", "install"], check=True)
                # Retry launching browser after installation
                self.browser = self.playwright.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
            else:
                raise
        self.context = self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            locale='en-US',
            timezone_id='America/New_York'
        )
        self.page = self.context.new_page()
        logger.info("Browser initialized successfully")
        
    def login(self):
        try:
            logger.info("Attempting to log in to LinkedIn...")
            self.page.goto('https://www.linkedin.com/login')
            time.sleep(2)  # Wait for page to stabilize
            
            # Wait for login form
            if not self.wait_for_element('#username', timeout=10000):
                raise Exception("Login page did not load properly")
            
            # Fill in credentials    
            self.page.fill('#username', self.username)
            time.sleep(1)
            self.page.fill('#password', self.password)
            time.sleep(1)
            
            # Click login and wait for navigation
            self.page.click('button[type="submit"]')
            time.sleep(5)  # Wait for login to complete
            
            # Verify login success
            if "feed" in self.page.url or "mynetwork" in self.page.url:
                logger.info("Successfully logged in to LinkedIn")
            else:
                raise Exception("Login unsuccessful")
                
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
        
    def apply_location_filter(self, location: str) -> None:
        """
        Applies the location filter to the current LinkedIn People search.

        Steps performed:
        1. Clicks on the "Locations" filter button using its XPath.
        2. Waits for the filter pane to load.
        3. Presses TAB twice to move focus to the location search bar.
        4. Types in the provided location.
        5. Presses the DOWN ARROW key to select the suggestion.
        6. Presses ENTER to apply the location selection.
        7. Clicks on the "SHOW RESULTS" button using the new XPath.
        8. Waits for the page to load the updated results.
        """
        logger.info("Applying location filter...")

        # Step 1: Click the "Locations" filter button.
        location_filter_button = self.page.query_selector('//button[contains(@id, "searchFilter_geoUrn")]')
        if not location_filter_button:
            logger.error("Location filter button not found.")
            return
        location_filter_button.click()
        time.sleep(3)  # Wait for the filter modal to load

        # Step 2: Press TAB twice to focus on the location search bar.
        self.page.keyboard.press("Tab")
        time.sleep(0.5)
        self.page.keyboard.press("Tab")
        time.sleep(0.5)

        # Step 3: Type the location into the search bar.
        self.page.keyboard.type(location)
        time.sleep(1)

        # Step 4: Press the DOWN arrow key to select the suggestion.
        self.page.keyboard.press("ArrowDown")
        time.sleep(0.5)

        # Step 5: Press ENTER to apply the location selection.
        self.page.keyboard.press("Enter")
        time.sleep(1)

        # Step 6: Click on the "SHOW RESULTS" button using the new XPath.
        show_results_xpath = '//div[contains(@id, "hoverable-outlet-locations-filter-value")]/div/div/div/form/fieldset/div[2]/button[2]'
        try:
            show_results_button = self.page.wait_for_selector(show_results_xpath, timeout=10000)
            show_results_button.click()
            time.sleep(5)  # Wait for updated results to load
            logger.info("Location filter applied and results loaded.")
        except Exception as e:
            logger.error(f"Could not find or click the 'Show Results' button using new XPath: {str(e)}")


    def search_and_scrape(self, keyword: str, location: str) -> list[LinkedInProfile]:
        logger.info(f"Starting search for profiles with keyword: {keyword}")
        profiles = []
        try:
            # Step 1: Navigate to LinkedIn Home Page.
            self.page.goto('https://www.linkedin.com/feed/', timeout=60000)
            time.sleep(3)
            
            # Step 2: Find the search bar and type in the keyword.
            search_box = self.page.query_selector('input.search-global-typeahead__input')
            if not search_box:
                search_box = self.page.query_selector('input[placeholder*="Search"]')
            if not search_box:
                raise Exception("Could not find search box")
            search_box.click()
            search_box.fill('')
            for char in keyword:
                search_box.type(char)
                time.sleep(0.2)
            time.sleep(1)
            self.page.keyboard.press('Enter')
            time.sleep(5)
            logger.info(f"Current URL after search: {self.page.url}")

            # Step 3: Click on the "People" filter button.
            people_button = None
            selectors_to_try = [
                'button.artdeco-pill.artdeco-pill--slate.artdeco-pill--choice.artdeco-pill--2.search-reusables__filter-pill-button:has-text("People")',
                'button[type="button"]:has-text("People")',
                '//button[contains(text(), "People")]'  # XPath
            ]
            for selector in selectors_to_try:
                try:
                    if selector.startswith('//'):
                        people_button = self.page.query_selector(f"xpath={selector}")
                    else:
                        people_button = self.page.query_selector(selector)
                    if people_button:
                        logger.info(f"Found People button using selector: {selector}")
                        break
                except Exception as e:
                    logger.error(f"Error trying selector {selector}: {str(e)}")
            if not people_button:
                logger.error("Could not find People filter button with any selector")
                return profiles
            logger.info("Clicking People filter button")
            people_button.click()
            time.sleep(5)
            logger.info(f"URL after clicking People: {self.page.url}")

            # ***** NEW LOCATION FILTER STEP (Between Steps 3 and 4) *****
            logger.info("Applying location filter before scraping profiles...")
            self.apply_location_filter(location)
            logger.info("Location filter applied. Proceeding with profile scraping...")

            # Step 4: Process the profiles after applying filters.
            logger.info("Waiting for results to load...")
            time.sleep(5)
            all_profile_data = []
            pages_to_scrape = 3
            for page_num in range(pages_to_scrape):
                try:
                    self.page.wait_for_selector('//div[contains(@class, "mb1")]', timeout=5000)
                    profile_containers = self.page.query_selector_all('//div[contains(@class, "mb1")]')
                    if not profile_containers:
                        logger.error(f"No profiles found on page {page_num + 1}")
                        break
                    logger.info(f"\nProcessing page {page_num + 1}")
                    logger.info(f"Found {len(profile_containers)} profile container(s)")
                    for container in profile_containers:
                        try:
                            text_content = container.inner_text().strip()
                            link_elements = container.query_selector_all('a')
                            links = [link.get_attribute('href') for link in link_elements if link.get_attribute('href')]
                            
                                # Parse the text content into lines
                            lines = [line.strip() for line in text_content.split("\n") if line.strip()]
                            if not lines or len(lines) < 3:
                                # Fallback if not enough information
                                name = text_content.split()[0]
                                current_role = ""
                                location = ""
                            else:
                                name = lines[0]
                                location = lines[-1]
                                current_role = lines[-2] if len(lines) >= 2 else ""
                            
                            logger.info("\nParsed Profile Data:")
                            logger.info(f"Text Content: {text_content}")
                            logger.info(f"Links: {links}")
                            logger.info("-" * 50)

                            profile_data = {
                                "TYPE": "People",
                                "NAME": name,
                                "CURRENT ROLE": current_role,
                                "LOCATION": location,
                                "PROFILE URL": links[0] if links else ""
                            }
                            all_profile_data.append(profile_data)
                        except Exception as e:
                            logger.error(f"Error parsing profile container: {str(e)}")
                            continue

                    if page_num < pages_to_scrape - 1:
                        # Wait for the page to settle after processing profiles
                        self.page.wait_for_timeout(2000)
                        
                        # Scroll smoothly through the page
                        logger.info("Scrolling through the page...")
                        self.scroll_smoothly()
                        
                        # Additional wait after scrolling
                        self.page.wait_for_timeout(1000)
                        
                        # Try multiple selectors for the Next button
                        logger.info("Looking for Next button...")
                        next_button = self.page.query_selector('//button[.//span[text()="Next"]]')
                        if not next_button:
                            next_button = self.page.query_selector('//button[contains(@class, "artdeco-pagination__button--next")]')
                        if not next_button:
                            logger.error("Next button not found")
                            break
                        next_button.click()
                        self.page.wait_for_timeout(2000)
                    logger.info(f"Completed scraping page {page_num + 1}")
                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                    break
            
            logger.info(f"\nTotal profiles scraped: {len(all_profile_data)}")
            csv_file = "linkedin_profiles.csv"
            # Update columns to match the actual data structure
            csv_columns = ["name", "about", "location", "profile_url"]
            try:
                with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=csv_columns)
                    writer.writeheader()
                    for data in all_profile_data:
                        # Convert the data keys to match our expected format
                        row_data = {
                            "name": data.get("NAME", ""),
                            "about": data.get("CURRENT ROLE", ""),
                            "location": data.get("LOCATION", ""),
                            "profile_url": data.get("PROFILE URL", "")
                        }
                        writer.writerow(row_data)
                logger.info(f"CSV file saved successfully to {csv_file}")
            except Exception as e:
                logger.error(f"Error saving CSV file: {str(e)}")
            return all_profile_data

        except Exception as e:
            logger.error(f"Error during search and scrape: {str(e)}")
            return profiles

    def cleanup(self):
        logger.info("Cleaning up browser resources...")
        if self.context and hasattr(self.context, "close"):
            self.context.close()
        if self.browser and hasattr(self.browser, "close"):
            self.browser.close()
        if self.playwright and hasattr(self.playwright, "stop"):
            self.playwright.stop()
        logger.info("Cleanup completed")


if __name__ == "__main__":
    tool = LinkedInTool()
    tool._run(
        keyword="software engineer",
        limit=10,
        location="India"
    )