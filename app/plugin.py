import sys
from typing import TYPE_CHECKING

sys.path.append('libs/ankiconnect')
if TYPE_CHECKING:
    from libs.ankiconnect.plugin import *
else:
    from plugin import * # to avoid code execution on import
sys.path.remove('libs/ankiconnect')