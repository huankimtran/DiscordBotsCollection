import time

# import webdriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

page_url = 'https://www.walgreens.com/findcare/vaccination/covid-19?ban=covid_vaccine2_landing_schedule'
# create webdriver object
driver = webdriver.Firefox()
# get to landig page
driver.get(page_url)
# get button to start schedule
element = driver.find_element_by_xpath("//a[@href='/findcare/vaccination/covid-19/location-screening']")
# Click to go to the search page
element.click()
# Wait until the transition finishes
wait = WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, "//a[@title='state eligibility guidelines']"), 'state eligibility guidelines'))
# Now you got to the search page, find the zipcode search input
zip_search_box = driver.find_element_by_id('inputLocation')
# Find the search button
search_btn = zip_search_box.find_element_by_xpath('../button')
# Find the result field
result_container =  zip_search_box.find_element_by_xpath('../../../../section[@class="mt25"]')
# Now input the zipcode and search
list_zip = [77061, 1121]
zip_search_box.clear()
for z_code in list_zip:
    # Send in the zipcode
    zip_search_box.send_keys(str(z_code))
    # Make sure no result available
    while True:
        try:
            p = result_container.find_element_by_xpath('./p')
        except NoSuchElementException as e:
            break
        continue
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
            print('Not available')
        else:
            print('available')
        break
    # Clear result box
    zip_search_box.clear()
    # Wait a little before next serach
    time.sleep(1)

driver.quit()