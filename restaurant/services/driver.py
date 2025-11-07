import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class DriverManager:
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    max_scrolls = 10
    scroll_pause_sec = 1.0
    timeout = 20

    def init(self) -> webdriver.Remote:
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')  # for Docker
        options.add_argument('--disable-dev-shm-usage')  # for memory
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'--user-agent="{self.user_agent}"')

        self.driver = webdriver.Remote(
            command_executor='http://selenium-hub:4444/wd/hub',
            options=options,
        )

        info_logger.info('Driver initialized.')

        return self.driver

    def quit(self) -> None:
        self.driver.quit()
        info_logger.info('All scraping completed successfully.')
