#!/usr/local/bin/python3
from selenium import webdriver
from time import sleep
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import undetected_chromedriver as uc


import os
import glob

import random

from PyPDF2 import PdfFileWriter, PdfFileReader

import tempfile
from functools import reduce
import json


#modify book address here, you can use the ones here to test the script
book_url="https://www.jstor.org/stable/10.1525/j.ctv1xxxq7"

#modify parent directory here
#the book will be saved to a new directory under the parent directory
parent_directory = "/Users/lws/Documents/School Downloads/"

#modify this if you do not need merged pdf book file
merge = True

#maximum time to complete recaptcha in seconds
time_for_recaptcha = 100

#To handle "Terms and Conditions" Agreement
terms_accepted = False

class ChromeWithPrefs(uc.Chrome):
    def __init__(self, *args, options=None, **kwargs):
        if options:
            self._handle_prefs(options)

        super().__init__(*args, options=options, **kwargs)

        # remove the user_data_dir when quitting
        self.keep_user_data_dir = False

    @staticmethod
    def _handle_prefs(options):
        prefs = options.experimental_options.get("prefs")
        if prefs:
            # turn a (dotted key, value) into a proper nested dict
            undot_prefs = {}
            for key, value in prefs.items():
                main_key, sub_key = key.split('.',1)
                if main_key not in undot_prefs:
                    undot_prefs[main_key]={}
                undot_prefs[main_key][sub_key] = value              

            # create an user_data_dir and add its path to the options
            user_data_dir = os.path.normpath(tempfile.mkdtemp())
            options.add_argument(f"--user-data-dir={user_data_dir}")

            # create the preferences json file in its default directory
            default_dir = os.path.join(user_data_dir, "Default")
            os.mkdir(default_dir)

            prefs_file = os.path.join(default_dir, "Preferences")
            with open(prefs_file, encoding="latin1", mode="w") as f:
                json.dump(undot_prefs, f)

            # pylint: disable=protected-access
            # remove the experimental_options to avoid an error
            del options._experimental_options["prefs"]

def accept_cookie():
    
    accept_button = driver.find_element('id',"onetrust-accept-btn-handler")
    accept_button.click()
    
def accept_terms():
    #dealing with possible recaptcha
    wait = WebDriverWait(driver, time_for_recaptcha)
    wait.until(EC.presence_of_element_located((By.TAG_NAME,"mfe-download-pharos-button")))
    
    accept_button = driver.find_elements('tag name',"mfe-download-pharos-button")[1]
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', accept_button)
    sbutton= shadow_root.find_element('id','button-element')
    
    actions = ActionChains(driver)
    actions.move_to_element(sbutton).click().perform()
    
    sleep(0.2)
    print("terms and conditions accepted!")
    global terms_accepted 
    terms_accepted = True
    
def get_latest_file(directory):
    try:
        return max(glob.glob(directory+'/*'), key=os.path.getctime)
    #possible to throw this error if a new file is just downloaded, as the temporary file no longer exists
    except FileNotFoundError: 
        return max(glob.glob(directory+'/*'), key=os.path.getctime)
        
def merge_JSTOR_chapters(input_paths,output_path):
    pdf_writer = PdfFileWriter()
 
    for path in input_paths:
        pdf_reader = PdfFileReader(path)
        for page in range(1,pdf_reader.getNumPages()):
            pdf_writer.addPage(pdf_reader.getPage(page))
 
    with open(output_path, 'wb') as fh:
        pdf_writer.write(fh)

        
directory = parent_directory + "New Folder " + datetime.now().strftime('%Y-%m-%d %H_%M_%S') + "/"
os.mkdir(directory)

#setting up the webdriver
prefs = {"plugins.always_open_pdf_externally": True,"download.default_directory":directory,"download.prompt_for_download":False,"download.directory_upgrade":True,"safebrowsing.enabled":True,"download.extensions_to_open": "applications/pdf"}
options = uc.ChromeOptions()
options.add_experimental_option("prefs", prefs)

# use the derived Chrome class that handles prefs
driver = ChromeWithPrefs(options=options)

print(driver.execute_script("return navigator.userAgent;"))


#navigate to the book page        
driver.get(book_url)

#dealing with possible recaptcha
wait = WebDriverWait(driver, time_for_recaptcha)
#until recaptcha is done
element = wait.until(EC.presence_of_element_located((By.CLASS_NAME,"download__mount-point")))

sleep(0.5)   

accept_cookie()

sleep(0.5)

#get the book title str
book_title = driver.find_element('xpath',"//*[@id='content']/div[2]/book-view-pharos-layout/div[1]/div[1]/div[1]/div[2]/book-view-pharos-heading").text
print(book_title)

#get the download button containers
chapter_links = driver.find_elements('tag name',"mfe-download-pharos-link")

#get the chapter title strs
chapter_titles = driver.find_elements('tag name',"book-view-pharos-link")[1:-1]
chapter_title_texts = [x.text for x in chapter_titles]

num_chapters = len(chapter_links)

print("number of files:",num_chapters)
print(chapter_title_texts)

#click the download
for i in range(num_chapters):
    link = chapter_links[i]
    
    #move the download button into view
    driver.execute_script("arguments[0].scrollIntoView(true);",link)
    
    #handle the shadow root
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', link)
    slink = shadow_root.find_element('id','link-element')
    
    #To resolve "Other element would receive the click" error if use slink.click() directly
    actions = ActionChains(driver)
    actions.move_to_element(slink).click().perform()
    
    #handle term acceptance
    if terms_accepted == False:
        accept_terms()
    
    #handle possible emergence of captcha again    
    wait = WebDriverWait(driver, time_for_recaptcha)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME,"download__mount-point")))
    
    #reduce download speed to avoid trigger captcha too frequently
    sleep(1+random.random())



files_to_merge = [] 
new_directory_name = parent_directory + book_title

#rename the chapters
for i in range(num_chapters):
    chapter_title_text = chapter_title_texts[i]
    current_name = directory + book_url.split('/')[-1] + '.'+str(i+1)+'.pdf'


    print('rename:',current_name,' to:',chapter_title_text)
    while os.path.exists(current_name)==False:
        pass
    os.rename(current_name, directory+chapter_title_text+".pdf") 
    files_to_merge.append(new_directory_name + '/' +chapter_title_text+".pdf")
    
   
#rename folder
os.rename(directory, new_directory_name)

#merge pdfs
if merge:
    merge_JSTOR_chapters(files_to_merge,new_directory_name + "/" + book_title + ".pdf")