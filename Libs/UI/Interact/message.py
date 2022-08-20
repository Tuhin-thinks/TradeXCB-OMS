import typing

from PyQt5 import QtWidgets


def show_message(parent: QtWidgets, title: str, text: str, mode: typing.Literal["info", "warning", "error", "question"]):
    message_box = QtWidgets.QMessageBox
    timer_pause_handle = None
    if hasattr(parent, "global_parent"):
        if hasattr(parent.global_parent, "pause_stylesheet_timer"):
            timer_pause_handle = parent.global_parent
    elif hasattr(parent, "pause_stylesheet_timer"):
        timer_pause_handle = parent

    if timer_pause_handle:
        setattr(timer_pause_handle, "pause_stylesheet_timer", True)
    if mode == "info":
        message_box.information(parent, title, text, QtWidgets.QMessageBox.Close)
    elif mode == "warning":
        message_box.warning(parent, title, text, QtWidgets.QMessageBox.Close)
    elif mode == "error":
        message_box.critical(parent, title, text, QtWidgets.QMessageBox.Close)
    elif mode == "question":
        button = message_box.question(parent, title, text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

    if timer_pause_handle:
        setattr(timer_pause_handle, "pause_stylesheet_timer", False)

    if mode == "question":
        return button
