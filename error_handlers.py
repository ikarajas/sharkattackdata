from constants import Constants
from helper import Helper

class ErrorHandlers:
    @staticmethod
    def generateErrorResponse(request, response, title, subTemplate, responseStatus):
        isGsaf = request.path.startswith("/gsaf")
        helper = Helper()
        template_values = {
            "title": title,
            "subtemplate": subTemplate
            }

        template = Constants.JINJA_ENVIRONMENT.get_template(helper.resolveTemplatePath("main.html", isGsaf))
        response.set_status(responseStatus)
        response.write(template.render(template_values))

    @staticmethod
    def generate404(request, response, responseStatus):
        ErrorHandlers.generateErrorResponse(request, response, "Page not found", "/templates/common/404_error.html", responseStatus)

    @staticmethod
    def handle404(request, response, exception):
        ErrorHandlers.generate404(request, response, 404)

    @staticmethod
    def handle500(request, response, exception):
        ErrorHandlers.generateErrorResponse(request, response, "Error", "/templates/common/500_error.html", 500)

