# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration
LOGIN_URL = "https://www.broadcastify.com/login"
# ARCHIVE_URL = "https://www.broadcastify.com/archives/feed/14744"
ARCHIVE_URL = "https://www.broadcastify.com/archives/feed/36636"
USERNAME = "YOUR_ACCOUNT"
PASSWORD = "YOUR_PASSWORD"
# DOWNLOAD_FOLDER = "/media/meow/Elements/ems_call/data/20250123_craw_data_2024all_n3_Dec"
DOWNLOAD_FOLDER = "/media/meow/Elements/ems_call/data/20260103_BostonEMS_2024"

# 要下載的特定日期列表 (格式: YYYYMMDD)
TARGET_DATES = [
    "20250401",
    "20250402",
    "20250403",
    "20250404",
    "20250616",
    "20250701",
    "20250702",
    "20250703",
    "20250705",
    "20250901",
    "20250902",
    "20250903",
    "20250904",
    "20250922",
    "20250923",
    "20250924",
    "20250925",
    "20250926",
    "20250927",
    "20250928",
    "20250929",
    "20250930",
    "20251201",
    "20251202",
    "20251203",
]

def parse_target_dates(dates):
    """將日期列表轉換成以 'Month Year' 為 key 的字典，值為該月要下載的日期列表"""
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    grouped = defaultdict(list)
    for date_str in dates:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        month_year = f"{month_names[month-1]} {year}"
        grouped[month_year].append(day)
    return grouped

TARGET_DATES_GROUPED = parse_target_dates(TARGET_DATES)


# Ensure the download folder exists
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Set up the Firefox browser
options = webdriver.FirefoxOptions()
# options.add_argument('--headless')  # Remove this argument if you want to see the browser
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "audio/mpeg, audio/mp3")
options.set_preference("browser.download.folderList", 2)  # Custom download path
options.set_preference("browser.download.dir", DOWNLOAD_FOLDER)
options.set_preference("browser.download.manager.showWhenStarting", False)
options.set_preference("browser.download.manager.useWindow", False)
options.set_preference("browser.helperApps.alwaysAsk.force", False)
options.set_preference("browser.download.manager.showAlertOnComplete", False)
driver = webdriver.Firefox(options=options)
driver.set_window_size(1920, 1080)  # Set window size for headless mode
wait = WebDriverWait(driver, 10)


def get_cookies_from_selenium(driver):
    """Get cookies from Selenium and return as a dict suitable for requests."""
    selenium_cookies = driver.get_cookies()
    # �o��^�� name: value �������r���²��A�� requests �ݭndomain��T
    # �᭱�|�Υt�@�ؤ�k�Ncookie�`�J��session��
    cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    return cookies

startDate = datetime(2024, 1, 3)
endDate = datetime(2024, 11, 30)
currentDate = startDate

def check_month_and_year(target_month_year):
    """ Check if the current month and year match the target """
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/main/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[1]/table/thead/tr[2]/th[2]"))
    )
    return element.text == target_month_year

def click_button(xpath):
    """ Click a button specified by the xpath """
    button = driver.find_element(By.XPATH, xpath)
    # Use JavaScript click for headless mode compatibility
    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", button)

def parse_month_year(month_year_str):
    """將 'Month Year' 格式轉換成 (year, month) 元組以便比較"""
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    parts = month_year_str.split()
    month = month_names.index(parts[0]) + 1
    year = int(parts[1])
    return (year, month)

def navigate_to_month_and_prepare_directory(driver, target_month_year):
    """
    Navigates to a specific month and year on a website and prepares the download directory.
    支援雙向導航（往前或往後）。
    """
    target_ym = parse_month_year(target_month_year)
    max_attempts = 50  # 防止無限循環
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/main/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[1]/table/thead/tr[2]/th[2]"))
            )
            current_month_year = element.text
            if current_month_year == target_month_year:
                print(f"Found the month {target_month_year}!")
                return True
            
            current_ym = parse_month_year(current_month_year)
            
            # 決定導航方向
            if current_ym > target_ym:
                # 當前月份比目標月份晚，往前（過去）導航
                button_xpath = "/html/body/main/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[1]/table/thead/tr[2]/th[1]"
            else:
                # 當前月份比目標月份早，往後（未來）導航
                button_xpath = "/html/body/main/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[1]/table/thead/tr[2]/th[3]"
            
            button = driver.find_element(By.XPATH, button_xpath)
            # Use JavaScript click for headless mode compatibility
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", button)
        except TimeoutException:
            print("Timeout waiting for the element, check the XPath.")
            return False
    
    print(f"無法導航到月份 {target_month_year}，已超過最大嘗試次數")
    return False

try:
    # Log in via Selenium
    driver.get(LOGIN_URL)
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="signinSrEmail"]'))
    )
    password_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="signinSrPassword"]'))
    )
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div/div/form/div[4]/div[2]/button'))
    )
    
    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    login_button.click()
    print("login_button clicked ok")

    # Wait for login to complete
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "button-menu-home-hover"))
    )
    print("Login successful")

    # Get User-Agent from Selenium
    user_agent = driver.execute_script("return navigator.userAgent;")
    print("User-Agent from Selenium:", user_agent)

    # Create a requests session and copy cookies & headers
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        # �p�G�ݭnReferer�Ψ�Lheader�]�b���[�J
        "Referer": ARCHIVE_URL
    })

    # �NSelenium��cookies��Jrequests session
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    # Navigate to archive page
    driver.get(ARCHIVE_URL)
    print("Accessed archive page")

    # 依照 TARGET_DATES_GROUPED 處理每個月份
    print(f"要處理的月份與日期: {dict(TARGET_DATES_GROUPED)}")
    
    for target_month_year, target_days in TARGET_DATES_GROUPED.items():
        print(f"\n========== 處理月份: {target_month_year}, 日期: {target_days} ==========")
        
        # 導航到目標月份
        navigate_to_month_and_prepare_directory(driver, target_month_year)
        
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/main/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[1]/table/thead/tr[2]/th[2]"))
        )
        os.makedirs(os.path.join(DOWNLOAD_FOLDER, str(element.text)), exist_ok=True)
        element_this_round = str(element.text)
        print("***element_this_round***is ", element_this_round)

        # 遍歷日曆找到目標日期
        for k in range(1, 7):
            for y in range(1, 8):
                button_xpath = f"/html/body/main/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[1]/table/tbody/tr[{k}]/td[{y}]"
                try:
                    button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, button_xpath))
                    )
                    class_attribute = button.get_attribute("class")
                    day_text = button.text.strip()
                    
                    # 檢查是否為有效日期且在目標日期列表中
                    if ("day" in class_attribute and 
                        "new day" not in class_attribute and 
                        "old day" not in class_attribute and 
                        "disabled day" not in class_attribute and
                        day_text.isdigit() and 
                        int(day_text) in target_days):
                        
                        print(f"找到目標日期: {day_text} (索引 [{k},{y}])")
                        
                        # Use JavaScript click for headless mode compatibility
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(2)

                        date_selector = wait.until(EC.presence_of_element_located((By.ID, "datepicker")))
                        available_days = date_selector.find_elements(By.XPATH, ".//td[contains(@class, 'day')]")

                        table_rows = driver.find_elements(By.XPATH, "/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/table/tbody/tr")
                        for x in range(1, len(table_rows) + 1):
                            try:
                                print("====start======================================")
                                button_dwn = driver.find_element(By.XPATH, f"/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/table/tbody/tr[{x}]/td[2]/a")
                                old_url = driver.current_url
                                mp3_url = button_dwn.get_attribute("href")
                                print(f"Requesting: {mp3_url}")

                                driver.execute_script("arguments[0].click();", button_dwn)
                                print("Button clicked via JavaScript")

                                WebDriverWait(driver, 10).until(lambda d: d.current_url != old_url)
                                new_url = driver.current_url
                                print(f"Redirected to new URL: {new_url}")

                                # 使用session下載確保cookies與user-agent一同
                                response = session.get(mp3_url, stream=True, allow_redirects=True)

                                final_url = response.url
                                print(f"Final redirected URL: {final_url}")
                                print(f"Status Code: {response.status_code}")
                                print(f"Headers: {response.headers}")
                                print("====done======================================")

                                if response.status_code == 200 and "audio/mpeg" in response.headers.get("Content-Type", ""):
                                    file_name = os.path.join(DOWNLOAD_FOLDER, os.path.basename(final_url))
                                    print(f"Downloading to: {file_name}")
                                    with open(file_name, "wb") as file:
                                        for chunk in response.iter_content(chunk_size=1024):
                                            if chunk:
                                                file.write(chunk)
                                    print(f"Downloaded: {file_name}")

                                    time.sleep(2)

                                    # After download, navigate back to archive URL
                                    driver.get(ARCHIVE_URL)
                                    print("Returned to archive page")
                                    time.sleep(2)  # Wait for the page to reload

                                    navigate_to_month_and_prepare_directory(driver, element_this_round)

                                    button_xpath = f"/html/body/main/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[1]/table/tbody/tr[{k}]/td[{y}]"
                                    button = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.XPATH, button_xpath))
                                    )
                                    # Use JavaScript click for headless mode compatibility
                                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                    time.sleep(0.5)
                                    driver.execute_script("arguments[0].click();", button)
                                    time.sleep(2)  # Wait for the page to reload
                                else:
                                    print(f"Failed to download {mp3_url}. Content-Type: {response.headers.get('Content-Type')}, Status code: {response.status_code}")
                            except Exception as e:
                                print(f"Error processing file {x}: {e}")
                except Exception as ee:
                    print(f"No clickable 'day' button at position [{k},{y}]: {str(ee)}")

        print(f"月份 {target_month_year} 處理完成")

    print("All dates processed successfully")

finally:
    time.sleep(10)
    driver.quit()
