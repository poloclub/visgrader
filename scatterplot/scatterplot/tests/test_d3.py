import os
import unittest
import re
from gradescope_utils.autograder_utils.decorators import weight, tags, number
from gradescope_utils.autograder_utils.decorators import partial_credit
from gradescope_utils.autograder_utils.files import check_submitted_files
from utils.output_blocker import NoStd
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.color import Color
from utils.rubric_helper import get_rubric_config
import numpy as np
import pandas as pd
from utils.gs_helper import load_meta_json
from autograde_viz.d3_scales import *
from autograde_viz.css_transforms import *
from bs4 import BeautifulSoup


class TestFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        if os.path.exists('/autograder'):  # gradescope run
            local_run = False
            url = 'http://localhost:8080/submission.html'
            driver = webdriver.Chrome(options=chrome_options)
            metadata_json = "/autograder/submission_metadata.json"

        else:
            local_run = True
            url = 'http://localhost:8080/submission.html'
            driver = webdriver.Chrome(
                executable_path="utils/chromedriver",
                options=chrome_options)
            metadata_json = "sample/submission_metadata.json"

        meta = load_meta_json(metadata_json)
        # cls.submitted_gtid = meta['users'][0]['sid']
        # cls.expected_gtid = '999999999'

        driver.get(url)

        # set chromedrive window dimensions to student submission dimensions
        rendered_width = driver.execute_script("return document.documentElement.scrollWidth")
        rendered_height = driver.execute_script("return document.documentElement.scrollHeight")
        driver.set_window_size(rendered_width,rendered_height)        

        cls.rubric_config = get_rubric_config('config/' + "scatterplot" + '/rubric.yaml')     
        cls.solution_title = cls.rubric_config["labels"]["title"]
        cls.solution_x_axis_label = cls.rubric_config["labels"]["x_axis_label"]
        cls.solution_y_axis_label = cls.rubric_config["labels"]["y_axis_label"]
        cls.solution_x_ticks = cls.rubric_config["data"]["x_ticks"]
        cls.solution_y_ticks = cls.rubric_config["data"]["y_ticks"]
        cls.submitted_title = None
        cls.submitted_x_axis_label = None
        cls.submitted_y_axis_label = None
        cls.submitted_x_axis = None
        cls.submitted_y_axis = None
        cls.submitted_x_ticks = None
        cls.submitted_y_ticks = None


        cls.driver = driver

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cls.soup = soup

    @classmethod
    def tearDownClass(cls) -> None: 
        cls.driver.quit()

    @weight(0.0)
    def test_002_d3_imports(self):
        """Functional advisory test - determine if the d3 lib imports are correct."""
        with NoStd():
            required_imports =  ['lib/d3/d3.min.js', 'lib/d3-dsv/d3-dsv.min.js']

            submitted_imports = []
            found_tags = self.soup.find_all("script")
            for tag in found_tags:
                if 'src' in list(tag.attrs.keys()):
                    submitted_imports.append(tag.attrs['src'])
            diff = list(set(required_imports).difference(set(submitted_imports)))
            same = len(list(set(submitted_imports).intersection(set(required_imports))))
            self.assertCountEqual(required_imports, submitted_imports, f"Found {same}/3 required imports. \nThe import {diff} was not found or could be referenced with a different path than required. \nThis will prevent required libraries from loading correctly during grading.")
        print("Found all required d3 imports.")


    @weight(0.0)
    def test_01_data_representation(self):
        """Test that there is one mark present for each required data point in the dataset."""
        df = pd.read_csv("data/cars.csv")
        df = df.dropna(subset=['Miles_per_Gallon', 'Horsepower'])
        df = df.reset_index(drop=True)

        try:
            circles = WebDriverWait(self.driver, 10) \
                .until(EC.presence_of_element_located((By.ID, "symbols"))) \
                .find_elements_by_tag_name("circle")
            desired_data_len = len(df)
            submitted_data_len = len(circles)
            self.assertEqual(desired_data_len, submitted_data_len, \
                f"Expected {desired_data_len} plotted marks. Found {submitted_data_len} instead.")
        except:
            raise NoSuchElementException
        
        print(f"Found {submitted_data_len} plotted marks")


    @weight(2.0)
    def test_02_circle_mark_positions(self):
        """Test that the circle marks are positioned correctly"""
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
        circle_marks = WebDriverWait(self.driver, 10) \
            .until(EC.presence_of_element_located((By.ID, "symbols"))) \
            .find_elements_by_tag_name("circle")
        circle_colors = list(set([s.value_of_css_property("fill") for s in circle_marks]))

        # get x/y axes width & height
        y_axis_height = WebDriverWait(self.driver, 10) \
            .until(EC.presence_of_element_located((By.ID, "y_axis"))) \
            .find_element_by_class_name("domain") \
            .rect['height']
        x_axis_width = WebDriverWait(self.driver, 10) \
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
            y = np.round(d3_scale_linear(webdriver=self.driver, datum=yd, domain_min=0, domain_max=max_mpg, range_min=0, range_max=y_axis_height, invert=True), 2)
            x = np.round(d3_scale_linear(webdriver=self.driver, datum=xd,  domain_min=0, domain_max=max_hp, range_min=0, range_max=x_axis_width), 2)
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
        self.assertTrue(x_tolerant, "circle marks are not positioned correctly within the x-axis")
        self.assertTrue(y_tolerant, "circle marks are not positioned correctly within the y-axis")
        print("Circle marks are positioned correctly ")
    
    
    @weight(2.5)
    def test_03_mouseover_interaction(self):
        """Test that the circle mark radius becomes larger on mouseover interaction"""
        # Scatterplot Circle Marks
        circle_marks = WebDriverWait(self.driver, 10) \
            .until(EC.presence_of_element_located((By.ID, "symbols"))) \
            .find_elements_by_tag_name("circle")        
        
        action = ActionChains(self.driver)
        # check that the radius changes on mouseover/hover
        targeted_circle_element = circle_marks[0]
        targeted_circle_radius_0 = targeted_circle_element.get_attribute('r')
        action.move_to_element(to_element=targeted_circle_element).perform()
        targeted_circle_radius_1 = targeted_circle_element.get_attribute('r')
        self.assertGreater(targeted_circle_radius_1, targeted_circle_radius_0, "Mark radius is not larger on mouseover")
        print('Correct implementation - circle mark radius is larger on mouseover.')

    @weight(2.5)
    def test_04_mouseout_interaction(self):
        """Test that the circle mark radius becomes smaller on mouseout event"""
        # Scatterplot Circle Marks
        circle_marks = WebDriverWait(self.driver, 10) \
            .until(EC.presence_of_element_located((By.ID, "symbols"))) \
            .find_elements_by_tag_name("circle")        
        
        action = ActionChains(self.driver)
        # check that the radius changes on mouseover/hover
        targeted_circle_element = circle_marks[0]
        action.move_to_element(to_element=targeted_circle_element).perform()
        targeted_circle_radius_0 = targeted_circle_element.get_attribute('r')
        action.move_by_offset(100,100).perform()
        targeted_circle_radius_1 = targeted_circle_element.get_attribute('r')
        self.assertLess(targeted_circle_radius_1, targeted_circle_radius_0, "Mark radius is not smaller on mouseout")
        print('Correct implementation - circle mark radius becomes smaller on mouseout.')


    @weight(1.5)
    def test_07_x_axis_tick_values_length(self):
        """Test for presence of the x-axis and tick values-"""
        with NoStd():
            try:
                self.submitted_x_axis = self.driver.find_element_by_tag_name("g").find_element_by_id("x_axis")
            except:
                self.submitted_x_axis = None
            try:
                x_ticks = self.submitted_x_axis.find_elements_by_class_name("tick")
                self.submitted_x_ticks = [t for t in x_ticks]
            except:
                self.submitted_x_ticks = None

            if self.submitted_x_axis is None:
                self.assertIsNotNone(self.submitted_x_axis,
                                     "X-axis not found \nCheck that the corresponding <g> element has the correct id and is inserted correctly within the DOM hierarchy.\nVerify that you have not appended any other elements to the x-axis <g> element.")
            elif self.submitted_x_axis:
                self.assertEqual(len(self.solution_x_ticks), len(self.submitted_x_ticks),
                                 f"Incorrect number of tick values ({len(self.submitted_x_ticks)}) found for x-axis. \n Verify axis domain and tick settings.")

        print(f"Found {len(self.submitted_x_ticks)} tick values for the x-axis")


    @weight(1.5)
    def test_08_y_axis_tick_values_length(self):
        """Test for presence of the y-axis and tick values-"""
        with NoStd():
            try:
                self.submitted_y_axis = self.driver.find_element_by_tag_name("g").find_element_by_id("y_axis")
                y_ticks = self.submitted_y_axis.find_elements_by_class_name("tick")
                self.submitted_y_ticks = [t for t in y_ticks]
            except:
                self.submitted_y_axis = None
                self.submitted_y_ticks = None

            if self.submitted_y_ticks is None:
                self.assertIsNotNone(self.submitted_y_axis,
                                     "y-axis not found \nCheck that the corresponding <g> element has the correct id and is inserted correctly within the DOM hierarchy.\nVerify that you have not appended any other elements to the y-axis <g> element.")
            elif self.submitted_y_axis:
                self.assertEqual(len(self.solution_y_ticks), len(self.submitted_y_ticks),
                                 f"Incorrect number of tick values ({len(self.submitted_y_ticks)}) found for y-axis. \nVerify axis domain and tick settings.")

        print(f"Found {len(self.submitted_y_ticks)} tick values for the y-axis")


    @weight(1.0)
    def test_09_x_axis_label(self):
        """Test for the correct x-axis label"""
        with NoStd():
            try:
                self.submitted_x_axis_label = self.driver.find_element_by_id("x_axis_label").text
            except:
                self.submitted_x_axis_label = None

            if self.submitted_x_axis_label is None:
                self.assertIsNotNone(self.submitted_x_axis_label,
                                     "X-axis label not found.  \nCheck that the corresponding <g> element has the correct id and is inserted correctly within the DOM hierarchy.\nVerify that you have not appended any other elements to the x-axis <g> element.")
            else:
                self.assertEqual(str(self.solution_x_axis_label).lower(), str(self.submitted_x_axis_label).lower(),
                                 f"Retrieved text '{self.submitted_x_axis_label}' for the x-axis label is incorrect.")
        print(f"Found x-axis label: '{self.submitted_x_axis_label}'")


    @weight(0.5)
    def test_10_y_axis_label(self):
        """Test for the correct y-axis label"""
        with NoStd():
            try:
                self.submitted_y_axis_label = self.driver.find_element_by_id("y_axis_label").text
            except:
                self.submitted_y_axis_label = None

            if self.submitted_y_axis_label is None:
                self.assertIsNotNone(self.submitted_y_axis_label,
                                     "Y-axis label not found.  \nCheck that the corresponding <g> element has the correct id and is inserted correctly within the DOM hierarchy.\nVerify that you have not appended any other elements to the y-axis <g> element.")
            else:
                self.assertEqual(str(self.solution_y_axis_label).lower(), str(self.submitted_y_axis_label).lower(),
                                 f"Retrieved text '{self.submitted_y_axis_label}' for the y-axis label is incorrect.")
        print(f"Found y-axis label: '{self.submitted_y_axis_label}'")


    @weight(0.5)
    def test_11_y_axis_label_orientation(self):
        """Test the y-axis label orientation"""
        with NoStd():
            try:
                self.submitted_y_axis_label = self.driver.find_element_by_id("y_axis_label").text
            except:
                self.submitted_y_axis_label = None            
            
            if self.submitted_y_axis_label is None:
                self.assertIsNotNone(self.submitted_y_axis_label,
                                    "Test fails becuase the y-axis label was not found.")
            else:
                try:
                    transform = self.driver.find_element_by_id("y_axis_label").value_of_css_property("transform")
                    y_axis_transform = parse_css_transform_matrix(transform)
                    y_axis_transform_angle = css_matrix_rotation(y_axis_transform)
                except:
                    y_axis_transform = None
                if y_axis_transform is None:
                    self.assertIsNotNone(y_axis_transform_angle, "The y-axis label was found but the label orientation could not be retrieved.")
                else:
                    self.assertEqual(-90.0, y_axis_transform_angle, "The y-axis label needs to be rotated to align with the y-axis.")
            print(f"y-axis label rotated by: {y_axis_transform_angle} degrees.")


    @weight(0.75)
    def test_12_y_axis_tick_value_domain(self):
        """Testing the y-scale tick values"""
        with NoStd():
            try:
                self.submitted_y_axis = self.driver.find_element_by_tag_name("g").find_element_by_id("y_axis")
                y_ticks = self.submitted_y_axis.find_elements_by_class_name("tick")
                self.submitted_y_ticks = [t for t in y_ticks]
            except:
                self.submitted_y_axis = None
                self.submitted_y_ticks = None             
            
            if self.submitted_y_axis is None:
                self.assertIsNotNone(self.submitted_y_axis, "Test fails becuase the y-axis was not found.")

            solution_min = min([t for t in self.solution_y_ticks])
            solution_max = max([t for t in self.solution_y_ticks])
            y_tick_values = np.sort([np.int(t.text.replace(',','')) for t in self.submitted_y_ticks])
            submitted_min = min(y_tick_values)
            submitted_max = max(y_tick_values)

            ticks_1_locations = [t.location['y'] for t in self.submitted_y_ticks][1:]
            ticks_2_locations = [t.location['y'] for t in self.submitted_y_ticks][:-1]
            steps = [ticks_1_locations[i] - ticks_2_locations[i] for i, value in enumerate(ticks_1_locations)]
            num_steps = set(steps)

            ticks_1_values = y_tick_values[1:]
            ticks_2_values = y_tick_values[:-1]
            value_spacing = [ticks_1_values[i] - ticks_2_values[i] for i, value in enumerate(ticks_1_values)]
            num_value_spaces = set(value_spacing)

            self.assertEqual(str(solution_min), str(submitted_min),
                             f"found incorrect lower bound ({submitted_min}) of y-scale domain. \nCheck the domain of the y-axis.")
            self.assertEqual(str(solution_max), str(submitted_max),
                             f"found incorrect upper bound ({submitted_max}) of y-scale domain. \nCheck the domain of the y-axis.")
            self.assertEqual(5, abs(list(num_value_spaces)[0]), "Incorrect spacing found between values in the y-axis ticks")
        print(f"Found y-axis values [{y_tick_values[0]},{y_tick_values[1]},...,{y_tick_values[-1]}].")


    @weight(0.25)
    def test_13_y_axis_orientation(self):
        """Testing for a left-oriented axis"""
        with NoStd():
            try:
                self.submitted_y_axis = self.driver.find_element_by_id("y_axis")
            except:
                self.submitted_y_axis = None            
                        
            if self.submitted_y_axis is None:
                self.assertIsNotNone(self.submitted_y_axis, "This test fails becuase the y-axis was not found.")
            else:
                try:
                    y_tick_groups = self.driver.find_element_by_id("y_axis").find_elements_by_class_name("tick")
                    y_tick_marks = [g.find_elements_by_tag_name("line") for g in y_tick_groups]
                    y_axis_tick_orientation = [np.int(mark[0].get_attribute('x2')) for mark in y_tick_marks]
                    y_axis_tick_orientation = list(set(y_axis_tick_orientation))[0] #orientation of tick maark                    
                except:
                    y_axis_tick_orientation = None

                if y_axis_tick_orientation is None:
                    self.assertIsNotNone(y_axis_tick_orientation, "The y-axis was found the but y-axis orientation could not be retrieved")
                else:
                    self.assertGreater(0, y_axis_tick_orientation, "The y-axis is likely NOT left-oriented. The y-axis tick marks should be displayed left of the axis. \nCheck the y-axis orientation settings.")
        print("y-axis is likely left-oriented.")


    @weight(2.75)
    def test_14_x_axis_tick_value_domain(self):
        """Testing the x-scale tick values"""
        with NoStd():
            try:
                self.submitted_x_axis = self.driver.find_element_by_tag_name("g").find_element_by_id("x_axis")
            except:
                self.submitted_x_axis = None
            try:
                x_ticks = self.submitted_x_axis.find_elements_by_class_name("tick")
                self.submitted_x_ticks = [t for t in x_ticks]
            except:
                self.submitted_x_ticks = None

            if self.submitted_x_axis is None:
                self.assertIsNotNone(self.submitted_x_axis, "Test fails becuase the x-axis was not found.")

            solution_min = min([t for t in self.solution_x_ticks])
            solution_max = max([t for t in self.solution_x_ticks])
            x_tick_values = np.sort([np.int(t.text.replace(',','')) for t in self.submitted_x_ticks])
            submitted_min = min(x_tick_values)
            submitted_max = max(x_tick_values)

            ticks_1_locations = [t.location['x'] for t in self.submitted_x_ticks][1:]
            ticks_2_locations = [t.location['x'] for t in self.submitted_x_ticks][:-1]
            steps = [ticks_1_locations[i] - ticks_2_locations[i] for i, value in enumerate(ticks_1_locations)]
            num_steps = set(steps)

            ticks_1_values = x_tick_values[1:]
            ticks_2_values = x_tick_values[:-1]
            value_spacing = [ticks_1_values[i] - ticks_2_values[i] for i, value in enumerate(ticks_1_values)]
            num_value_spaces = set(value_spacing)

            self.assertEqual(str(solution_min), str(submitted_min),
                             f"found incorrect lower bound ({submitted_min}) of x-scale domain. \nCheck the domain of the x-axis.")
            self.assertEqual(str(solution_max), str(submitted_max),
                             f"found incorrect upper bound ({submitted_max}) of x-scale domain. \nCheck the domain of the x-axis.")
            self.assertEqual(20, abs(list(num_value_spaces)[0]), "Incorrect spacing found between values in the x-axis ticks")
        print(f"Found y-axis values \n{x_tick_values}.")            

    @weight(0.25)
    def test_15_x_axis_orientation(self):
        """Testing for a bottom-oriented x-axis"""
        with NoStd():
            try:
                self.submitted_x_axis = self.driver.find_element_by_tag_name("g").find_element_by_id("x_axis")
            except:
                self.submitted_x_axis = None

            if self.submitted_x_axis is None:
                self.assertIsNotNone(self.submitted_x_axis, "This test fails becuase the x-axis was not found in test Q3.d part 1.")
            else:
                try:
                    x_tick_groups = self.driver.find_element_by_id("x_axis").find_elements_by_class_name("tick")
                    x_tick_marks = [g.find_elements_by_tag_name("line") for g in x_tick_groups]
                    x_tick_marks_y2 = [np.int(mark[0].get_attribute('y2')) for mark in x_tick_marks] #orientation of tick mark
                    x_axis_tick_orientation = list(set(x_tick_marks_y2))[0]
                except:
                    x_axis_tick_orientation = None

                if x_axis_tick_orientation is None:
                    self.assertIsNotNone(x_axis_tick_orientation, "The x-axis was found but the x-axis orientation could not be retrieved")
                else:
                    self.assertLess(0, x_axis_tick_orientation, "The x-axis is likely NOT bottom-oriented. The x-axis tick marks should be displayed below the axis. \nCheck the x-axis orientation settings.")
        print("x-axis is likely bottom-oriented.")

    @weight(0.5)
    def test_16_chart_title(self):
        """Test for the title displayed above barplot"""
        with NoStd():
            try:
                self.submitted_title = self.driver.find_element_by_id("title").text
            except:
                self.submitted_title = None

            if self.submitted_title is None:
                self.assertIsNotNone(self.submitted_title, "Chart title not found")
            elif type(self.submitted_title) == str:
                self.assertEqual(str(self.solution_title).lower(), str(self.submitted_title).lower(),
                                 "Chart title: '" + self.submitted_title + "' incorrect")
        print(f"Found chart title: {self.submitted_title}")
