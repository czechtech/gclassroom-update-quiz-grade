from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging, sys, os, io, time
import urllib
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def wait_for_load():
    global driver
    width = 0
    prev_width = -1
    while width != prev_width:
        time.sleep(0.1)
        prev_width = width
        width = driver.find_elements_by_xpath("//nav[@role='navigation']/div[last()]/div//div")[0].size['width']
    #time.sleep(0.5)

def wait_for_dialog_clear():
    global driver
    driver.implicitly_wait(0)
    while len(driver.find_elements_by_xpath("//div[@role='alertdialog']")) > 0:
        time.sleep(0.5)
    driver.implicitly_wait(15)


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Create headless web browser
logging.info("Creating Chrome browser")
chrome_options = Options()
#chrome_options.add_argument("--headless")
driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options=chrome_options)
driver.implicitly_wait(15)

# Login Pages:
logging.info("Loading https://accounts.google.com...")
driver.get("https://accounts.google.com/")
username = driver.find_element_by_id('identifierId')
next = driver.find_element_by_id('identifierNext')
print("Login to https://accounts.google.com")
username.send_keys(raw_input("Email: "))
next.click()
logging.info("Clicked next...")
password = driver.find_element_by_name('password')
next = driver.find_element_by_id('passwordNext')
password.send_keys(raw_input("Password: "))
logging.info("Logging in...")
next.click()
if not driver.find_elements_by_xpath("//h1[contains(text(),'Welcome')]"):
    print("Login Failed")


# Navigate to Classroom Courses
logging.info("Loading https://classroom.google.com...")
driver.get("https://classroom.google.com/?emr=0")
wait_for_load()

# Courses
ol = driver.find_element_by_tag_name("ol")
classes = ol.find_elements_by_tag_name("li")
for number,c in enumerate(classes):
    name = c.find_element_by_tag_name("h2").text.replace('\n',' - ')
    print(str(number+1) + ") " + name)
number = int(raw_input("Which class? ")) - 1
class_url = classes[number].find_element_by_tag_name("a").get_attribute("href")

# Navigate to Classwork
logging.info("Loading Assignments & Checking for Quizzes...")
class_url = class_url.replace("/c/","/w/")
driver.get(class_url+"/t/all")

wait_for_load()

# Assignment Urls
assignment_urls = []
assignment_names = []
driver.find_element_by_xpath("//div[@aria-label='Assignment']") # This is to delay while the page loads
for li in driver.find_elements_by_xpath("//main//descendant::li[@data-stream-item-type='assignment']"):
    li.click()
    name = li.text.split("\n")[0]
    logging.info("Checking "+"'"+name+"'...")
    driver.implicitly_wait(2)
    docs = li.find_elements_by_xpath(".//div[@data-include-stream-item-materials='true']/div")
    if len(docs) == 1 and "Forms" in docs[0].text:
        a = li.find_element_by_tag_name("a")
        assignment_urls.append(a.get_attribute("href"))
        assignment_names.append(name)
    driver.implicitly_wait(15)
logging.info("Found "+str(len(assignment_urls))+" Assignments containing Google Forms")

# Open Each Assignment (parallelize this!)
for url, name in zip(assignment_urls, assignment_names):
    logging.info("Loading '"+name+"'...")
    driver.get(url)
    wait_for_load()
    
    # Import Grades from Form Data
    logging.info("Looking to import...")
    driver.find_element_by_xpath("//div[text()='Assigned']") # This is to delay while the page loads
    driver.find_elements_by_xpath("//div[@role='button']//span[text()='Import Grades']")[-1].click() #1
    #logging.info("Confirming...")
    driver.find_elements_by_xpath("//div[@role='button']//span[text()='Import']")[-1].click()
    logging.info("Importing grades...")
    wait_for_dialog_clear()

    # Identify New/Draft Grades
    drafts_count = 0
    students = driver.find_elements_by_xpath("//table[@aria-label='Students']")[-1]
    table_container = students.find_element_by_xpath('../..')
    for row in students.find_elements_by_tag_name("tr"):
        driver.execute_script('arguments[0].scrollTop += 60', table_container) #scroll
        if "Draft" in row.text:
            row.find_element_by_xpath(".//div[@role='checkbox']").click()
            drafts_count += 1
    logging.info(str(drafts_count)+" Grades to Return")


    # Return New/Draft Grades
    if drafts_count > 0:
        # Click to confrim returning Grades
        driver.find_elements_by_xpath("//div[@role='button']//span[text()='Return']")[-1].click()
        #logging.info("Confirming return...")
        alert_div = driver.find_element_by_xpath("//div[@role='alertdialog']")

        # Are any sumissions un-turned-in?
        if "unsubmitted" in alert_div.text:
            alert_div.find_elements_by_xpath(".//div[@role='button']//span[text()='Return']")[-1].click()
            driver.find_element_by_xpath("//div[@role='alertdialog']//textarea") # This is to delay
            # Update alert_div
            alert_div = driver.find_element_by_xpath("//div[@role='alertdialog']")

        # Click to Return Grades
        logging.info("Returning...")
        alert_div.find_elements_by_xpath(".//div[@role='button']//span[text()='Return']")[-1].click()
        wait_for_dialog_clear()

    logging.info("Done.")    






# Quit:
driver.quit()
