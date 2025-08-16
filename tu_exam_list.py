# tu_exam_list.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import requests
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TUExamScraper:
    def __init__(self, symbol_number):
        self.symbol_number = symbol_number
        self.driver = self._setup_driver()
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Configure and return a Chrome WebDriver instance."""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def take_screenshot(self, name: str) -> str:
        """Take a single screenshot at the end and return the filename."""
        filename = f'{name}_{self.symbol_number}.png'
        self.driver.save_screenshot(filename)
        logger.info(f"Final screenshot saved as {filename}")
        return filename
    
    def process_with_ocr(self, image_path):
        """Process the screenshot with OCR"""
        try:
            logger.info("Processing with OCR...")
            url = "https://api.ocr.space/parse/image"
            
            with open(image_path, 'rb') as f:
                response = requests.post(
                    url,
                    files={"image": f},
                    data={
                        "apikey": 'K88919177488957',
                        "language": "eng",
                        "isTable": "true",
                        "OCREngine": "2"
                    }
                )
            
            if response.status_code == 200:
                result = response.json()
                if result["IsErroredOnProcessing"]:
                    raise Exception(f"OCR error: {result['ErrorMessage']}")
                
                ocr_text = result["ParsedResults"][0]["ParsedText"]
                self.parse_marksheet(ocr_text)
                return ocr_text
            raise Exception(f"API request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            return None
    
    def parse_marksheet(self, text):
        """Parse and display structured data from OCR text"""
        data = {
            "name": None,
            "roll_no": None,
            "program": None,
            "exam": None,
            "subjects": [],
            "total_marks": None,
            "obtained_marks": None,
            "result": None
        }

        def extract(pattern, text, group=1):
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return match.group(group).strip() if match else None

        # Extract fields
        data["name"] = extract(r"NAME:\s*(.+)", text)
        data["roll_no"] = extract(r"ROLL NO:\s*(\d+)", text)
        data["program"] = extract(r"PROGRAM:\s*(.+?)(?:\n|EXAM|$)", text)
        data["exam"] = extract(r"EXAM:\s*(.+?)(?:\n|PROGRAM|$)", text)
        data["total_marks"] = extract(r"Total\s*Marks:\s*(\d+)", text) or extract(r"Total\s*Marks\s*(\d+)", text)
        data["obtained_marks"] = extract(r"Obtained\s*Marks:\s*(\d+)", text) or extract(r"Obtained\s*Marks\s*(\d+)", text)
        data["result"] = extract(r"Result:\s*(\w+)", text)

        # Extract subjects
        subject_matches = re.finditer(
            r"([A-Z]{2,4}[:\s]*\d*[:\s]*[^\n\d]+?)\s+(\d+)\s+(\d+\.?\d*)\s+(\d+)", 
            text
        )
        for match in subject_matches:
            data["subjects"].append({
                "subject": match.group(1).strip(),
                "full_marks": match.group(2),
                "pass_marks": match.group(3),
                "obtained_marks": match.group(4)
            })

        # Print structured results
        print("\n=== Marksheet Data ===")
        print(f"Name: {data['name']}")
        print(f"Roll No: {data['roll_no']}")
        print(f"Program: {data['program']}")
        print(f"Exam: {data['exam']}\n")
        
        print("Subjects:")
        for sub in data['subjects']:
            print(f"- {sub['subject']}: {sub['obtained_marks']}/{sub['full_marks']}")
        
        print(f"\nTotal Marks: {data['total_marks']}")
        print(f"Obtained Marks: {data['obtained_marks']}")
        print(f"Result: {data['result']}")
    
    def run(self):
        try:
            logger.info("Loading results page...")
            self.driver.get("https://result.tuexam.edu.np/")
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)

            # Get all exam options
            exam_select = Select(WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "select"))
            ))
            
            # Filter and display BSC exams
            bsc_options = []
            logger.info("\nAvailable BSC Exams:")
            for i, option in enumerate([opt for opt in exam_select.options if "BSC" in opt.text], 1):
                bsc_options.append((i, option.get_attribute('value'), option.text))
                logger.info(f"{i}. {option.text}")
            
            if not bsc_options:
                logger.warning("No BSC exams found!")
                return
            
            # Get user selection
            while True:
                try:
                    selection = int(input("\nEnter the number of the exam you want to select: "))
                    if 1 <= selection <= len(bsc_options):
                        selected_value = bsc_options[selection-1][1]
                        exam_select.select_by_value(selected_value)
                        logger.info(f"Selected exam: {bsc_options[selection-1][2]}")
                        break
                    print(f"Please enter a number between 1 and {len(bsc_options)}")
                except ValueError:
                    print("Please enter a valid number.")
            
            # Select program
            program_label_xpath = "//label[contains(text(), 'Program')]"
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, program_label_xpath)))
            time.sleep(1)
            
            program_label = self.driver.find_element(By.XPATH, program_label_xpath)
            program_select = Select(self.driver.find_element(By.ID, program_label.get_attribute("for")))
            
            for option in program_select.options:
                if "Bachelor Degree in Science (B.Sc.)" in option.text:
                    program_select.select_by_visible_text(option.text)
                    break
            
            # Select program duration
            duration_label_xpath = "//label[contains(text(), 'Program Duration')]"
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, duration_label_xpath)))
            time.sleep(1)
            
            duration_label = self.driver.find_element(By.XPATH, duration_label_xpath)
            duration_select = Select(self.driver.find_element(By.ID, duration_label.get_attribute("for")))
            
            for option in duration_select.options:
                if option.text in ["1st Year", "2nd Year", "3rd Year", "4th Year"]:
                    duration_select.select_by_visible_text(option.text)
                    break
            
            # Enter symbol number and search
            symbol_number_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Symbol Number')]"))
            )
            symbol_number_input.send_keys(self.symbol_number)
            
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search')]"))
            )
            search_button.click()
            
            # Wait for results and take final screenshot
            time.sleep(5)
            screenshot_path = self.take_screenshot('result')
            
            # Process the screenshot with OCR
            self.process_with_ocr(screenshot_path)
            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
        finally:
            self.driver.quit()
            logger.info("Browser closed.")

if __name__ == "__main__":
    # Get symbol number from user at the start
    symbol_number = input("Enter your symbol number: ").strip()
    scraper = TUExamScraper(symbol_number)
    scraper.run()
