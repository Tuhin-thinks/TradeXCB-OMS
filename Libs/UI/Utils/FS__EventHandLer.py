import os.path
import re

import pandas as pd
from PyQt5 import QtCore

from Libs.globals import *

logger = exception_handler.getFutureLogger(__name__)


class FS_LogModifyHandler(QtCore.QObject):
    file_changed = QtCore.pyqtSignal(object)

    def __init__(self, watch_loc_list: typing.List[str]):
        super(FS_LogModifyHandler, self).__init__()

        self.watch_loc_list = watch_loc_list
        self._check_timer = None
        self.last_update_time_dict = {path: os.stat(path).st_mtime_ns for path in self.watch_loc_list}
        self._watcher = QtCore.QFileSystemWatcher()
        self._watcher.addPaths(self.watch_loc_list)  # adding multiple log files paths
        self._watcher.fileChanged.connect(self._on_file_change)

        if os.name == "nt":  # only required for windows
            self._additional_check_timer()

    def _additional_check_timer(self):
        """
        needed because Windows does not recognize file changes when using logging
        :return:
        """
        self._check_timer = QtCore.QTimer()
        self._check_timer.timeout.connect(self.is_updated)
        self._check_timer.start(200)

    def is_updated(self):
        try:
            for path in self.watch_loc_list:
                if os.stat(path).st_mtime_ns != self.last_update_time_dict[path]:
                    self.update_view(path)
        except (FileNotFoundError, FileExistsError):
            pass

    def update_view(self, watch_loc):
        if self.last_update_time_dict[watch_loc] == os.stat(watch_loc).st_mtime_ns:
            return
        try:
            with open(watch_loc, 'r') as reader:
                for line in reversed(list(reader)):
                    if re.search(settings.LOG_MATCHER_REGEX, line):
                        group_dict = re.search(settings.LOG_MATCHER_REGEX, line).groupdict()
                        timestamp = group_dict["timestamp"]
                        log_level = group_dict["log"]
                        message = group_dict["message"]
                        source = group_dict["source"]
                        try:
                            self.file_changed.emit((timestamp, log_level, message, source))
                            self.last_update_time_dict[watch_loc] = os.stat(watch_loc).st_mtime_ns
                            break
                        except RuntimeError:
                            pass
        except (FileNotFoundError, FileExistsError):
            logger.critical(f"{watch_loc} missing replace it for proper functioning.")

    def _on_file_change(self, path: str):
        try:
            self.update_view(path)
        except (FileNotFoundError, FileExistsError):
            pass

    def deleteLater(self) -> None:
        if self._check_timer:
            self._check_timer.stop()
        super(FS_LogModifyHandler, self).deleteLater()


class Position_CSVModifyHandler(QtCore.QObject):
    file_changed = QtCore.pyqtSignal(tuple)

    def __init__(self, watch_loc):
        super(Position_CSVModifyHandler, self).__init__()
        self.watch_loc = watch_loc
        self.last_update_time = None
        self.last_update_line = None
        self._check_timer = None
        self._watcher = QtCore.QFileSystemWatcher()
        self._watcher.addPath(self.watch_loc)
        self._watcher.fileChanged.connect(self._on_file_change)

        # if os.name == "nt":  # only required for windows
        self._additional_check_timer()

    def _additional_check_timer(self):
        """
        needed because Windows does not recognize file changes when using logging
        :return:
        """
        self._check_timer = QtCore.QTimer()
        self._check_timer.timeout.connect(self.is_updated)
        self._check_timer.start(100)

    def is_updated(self):
        try:
            if os.stat(self.watch_loc).st_mtime_ns != self.last_update_time:
                self.update_view()
        except (FileNotFoundError, FileExistsError):
            pass

    @QtCore.pyqtSlot()
    def _on_file_change(self):
        try:
            self.update_view()
        except (FileNotFoundError, FileExistsError):
            pass

    def deleteLater(self) -> None:
        if self._check_timer:
            self._check_timer.stop()
        super(Position_CSVModifyHandler, self).deleteLater()

    def get_headers(self) -> typing.List:
        positions_df = pd.read_csv(self.watch_loc)
        return positions_df.columns.tolist()

    def update_view(self):
        try:
            if self.last_update_time == os.stat(self.watch_loc).st_mtime_ns:
                return
            try:
                positions_df = pd.read_csv(self.watch_loc)
                self.file_changed.emit((positions_df,))
                self.last_update_time = os.stat(self.watch_loc).st_mtime_ns
            except Exception as e:
                pass
        except (FileNotFoundError, FileExistsError):
            pass
