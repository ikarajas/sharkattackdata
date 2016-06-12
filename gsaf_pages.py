from pages import *

class GsafMainPage(MainPage):
    def handle(self):
        return {
            "breadcrumb_data": self.getBreadcrumbData(None),
            "countries": sorted(self.helper.getCountries(), key=lambda c: c.name)
            }

    def __init__(self, *args):
        super(GsafMainPage, self).__init__(*args)
        
class GsafAttackPage(AttackPage):
    def __init__(self, *args):
        super(GsafAttackPage, self).__init__(*args)
        
class GsafAreaPage(AreaPage):
    def __init__(self, *args):
        super(GsafAreaPage, self).__init__(*args)
        
class GsafCountryPage(CountryPage):
    def __init__(self, *args):
        super(GsafCountryPage, self).__init__(*args)

