import os
import jinja2

class Constants:
    SiteDescription = "Welcome to Shark Attack Data. The aim of this website is to increase understanding, and promote an informed " + \
    "discussion on the subject of shark attacks; when, where and how they occur. Through visualisation of the data, it aims to help " + \
    "identify where patterns exist in terms of both geography and time."
    UrlPartCountryRegex = r"([A-Za-z\-_]+)"
    UrlPartAreaRegex = r"([A-Za-z0-9\-_]+)"
    UrlPartGsafCaseNumberRegex = r"([A-Za-z0-9\-\._]+)"
    JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)
