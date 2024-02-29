from flask_assets import Environment
from flask_babel import Babel

from .raspiconfig import RaspiConfig

assets = Environment()
babel = Babel()
raspiconfig = RaspiConfig()
