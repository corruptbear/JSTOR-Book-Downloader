#!/usr/local/bin/python3
from selenium import webdriver
from time import sleep
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import glob

from PyPDF2 import PdfFileWriter, PdfFileReader

#modify book address here
url="https://www.jstor.org/stable/10.7722/j.ctt1x71xw"
#modify parent directory here
parent_directory = "/Users/lws/Documents/School Downloads/"
#modify driver path here
driver_path = "/usr/local/bin/chromedriver" 
#modify this if you do not need merged pdf book file
merge = True

#maximum time to complete recaptcha in seconds
time_for_recaptcha = 100

#To handle "Terms and Conditions" Agreement
terms_accepted = False

def accept_terms():
    #dealing with possible recaptcha
    wait = WebDriverWait(driver, time_for_recaptcha)
    wait.until(EC.presence_of_element_located((By.ID,"acceptTC")))
    driver.find_element_by_id("acceptTC").click()
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
        
directory = parent_directory + "New Folder " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "/"
os.mkdir(directory)

#setting up the webdriver
chrome_options = webdriver.ChromeOptions()
prefs = {"plugins.always_open_pdf_externally": True,"download.default_directory":directory,"download.prompt_for_download":False,"download.directory_upgrade":True,"safebrowsing.enabled":True,"download.extensions_to_open": "applications/pdf"}
chrome_options.add_experimental_option("prefs",prefs)
driver = webdriver.Chrome(driver_path, options=chrome_options) 

#navigate to the book page        
driver.get(url)

#dealing with possible recaptcha
wait = WebDriverWait(driver, time_for_recaptcha)
element = wait.until(EC.presence_of_element_located((By.CLASS_NAME,"pdfLink")))

sleep(0.5)   

book_title = driver.find_element_by_xpath("//*[@id='content']/div[1]/div[2]/div[1]/div/div/div[1]/div/div/div[2]/h1").text
print(book_title)

chapter_links = driver.find_elements_by_class_name("pdfLink")
chapter_titles = driver.find_elements_by_class_name("chapter-title")

num_chapters = len(chapter_links)
print("number of files:",num_chapters)

#collect urls first to avoid stale element error
download_urls = [chapter_link.get_attribute("href") for chapter_link in chapter_links]
chapter_title_texts = [chapter_title.find_element_by_xpath(".//div[2]/div[1]/a/span").text for chapter_title in chapter_titles]

for i in range(num_chapters):
    download_url = download_urls[i] 
    title_text = chapter_title_texts[i]

    print("to download: "+download_url)
    
    driver.get(download_url)
    
    sleep(0.05)
    
    if terms_accepted == False:
        accept_terms()
    
    while get_latest_file(directory).find(".crdownload")!=-1:
        sleep(0.1)
        
    #rename latest downloaded file
    os.rename(get_latest_file(directory), directory+title_text+".pdf") 
    print(directory+title_text+".pdf"+" downloaded")
    
#rename folder
new_directory_name = parent_directory + book_title
os.rename(directory, new_directory_name)

#merge pdfs
if merge:
    files = list(filter(os.path.isfile, glob.glob(new_directory_name + "/*")))
    files.sort(key=lambda x: os.path.getctime(x))
    merge_JSTOR_chapters(files,new_directory_name + "/" + book_title + ".pdf")