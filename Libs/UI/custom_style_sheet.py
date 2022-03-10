import json
from typing import Dict, Union

from PyQt5.QtGui import QBrush, QPalette

import Libs.globals
from Libs.Storage.manage_local import get_user_preference_table, set_custom_stylesheet_values


class CustomStyleSheet:
    def __init__(self, palette: 'QPalette'):
        set_custom_stylesheet_values()
        ui_data = json.loads(get_user_preference_table("ui_data"))
        self.os_based_customizations = {
            "tab_padding_main": ui_data.get("tab_padding_main") or "",
            "tab_padding_sub": ui_data.get("tab_padding_sub") or "",
            "min_tab_width_sub": ui_data.get("min_tab_width_sub") or "",
            'tab_min_height_main': ui_data.get("tab_min_height_main") or "",
            'tab_min_height_sub': ui_data.get("tab_min_height_sub") or "",
            "main_tab_width": ui_data.get("main_tab_width") or "",
            "min_tab_width_main": ui_data.get("min_tab_width_main") or ""
        }
        self._home_stylesheet = {
            "light": """
QPushButton, QLabel, QLineEdit, QComboBox, QCheckbox{
    font: $widget_common_font$
}
QMenuBar{
    font: 10pt "Serif";
    color: rgb(255, 255, 255);
    background-color:black;
}
QStatusBar{
    font: 10pt "Serif";
    color: rgb(255, 255, 255);
    background-color: rgb(0, 0, 0);
}
""",
            "dark": ""}
        self._dark_style = {
            "pushbutton": """
        QPushButton {
            border-radius: 2px;
            padding: 0.2em 0.2em 0.3em 0.2em;
            border: 1px solid rgb(100, 100, 100);
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #f4f4f4, stop:0.1 #8F8F8F, stop:1  #7B7B7B);
            color: white;
            min-width: 70px;
        }
        QPushButton::pressed{
             background: qlineargradient(spread:pad, x1:0.516, y1:0, x2:0.532, y2:1, stop:0 rgba(167, 167, 167, 255), stop:0.0894737 rgba(48, 48, 48, 255), stop:0.905263 rgba(43, 43, 43, 255), stop:1 rgba(147, 147, 147, 255))
        }"""}
        self.gradient_frame = {
            'light': """#frame_bg_gradient_frame{
    background-color: $grad_frame_bg$;
    border:2px outset transparent;
    border-radius: 15px 15px 15px 5px;
    background-repeat: 0;
    background-position: center;
}
.QLabel{
    color: $api_det_inp_lbl_color$;
}
""",
            'dark': ""}
        self.table_view_stylesheet = {"light": """QHeaderView{
    color: white;
    background-color: transparent; /* header background*/
}
QTableView{
    gridline-color: rgba(255, 255, 255, 80);
    selection-background-color: $table_view_selection_bg_color$;
}
QTableView::item{
    color: palette(WindowText);
}
QHeaderView::section {
    color: white;
    background-color: #343434;
    font-size: 9pt;
    padding: 2px;
    border: 1px solid #4a4a4a;
    margin: 2px;
}
QTableView QTableCornerButton::section{
    border: 1px solid black;
    background-color: transparent;
}
"""}
        self.api_det_inp_frame = {"light": """#frame_api_details_inp{
border:2px outset transparent;
    border-radius: 15px 15px 15px 5px;
}
#frame_api_details_inp QLabel{
    color: $api_det_inp_lbl_color$;
    font: 10pt "Serif";
}
#frame_api_details_inp::hover{
    background-color: rgba(254, 254, 254, 30);
    border:2px outset transparent;
    border-radius: 15px 15px 15px 5px;
}
.QLineEdit{
    border: 1px solid gray;
    border-radius: 5px;
    padding: 0.6ex;
    font-weight: bold;
    font: 10pt "Serif";
}""", 'dark': ""}
        self.tabwidget_ = {'light': """QTabWidget{
            color: $main_tab_font_color$;
        }
        QTabWidget::pane {
            /*border: 1px solid white;*/
            background: $pane_bg$;
            color: $main_tab_font_color$;
        }
        QTabWidget::tab-bar {
            alignment: center;
        }
        QTabBar::tab {
            /*border: 1px solid $main_tab_font_color$;*/
            color: $main_tab_font_color$;
            font: $tab_common_font$;
            margin-left: 5px;
        }


QTabBar::tab:selected {
    background:qlineargradient(spread:reflect, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0, 90, 255, 255), stop:0.231579 rgba(0, 63, 178, 255), stop:0.542105 rgba(5, 5, 5, 255), stop:0.8 rgba(0, 63, 178, 255), stop:1 rgba(0, 90, 255, 255));
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}
QTabBar::tab:!selected {
    background: qlineargradient(spread:reflect, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0, 90, 255, 255), stop:0.231579 rgba(0, 63, 178, 255), stop:0.542105 rgba(5, 5, 5, 255), stop:0.8 rgba(0, 63, 178, 255), stop:1 rgba(0, 90, 255, 255));
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
}
        QTabBar::tab:!selected:hover {
            background: $tab_not_sel_hov_bg$;
            color: $tab_not_sel_hov_color$;
        }
        QTabBar::tab:top:!selected {
            margin-top: 2ex;
        }
        QTabBar::tab:bottom:!selected {
            margin-bottom: 0px;
        }
        QTabBar::tab:top, QTabBar::tab:bottom {    
            min-width: $min_tab_width_main$;  /* for main tab type */
            min-height: $tab_min_height_main$;
            margin-right: -1px;
            padding-top: 5px;
            padding-bottom: 5px;
        }
        QTabBar::tab:top:selected {
            border-bottom-color: none;
        }
        QTabBar::tab:bottom:selected {
            border-top-color: none;
        }
        QTabBar::tab:top:last, QTabBar::tab:bottom:last,
        QTabBar::tab:top:only-one, QTabBar::tab:bottom:only-one {
            margin-right: 0;
        }
        QTabBar::tab:left:!selected {
            margin-right: 3px;
        }
        QTabBar::tab:right:!selected {
            margin-left: 3px;
        }
        QTabBar::tab:left, QTabBar::tab:right {
            min-height: 5ex;
            margin-bottom: -1px;
            padding: 10px 5px 10px 5px;
        }
        QTabBar::tab:left:selected {
            border-left-color: none;
            border-right: none;
        }
        QTabBar::tab:right:selected {
            border-right-color: none;
            border-left: none;
        }
        QTabBar::tab:left:last, QTabBar::tab:right:last,
        QTabBar::tab:left:only-one, QTabBar::tab:right:only-one {
            margin-bottom: 0;
        }

        QTabBar::tab:first:selected {
        margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
        }
        QTabBar::tab:last:selected {
        margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
        }
        QTabBar::tab:only-one {
        margin: 0; /* if there is only one tab, we don't want overlapping margins */
        }
        QTabBar::tab:first:!selected {
            border-top-left-radius: 5px;
        }
        QTabBar::tab:last:!selected {
            border-top-right-radius: 5px;
        }
        """, 'dark': ""}
        self.tabwidget_2_ = {"light": """QTabWidget{
            color: $main_tab_font_color$;
        }
        QTabWidget::pane {
            border: 1px solid none;
            background: white;
            color: $main_tab_font_color$;
        }
        QTabWidget::tab-bar {
            alignment: center;
        }
        QTabBar::tab {
            /*border: 1px solid $main_tab_font_color$;*/
            color: $main_tab_font_color$;
            font: $tab_common_font$;
        }
        QTabBar::tab:selected {
            background:qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(162, 162, 162, 255), stop:0.3 rgba(45, 45, 45, 255), stop:0.747368 rgba(35, 35, 35, 255), stop:1 rgba(118, 118, 118, 255));
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:!selected {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(162, 162, 162, 255), stop:0.257895 rgba(0, 0, 0, 255), stop:0.747368 rgba(0, 0, 0, 255), stop:1 rgba(118, 118, 118, 255));
            border-top-left-radius: 2px;
            border-top-right-radius: 2px;
        }
        QTabBar::tab:!selected:hover {
            background: $tab_not_sel_hov_bg$;
            color: $tab_not_sel_hov_color$;
        }
        QTabBar::tab:top:!selected {
            margin-top: 2ex;
        }
        QTabBar::tab:bottom:!selected {
            margin-bottom: 0px;
        }
        QTabBar::tab:top, QTabBar::tab:bottom {
            min-width: $min_tab_width_sub$;  /* for sub tab type */
            min-height: $tab_min_height_sub$;
            padding-top: 5px;
            padding-bottom: 5px;
            padding-left: 1px;
            padding-right: 2px;
        }
        QTabBar::tab:top:selected {
            border-bottom-color: none;
        }
        QTabBar::tab:bottom:selected {
            border-top-color: none;
        }
        QTabBar::tab:top:last, QTabBar::tab:bottom:last,
        QTabBar::tab:top:only-one, QTabBar::tab:bottom:only-one {
            margin-right: 0;
        }
        QTabBar::tab:left:!selected {
            margin-right: 3px;
        }
        QTabBar::tab:right:!selected {
            margin-left: 3px;
        }
        QTabBar::tab:left, QTabBar::tab:right {
            min-height: 5ex;
            margin-bottom: -1px;
            padding: 10px 5px 10px 5px;
        }
        QTabBar::tab:left:selected {
            border: none;
        }
        QTabBar::tab:right:selected {
            border: none;
        }
        QTabBar::tab:left:last, QTabBar::tab:right:last,
        QTabBar::tab:left:only-one, QTabBar::tab:right:only-one {
            margin-bottom: 0;
        }

        QTabBar::tab:first:selected {
        margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
        }
        QTabBar::tab:last:selected {
        margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
        }
        QTabBar::tab:only-one {
        margin: 0; /* if there is only one tab, we don't want overlapping margins */
        }""", 'dark': ""}
        self.home_frame = {"light": """#frame_home_main_frame{
    background-color: qlineargradient(spread:pad, x1:0, y1:0.568409, x2:1, y2:0.545, stop:0 $frame_bg_left$, stop:0.494737 $frame_bg_mid$, stop:1 $frame_bg_right$);
    background-repeat: none;
    background-position: center;
    background-origin: content;
}""", 'dark': ""}
        self.palette = palette

        self.color_rules = {}
        self.update_custom_rules()
        self.generate_black_styles()

    def update_custom_rules(self, mode='dark'):
        def QBrush_to_Str(brush: 'QBrush', alpha=255):
            r, g, b = brush.color().red(), brush.color().green(), brush.color().blue()
            color_string = f"rgba{r, g, b, alpha}"
            return color_string

        palette_color_mid = QBrush_to_Str(self.palette.midlight())
        palette_color_light = QBrush_to_Str(self.palette.light())
        palette_color_dark = QBrush_to_Str(self.palette.dark())
        palette_color_button = QBrush_to_Str(self.palette.button())
        palette_color_midlight = QBrush_to_Str(self.palette.midlight())
        self.color_rules.update(
            {
                "tab_selected_bg": f"qlineargradient(spread:pad, x1:0.495, y1:0, x2:0.516, y2:1, stop:0 {palette_color_mid}, stop:1 {palette_color_light})",
                "main_tab_font_color": QBrush_to_Str(
                    self.palette.windowText() if mode == 'dark' else self.palette.text()),
                "sub_tab_font_color": QBrush_to_Str(
                    self.palette.windowText() if mode == 'dark' else self.palette.light()),
                "pane_bg": QBrush_to_Str(self.palette.base(), 100),
                "tab_not_sel_bg": f"qlineargradient(spread:pad, x1:0.505, y1:0.028, x2:0.526, y2:1, stop:0 {palette_color_dark}, stop:1 {palette_color_midlight})",
                "sub_tab_selected_bg": f"{(palette_color_light if mode == 'dark' else palette_color_dark)}",
                "sub_tab_not_selected_bg": f"qlineargradient(spread:pad, x1:0.495, y1:0, x2:0.495, y2:1, stop:0 {palette_color_dark}, stop:0.484211 {palette_color_light}, stop:1 {palette_color_dark})",
                "tab_not_sel_hov_bg": QBrush_to_Str(self.palette.mid()),
                "tab_not_sel_hov_color": QBrush_to_Str(self.palette.brightText()),
                "sub_tab_not_sel_hov_color": QBrush_to_Str(self.palette.dark()),
                "frame_bg_left": QBrush_to_Str(self.palette.dark()),
                "frame_bg_mid": QBrush_to_Str(self.palette.mid()),
                "frame_bg_right": QBrush_to_Str(self.palette.light()),
                "grad_frame_bg": f"qlineargradient(spread:reflect, x1:0, y1:0, x2:1, y2:1, stop:0 {QBrush_to_Str(self.palette.light())}, stop:1 {QBrush_to_Str(self.palette.midlight(), alpha=107)})",
                "api_det_inp_lbl_color": 'white;' if mode == 'dark' else 'black;',
                "tab_common_font": '9pt "Serif";',
                "widget_common_font": '9pt "Serif";',
                "table_view_font": f'{Libs.globals.settings.TABLE_FONT_SIZE}pt "Serif";',
                "headerView_font": f'{Libs.globals.settings.HEADER_VIEW_FONT}pt "Serif";',
                "table_view_border_color": QBrush_to_Str(self.palette.text()),
                "table_view_bg": QBrush_to_Str(self.palette.window()),
                "table_view_grid_line_color": QBrush_to_Str(self.palette.text()),
                "header_view_bg": palette_color_mid,
                "table_view_selection_bg_color": QBrush_to_Str(self.palette.highlight()),
            }
        )

    def generate_black_styles(self):
        """ Generate black style from light style. """
        black_style = []
        for word in self.tabwidget_['light'].split('\n'):
            if 'white' in word:
                black_style.append(word.replace('white', 'black'))
            elif 'black' in word:
                black_style.append(word.replace('black', 'white'))
            elif '#999' in word:
                black_style.append(word.replace('#999', '#686868'))
            else:
                black_style.append(word)

        self.tabwidget_.update({'dark': '\n'.join(black_style)})

        black_style = []
        for word in self.tabwidget_2_['light'].split('\n'):
            if 'white' in word:
                black_style.append(word.replace('white', 'black'))
            elif 'black' in word:
                black_style.append(word.replace('black', 'white'))
            elif '#999' in word:
                black_style.append(word.replace('#999', '#686868'))
            else:
                black_style.append(word)
        self.tabwidget_2_.update({'dark': '\n'.join(black_style)})

        self.home_frame['dark'] = self.home_frame['light']
        self.gradient_frame['dark'] = self.gradient_frame['light']
        self.api_det_inp_frame['dark'] = self.api_det_inp_frame['light']
        self.table_view_stylesheet['dark'] = self.table_view_stylesheet['light']
        self._home_stylesheet['dark'] = self._home_stylesheet['light']

    def parse_stylesheet(self, stylesheet: str) -> str:
        """replace key from dictionary with corresponding values"""
        new_stylesheet = stylesheet

        for key, val in self.os_based_customizations.items():
            if f"${key}$" in new_stylesheet:
                new_stylesheet = new_stylesheet.replace(f"${key}$", val)

        for key, val in self.color_rules.items():
            if f"${key}$" in new_stylesheet:
                new_stylesheet = new_stylesheet.replace(f"${key}$", val)

        return new_stylesheet

    def parse_stylesheet_dict(self, style_dict: dict) -> Dict:
        new_style_dict = {}
        for mode, style in style_dict.items():
            new_style_dict[mode] = self.parse_stylesheet(style)
        return new_style_dict

    def tabwidget(self, mode: str, palette: Union['QPalette', None] = None) -> str:
        if palette:
            self.palette = palette
            self.update_custom_rules(mode)
        temp_style_string = self.parse_stylesheet_dict(self.tabwidget_)[mode]
        # with open("tabwidget_.txt", 'w') as writer:
        #     writer.write(temp_style_string)
        return temp_style_string

    def tabwidget_2(self, mode: str, palette: Union['QPalette', None] = None) -> str:
        if palette:
            self.palette = palette
            self.update_custom_rules(mode)

        temp_style_string = self.parse_stylesheet_dict(self.tabwidget_2_)[mode]
        # with open("tabwidget_2_style.txt", 'w') as writer:
        #     writer.write(temp_style_string)
        return temp_style_string

    def tableview(self, mode: str, palette: Union['QPalette', None] = None) -> str:
        if palette:
            self.palette = palette
            self.update_custom_rules(mode)
        _stylesheet_string = self.parse_stylesheet_dict(self.table_view_stylesheet)[mode]
        # with open("table_view_stylesheet.txt", 'w') as writer:
        #     writer.write(_stylesheet_string)
        return _stylesheet_string

    def home_main_frame(self, mode: str, palette: Union['QPalette', None] = None) -> str:
        if palette:
            self.palette = palette
            self.update_custom_rules(mode)
        _stylesheet_string = self.parse_stylesheet_dict(self.home_frame)[mode]
        # with open("home_frame.txt", 'w') as writer:
        #     writer.write(_stylesheet_string)
        return _stylesheet_string

    def bg_gradient_frame(self, mode: str, palette: Union['QPalette', None] = None) -> str:
        if palette:
            self.palette = palette
            self.update_custom_rules(mode)
        _stylesheet_string = self.parse_stylesheet_dict(self.gradient_frame)[mode]
        # with open("gradient_frame.txt", 'w') as writer:
        #     writer.write(_stylesheet_string)
        return _stylesheet_string

    def api_inp_details_frame(self, mode: Libs.globals.typing.Literal["dark", "light"],
                              palette: Union['QPalette', None] = None) -> str:
        if palette:
            self.palette = palette
            self.update_custom_rules(mode)
        _stylesheet_string = self.parse_stylesheet_dict(self.api_det_inp_frame)[mode]
        # with open("api_det_inp_frame.txt", 'w') as writer:
        #     writer.write(_stylesheet_string)
        return _stylesheet_string

    def home_stylesheet(self, mode: str):
        _stylesheet_string = self.parse_stylesheet_dict(self._home_stylesheet)[mode]
        # with open("_home_stylesheet.txt", 'w') as writer:
        #     writer.write(_stylesheet_string)
        return _stylesheet_string

    @staticmethod
    def menu_stylesheet():
        return """
        border: 1px solid white;
        border-radius: 2px;
        background-color: black;
        color: white;
        selection-background-color: #1F3A93 /*Jackson's purple*/;
        selection-color: white;"""

    def get_dark_style(self, widget):
        _stylesheet_string = self._dark_style.get(widget) or ''
        # with open("widget.txt", 'w') as writer:
        #     writer.write(_stylesheet_string)
        return _stylesheet_string
