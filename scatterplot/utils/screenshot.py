#!/usr/bin/env

"""
Util script to generate screenshot of solution plot
"""

import os
from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

if os.path.exists('/autograder'):  # gradescope run
    local_run = False
    driver = webdriver.Chrome(options=chrome_options)
else:
    local_run = True
    driver = webdriver.Chrome(
        executable_path="utils/chromedriver",
        options=chrome_options)

# take screenshot of solution ( must perform on GS , becuase uploading a local copy could have different dimensions/shape
url = 'http://localhost:8080/solution.html'
driver.get(url)
# set chromedrive window dimensions to student submission dimensions
rendered_width = driver.execute_script("return document.documentElement.scrollWidth")
rendered_height = driver.execute_script("return document.documentElement.scrollHeight")
driver.set_window_size(rendered_width,rendered_height)
driver.save_screenshot('../solution/solution_plot.png')
driver.quit()
