import base64
from io import BytesIO
import os
from PIL import Image, ImageChops
from appium.webdriver.common.mobileby import MobileBy
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from tests import info


class BaseElement(object):
    class Locator(object):

        def __init__(self, by, value):
            self.by = by
            self.value = value

        @classmethod
        def xpath_selector(locator, value):
            return locator(MobileBy.XPATH, value)

        @classmethod
        def accessibility_id(locator, value):
            return locator(MobileBy.ACCESSIBILITY_ID, value)

        @classmethod
        def text_selector(locator, text):
            return BaseElement.Locator.xpath_selector('//*[@text="' + text + '"]')

        @classmethod
        def text_part_selector(locator, text):
            return BaseElement.Locator.xpath_selector('//*[contains(@text, "' + text + '")]')

        def __str__(self, *args, **kwargs):
            return "%s:%s" % (self.by, self.value)

    def __init__(self, driver):
        self.driver = driver
        self.locator = None

    @property
    def name(self):
        return self.__class__.__name__

    def navigate(self):
        return None

    def find_element(self):
        info('Looking for %s' % self.name)
        try:
            return self.driver.find_element(self.locator.by, self.locator.value)
        except NoSuchElementException as exception:
            exception.msg = "'%s' is not found on screen, using: '%s'" % (self.name, self.locator)
            raise exception

    def find_elements(self):
        info('Looking for %s' % self.name)
        return self.driver.find_elements(self.locator.by, self.locator.value)

    def wait_for_element(self, seconds=10):
        try:
            return WebDriverWait(self.driver, seconds) \
                .until(expected_conditions.presence_of_element_located((self.locator.by, self.locator.value)))
        except TimeoutException as exception:
            exception.msg = "'%s' is not found on screen, using: '%s', during '%s' seconds" % (self.name, self.locator,
                                                                                               seconds)
            raise exception

    def wait_for_visibility_of_element(self, seconds=10):
        try:
            return WebDriverWait(self.driver, seconds) \
                .until(expected_conditions.visibility_of_element_located((self.locator.by, self.locator.value)))
        except TimeoutException as exception:
            exception.msg = "'%s' is not found on screen, using: '%s', during '%s' seconds" % (self.name, self.locator,
                                                                                               seconds)
            raise exception

    def scroll_to_element(self):
        for _ in range(9):
            try:
                return self.find_element()
            except NoSuchElementException:
                info('Scrolling down to %s' % self.name)
                self.driver.swipe(500, 1000, 500, 500)

    def is_element_present(self, sec=5):
        try:
            info('Wait for %s' % self.name)
            return self.wait_for_element(sec)
        except TimeoutException:
            return False

    def is_element_displayed(self, sec=5):
        try:
            info('Wait for %s' % self.name)
            return self.wait_for_visibility_of_element(sec)
        except TimeoutException:
            return False

    @property
    def text(self):
        return self.find_element().text

    @property
    def template(self):
        try:
            return self.__template
        except FileNotFoundError:
            raise FileNotFoundError('Please add %s image as template' % self.name)

    @template.setter
    def template(self, value):
        self.__template = Image.open(os.sep.join(__file__.split(os.sep)[:-1]) + '/elements_templates/%s' % value)

    @property
    def image(self):
        return Image.open(BytesIO(base64.b64decode(self.find_element().screenshot_as_base64)))

    def is_element_image_equals_template(self):
        return not ImageChops.difference(self.image, self.template).getbbox()

    def swipe_element(self):
        element = self.find_element()
        location, size = element.location, element.size
        x, y = location['x'], location['y']
        width, height = size['width'], size['height']
        self.driver.swipe(start_x=x + width / 2, start_y=y + height / 2, end_x=x, end_y=y + height / 2)


class BaseEditBox(BaseElement):

    def __init__(self, driver):
        super(BaseEditBox, self).__init__(driver)

    def send_keys(self, value):
        self.find_element().send_keys(value)
        info("Type '%s' to %s" % (value, self.name))

    def set_value(self, value):
        self.find_element().set_value(value)
        info("Type '%s' to %s" % (value, self.name))

    def clear(self):
        self.find_element().clear()
        info('Clear text in %s' % self.name)

    def click(self):
        self.find_element().click()
        info('Tap on %s' % self.name)


class BaseText(BaseElement):

    def __init__(self, driver):
        super(BaseText, self).__init__(driver)

    @property
    def text(self):
        text = self.find_element().text
        info('%s is %s' % (self.name, text))
        return text


class BaseButton(BaseElement):

    def __init__(self, driver):
        super(BaseButton, self).__init__(driver)

    def click(self):
        self.find_element().click()
        info('Tap on %s' % self.name)
        return self.navigate()

    def click_until_presence_of_element(self, desired_element, attempts=3):
        counter = 0
        while not desired_element.is_element_present(1) and counter <= attempts:
            try:
                info('Tap on %s' % self.name)
                self.find_element().click()
                info('Wait for %s' % desired_element.name)
                desired_element.wait_for_element(5)
                return self.navigate()
            except (NoSuchElementException, TimeoutException):
                counter += 1
