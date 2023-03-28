import os
import unittest
import re
from collections import Counter
from gradescope_utils.autograder_utils.decorators import weight, tags, number
from gradescope_utils.autograder_utils.decorators import partial_credit
from gradescope_utils.autograder_utils.files import check_submitted_files
import selenium
import selenium.common.exceptions
from utils.rubric_helper import get_rubric_config
from selenium import webdriver
import numpy as np
from autograde_viz.css_transforms import *

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

        driver.get(url)
        
        # set chromedrive window dimensions to student submission dimensions
        rendered_width = driver.execute_script("return document.documentElement.scrollWidth")
        rendered_height = driver.execute_script("return document.documentElement.scrollHeight")
        driver.set_window_size(rendered_width,rendered_height)
        
        cls.rubric_config = get_rubric_config('config/' + "scatterplot" + '/rubric.yaml')        
        
        cls.driver = driver

    @classmethod
    def tearDownClass(cls) -> None:
        cls.driver.quit()
    
    @weight(0.0)
    def test_0_required_elements(self):
        """Functional Advisory Test - presence of required elements."""
        # this test looks for required elements from a .yaml file
        # try lookup on element by id
        # match element with required tag name, e.g., <g>, <sv>, etc.
        # raise no such element exception if lookup fails.
        # fail test under either of 2 conditions:
        # 1. the element does not match the tag name for a given id
        # 2. an element is missing (no such element)
        required_elements = self.rubric_config["elements"]
        results = "Found: "
        for elem in required_elements:
            ids = required_elements[elem]
            matched_elems = 0
            required_elems = len(ids)
            for i in ids:
                try:
                    search_element = self.driver.find_element_by_id(i)
                    tag_name = search_element.tag_name
                    self.assertEqual(elem, tag_name, f"tag name for id {i} is incorrect.")
                    new_result = f"<{tag_name} id='{i}'>\n"
                    results = f"{results}, {new_result}"
                    matched_elems +=1                    
                except selenium.common.exceptions.NoSuchElementException as nse:
                    print(f"could not find an element with id='{i}' \n {nse}")            
            self.assertEqual(matched_elems, required_elems, \
                f"Missing {np.abs(required_elems-matched_elems)} {elem} element(s). \n\
                    Expected: {required_elements}")
        print(f"expected: {required_elements}. \n {results}")

    @weight(0.0)
    def test_1_plot_info(self):
        """Functional Advisory Test - Plot Information"""
        try:
            svg_height = self.driver.find_element_by_id("container").rect['height']
            svg_width = self.driver.find_element_by_id("container").rect['width']    
            # print(f"svg dims: {svg_width} X {svg_height}")

            # container group transform / translation
            g = self.driver.find_element_by_id("container").find_element_by_id("plot")
            g_transform = g.value_of_css_property("transform")
            g_matrix = parse_css_transform_matrix(g_transform)
            g_transform_xy = css_matrix_translation(g_matrix)
            # print(f"g element translated x: {g_transform_xy[0]}, y: {g_transform_xy[1]}")

            # assumed left margin = g transform x
            assumed_left_margin = g_transform_xy[0]
            
            # assumed top margin = g transform y
            assumed_top_margin = g_transform_xy[1]    
            
            # assumed margin.right = svg width - margin.left - x domain width
            assumed_width = self.driver.find_element_by_id("x_axis").find_element_by_class_name("domain").size['width']
            assumed_right_margin = svg_width - assumed_left_margin - assumed_width

            # assume margin.bottom = svg height - margin.top - y domain height
            assumed_height = self.driver.find_element_by_id("y_axis").find_element_by_class_name("domain").size['height']    
            assumed_bottom_margin = svg_height - assumed_top_margin - assumed_height
        
        except selenium.common.exceptions.NoSuchElementException as e:
            print(f"Missing element(s): {e}")

        plot_info = f"The autograder has found the following layout/size specification: \n\n\
            <svg> dimensions width: {svg_width} height: {svg_height} \n\n\
            container <g> transform / translation x: {g_transform_xy[0]} y: {g_transform_xy[1]} \n\n\
            x-axis <path class='domain'> width: {assumed_width} \n\n\
            y-axis <path class='domain'> height: {assumed_height} \n\
            _________________________________________________________\n\n\
            Auto-grading assumptions: \n\
            The following values are assumed for evaluating scales and element scaling / positioning: \n\n\
            Inner chart dimensions: \n\n\
            innert chart width: {assumed_width} (x-axis <path class='domain'> width) \n\n\
            inenrt chart height: {assumed_height} (y-axis <path class='domain'> height) \n\n\
            margin + padding left: {g_transform_xy[0]} (container <g> transform x) \n\n\
            margin + padding right: {assumed_right_margin} (<svg> width - margin.left - padding.left - inner chart width) \n\n\
            margin + padding top: {g_transform_xy[1]} (container <g> transform y) \n\n\
            margin + padding bottom: {assumed_bottom_margin} (<svg> width - margin.top - padding.top - inner chart height) \n\n\
            x-axis range: 0-{assumed_width} \n\n\
            y-axis range: {assumed_height}-0 \n\n"
        
        print(plot_info)

    def test_2_duplicate_ids(self):
        # duplicate ids
        ids = self.driver.find_elements_by_xpath('//*[@id]')
        elem_ids = []
        for ii in ids:
            ii_a = ii.get_attribute('id')
            # print (ii_a)
            elem_ids.append(ii_a)
        
        dupes =  list((Counter(elem_ids) - Counter(set(elem_ids))).keys())
        self.assertEqual(0, len(dupes), f"Found {len(dupes)} duplicate(s): {dupes}.\n \
            Duplicate ids will likely cause other tests to fail. \n \
            Note that this test only searches for elements with dupicate ids after initial load of 'submission.html'. \n \
            Any subsequent element insertion could still result in un-detected duplicate ids and failed tests.")
        print(f"Found {len(dupes)} duplicate(s): {dupes}")        

