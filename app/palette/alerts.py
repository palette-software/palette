""" Alert configuration """
# pylint: enable=relative-import,missing-docstring
import akiri.framework.sqlalchemy as meta

from controller.profile import Role
from controller.system import SystemKeys
from controller.alert_setting import AlertSetting

from .option import TimeOption, PercentOption
from .page import PalettePage
from .rest import required_role, PaletteRESTApplication


class AlertsPage(PalettePage):
    """ The support case page in the user interface. """
    TEMPLATE = 'alerts.mako'
    active = 'alerts'


# Maybe break this into Storage, CPU, Workbook?
class AlertsApplication(PaletteRESTApplication):
    """Handler from 'MONITORING' section."""

    LOW_WATERMARK_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HIGH_WATERMARK_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_LOAD_WARN_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_LOAD_ERROR_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_PERIOD_WARN_RANGE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
    CPU_PERIOD_ERROR_RANGE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
    WORKBOOK_LOAD_WARN_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30,
                                35, 40, 45]
    WORKBOOK_LOAD_ERROR_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30,
                                 35, 40, 45]

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        """
        Serves the GET requests
        :param req:
        :return: the settings for the TOTAL load thresholds
        """
        config = []

        # watermark low
        percent = req.system[SystemKeys.WATERMARK_LOW]
        option = PercentOption(SystemKeys.WATERMARK_LOW, percent,
                               self.LOW_WATERMARK_RANGE)
        config.append(option.default())

        # watermark high
        percent = req.system[SystemKeys.WATERMARK_HIGH]
        option = PercentOption(SystemKeys.WATERMARK_HIGH, percent,
                               self.HIGH_WATERMARK_RANGE)
        config.append(option.default())

        # workbook warn (formerly http load warn)
        seconds = req.system[SystemKeys.HTTP_LOAD_WARN]
        option = TimeOption(SystemKeys.HTTP_LOAD_WARN, seconds,
                            {'seconds': self.WORKBOOK_LOAD_WARN_RANGE})
        config.append(option.default())

        # workbook error (formerly http load error)
        seconds = req.system[SystemKeys.HTTP_LOAD_ERROR]
        option = TimeOption(SystemKeys.HTTP_LOAD_ERROR, seconds,
                            {'seconds': self.WORKBOOK_LOAD_ERROR_RANGE})
        config.append(option.default())

        # cpu load warn
        percent = req.system[SystemKeys.CPU_LOAD_WARN]
        option = PercentOption(SystemKeys.CPU_LOAD_WARN, percent,
                               self.CPU_LOAD_WARN_RANGE)
        config.append(option.default())

        # cpu load error
        percent = req.system[SystemKeys.CPU_LOAD_ERROR]
        option = PercentOption(SystemKeys.CPU_LOAD_ERROR, percent,
                               self.CPU_LOAD_ERROR_RANGE)
        config.append(option.default())

        # cpu period warn
        seconds = req.system[SystemKeys.CPU_PERIOD_WARN]
        option = TimeOption(SystemKeys.CPU_PERIOD_WARN, seconds,
                            {'minutes': self.CPU_PERIOD_WARN_RANGE})
        config.append(option.default())

        # cpu period error
        seconds = req.system[SystemKeys.CPU_PERIOD_ERROR]
        option = TimeOption(SystemKeys.CPU_PERIOD_ERROR, seconds,
                            {'minutes': self.CPU_PERIOD_ERROR_RANGE})
        config.append(option.default())

        return {'config': config}

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        """
        Saves the settings for the TOTAL load thresholds
        :param req:
        :return: success
        """
        # pylint: disable=unused-argument
        req.system[SystemKeys.WATERMARK_LOW] = req.POST['disk-watermark-low']
        req.system[SystemKeys.WATERMARK_HIGH] = req.POST['disk-watermark-high']

        req.system[SystemKeys.CPU_LOAD_WARN] = req.POST['cpu-load-warn']
        req.system[SystemKeys.CPU_LOAD_ERROR] = req.POST['cpu-load-error']

        req.system[SystemKeys.CPU_PERIOD_WARN] = req.POST['cpu-period-warn']
        req.system[SystemKeys.CPU_PERIOD_ERROR] = req.POST['cpu-period-error']

        req.system[SystemKeys.HTTP_LOAD_WARN] = req.POST['http-load-warn']
        req.system[SystemKeys.HTTP_LOAD_ERROR] = req.POST['http-load-error']

        meta.commit()
        return {}


# Maybe break this into Storage, CPU, Workbook?
class CPUAlertsProcessesApplication(PaletteRESTApplication):
    """Handler from 'PROCESS CPU' section."""

    CONFIG_KEY = 'config'

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        """
        Serves the GET requests
        :param req:
        :return: the settings for the process based CPU thresholds
        """
        # pylint: disable=unused-argument

        config = AlertSetting.get_all(AlertSetting.CPU)

        return {self.CONFIG_KEY: config}

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        """
        Saves the settings for the process based CPU thresholds
        :param req:
        :return:
        """
        import json
        body_as_json = json.loads(req.body)
        AlertSetting.update_all(body_as_json[self.CONFIG_KEY], AlertSetting.CPU)
        return {}


# Maybe break this into Storage, CPU, Workbook?
class MemoryAlertsProcessesApplication(PaletteRESTApplication):
    """Handler from 'PROCESS MEMORY' section."""

    CONFIG_KEY = 'config'

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        """
        Serves the GET requests
        :param req:
        :return: the settings for the process based memory thresholds
        """
        # pylint: disable=unused-argument

        config = AlertSetting.get_all(AlertSetting.MEMORY)

        return {self.CONFIG_KEY: config}

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        """
        Saves the settings for the process based memory thresholds
        :param req:
        :return:
        """
        import json
        body_as_json = json.loads(req.body)
        AlertSetting.update_all(body_as_json[self.CONFIG_KEY], AlertSetting.MEMORY)
        return {}
