from flask_assets import Environment
from flask_babel import Babel

from .raspiconfig import RaspiConfig
from .settings import Settings
from .usrmgmt import Usrmgmt

assets = Environment()
babel = Babel()
settings = Settings()
raspiconfig = RaspiConfig()
usrmgmt = Usrmgmt()
