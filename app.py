import logging
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levellevel)s - %(message)s')

app = Flask(__name__)

USERNAME = "dimabagow@gmail.com"
PASSWORD = "A@2moloko777"

driver = None

def initialize_driver():
    global driver
    if driver is None:
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')  # Режим без графического интерфейса
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        login_to_opencorporates()

def login_to_opencorporates():
    global driver
    login_url = "https://opencorporates.com/users/sign_in"
    logging.info(f"Переход на страницу логина: {login_url}")
    driver.get(login_url)
    
    wait = WebDriverWait(driver, 10)
    
    logging.info("Ожидание загрузки поля для ввода email")
    username_field = wait.until(EC.presence_of_element_located((By.ID, "user_email")))
    
    logging.info("Ожидание загрузки поля для ввода пароля")
    password_field = wait.until(EC.presence_of_element_located((By.ID, "user_password")))
    
    logging.info("Ввод учетных данных")
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    
    # Поиск и нажатие кнопки входа
    logging.info("Поиск кнопки входа по селектору button[type='submit']")
    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    login_button.click()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        companies = request.form['companies'].split('\n')
        all_results = []
        for company in companies:
            company = company.strip()
            if company:
                results = search_company(company)
                for result in results:
                    result["Company Name"] = company  # Обновляем название компании в результатах
                all_results.extend(results)
        return render_template('results.html', companies=companies, results=all_results)
    return render_template('index.html')

def search_company(company_name):
    global driver
    initialize_driver()
    
    search_url = f"https://opencorporates.com/companies/us_tx?action=search_companies&branch=&commit=Go&controller=searches&inactive=false&mode=best_fields&nonprofit=false&order=incorporation_date-asc&q={company_name}&search_fields%5B%5D=name&search_fields%5B%5D=previous_names&search_fields%5B%5D=company_number&search_fields%5B%5D=other_company_numbers&type=companies&utf8=%E2%9C%93"
    logging.info("Сформированный URL для поиска: " + search_url)

    results_list = []

    try:
        # Переход по сформированному URL поиска компании
        logging.info("Переход по URL для поиска компании")
        driver.get(search_url)
        
        # Ожидание загрузки результатов поиска (пример ожидания наличия элемента с классом 'search-result')
        logging.info("Ожидание загрузки результатов поиска")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "results")))
        
        logging.info("Поиск выполнен. Текущий заголовок страницы: " + driver.title)

        # Парсинг HTML с использованием BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = soup.find('ul', id='companies').find_all('li', class_='search-result')

        # Извлечение данных
        for result in results:
            company_name = result.find('a', class_='company_search_result').text.strip()
            jurisdiction = result.find('a', class_='jurisdiction_filter').get('title', '').split(' ')[-1].strip('()')
            company_number = result.find('a', class_='company_search_result')['href'].split('/')[-1]
            incorporation_date_elem = result.find('span', class_='start_date')
            incorporation_date = incorporation_date_elem.text.strip() if incorporation_date_elem else 'N/A'
            address_elem = result.find('span', class_='address')
            address = address_elem.text.strip() if address_elem else 'N/A'

            results_list.append({
                'Company Name': company_name,
                'Jurisdiction': jurisdiction,
                'Company Number': company_number,
                'Incorporation Date': incorporation_date,
                'Address': address
            })
    except Exception as e:
        logging.error("Возникла ошибка: ", exc_info=True)

    return results_list

if __name__ == '__main__':
    app.run(debug=True)
