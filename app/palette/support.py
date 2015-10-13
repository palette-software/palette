""" Support case application support. """
#pylint: enable=relative-import,missing-docstring
from copy import deepcopy
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import akiri.framework.sqlalchemy as meta

from controller.mailer import Mailer
from controller.profile import Role
from controller.system import SystemKeys
from controller.util import DATEFMT

from .option import ListOption
from .page import PalettePage
from .rest import PaletteRESTApplication, status_ok
from .rest import required_parameters, required_role

NONE = '--None--'

FIELDS = ('problem:statement',
          'problem:category',
          'problem:impact',
          'problem:description',
          'contact:name',
          'contact:phone',
          'contact:email',
          'contact:company',
          'contact:language',
          'contact:timezone',
          'environment:product',
          'environment:language',
          'environment:version',
          'environment:build-number',
          'environment:operating-system',
          'environment:data-source')

def _subject(text):
    """ Build the mail subject: first 5 words of the problem + the date. """
    tokens = [token.strip() for token in text.split()]
    if len(tokens) > 5:
        tokens = tokens[0:5]
    timestamp = datetime.now().strftime(DATEFMT)
    return ' '.join(tokens) + ' ' + timestamp

def _text(key, value):
    """ format the key/value as plaintext """
    text = key.upper() + ':\n'
    text += value + '\n'
    text += '\n'
    return text

def _html(key, value):
    """ format the key/value as html """
    html = '<div style="margin-bottom:3em">'
    html += '<h3>' + key + '</h3>'
    html += '<p>' + value + '</p>'
    html += '</div>'
    return html

def _display_name(name):
    """ translate the name to a display-able format. """
    name = name.replace('-', ' ').title()
    return name.replace(':', ' ')

class SupportCaseApplication(PaletteRESTApplication):
    """ Email the POST data to Tableau support. """

    def service_GET(self, req):
        """ Handle GET requests """
        # pylint: disable=unused-argument
        config = [SupportCaseCategoryOption('problem:category'),
                  SupportCaseImpactOption('problem:impact'),
                  SupportCaseLangOption('contact:language'),
                  SupportCaseTzOption('contact:timezone'),
                  SupportCaseProductOption('environment:product'),
                  SupportCaseLangOption('environment:language'),
                  SupportCaseVersionOption('environment:version'),
                  SupportCaseOSOption('environment:operating-system'),
                  SupportCaseDataSourceOption('environment:data-source')
        ]
        data = {'config': [option.default() for option in config]}

        profile = req.environ['REMOTE_USER']
        if profile.userid > 0:
            if profile.friendly_name:
                data['contact:name'] = profile.friendly_name
            if profile.email:
                data['contact:email'] = profile.email

        company_name = req.system[SystemKeys.COMPANY_NAME]
        if company_name:
            data['contact:company'] = company_name
        meta.commit()

        return data

    @required_parameters('problem:statement', 'contact:email')
    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        """ Handle POST requests """
        subject = _subject(req.params['problem:statement'])
        text = ''
        html = '<html><head></head><body>'

        params = deepcopy(req.POST)

        # handle the known fields
        for key in FIELDS:
            if not key in params:
                continue
            name = _display_name(key)
            value = params[key]
            if not value:
                value = NONE
            # text version
            text += _text(name, value)
            # html version
            html += _html(name, value)
            del params[key]

        # add anything else that was sent
        for key in params:
            name = _display_name(key)
            value = params[key]
            if not value:
                value = NONE
            # text version
            text += _text(name, value)
            # html version
            html += _html(name, value)

        html += '</body>'

        # see the last example at:
        # https://docs.python.org/2/library/email-examples.html
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        sender = req.params['contact:email']
        phone = req.params.get('contact:phone')

        if phone:
            profile = req.environ['REMOTE_USER']
            if profile.userid > 0:
                profile.phone = phone

        company_name = req.params.get('contact:company')
        if company_name:
            req.system[SystemKeys.COMPANY_NAME] = company_name
        else:
            del req.system[SystemKeys.COMPANY_NAME]
        meta.commit()

        mailer = Mailer(sender)
        mailer.send_msg(req.system[SystemKeys.SUPPORT_CASE_EMAIL],
                        subject, msg, bcc=[sender])
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


class SupportCaseProductOption(ListOption):
    """ The Product options """

    def __init__(self, name):
        options = [
            NONE,
            "Tableau Server",
            "Tableau Desktop + Server",
            "Tableau Reader",
            "Tableau Public",
            "Tableau App (Mobile)",
            "Tableau Online"
        ]
        super(SupportCaseProductOption, self).__init__(name, NONE, options)

class SupportCaseVersionOption(ListOption):
    """ All possible Tableau version options """

    def __init__(self, name):
        options = [
            NONE,
            "9.2", "9.1",
            "9.0.6", "9.0.5", "9.0.4", "9.0.3", "9.0.2", "9.0.1", "9.0.0",
            "8.3.10", "8.3.9", "8.3.8", "8.3.7", "8.3.6", "8.3.5",
            "8.3.4", "8.3.3", "8.3.2", "8.3.1", "8.3.0",
            "8.2.15", "8.2.14", "8.2.13", "8.2.12", "8.2.11", "8.2.10",
            "8.2.9", "8.2.8", "8.2.7", "8.2.6", "8.2.5",
            "other"
        ]
        super(SupportCaseVersionOption, self).__init__(name, NONE, options)


class SupportCaseOSOption(ListOption):
    """ All possible Operating Systems """

    def __init__(self, name):
        options = [
            NONE,
            "Windows 10",
            "Windows 8.1",
            "Windows 8",
            "Windows 7",
            "Windows Vista",
            "Windows XP",
            "Mac OS",
            "Windows Server 2012",
            "Windows Server 2008",
            "Windows Server 2003",
            "iOS",
            "Android"
        ]
        super(SupportCaseOSOption, self).__init__(name, NONE, options)


class SupportCaseDataSourceOption(ListOption):
    """ All possible data source options """

    def __init__(self, name):
        options = [
            NONE,
            "Amazon Aurora", "Amazon Elastic MapReduce",
            "Amazon Redshift", "Aster Data nCluster",
            "Birst", "Cache",
            "Cloudera Hadoop Hive", "DataStax Enterprise",
            "DB2", "Essbase", "EXASolution", "Excel", "Firebird",
            "Google Analytics", "Google BigQuery", "Google Cloud SQL",
            "Greenplum", "Hortonworks Hadoop Hive", "IBM BigInsights",
            "IBM OLAP", "MapR Hadoop Hive", "MarkLogic", "Microsoft Azure SQL",
            "Microsoft Azure Marketplace DataMarket",
            "MSAS", "MS SQL Server", "MySQL", "Netezza",
            "Odata", "ODBC", "Oracle",
            "ParAccel", "Postgres", "Powerpivot", "Progress OpenEdge",
            "R File", "Salesforce.com", "SAP HANA",
            "SAP NetWeaver Business Warehouse",
            "SAS file", "Spark SQL", "Splunk", "SPSS file",
            "Sybase ASE", "Sybase IQ", "Tableau Data Engine",
            "Teradata", "Text Files",
            "Vectorwise", "Vertica"
        ]
        super(SupportCaseDataSourceOption, self).__init__(name, NONE, options)
