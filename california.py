import requests
from pyvirtualdisplay import Display
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.chrome.options import Options

# Email Information
MESSAGES_URL = ''
API_KEY = ''
FROM_EMAIL = ''
TO_EMAIL = ''

SHORT_TIMEOUT = 5 
LONG_TIMEOUT = 15
LOADER_ID = 'divUnitloader_box'
URL = 'https://www.reservecalifornia.com/CaliforniaWebHome/Facilities/AdvanceSearch.aspx'


def send_email(body):
    """Send an email."""
    return requests.post(
        MESSAGES_URL,
        auth=('api', API_KEY),
        data={'from': FROM_EMAIL,
              'to': [TO_EMAIL],
              'subject': 'Campground matches found',
              'text': body}) 


def WaitForLoader(driver):
  try:
    # wait for loading element to appear
    # : need to make sure we don't prematurely check if element
    # : has disappeared before it has had a chance to appear
    WebDriverWait(
            driver, SHORT_TIMEOUT
    ).until(EC.presence_of_element_located((By.ID, LOADER_ID)))
    print "loader found"

    # then wait for it to disappear
    WebDriverWait(
            driver, LONG_TIMEOUT
    ).until(EC.invisibility_of_element_located((By.ID, LOADER_ID)))
    print 'done waiting for loader'
  except TimeoutException:
        print "Timed out waiting for loader to dissapear"


def CheckForDates(driver, target_dates):
  matches = []
  table_id = 'divUnitGridlist'
  table = driver.find_element_by_id(table_id)
  tds = table.find_elements_by_tag_name('td')
  for td in tds:
    td_title = td.get_attribute('title')
    for date in target_dates:
      date_str = date.strftime('%m/%d/%Y')
      date_parts = date_str.split('/')
      if date_parts[0][0] == '0':
        date_parts[0] = date_parts[0][1:]
      if date_parts[1][0] == '0':
        date_parts[1] = date_parts[1][1:]
      date_str = '/'.join(date_parts)
      expected_titles = [
          '1  is available on {}'.format(date_str),
          '2  is available on {}'.format(date_str),
          '3  is available on {}'.format(date_str)]
      if td_title in expected_titles:
        matches.append(date_str)
        print "match!"
  return matches


display = Display(visible=0, size=('1366', '768'))
display.start()

driver = webdriver.Firefox(executable_path = '/usr/local/bin/geckodriver')
print "driver created"
driver.get(URL)
print "url got"

# Home Page  
WaitForLoader(driver)

auto_elem = driver.find_element_by_id('autocomplete2')
auto_elem.click()
auto_elem.clear()
auto_elem.send_keys('Angel Island SP')

timeout = 10
try:
  element_present = EC.presence_of_element_located((By.CLASS_NAME, 'Park-icon'))
  WebDriverWait(driver, timeout).until(element_present)
except TimeoutException:
      print "Timed out waiting for icon to load"

popup_elem = driver.find_element_by_class_name('Park-icon')
popup_elem.click()

timeout = 10
try:
  element_present = EC.presence_of_element_located((By.ID, 'divPark614'))
  WebDriverWait(driver, timeout).until(element_present)
except TimeoutException:
      print "Timed out waiting for divPark14 to load"

div_elem = driver.find_element_by_id('divPark614')

btn_success_class = 'btn btn-success'
btn_danger_class = 'btn btn-danger'
btn_elems = div_elem.find_elements_by_tag_name('a')
btn_elem = None
for btn in btn_elems:
  btn_class = btn.get_attribute('class')
  if btn_class == btn_success_class: 
    btn_elem = btn 
    break

btn_elem.click()

# Facility Page
print 'Facility Page'
btn_elem = None
facilities_to_check = ['East Bay (sites 1-3)', 'Ridge (sites 4-6)']
facilities = driver.find_elements_by_class_name('facilility_sub_box')
for facility in facilities:
  facility_name_elem = facility.find_element_by_class_name('main_tit_sub_facility')
  if facility_name_elem.text == 'East Bay (sites 1-3)':
    btn_elems = facility.find_elements_by_tag_name('a')
    for btn in btn_elems:
      btn_class = btn.get_attribute('class')
      if btn_class == btn_success_class: 
        btn_elem = btn 
        break
      if btn_class == btn_danger_class: 
        btn_elem = btn 
        break
    break

btn_elem.click()

# Reservation Page
print 'Reservation Page'
target_dates = [
  datetime(2017, 9, 19),
  datetime(2017, 9, 23),
  datetime(2017, 9, 30),
  datetime(2017, 10, 7),
  datetime(2017, 10, 14),
]

count = 0
found_matches = []
while count < 10:
  month_box = driver.find_element_by_class_name('month_name_box')
  #driver.save_screenshot('screenie_' + str(count) + '.png')
  #print "screen shot taken"
  print month_box.text
  matches = CheckForDates(driver, target_dates)
  if matches:
    print "we have matches! %s" % matches
    found_matches.extend(matches)
  next_days_id = 'NextDays'
  nextDays = driver.find_element_by_id(next_days_id)
  nextDays.click()
  print "getting next days"
  WaitForLoader(driver)
  count += 1

if found_matches:

# quit browser
driver.quit()
# quit Xvfb display
display.stop()

#dates = driver.find_element_by_class_name('date_value')
#titles = dates.find_elements_by_tag_name('th')
#for title in titles:
#  date_text = title.get_attribute('title')
#  print date_text
#  datetime_object = datetime.strptime(date_text, '%A, %B %d, %Y')
#  if datetime_object in target_dates:
#    print "match!" 
#  

