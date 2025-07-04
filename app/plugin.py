import sys
from typing import TYPE_CHECKING

import anki.collection  # fix anki circular import
import anki.lang

from app.gui_stubs import install_gui_stubs

install_gui_stubs()
anki.lang.set_lang("en_US")  # TODO: Implement language selection

sys.path.append("libs/ankiconnect")
if TYPE_CHECKING:
    from libs.ankiconnect.plugin import *
else:
    from plugin import *  # to avoid code execution on import
sys.path.remove("libs/ankiconnect")
