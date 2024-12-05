from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import requests

# Configuration
LOGIN_URL = "https://www.broadcastify.com/login"
ARCHIVE_URL = "https://www.broadcastify.com/archives/feed/14744"
USERNAME = ""
PASSWORD = ""
DOWNLOAD_FOLDER = "/media/meow/Elements/ems_call/data"

# Ensure the download folder exists
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Set up the Firefox browser
options = webdriver.FirefoxOptions()
# options.add_argument('--headless')  # Remove this argument if you want to see the browser
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "audio/mpeg, audio/mp3, application/octet-stream")
driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 10)

def get_cookies_from_selenium(driver):
    selenium_cookies = driver.get_cookies()
    cookies = {}
    for cookie in selenium_cookies:
        cookies[cookie['name']] = cookie['value']
    return cookies

try:
    # Log in
    driver.get(LOGIN_URL)
    # Wait for the username input field to load
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="signinSrEmail"]'))
    )
    
    # Wait for the password input field to become clickable
    password_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="signinSrPassword"]'))
    )
    
    # Wait for the login button to become clickable
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div/div/form/div[4]/div[2]/button'))
    )
    
    # Input username and password, then click login
    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    login_button.click()
    print("okok")

    # Wait for login to complete
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "button-menu-home-hover"))  # Replace with the actual dashboard element
    )
    print("Login successful")

    session = requests.Session()  # Use a session to maintain cookies
    session.cookies.update(get_cookies_from_selenium(driver))  # Pass cookies from Selenium

    # Navigate to archive page
    driver.get(ARCHIVE_URL)
    print("Accessed archive page")

    # Select dates from the dropdown
    date_selector = wait.until(EC.presence_of_element_located((By.ID, "datepicker")))
    available_days = date_selector.find_elements(By.XPATH, ".//td[contains(@class, 'day')]")

    for day in available_days:
        day_class = day.get_attribute("class")
        if "active" in day_class or "available" in day_class:  # Adjust if necessary
            date_value = day.get_attribute("data-date")
            print(f"Processing date: {date_value}")
            day.click()
            time.sleep(2)  # Wait for the page to load

            # Fetch all MP3 file links for the selected date
            # Start downloading MP3 files

            table_rows = driver.find_elements(By.XPATH, "/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/table/tbody/tr")
            for x in range(1, len(table_rows) + 1):
                try:
                    print("====start======================================")
                    # Locate the download button
                    button = driver.find_element(By.XPATH, f"/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/table/tbody/tr[{x}]/td[2]/a")
                    old_url = driver.current_url
                    mp3_url = button.get_attribute("href")
                    print(f"Requesting: {mp3_url}")

                    # button.click()
                    # print("click done!")

                    driver.execute_script("arguments[0].click();", button)
                    print("Button clicked via JavaScript")

                    WebDriverWait(driver, 10).until(lambda d: d.current_url != old_url)
                    new_url = driver.current_url
                    print(f"Redirected to new URL: {new_url}")

                    # time.sleep(5)

                    # Send GET request and follow redirects
                    response = requests.get(mp3_url, stream=True, allow_redirects=True)
                    

                    # Check if the final URL contains ".mp3"
                    final_url = response.url
                    print(f"Final redirected URL: {final_url}")
                    print(f"Status Code: {response.status_code}")
                    print(f"Headers: {response.headers}")
                    print("====done======================================")

                    # Verify the response is a valid MP3
                    # content_type = response.headers.get("Content-Type")
                    # if response.status_code == 200 and "audio/mpeg" in response.headers.get("Content-Type", ""):
                    if response.status_code == 200 and "audio/mpeg":

                        # Use the final URL to determine the file name
                        file_name = os.path.join(DOWNLOAD_FOLDER, os.path.basename(new_url))
                        print(f"Downloading to: {file_name}")

                        # Save the MP3 file
                        with open(file_name, "wb") as file:
                            for chunk in response.iter_content(chunk_size=1024):
                                if chunk:  # filter out keep-alive chunks
                                    file.write(chunk)
                        print(f"Downloaded: {file_name}")
                    else:
                        print(f"Failed to download {mp3_url}. Content-Type: {response.headers.get('Content-Type')}, Status code: {response.status_code}")
                except Exception as e:
                    print(f"Error processing file {x}: {e}")

    print("All dates processed successfully")
finally:
    time.sleep(10)
    driver.quit()




