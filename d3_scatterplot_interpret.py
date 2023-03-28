
from bs4  import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.color import Color
from autograde_viz.d3_scales import *
import re
import json
import numpy as np
import pandas as pd

"""
Scratch file for figuring how to scrape a d3 scatterplot 
run a local server as indicated in readme.md
"""

if __name__ == '__main__':

    url = 'http://localhost:3000/submission.html'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(
        executable_path="utils/chromedriver",
        options=chrome_options)

    driver.get(url)  # must be running a localserver in the submission/ dir

    # set chromedrive window dimensions to plot page dimensions
    rendered_width = driver.execute_script("return document.documentElement.scrollWidth")
    rendered_height = driver.execute_script("return document.documentElement.scrollHeight")
    driver.set_window_size(rendered_width,rendered_height)        

    # Title Tag
    title = driver.find_element_by_id("title").text


    # Filter data where Miles_per_Gallon & Horsepower are not missing. 
    df = pd.read_csv("data/cars.csv")
    df = df.dropna(subset=['Miles_per_Gallon', 'Horsepower'])
    df = df[['Miles_per_Gallon', 'Horsepower']]
    df = df.reset_index(drop=True)
    max_hp = df["Horsepower"].values.max()
    max_mpg = df["Miles_per_Gallon"].values.max()
    

    symbol_position_tolerance = 2

    ########################################
    # Get rank symbols: positions & labels #
    ########################################
    # get all circles

    # Scatterplot Circle Marks
    circle_marks = WebDriverWait(driver, 10) \
        .until(EC.presence_of_element_located((By.ID, "symbols"))) \
        .find_elements_by_tag_name("circle")
    circle_colors = list(set([s.value_of_css_property("fill") for s in circle_marks]))

    # get x/y axes width & height
    y_axis_height = WebDriverWait(driver, 10) \
        .until(EC.presence_of_element_located((By.ID, "y_axis"))) \
        .find_element_by_class_name("domain") \
        .rect['height']
    x_axis_width = WebDriverWait(driver, 10) \
        .until(EC.presence_of_element_located((By.ID, "x_axis"))) \
        .find_element_by_class_name("domain") \
        .rect['width']    

    # store x,y positions
    grouped_symbol_positions = {c: {'x': [], 'y': []} for c in circle_colors}
    for s in circle_marks:
        k = s.value_of_css_property("fill")
        x = np.round(np.float(s.get_attribute('cx')), 2)
        y = np.round(np.float(s.get_attribute('cy')), 2)
        grouped_symbol_positions[k]['x'].append(x)
        grouped_symbol_positions[k]['y'].append(y)

    actual_symbol_positions = {c: None for c in grouped_symbol_positions.keys()}
    for k in actual_symbol_positions.keys():
        x_coords = grouped_symbol_positions[k]['x']
        y_coords = grouped_symbol_positions[k]['y']
        actual_symbol_positions[k] = pd.DataFrame({'x': x_coords, 'y': y_coords})

    # each key will hold a dataframe of xy coords
    expected_symbol_positions = {'symbols': None}

    # iterate through each column (key of expected symbol) by the axes
    x_coords = []
    y_coords = []
    for a in df.axes[0].values:
        xd = df.iloc[a][1]
        yd = df.iloc[a][0]
        y = np.round(d3_scale_linear(webdriver=driver, datum=yd, domain_min=0, domain_max=max_mpg, range_min=0, range_max=y_axis_height, invert=True), 2)
        x = np.round(d3_scale_linear(webdriver=driver, datum=xd,  domain_min=0, domain_max=max_hp, range_min=0, range_max=x_axis_width), 2)
        x_coords.append(x)
        y_coords.append(y)
    expected_symbol_positions['symbols'] = pd.DataFrame({'x': x_coords, 'y': y_coords})

    # take each group and of symbols (circles) get x,y coords
    # ensure w/in tolerance
    matches = {}
    sorted_matches = {}
    for ak in actual_symbol_positions.keys():
        for j in expected_symbol_positions.keys():

            # try to match on circle symbol positions
            diff = actual_symbol_positions[ak].sub(expected_symbol_positions[j])
            # these filtered dfs will contain any symbol position > than the tolerance.
            x_tolerant = diff[np.abs(diff['x']) > symbol_position_tolerance].empty
            y_tolerant = diff[np.abs(diff['y']) > symbol_position_tolerance].empty
            match = x_tolerant and y_tolerant
            if match:
                matches[j] = ak
                break

    # Circle Mark Colors
    circle_mark_colors = list(set([l.value_of_css_property("fill") for l in circle_marks]))
    circle_mark_hex_colors = [Color.from_string(c).hex for c in circle_mark_colors]

    # interaction 
    action = ActionChains(driver)
    # check that the radius changes on mouseover/hover
    targeted_circle_element = circle_marks[0]
    targeted_circle_radius_0 = targeted_circle_element.get_attribute('r')
    action.move_to_element(to_element=targeted_circle_element).perform()
    targeted_circle_radius_1 = targeted_circle_element.get_attribute('r')
    print(f'radius b/f hover: {targeted_circle_radius_0}, after hover: {targeted_circle_radius_1}')

