""" Support case application support. """
#pylint: enable=relative-import,missing-docstring

from controller.mailer import Mailer
from controller.profile import Role
from controller.system import SystemKeys

from .option import ListOption
from .page import PalettePage
from .rest import PaletteRESTApplication, status_ok
from .rest import required_parameters, required_role

NONE = '--None--'

class SupportCaseApplication(PaletteRESTApplication):
    """ Email the POST data to Tableau support. """

    def service_GET(self, req):
        """ Handle GET requests """
        # pylint: disable=unused-argument
        config = [SupportCaseCategoryOption('problem-category'),
                  SupportCaseImpactOption('problem-impact'),
                  SupportCaseLangOption('contact-language'),
                  SupportCaseTzOption('contact-tz')
        ]
        return {'config': [option.default() for option in config]}

    @required_parameters('problem-statement', 'contact-email')
    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        """ Handle POST requests """
        subject = 'Support Case: ' + req.params['problem-statement']
        message = ''

        for key in req.params:
            name = key.replace('-', ' ').title()
            message += name + ':\n'
            message += req.params[key] + '\n'
            message += '\n'

        sender = req.params['contact-email']

        mailer = Mailer(sender)
        mailer.send_msg(req.system[SystemKeys.SUPPORT_CASE_EMAIL],
                        subject, message, bcc=[sender])
        return status_ok()

class SupportCasePage(PalettePage):
    """ The support case page in the user interface. """
    TEMPLATE = 'support-case.mako'
    active = 'support-case'

class SupportCaseCategoryOption(ListOption):
    """ Category options """

    def __init__(self, name):
        options = [
            NONE,
            "I need assistance connecting to data / accessing data",
            "I need assistance with a data extract",
            "I need assistance optimizing the product performance",
            "I need assistance with product licensing/activation",
            "I need assistance to configure the product correctly",
            "I need assistance installing/upgrading the product",
            "I need assistance with user authentication/permissions",
            "I need assistance with filters or actions in a workbook",
            "I need assistance with calculations",
            "I need assistance creating a dashboard/view",
            "I need assistance working with dates and times",
            "I need assistance with formatting and display",
            "I need assistance with maps in a visualization",
            "I need assistance printing or exporting a visualization",
            "I need assistance sharing or publishing a visualization"
        ]
        super(SupportCaseCategoryOption, self).__init__(name, NONE, options)


class SupportCaseImpactOption(ListOption):
    """ Impact options """

    def __init__(self, name):
        options = [
            NONE,
            "How-to/General Information",
            "Standard Support Issue",
            "Major impact on current work/project",
            "System down/Total loss of fuctionality"
        ]
        super(SupportCaseImpactOption, self).__init__(name, NONE, options)


class SupportCaseLangOption(ListOption):
    """ Preferred Language options """

    def __init__(self, name):
        options = [
            "English",
            "French",
            "German",
            "Japanese",
            "Korean",
            "Mandarin",
            "Portuguese",
            "Spanish"
        ]
        super(SupportCaseLangOption, self).__init__(name, "English", options)


DEFAULT_TZ = "North/Central/South America"

class SupportCaseTzOption(ListOption):
    """ Preferred Timezone options """

    def __init__(self, name):
        options = [
            DEFAULT_TZ,
            "Europe/Middle East/Africa"
            "Asia Pacific"
        ]
        super(SupportCaseTzOption, self).__init__(name, DEFAULT_TZ, options)
