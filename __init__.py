# -*- coding: utf-8 -*-
"""
Entry point for VocabularyBuilder Anki extension.
"""

import os
import sys
from aqt import mw
from sys import stderr

__all__ = []


sys.path.insert(0, os.path.join(mw.pm.addonFolder(), "vocabulary_builder"))
sys.path.insert(0, os.path.join(mw.pm.addonFolder(), "vocabulary_builder",
                                                     "libs"))


if __name__ == "__main__":
    stderr.write(
        "VocbularyBuilder is an add-on for Anki.\n"
        "It is not intended to be run directly.\n"
        "To learn more or download Anki, visit <https://apps.ankiweb.net>.\n"
    )
    exit(1)


# n.b. Import is intentionally placed down here so that Python processes it
# only if the module check above is not tripped.

from . import vocabulary_builder  # noqa, pylint:disable=wrong-import-position

vocabulary_builder.addMenuItem()
