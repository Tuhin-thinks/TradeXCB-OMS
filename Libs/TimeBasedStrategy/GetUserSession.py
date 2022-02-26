import urllib.parse as urlparse

import onetimepass as otp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Libs.Files import handle_user_details
from Libs.Utils.auto_driver_donwnload import download_driver
from Libs.globals import *

logger = exception_handler.getFutureLogger(__name__)


class ZerodhaAccessToken:
    def __init__(self):
        api_details_dict = handle_user_details.read_user_settings()

        self.apiKey = api_details_dict["API Key"]
        self.apiSecret = api_details_dict["API Secret"]
        self.accountUserName = api_details_dict["Account User Name"]
        self.accountPassword = api_details_dict["Account Password"]
        self.securityPin = api_details_dict["Security Pin"]
        self.totp_secret = api_details_dict["TOTP Secret"]
        self.pkl_file_name = settings.DATA_FILES.get("get_user_session_pickle")
        self.access_token, self.enctoken = self.getaccesstoken()

    def get_totp_token(self):
        return otp.get_totp(self.totp_secret)

    def generate_access_token(self, login_url):
        try:

            logger.info('generate access token :: Process Started')

            # login_url = "https://kite.trade/connect/login?v=3&api_key={apiKey}".format(apiKey=self.apiKey)

            # change the chrome driver path
            # chrome_driver_path = "/home/vinay.kachare@SMECORNER.COM/Downloads/chromedriver_linux64/chromedriver"
            # chrome_driver_path = "{}/chromedriver.exe".format(os.getcwd())
            chrome_driver_path = download_driver()
            options = Options()

            # ------------------ By enabling below option you can run chrome without UI
            options.add_argument('--headless')

            # ------------------ chrome driver object
            driver = webdriver.Chrome(chrome_driver_path, options=options)

            # ------------------ load the url into chrome
            driver.get(login_url)

            # ------------------ wait to load the site
            wait = WebDriverWait(driver, 20)

            # ------------------ Find User Id field and set user id
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]'))) \
                .send_keys(self.accountUserName)

            # ------------------ Find password field and set user password
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]'))) \
                .send_keys(self.accountPassword)

            # ------------------ Find submit button and click
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))) \
                .submit()

            # ------------------ Find pin field and set  pin value
            time.sleep(10)
            # driver.implicitly_wait(10)
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]'))).click()
            driver.find_element(By.XPATH, '//input[@type="text"]').send_keys(self.get_totp_token())

            # ------------------ Final Submit
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))).submit()

            # ------------------ wait for redirection
            wait.until(EC.url_contains('status=success'))

            # ------------------ get the token url after success
            tokenurl = driver.current_url
            parsed = urlparse.urlparse(tokenurl)

            # ------------------ Find User Id field and set user id
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]'))) \
                .send_keys(self.accountUserName)

            # ------------------ Find password field and set user password
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]'))) \
                .send_keys(self.accountPassword)

            # ------------------ Find submit button and click
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))) \
                .submit()

            # ------------------ Find pin field and set  pin value
            time.sleep(10)
            driver.implicitly_wait(10)
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]'))).click()
            driver.find_element(By.XPATH, '//input[@type="text"]').send_keys(self.get_totp_token())

            # ------------------ Final Submit
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))).submit()
            time.sleep(2)
            driver.implicitly_wait(2)
            # ------------------ store the cookies
            cookies_kite = driver.get_cookies()
            # print(cookies_kite)
            enctoken = \
                [entoken for entoken in [cookie for cookie in cookies_kite] if entoken.get('name', None) == 'enctoken'][
                    0][
                    'value']

            driver.close()
            return urlparse.parse_qs(parsed.query)['request_token'][0], enctoken
        except Exception as ex:
            logger.error("Error Ocured during request genration process", exc_info=True)
            raise

    def getaccesstoken(self):
        import pickle
        import datetime as dt

        try:

            token_data = None
            if os.path.exists(self.pkl_file_name) and os.path.getsize(self.pkl_file_name) > 0:
                with open(self.pkl_file_name, 'rb') as pkl_file:
                    token_data = pickle.load(pkl_file)

            expiry_time = dt.datetime.now()
            expiry_time = expiry_time.replace(hour=8, minute=0, second=0, microsecond=0)

            if token_data is None or token_data['token_date'] < expiry_time:
                from kiteconnect import KiteConnect
                kite = KiteConnect(api_key=self.apiKey)
                request_token, enctoken = self.generate_access_token(kite.login_url())
                data = kite.generate_session(request_token, api_secret=self.apiSecret)

                token_data = {'access_token': data['access_token'], 'token_date': dt.datetime.now(),
                              'enctoken': enctoken}
                with open(self.pkl_file_name, 'wb') as pkl_file:
                    pickle.dump(token_data, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)

            logger.info('Token Generated : {}'.format(str(token_data['access_token'])))

            return token_data['access_token'], token_data['enctoken']

        except Exception as ex:
            logger.error(f"Error Ocured during unpickle. {ex.__str__()}", exc_info=True)
            traceback.print_tb(ex.__traceback__)
            raise


# ------------------ Initialise the class object with required parameters
if __name__ == "__main__":
    try:
        _ztoken = ZerodhaAccessToken()
        # print(_ztoken)
    except Exception as ex:
        logger.error("Error Ocured during access token genration process", exc_info=True)

# print(actual_token)
