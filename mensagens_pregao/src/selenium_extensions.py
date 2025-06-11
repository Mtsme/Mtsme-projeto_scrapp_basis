class element_has_atribute_value(object):
    """An expectation for checking that an element has a particular attribute with value

    locator - used to find the element
    returns the WebElement once it has the particular value set
    """
    def __init__(self, locator, attribute_name):
        self.locator = locator
        self.attribute_name = attribute_name

    def __call__(self, driver):
        element = driver.find_element(*self.locator)   # Finding the referenced element
        if element.get_attribute(self.attribute_name):
            return element
        else:
            return False