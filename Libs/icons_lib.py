import os

from PyQt5.QtGui import QIcon, QPixmap
from Libs.Utils import settings

BASE = os.path.dirname(__file__)


class Icons:
    icons_dir = os.path.join(BASE, 'UI', 'icons')
    icons = {'user-icon': 'user_icon.png', 'passwd-icon': 'key.png', 'pen-icon': 'pen.png',
             'mail-icon': 'email_icon.png', 'mobile-icon': 'mobile_icon.png', 'delete-icon': 'delete.png',
             'add-symbol-icon': 'add.png', 'close-strategy_name-icon': 'close.png', 'broken-image': "broken.png",
             "export-icon": "export.png", "start-trading-color": "start-icon-color.png",
             "restart-icon-white": 'restart-icon.png',
             "stop-trading-color": "stop-icon-color.png", "current_app_logo-full": settings.CURRENT_APP_LOGO,
             "current_app_logo-image": settings.APP_LOGO_img_only, "start-trading-button": 'start-button.png',
             'stop-trading-button': 'stop-button.png', "app-logo-alpha": "iDelta-icon-alpha.png"}

    def __init__(self):
        pass

    @classmethod
    def get(cls, icons_name):
        if icons_name in cls.icons:
            return QIcon(os.path.join(cls.icons_dir, cls.icons[icons_name]))
        else:
            return QIcon(os.path.join(cls.icons_dir, cls.icons["broken-image"]))

    @classmethod
    def get_pixmap(cls, icons_name):
        if icons_name in cls.icons:
            return QPixmap(os.path.join(cls.icons_dir, cls.icons[icons_name]))
        else:
            return QPixmap(os.path.join(cls.icons_dir, cls.icons["broken-image"]))
