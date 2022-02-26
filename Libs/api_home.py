import threading
import webbrowser
import json
import os.path

import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets

from Libs import api_edit_dialog, icons_lib
from Libs.TimeBasedStrategy.idelta_algo_executor import AlgoExecutor
from Libs.Concurrency import UI__Runnable, CSV_Loader
from Libs.Files import handle__SaveOpen, TradingSymbolMapping as SymbolMapping
from Libs.Storage import Cloud, manage_local
from Libs.UI import Interact, Theme, home
from Libs.UI.CustomWidgets import (Image_View_Label, LogTable, PositionsTable, Strategy,
                                   TradingSymbolTable, NotificationWidget)
from Libs.UI.Utils import widget_handling
from Libs.UI.custom_style_sheet import CustomStyleSheet
from Libs.Utils import calculations
from Libs.TimeBasedStrategy import config
from Libs.globals import *

BASE_DIR = os.path.dirname(__file__)
ICONS_DIR = os.path.join(BASE_DIR, 'UI', 'icons')

logger = exception_handler.getFutureLogger(__name__)


class ApiHome(QtWidgets.QMainWindow):
    opened = QtCore.pyqtSignal()
    window_closed = QtCore.pyqtSignal()
    add_notification_widget_signal = QtCore.pyqtSignal(object)

    def __init__(self, geometry: typing.Union[QtCore.QRect, None] = None):
        super(ApiHome, self).__init__()
        self._notif_timer = None
        self.notifications_downloading = False
        self.strategy_algorithm_object = None
        self.oi_data_refreshing = False
        self.backtesting_algorithm_object = None
        self.api_inp_edit_dialog = None
        self.style_refresh_timer = None
        self.strategy_algo_runner_thread = None
        self.opt_update_timer = None
        self.positionView = None
        self.strategy_tables = []
        self.opt_chain_frames = []
        self.tableView_logs: 'LogTable.LogView' = None
        self.pause_stylesheet_timer = False
        self.ui = home.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.frame_trade_buttons.sizePolicy().setRetainSizeWhenHidden(True)

        # -------------- some explicit value settings -----------------
        self.ui.pushButton_recal_oi_timer.setText("Refresh")
        self.setWindowTitle(f"{settings.APP_NAME} {settings.App_VERSION} {settings.EXTENSION}")
        self.ui.label_app_logo.setPixmap(icons_lib.Icons.get_pixmap("app-logo-alpha"))  # top logo
        self.ui.label_app_logo.setMaximumSize(100, 107)
        self.ui.label_app_logo.setMinimumSize(90, 97)
        self.ui.pushButton_recal_oi_timer.setIcon(icons_lib.Icons.get("restart-icon-white"))
        self.ui.pushButton_recal_oi_timer.setIconSize(QtCore.QSize(24, 24))
        self.ui.pushButton_start_trading.setIcon(QtGui.QIcon(icons_lib.Icons().get("start-trading-button")))
        self.ui.pushButton_start_trading.setIconSize(QtCore.QSize(12, 12))
        self.ui.pushButton_stop_trading.setIcon(QtGui.QIcon(icons_lib.Icons().get("stop-trading-button")))
        self.ui.pushButton_stop_trading.setIconSize(QtCore.QSize(12, 12))

        self.vertical_layout_notification = QtWidgets.QVBoxLayout()
        self.ui.scrollAreaWidgetContents_notif.setLayout(self.vertical_layout_notification)

        self.ui.tabWidget.setMinimumHeight(settings.MIN_HEIGHT)

        exception_handler.deleteLogs()

        self.thread_pool = QtCore.QThreadPool()

        self.themes = Theme.get_available_themes()  # collect all themes available
        self.palette_sensitive_widgets = []

        if geometry:  # tries to reposition according to the original position of the login window
            self.setGeometry(geometry)

        self.custom_palette_now = None
        self.label_strategies_image = Image_View_Label.ImageViewer(None)
        self.ui.gridLayout_strategies_image.addWidget(self.label_strategies_image, 1, 0, 1, 1, QtCore.Qt.AlignTop)
        self.ui.frame_strategy_picture.setMinimumHeight(settings.MIN_HEIGHT)
        self.ui.frame_strategy_picture.setStyleSheet("""background-color: #D9D9D9;""")  # to fit the strategy background color
        self.custom_style_sheet = CustomStyleSheet(self.palette())

        # ---------- show option details analysis page on window open -------------
        self.ui.tabWidget.currentChanged.connect(self.tab_index_changed)
        self.ui.tabWidget.setCurrentIndex(0)
        self.trading_sym_scroll_layout = QtWidgets.QVBoxLayout(self.ui.scrollAreaWidgetContents_trading_symb)
        self.ui.scrollArea_trading_symb.verticalScrollBar().rangeChanged.connect(self.scrollBottom)

        # ------------ menu actions --------------
        self.repair_menu = QtWidgets.QMenu("Repair")
        self.repair_menu.addAction("Clean cached files", self.repair_cached_files)
        self.ui.menubar.addAction(self.repair_menu.menuAction())

        # ------------ add available themes -------------
        self.ui.menuChoose_Theme.deleteLater()
        self.ui.menuSettings.deleteLater()
        # for theme_name, theme_path in self.themes.items():
        #     action = QtWidgets.QAction(theme_name, self)
        #     action.triggered.connect(partial(self.change_theme, theme_name))
        #     self.ui.menuChoose_Theme.addAction(action)

        self.ui.actionEdit_api_details.triggered.connect(self.open_api_edit_window)

        # ---------- add strategies options [combobox] ----------------
        self.ui.comboBox_strategy_select.blockSignals(True)
        self.ui.comboBox_strategy_select.addItems(app_data.STRATEGIES)
        self.ui.comboBox_strategy_select.blockSignals(False)
        self.ui.comboBox_trading_symb_select_strategy.addItems(app_data.STRATEGIES)
        self.ui.comboBox_strategy_select.currentIndexChanged[str].connect(self.strategies__strategy_option_change)
        self.ui.comboBox_select_log.addItems(app_data.LOG_OPTIONS)
        # ------------ refresh the image pixmap to the label ---------------
        QtCore.QTimer.singleShot(500, lambda: self.strategies__strategy_option_change(""))
        self.ui.comboBox_select_log.currentIndexChanged[int].connect(self.change_log_filter)
        self.ui.comboBox_trading_mode.addItems(("Real Live Trading", "Real Paper Trading"))

        widget_handling.add_sensitive_widgets_to_palette(self)
        # ------------ get user's saved preference for theme name (DEFAULT THEME IS DARK) --------------
        self.current_theme = theme_name = manage_local.get_user_preference_table("THEME_NAME") or "Dark"
        self.change_theme(theme_name, show_update_message=False)
        self.ui.comboBox_strategy_select.setPalette(self.custom_palette_now)
        # self.start_style_sheet_refresh_timer()  # start stylesheet refresh timer (every 5 sec update)
        with open(os.path.join(settings.DATA_FILES_DIR, "dark_style"), 'r') as reader:
            stylesheet = reader.read()
        QtWidgets.QApplication.instance().setStyleSheet(stylesheet)
        # self.setStyleSheet(stylesheet)

        # self.setStyleSheet(self.custom_style_sheet.home_stylesheet("dark"))
        # assign custom palette to required widgets
        if self.custom_palette_now is not None:
            _ = [x.setPalette(self.custom_palette_now) for x in self.palette_sensitive_widgets]

        # ------------ add oi table views --------------
        self.add_log_view()
        self.add_positions_view()
        self.add_ExcelViews()
        self.refresh_stylesheet()
        self.check_data_files()

        # --------------- [Signals] button clicks -----------------------------
        self.ui.pushButton_clear_logs.clicked.connect(self.clear_future_logs)
        self.ui.pushButton_add_strategy.clicked.connect(self.add_strategy)
        self.ui.pushButton_all_logs.clicked.connect(partial(self.change_log_filter, 0))
        self.ui.pushButton_export_positions_pos.clicked.connect(self.save_position_table)
        self.ui.pushButton_export_logs.clicked.connect(self.save_error_logs)
        self.ui.pushButton_recal_oi_timer.clicked.connect(self.restart_oi_thread)

        # ================= Data-Export Functions ====================
        self.ui.pushButton_save_all_strategy.clicked.connect(self.save_strategies)

        # ===================== initialise strategy algorithm object =================
        # self.strategy_algorithm_object = MainManager(None)  # add trading symbol algo here
        # button clicks for handling strategy algorithm
        self.ui.pushButton_start_trading.clicked.connect(self.start_trading)
        self.ui.pushButton_stop_trading.clicked.connect(self.stop_trading)

        # ----------------- start fetching OI data from Cloud ------------------
        self.initial_launch = True  # flag variable to determine whether to refresh data instantly
        self.start_oi_thread()
        self.start_ts_data_loader_thread()
        self.start_notif_thread()

    # -----------------------> END OF __init__ <----------------------------
    def open_api_edit_window(self):
        """opens API input details dialog"""
        self.api_inp_edit_dialog = api_edit_dialog.APIDialog(self.custom_style_sheet, self.current_theme,
                                                             self.custom_palette_now, self)
        self.api_inp_edit_dialog.submit_clicked.connect(self.verify_api_login)
        self.api_inp_edit_dialog.show()

    # ======================= EXPORT SLOTS =================================
    @QtCore.pyqtSlot()
    def save_strategies(self):
        handle__SaveOpen.export_as_excel(self)

    # ===================== EXPORT SLOTS END =================================
    @staticmethod
    def check_data_files():
        threading.Thread(target=config.download_instruments_file).start()
    
    def repair_cached_files(self):
        items = (settings.DATA_FILES.get("INSTRUMENTS_CSV"), settings.DATA_FILES.get('get_user_session_pickle'))
        size = 0
        for item_path in items:
            if os.path.exists(item_path):
                size += round(os.path.getsize(item_path) / 1000 / 1024, 2)
                os.remove(item_path)
        self.check_data_files()
        Interact.show_message(self, "Repair Complete",
                              f"Cached files have been removed. Cleared <b>{size}MB</b>",
                              "info")

    @QtCore.pyqtSlot(str)
    def change_theme(self, theme_name: str, show_update_message=False):
        try:
            widget_handling.change_theme(self, theme_name)
            self.setPalette(self.custom_palette_now)
            self.ui.tabWidget.setPalette(self.custom_palette_now)
            if theme_name:
                self.current_theme = theme_name
                manage_local.set_user_preference_table({"THEME_NAME": theme_name})
                if show_update_message:
                    self.ui.statusbar.showMessage(
                        "Theme preference saved, complete changed visible after next restart.",
                        2000)
        # if last user preference theme is unavailable, then use the first one among whatever is available
        except Exception:
            if self.themes:
                self.current_theme = list(self.themes.keys())[0]
                manage_local.set_user_preference_table({"THEME_NAME": theme_name})
                self.change_theme(self.current_theme, show_update_message=False)

    @QtCore.pyqtSlot(int)
    def change_log_filter(self, filter_code):
        if filter_code == 0:
            self.ui.comboBox_select_log.setCurrentIndex(0)
            self.tableView_logs.filter_role_changed.emit("all")
        elif filter_code == 1:
            self.tableView_logs.filter_role_changed.emit("future")

    def add_log_view(self):
        self.tableView_logs = LogTable.LogView(parent=self.ui.frame_bottom1, global_parent=self)
        self.ui.frame_bottom1.layout().addWidget(self.tableView_logs)
        # self.tableView_logs.setStyleSheet(self.custom_style_sheet.tableview("dark"))
        self.palette_sensitive_widgets.append(self.tableView_logs)
        self.update()

    def add_positions_view(self):
        self.ui.frame_positions_top.setMinimumHeight(45 if os.name == 'posix' else 50)
        self.positionView = PositionsTable.PositionsView(self.ui.frame_positions_table, global_parent=self)
        self.ui.gridLayout_positions_table.addWidget(self.positionView, 0, 0, 1, 1)
        self.positionView.setStyleSheet(self.custom_style_sheet.tableview("dark"))
        self.palette_sensitive_widgets.append(self.positionView)
        self.positionView.update()

    def add_ExcelViews(self):
        """
        adding 6 [Option Chain analysis] tableViews
        :return:
        """
        self.opt_chain_frames = []  # store all frames containing the Excel views
        widget_handling.add_option_analysis_views(self)

    def clear_future_logs(self):
        """Clears log for UI/view only"""
        self.tableView_logs.clear()

    def oi_runnable_complete(self):
        self.oi_data_refreshing = False

    def stop_trading(self):
        try:
            self.strategy_algorithm_object.signal_stop_strategy_timer.emit()
        except Exception:
            pass
        finally:
            self.stop_trading_thread()
            logger.info("Strategy algorithm Stopped successfully")
        self.ui.pushButton_start_trading.setEnabled(True)
        self.ui.pushButton_stop_trading.setDisabled(True)

    def stop_trading_thread(self):
        try:
            self.strategy_algo_runner_thread.wait(10)
            self.strategy_algo_runner_thread.quit()
        except Exception as e:
            pass
        try:
            self.strategy_algorithm_object.disconnect()
        except Exception:
            pass

    def error_stop_trade_algorithm(self, message: str):  # on strategy algorithm stop
        Interact.show_message(self, "Algorithm stopped", message, "warning")
        self.stop_trading()
        self.ui.pushButton_start_trading.setEnabled(True)
        self.ui.pushButton_stop_trading.setDisabled(True)
        logger.info("Strategy algorithm Stopped successfully")

    def error_stop_backtest_algo(self, message: str):  # in backtesting algorithm stop
        Interact.show_message(self, "Algorithm stopped", message, "warning")
        self.stop_trading_thread()
        self.stop_trading()

    def start_trading(self):
        """
        ------------ start strategy trading algorithm ---------------
        :return:
        """
        trading_mode_index = self.ui.comboBox_trading_mode.currentIndex()
        if trading_mode_index == 0:
            Interact.show_message(self, "Trading Mode Not Selected",
                                  "Please select a Trading Mode to proceed", "warning")
            return
        # ------------- set button accessibility ---------------
        self.ui.pushButton_start_trading.setDisabled(True)
        self.ui.pushButton_stop_trading.setDisabled(False)

        # ------------------ create thread and init object ------------
        trading_mode_text = self.ui.comboBox_trading_mode.currentText()
        trading_mode_index = settings.TRADING_NAME_INDEX_MAPPING[trading_mode_text]
        if trading_mode_index in (0, 1):  # Need to run MainManager script
            # passing parent to overcome 'QThread: Destroyed while thread is still running'
            self.strategy_algo_runner_thread = QtCore.QThread()
            self.strategy_algorithm_object = AlgoExecutor(paper_trade=trading_mode_index)
            self.strategy_algorithm_object.error_stop.connect(self.error_stop_trade_algorithm)
            self.strategy_algorithm_object.moveToThread(self.strategy_algo_runner_thread)
            self.strategy_algo_runner_thread.started.connect(self.strategy_algorithm_object.start_strategy_timer)
            self.strategy_algo_runner_thread.start()
        else:  # need to run backtesting script
            pass

    def refresh_stylesheet(self):
        if not self.pause_stylesheet_timer:
            widget_handling.change_theme(self, self.current_theme)

    def start_notif_thread(self):
        code_, dict_ = manage_local.get_to_fill_data()
        email_id = dict_.get("email_id")
        password_dec = dict_.get("password_dec")
        user_name = dict_.get("user_name")
        if code_ == 1 and email_id:
            # self.check_login(user_name, password_dec, email_id)  # another level of authentication can be added here
            downloader = Cloud.DownloadTableData(user_name, email_id, password_dec)
            self.download_notifications_timer(downloader)

    def download_notifications_timer(self, downloader: 'Cloud.DownloadTableData'):
        self.add_notification_widget_signal.connect(self.add_notification_widget)
        self._notif_timer = QtCore.QTimer()
        self._notif_timer.timeout.connect(partial(self.restart_notification_download, downloader))
        self._notif_timer.start(1 * 60 * 1000)  # update notifications after 1 minute

        self.restart_notification_download(downloader)

    def restart_notification_download(self, downloader):
        if not self.notifications_downloading:
            self.notifications_downloading = True
            widgets_count = self.ui.scrollAreaWidgetContents_notif.layout().count()
            for index in range(widgets_count-1, -1, -1):
                item = self.ui.scrollAreaWidgetContents_notif.layout().takeAt(index)
                widget = item.widget()
                self.ui.scrollAreaWidgetContents_notif.layout().removeWidget(widget)
                widget.deleteLater()
            notif_updater_thread = threading.Thread(target=self.fetch_notifications, args=(downloader,))
            notif_updater_thread.start()

    def fetch_notifications(self, downloader: 'Cloud.DownloadTableData'):
        # self.ui.statusbar.showMessage("Updating notifications now", 2 * 1000)
        code, notifications = downloader.get_notifications(1)
        if code == 0 and isinstance(notifications, list):
            for notification in notifications:
                self.add_notification_widget_signal.emit(notification)
        self.notifications_downloading = False

    def add_notification_widget(self, notification_data: typing.Tuple):
        viewport_width = self.ui.scrollArea_notif.viewport().size().width()
        _notification_widget = NotificationWidget.NotificationWidget(self.ui.scrollAreaWidgetContents_notif, viewport_width)
        _notification_widget.set_notif_time(notification_data[0])
        _notification_widget.set_notif_message(notification_data[1])
        self.ui.scrollAreaWidgetContents_notif.layout().addWidget(_notification_widget)
        _max_pos = self.ui.scrollArea_notif.verticalScrollBar().maximum()
        self.ui.scrollArea_notif.verticalScrollBar().setValue(_max_pos)
        self.update()

    def start_oi_thread(self):
        """Start option chain analysis at startup of program [api_home window]"""
        code_, dict_ = manage_local.get_to_fill_data()
        email_id = dict_.get("email_id")
        password_dec = dict_.get("password_dec")
        user_name = dict_.get("user_name")
        if code_ == 1 and email_id:
            # self.check_login(user_name, password_dec, email_id)  # another level of authentication can be added here
            downloader = Cloud.DownloadTableData(user_name, email_id, password_dec)
            self.restart_download_timer(downloader)

    def restart_oi_thread(self):
        """gets called when user changes and activates the new time frame"""
        try:
            self.opt_update_timer.stop()
            self.start_oi_thread()  # resets the timer and start the timer with new time frame
        except Exception as e:
            logger.warning(f'Error occurred while restarting OI update timer, err: {e.__str__()}', exc_info=True)
            self.ui.statusbar.showMessage("Please try to recalibrate again.", 2 * 1000)

    def restart_download_timer(self, downloader):
        time_frame = (5, 10, 15)[self.ui.comboBox_time_frame.currentIndex()]
        logger.info(f"Recalibrating update timer to {time_frame} minutes.")
        self.opt_update_timer = QtCore.QTimer()
        self.opt_update_timer.timeout.connect(partial(self.timeout_, time_frame, downloader))
        self.timeout_(time_frame, downloader)  # fetch data immediately for first time
        self.opt_update_timer.start(1 * 1000)
        logger.info(f"Update timer recalibrated to {time_frame} minutes.")

    def timeout_(self, timeframe, downloader):
        is_required, remaining_time = calculations.is_refresh_required(timeframe)
        if not self.oi_data_refreshing and is_required or self.initial_launch:
            self.oi_data_refreshing = True  # lock further refresh
            self.initial_launch = False
            table_updater_runnable = UI__Runnable.OptDataUpdateWorker(self.data_fetcher, timeframe, downloader)
            table_updater_runnable.signals.stopped.connect(self.oi_runnable_complete)
            self.thread_pool.start(table_updater_runnable)
            logger.info("Updating OI data")
            self.ui.statusbar.showMessage("Updating OI data now", 5 * 1000)
        else:
            if remaining_time.isdigit():
                self.ui.statusbar.showMessage(f"updating data in ({remaining_time}) seconds...", 2 * 1000)
            else:
                self.ui.statusbar.showMessage(remaining_time)

    def data_fetcher(self, time_frame, downloader):
        code_, json_df_list = downloader.download_data(time_frame)  # return code 0 means success (-1 failure)
        if code_ == 0 and type(json_df_list) == dict:
            # this loop will update data to all views
            for index, frame_tuple in enumerate(self.opt_chain_frames, 0):
                try:
                    excel_view_frame, frame_name = frame_tuple
                    if json_df_list.get(frame_name):
                        json_data = json_df_list[frame_name]
                        df = pd.read_json(json_data)
                        if frame_name == 'deltaReport':
                            df['DELTA_CROSSOVER'] = df[['DELTA_CE', 'DELTA_PE']].apply(
                                calculations.delta_crossover_check, axis=1)
                        elif frame_name == 'premiumReport':
                            df['Vwap_Crossover_CE'], df['Vwap_Crossover_PE'] = zip(*df[
                                ['Price_CE', 'Price_PE', 'Vwap_CE', 'Vwap_PE']].apply(calculations.vwap_crossover_check,
                                                                                      axis=1))
                        excel_view_frame.update_model_data(df)
                    else:
                        if frame_name in ("crossOvers", "marketProfile"):
                            json_data = json_df_list.get("optionDetailAnalysis")
                            if json_data:
                                df = pd.read_json(json_data)
                                # give the mentioned complete data, they filter out what only required
                                excel_view_frame.update_model_data(df)
                            else:
                                logger.warning(f"Table data not updated for : {frame_name}")
                except KeyError as e:
                    logger.warning(f"Key not matching for: {index}: {e.__str__()}")

    @staticmethod
    def verify_api_login(api_det_dict: dict):
        """redict user to web-browser to press authorization button"""
        link_template = "https://kite.zerodha.com/connect/login?v=3&api_key={api_key}"
        link_template = link_template.format(api_key=api_det_dict.get("API Key"))
        webbrowser.open_new_tab(link_template)

    @QtCore.pyqtSlot(int)
    def tab_index_changed(self, index: int):
        """Gets called when current tab index changes"""
        if index == 0:  # index 0 is option detail analysis
            self.hide_trade_frame()
        else:
            self.hide_trade_frame(show_=True)
        if index not in (0, 2):
            self.pause_stylesheet_timer = False
        else:
            self.pause_stylesheet_timer = True

    def hide_trade_frame(self, show_=False):
        """Hide frame containing following buttons:
            1. verify API Login
            2-3. Start/Stop trading
            4. Trading Mode
        """
        if show_:
            self.ui.frame_trade_buttons.setHidden(False)
        else:
            self.ui.frame_trade_buttons.setHidden(True)

    @QtCore.pyqtSlot(tuple)
    def accept_export_instruments_data(self, *args):
        ce_instrument, pe_instrument, strategy_name, symbol_name = args[0]
        required_table = None
        table_found = False
        with open(settings.DEFAULT_DATA_FILE, 'r') as reader:
            default_dict = json.load(reader)
            default_dict['CE_Instrument']['default_value'] = ce_instrument
            default_dict['PE_Instrument']['default_value'] = pe_instrument
            default_dict['Symbol Name']['default_value'] = symbol_name
            default_dict['Entry_Time']['default_value'] = calculations.get_default_entry_time()
            temp_dict = {}
            for key, value in default_dict.items():
                temp_dict[key] = value['default_value']
            df_ = pd.DataFrame(temp_dict, index=range(0, 1))

        for strategy_table in self.strategy_tables:
            if strategy_table.strategy == strategy_name:
                required_table = strategy_table
                strategy_table.load_saved_values(df_.values.tolist())
                table_found = True
                break

        if not table_found:  # if table not already created, create a new table and add instruments to it
            item_count = self.ui.comboBox_trading_symb_select_strategy.count()
            choice_box = self.ui.comboBox_trading_symb_select_strategy
            strategy_choice_index = [choice_box.itemText(_index) for _index in range(item_count)].index(strategy_name)
            self._add_strategy(strategy_name, strategy_choice_index)
            self.accept_export_instruments_data(*args)

    @QtCore.pyqtSlot()
    def add_strategy(self):
        """adds a new strategy_name table with default columns (as preset)"""
        current_strategy_text = self.ui.comboBox_trading_symb_select_strategy.currentText()  # current text|name of the strategy_name
        current_index = self.ui.comboBox_trading_symb_select_strategy.currentIndex()  # get currently selected strategy_name index
        if current_index == 0:
            message = "Please select a <b>Strategy Name</b> before adding"
            if self.ui.comboBox_trading_symb_select_strategy.count() == 1:
                message = "All strategies already added. No more strategy to add."
            Interact.show_message(self, "Cannot add Strategy", message, "warning")
            return
        self._add_strategy(current_strategy_text, current_index, add_default_rows=True)  # manual add of strategy

    def _add_strategy(self, strategy_text: str, strategy_index: int, add_default_rows=False):
        strategy_table = TradingSymbolTable.StrategyView(strategy_text, global_parent=self)
        strategy_frame = Strategy.strategy_frame(strategy_table, self, to_add_default_rows=add_default_rows)
        strategy_frame.delete_strategy.connect(partial(self.delete_strategy, strategy_frame, strategy_text))
        self.trading_sym_scroll_layout.addWidget(strategy_frame)

        if strategy_text.lower() != 'pyramiding strategy':  # don't remove option if it's a pyramiding strategy
            self.ui.comboBox_trading_symb_select_strategy.removeItem(strategy_index)  # cannot add duplicate strategy_name
            self.ui.comboBox_trading_symb_select_strategy.setCurrentIndex(0)  # reset to select strategy_name

        self.strategy_tables.append(strategy_table)  # add strategy tables to a list, for future reference
        self.palette_sensitive_widgets.extend([strategy_frame, strategy_table])

    def start_ts_data_loader_thread(self):
        self.ts_data_loader_thread = QtCore.QThread()
        self.loader_object = CSV_Loader.StrategySavedLoader()
        self.loader_object.strategies_loaded.connect(self.create_strategy_tables)
        self.loader_object.moveToThread(self.ts_data_loader_thread)
        self.ts_data_loader_thread.started.connect(self.loader_object.load_workbook_data)
        self.ts_data_loader_thread.start()

    @QtCore.pyqtSlot(dict)
    def create_strategy_tables(self, loaded_strategies: dict):
        """
        1. Load saved data
        2. iterate on strategies that are having saved data
        3. create tables for those strategies and delete those index from choice-box
        :return:
        """
        item_count = self.ui.comboBox_trading_symb_select_strategy.count()
        choice_box = self.ui.comboBox_trading_symb_select_strategy
        all_cols = SymbolMapping.StrategiesColumn.all_columns
        for strategy_text, table_rows in loaded_strategies.items():
            strategy_choice_index = [choice_box.itemText(_index) for _index in range(item_count)].index(strategy_text)
            self._add_strategy(strategy_text, strategy_choice_index)
            st_cols = SymbolMapping.StrategiesColumn.strategy_dict[strategy_text]
            df_ = pd.DataFrame(table_rows, columns=all_cols)
            self.strategy_tables[-1].load_saved_values(df_[st_cols].values.tolist())

    @QtCore.pyqtSlot()
    def delete_strategy(self, widget: QtWidgets.QWidget, strategy_name: str):
        widget.deleteLater()  # schedule widget for deletion
        current_options = {"Select Strategy", strategy_name}
        for item_index in range(self.ui.comboBox_trading_symb_select_strategy.count()):
            item_text = self.ui.comboBox_trading_symb_select_strategy.itemText(item_index)
            current_options.add(item_text)
        _ = [self.ui.comboBox_trading_symb_select_strategy.removeItem(0)
             for _ in
             range(self.ui.comboBox_trading_symb_select_strategy.count())]  # remove all items from strategy choices
        self.ui.comboBox_trading_symb_select_strategy.addItems(
            [strategy for strategy in ["Select Strategy"] + app_data.STRATEGIES if strategy in current_options]
        )  # add new items (refill delete strategy in choices)
        self.strategy_tables.remove(widget.strategy_table)  # delete the widget object from list

    @QtCore.pyqtSlot(int, int)
    def scrollBottom(self, min_: int, max_: int):
        """scroll to bottom of scroll area, when new strategy_name table added"""
        self.ui.scrollArea_trading_symb.verticalScrollBar().setValue(max_)

    @QtCore.pyqtSlot(str)
    def strategies__strategy_option_change(self, curr_text: str):
        """change strategy_name tab label's pixmap"""
        if curr_text == '':  # curr_text sent as '' to render initial pixmap
            _default_strategy_name = app_data.STRATEGIES[0]
            curr_text = _default_strategy_name
        _img_path = os.path.join(ICONS_DIR, 'strategies', "iDelta+Strategies",
                                 f"{app_data.strategies_name_to_img_mapper.get(curr_text)}.PNG")
        if not os.path.exists(_img_path):
            return
        pixmap = QtGui.QPixmap(_img_path)
        self.label_strategies_image.update_pixmap(pixmap)
        self.update()

    @QtCore.pyqtSlot()
    def save_position_table(self):
        try:
            path = handle__SaveOpen.save_file(self, "Save Positions", '', "CSV (*.csv)")
            self.positionView.save_data(path)  # path validity checking done inside this function
        except Exception as e:
            logger.warning(f"Error saving file: {e.__str__()}")

    @QtCore.pyqtSlot()
    def save_error_logs(self):
        try:
            path = handle__SaveOpen.save_file(self, "Save Program Logs", '', "CSV (*.csv)")
            self.tableView_logs.save_data(path)  # path validity checking done inside this function
        except Exception as e:
            logger.warning(f"Error saving file: {e.__str__()}")

    def show_status(self, message: str):
        self.ui.statusbar.showMessage(message, 2.5 * 1000)  # show for 2.5secs

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        widget_handling.add_sensitive_widgets_to_palette(self)
        super(ApiHome, self).paintEvent(a0)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if event.spontaneous():
            self.pause_stylesheet_timer = True
            messageButton = QtWidgets.QMessageBox().question(self, "close window",
                                                             "Are you sure you want to close the application?",
                                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                             QtWidgets.QMessageBox.Yes)
            if messageButton == QtWidgets.QMessageBox.Yes:
                event.accept()
                self.window_closed.emit()
                logger.info("Exit from API Home")
            else:
                event.ignore()
            try:
                self.style_refresh_timer.stop()
            except Exception:
                pass
        else:
            event.accept()
            self.window_closed.emit()
        self.pause_stylesheet_timer = False
