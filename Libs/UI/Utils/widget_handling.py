import Libs.globals
from Libs.UI import parse_palette, home
from Libs.UI.CustomWidgets import ExcelView__Frame, SlidingStackedWidget
from PyQt5 import QtWidgets


def add_sensitive_widgets_to_palette(parent: 'QtWidgets.QMainWindow'):
    # create list of widgets, for which palette needs to be updated
    for widget in [parent.ui.comboBox_strategy_select,
                   parent.ui.scrollAreaWidgetContents_trading_symb, parent.positionView,
                   parent.tableView_logs]:
        if widget not in parent.palette_sensitive_widgets:
            parent.palette_sensitive_widgets.append(widget)

    for child in parent.findChildren(QtWidgets.QLabel):
        if child not in parent.palette_sensitive_widgets:
            parent.palette_sensitive_widgets.append(child)

    for child in parent.findChildren(QtWidgets.QPushButton):
        if child not in parent.palette_sensitive_widgets:
            parent.palette_sensitive_widgets.append(child)

    for child in parent.findChildren(QtWidgets.QComboBox):
        if child not in parent.palette_sensitive_widgets:
            parent.palette_sensitive_widgets.append(child)

    for child in parent.findChildren(QtWidgets.QTableView):
        if child not in parent.palette_sensitive_widgets:
            parent.palette_sensitive_widgets.append(child)


def change_theme(parent, theme_name: str):
    """
    To change/sync UI theme
    :param theme_name: Dark, Dark - Enhanced Green, Dark - Blue
    :param parent: ApiHome (MainWindow)
    """
    theme_path = parent.themes.get(theme_name) or "Dark.xml"
    if not theme_path or not Libs.globals.os.path.exists(theme_path):
        return

    palette = parse_palette.parse_xml(theme_path)  # parse xml and create palette
    parent.setPalette(palette)

    parent.custom_palette_now = palette
    mode = 'dark' if theme_name.startswith('Dark') else 'light'
    dark_style = parent.custom_style_sheet.tabwidget(mode=mode, palette=parent.custom_palette_now)
    dark_style_2 = parent.custom_style_sheet.tabwidget_2(mode=mode, palette=parent.custom_palette_now)

    # don't update TradingSymbols tab, when there are strategy tables added, this may freeze the GUI
    # if not parent.strategy_tables:
    parent.ui.tabWidget.setStyleSheet(dark_style)
        # parent.to_update_parent_stylesheet = False
    parent.ui.tabWidget_opt_chain_analysis.setStyleSheet(dark_style_2)

    # assign custom palette to required widgets
    for index in range(len(parent.palette_sensitive_widgets) - 1, -1, -1):
        widget = parent.palette_sensitive_widgets[index]
        try:
            widget.setPalette(parent.custom_palette_now)
        except (RuntimeError, AttributeError):
            del parent.palette_sensitive_widgets[index]
    parent.update()


def reset_combobox_options(args: tuple):
    """Delete and adds new options to the combobox passed argument
    :param args: received from emit signal
    """
    comboBox, new_options, default_option = args
    _ = [comboBox.removeItem(0) for _ in range(comboBox.count())]
    if default_option:
        new_options.insert(0, default_option)
    comboBox.addItems(new_options)


def add_option_analysis_views(parent):
    set_opt_chain_analysis_tab_layouts(parent)
    frame_optionDetailAnalysis = ExcelView__Frame.DisplayFrame("OPTION_DETAILS_ANALYSIS", Libs.globals.app_data.OPTION_DETAILS_ANALYSIS,
                                                               parent.ui.tabWidget_opt_chain_analysis, parent)
    parent.gridLayout_optDetailAnalysis.addWidget(frame_optionDetailAnalysis, 0, 0, 1, 1)

    frame_optionGreeks = ExcelView__Frame.DisplayFrame("OPTION_GREEKS", Libs.globals.app_data.OPTION_GREEKS,
                                                       parent.ui.tabWidget_opt_chain_analysis, parent)
    parent.gridLayout_optionGreeks.addWidget(frame_optionGreeks, 0, 0, 1, 1)

    frame_marketProfile = ExcelView__Frame.DisplayFrame("MARKET_PROFILE", Libs.globals.app_data.MARKET_PROFILE,
                                                        parent.ui.tabWidget_opt_chain_analysis, parent)
    parent.gridLayout_MarketProfile.addWidget(frame_marketProfile, 0, 0, 1, 1)

    frame_crossOvers = ExcelView__Frame.DisplayFrame("CROSSOVER", Libs.globals.app_data.CROSSOVER,
                                                     parent.ui.tabWidget_opt_chain_analysis, parent)
    parent.gridLayout_Crossovers.addWidget(frame_crossOvers, 0, 0, 1, 1)

    frame_deltaReport = ExcelView__Frame.DisplayFrame("DELTA_REPORT", Libs.globals.app_data.DELTA_REPORT,
                                                      parent.ui.tabWidget_opt_chain_analysis, parent)
    frame_deltaReport.export_instruments_data.connect(parent.accept_export_instruments_data)
    parent.gridLayout_DeltaReport.addWidget(frame_deltaReport, 0, 0, 1, 1)

    frame_premiumReport = ExcelView__Frame.DisplayFrame("PREMIUM_REPORT", Libs.globals.app_data.PREMIUM_REPORT,
                                                        parent.ui.tabWidget_opt_chain_analysis, parent)
    frame_deltaReport.export_instruments_data.connect(parent.accept_export_instruments_data)
    parent.gridLayout_premiumReport.addWidget(frame_premiumReport, 0, 0, 1, 1)

    frame_signals = ExcelView__Frame.DisplayFrame("SIGNALS", Libs.globals.app_data.SIGNALS,
                                                  parent.ui.frame_signals_holder, parent)
    parent.gridLayout_signals.addWidget(frame_signals, 0, 0, 1, 1)

    parent.opt_chain_frames = [
        (frame_optionDetailAnalysis, "optionDetailAnalysis"),  # received from DB
        (frame_optionGreeks, "optionGreeks"),  # received from DB
        (frame_marketProfile, "marketProfile"),  # derived from optionDetailAnalysis
        (frame_crossOvers, "crossOvers"),  # derived from optionDetailAnalysis
        (frame_deltaReport, "deltaReport"),  # received from DB
        (frame_premiumReport, "premiumReport"),  # received from DB
        (frame_signals, "signals")  # received from DB
    ]
    for frame_info in parent.opt_chain_frames:
        frame_widget = frame_info[0]
        if frame_widget not in parent.palette_sensitive_widgets:
            parent.palette_sensitive_widgets.append(frame_widget)


def set_opt_chain_analysis_tab_layouts(parent):
    """set layouts to all tabs under option details analysis section"""
    parent.gridLayout_optDetailAnalysis = QtWidgets.QGridLayout(parent.ui.tab_optDetailAnalysis)
    parent.gridLayout_optDetailAnalysis.setContentsMargins(0, 0, 0, 0)
    parent.gridLayout_optDetailAnalysis.setSpacing(0)

    parent.gridLayout_optionGreeks = QtWidgets.QGridLayout(parent.ui.tab_optionGreeks)
    parent.gridLayout_optionGreeks.setContentsMargins(0, 0, 0, 0)
    parent.gridLayout_optionGreeks.setSpacing(0)

    parent.gridLayout_MarketProfile = QtWidgets.QGridLayout(parent.ui.tab_MarketProfile)
    parent.gridLayout_MarketProfile.setContentsMargins(0, 0, 0, 0)
    parent.gridLayout_MarketProfile.setSpacing(0)

    parent.gridLayout_Crossovers = QtWidgets.QGridLayout(parent.ui.tab_Crossovers)
    parent.gridLayout_Crossovers.setContentsMargins(0, 0, 0, 0)
    parent.gridLayout_Crossovers.setSpacing(0)

    parent.gridLayout_DeltaReport = QtWidgets.QGridLayout(parent.ui.tab_DeltaReport)
    parent.gridLayout_DeltaReport.setContentsMargins(0, 0, 0, 0)
    parent.gridLayout_DeltaReport.setSpacing(0)

    parent.gridLayout_premiumReport = QtWidgets.QGridLayout(parent.ui.tab_premiumReport)
    parent.gridLayout_premiumReport.setContentsMargins(0, 0, 0, 0)
    parent.gridLayout_premiumReport.setSpacing(0)

    # ============================= SIGNALS ==============================
    parent.ui: 'home.Ui_MainWindow' = parent.ui
    parent.ui.stackedWidget_signals = SlidingStackedWidget.SlidingStackedWidget(parent.ui.tab_signals)
    # to display all stocks
    parent.ui.page_all_signals = QtWidgets.QWidget()
    # to store data rows that has only NIFTY/BANKNIFTY as Name
    parent.ui.page_nifty_bank_nifty = QtWidgets.QWidget()

    parent.ui.stackedWidget_signals.addWidget(parent.ui.page_all_signals)
    parent.ui.stackedWidget_signals.addWidget(parent.ui.page_nifty_bank_nifty)

    parent.ui.gridLayout_page_all_signals = QtWidgets.QGridLayout(parent.ui.page_all_signals)
    parent.ui.gridLayout_page_all_signals.setContentsMargins(0, 0, 0, 0)
    parent.ui.gridLayout_page_all_signals.setSpacing(0)

    parent.ui.gridLayout_signals_holder_filtered = QtWidgets.QGridLayout(parent.ui.page_nifty_bank_nifty)
    parent.ui.gridLayout_signals_holder_filtered.setContentsMargins(0, 0, 0, 0)
    parent.ui.gridLayout_signals_holder_filtered.setSpacing(0)

    parent.ui.gridLayout_signals_tab.addWidget(parent.ui.stackedWidget_signals, 1, 0, 1, 1)

    parent.ui.frame_signals_holder = QtWidgets.QFrame(parent.ui.page_all_signals)
    parent.ui.frame_signals_holder_filtered = QtWidgets.QFrame(parent.ui.page_nifty_bank_nifty)
    parent.ui.frame_signals_holder_filtered.setObjectName("frame_signals_holder_filtered")

    parent.ui.gridLayout_page_all_signals.addWidget(parent.ui.frame_signals_holder)
    parent.ui.gridLayout_signals_holder_filtered.addWidget(parent.ui.frame_signals_holder_filtered)

    parent.gridLayout_signals = QtWidgets.QGridLayout(parent.ui.frame_signals_holder)
    parent.gridLayout_signals.setContentsMargins(0, 0, 0, 0)
    parent.gridLayout_signals.setSpacing(0)
