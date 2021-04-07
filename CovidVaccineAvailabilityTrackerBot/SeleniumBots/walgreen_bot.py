import time
import threading
import random
import asyncio
import zipcodes as zp

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WallGreenBot:
    def __init__(self, discord_client) -> None:
        # Predifined value
        self.session_duration = 900             # Duration of one session, after this, new session will be spawn, currently set at 15 mins
        self.delay_between_session = 10         # Delay between session
        # Init
        self.discord_client = discord_client
        self.page_url = f'https://www.walgreens.com/findcare/vaccination/covid-19?ban={random.randint(10000, 99999)}'
        self.user_zipcode_map = self.load_log_file()
        self.zipcode_status_map = dict()
        self.lock = threading.Lock()
        self.driver = self.get_to_search_page()
        self.session_begin_time = time.time()

    def save_log_file(self):
        with open('walgreen_bot_user_zip_map.log', 'w') as f:
            f.write(str(self.user_zipcode_map))
    
    def load_log_file(self):
        try:
            with open('walgreen_bot_user_zip_map.log') as f:
                return eval(f.read())
        except Exception as e:
            return dict()
    
    def __del__(self):
        try:
            self.driver.quit()
            print('Selenium session closed')
        except Exception as e:
            pass
        print('Bot terminated')

    def get_to_search_page(self):
        while True:
            try:
                # Run headless
                fireFoxOptions = webdriver.FirefoxOptions()
                fireFoxOptions.set_headless()
                # Spawn the browser
                driver = webdriver.Firefox(firefox_options=fireFoxOptions)
                # Connect to landing page
                driver.get(self.page_url)
                # get button to start schedule
                element = driver.find_element_by_xpath(
                    "//a[@href='/findcare/vaccination/covid-19/location-screening']")
                # Bypass bot detector, not so effective though
                time.sleep(random.randint(0, 5))
                element.click()
                # Wait until the transition finishes
                WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element(
                    (By.XPATH, "//a[@title='state eligibility guidelines']"), 'state eligibility guidelines'))
                # Now you got to the search page, find the zipcode search input
                zip_search_box = driver.find_element_by_id('inputLocation')
                # Find the search button
                search_btn = zip_search_box.find_element_by_xpath('../button')
                # Wait until the auto fill zipcode appears, clear then start checking
                while len(zip_search_box.get_attribute('value')) == 0:
                    time.sleep(0.1)
                zip_search_box.clear()
            except Exception as e:
                print('Error getting to the search page, will retry!\n{e}')
                try:
                    driver.quit()
                except Exception as e:
                    pass
                # Wait a while before retry
                time.sleep(self.session_duration)
                print('retrying...')
                continue
            break
        return driver
        

    def subscribe_user_to_zipcode(self, user_name, zipcode_list):
        """
            Subscribing a user whose name is user_name to
            zipcodes listed in the list 
        """
        with self.lock:
            did_change = False
            for zipcode in zipcode_list:
                # Check if zipcode valid
                try:
                    match_list = zp.matching(str(zipcode))
                except Exception:
                    print(f'Invalid zipcode {zipcode}')
                    continue
                if len(match_list) == 0:
                    print(f'Invalid zipcode {zipcode}')
                    continue
                # Process if valid
                if zipcode not in self.user_zipcode_map:
                    self.user_zipcode_map[zipcode] = set()
                # Add user to the subscriber set of this zipcode
                self.user_zipcode_map[zipcode].add(user_name)
                did_change = True
            # Back up 
            if did_change:
                self.save_log_file()
    
    def unsubscribe_user_from_zipcode(self, user_name, zipcode_list):
        """
            Unsubscribing a user whose name is user_name from
            zipcodes listed in the list 
        """
        with self.lock:
            did_change = False
            for zipcode in zipcode_list:
                if zipcode in self.user_zipcode_map:
                    try:
                        self.user_zipcode_map[zipcode].remove(user_name)
                        if len(self.user_zipcode_map[zipcode]) == 0:
                            del self.user_zipcode_map[zipcode]
                            del self.zipcode_status_map[zipcode]
                        did_change = True
                    except Exception as e:
                        continue
            # Backup
            if did_change:
                self.save_log_file()

    def run(self):
        # Check if session expired
        if time.time() - self.session_begin_time >= self.session_duration:
            # Session expire, renew
            self.driver.quit()
            del self.driver
            # Delay just to make sure
            time.sleep(self.delay_between_session)
            # Spawn new session
            self.driver = self.get_to_search_page()
        # Run like normal
        driver = self.driver
        # Now you got to the search page, find the zipcode search input
        zip_search_box = driver.find_element_by_id('inputLocation')
        # Find the search button
        search_btn = zip_search_box.find_element_by_xpath('../button')
        # Find the result field
        result_container = zip_search_box.find_element_by_xpath(
            '../../../../section[@class="mt25"]')
        # Now input the zipcode and search
        list_zip = list(self.user_zipcode_map.keys())
        zip_search_box.clear()
        #  Start checking
        for z_code in list_zip:
            if z_code not in self.zipcode_status_map:
                self.zipcode_status_map[z_code] = False
            # Send in the zipcode
            zip_search_box.send_keys(str(z_code))
            # Make sure no result available
            while True:
                try:
                    p = result_container.find_element_by_xpath('./p')
                except NoSuchElementException as e:
                    break
                time.sleep(0.1)
            # Search
            search_btn.click()
            # Wait till result available
            while True:
                # Check for result
                try:
                    p = result_container.find_element_by_xpath('./p')
                except NoSuchElementException as e:
                    # Result not yet avaialable
                    time.sleep(0.1)
                    continue
                result = p.get_attribute('innerText')
                # Check result
                if 'not available' in result:
                    self.zipcode_status_map[z_code] = False
                    # print(f'Not available {z_code}')
                else:
                    if not self.zipcode_status_map[z_code]:
                        # Status of this zipcode has been flipped, announce
                        self.announce(z_code)
                    # Record the change
                    self.zipcode_status_map[z_code] = True
                    # print(f'Available {z_code}')
                break
            # Clear result box
            zip_search_box.clear()
            # Wait a little before next serach
            time.sleep(0.5)
    
    def announce(self, z_code):
        # Build message
        msg = f'Wallgreen\'s vaccine at Zipcode {z_code} is available, go to https://www.walgreens.com/findcare/vaccination/covid-19/ to get your shot\n'
        for user in self.user_zipcode_map[z_code]:
            msg += f'{user} '
        # Announce
        self.discord_client.send_msg_to_channel(msg)
        # Yield for the main thread to post msg
        time.sleep(0)