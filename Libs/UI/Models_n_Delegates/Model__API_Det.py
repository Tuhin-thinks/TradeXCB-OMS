import typing

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt

from Libs.Utils import settings
from Libs.Storage import app_data
from Libs.UI.Utils.field_validator import is_valid_broker_field


class Delegate_Slices(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: QtWidgets.QTableView):
        super(Delegate_Slices, self).__init__(parent)

    def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        editor = QtWidgets.QSpinBox(parent)
        editor.setMinimum(1)
        editor.setMaximum(settings.MAX_LOT_SIZE_ANY_INSTRUMENT)
        editor_data = index.data(Qt.EditRole)
        if isinstance(editor_data, int):
            editor.setValue(editor_data)
        elif isinstance(editor_data, str) and editor_data.isdigit():
            editor.setValue(int(editor_data))
        editor.editingFinished.connect(self.commit_editor)
        return editor

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        editor_data = index.data(Qt.EditRole)
        if isinstance(editor_data, int):
            editor.setValue(editor_data)
        elif isinstance(editor_data, str) and editor_data.isdigit():
            editor.setValue(int(editor_data))

    def setModelData(self, editor: QtWidgets.QSpinBox, model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        value = editor.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
                             index: QtCore.QModelIndex) -> None:
        editor.setGeometry(option.rect)

    def commit_editor(self) -> None:
        editor = self.sender()
        self.commitData.emit(editor)


class Delegate_API_Det(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget):
        super(Delegate_API_Det, self).__init__(parent)

    def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        # create lineEdit as editor
        editor = QtWidgets.QLineEdit(parent)
        editor.setAlignment(Qt.AlignCenter)
        editor.move(option.rect.x(), option.rect.y())
        editor.resize(option.rect.width(), option.rect.height())
        editor.editingFinished.connect(self.commit_editor)
        if index.column() not in (0, 1, app_data.API_DETAILS_COLUMNS.index('No of Lots')):
            editor.setEchoMode(QtWidgets.QLineEdit.Password)
        return editor

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)  # save the editor's current state to the model

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class Delegate_Broker_Type(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget):
        super(Delegate_Broker_Type, self).__init__(parent)

        self.choices = app_data.BROKER_NAMES

    def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        # create lineEdit as editor
        editor = QtWidgets.QComboBox(parent)
        if index.row() == 0:
            editor.addItems(["Zerodha", "IIFL"])
        else:
            editor.addItems(self.choices)
        editor.move(option.rect.x(), option.rect.y())
        editor.resize(option.rect.width(), option.rect.height())
        editor.currentIndexChanged.connect(self.commit_editor)
        return editor

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)  # save the editor's current state to the model

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class Model_API_Det(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        super(Model_API_Det, self).__init__(parent)
        if not data:
            data = []
        self.data_list = data
        self.header_labels = app_data.API_DETAILS_COLUMNS

    def rowCount(self, parent=None):
        return len(self.data_list)

    def columnCount(self, parent=None):
        return len(self.header_labels)

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlags:
        column_name = self.header_labels[index.column()]
        broker_name = self.data_list[index.row()][self.header_labels.index("Stock Broker Name")]
        is_generic_field = column_name in app_data.broker_api_fields['common_fields']
        if not is_generic_field and not is_valid_broker_field(broker_name, column_name):
            return Qt.NoItemFlags
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            column_name = self.header_labels[index.column()]
            broker_name = self.data_list[index.row()][self.header_labels.index("Stock Broker Name")]
            is_generic_field = column_name in app_data.broker_api_fields['common_fields']
            if role == Qt.DisplayRole:
                item = self.data_list[index.row()][index.column()]
                if item is None:
                    return None
                elif (not is_generic_field) and is_valid_broker_field(broker_name, column_name):
                    return "*" * len(item)
                else:
                    if is_valid_broker_field(broker_name, column_name):
                        return item
                    else:
                        return "N/A"
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            elif role == Qt.EditRole:
                return self.data_list[index.row()][index.column()]
            elif role == Qt.BackgroundRole:
                if not is_generic_field and not is_valid_broker_field(broker_name, column_name):
                    return QtGui.QColor(Qt.lightGray)
            elif role == Qt.ForegroundRole:
                if not is_generic_field and not is_valid_broker_field(broker_name, column_name):
                    return QtGui.QColor(Qt.darkGray)
            elif role == Qt.ToolTipRole:
                if not is_generic_field and not is_valid_broker_field(broker_name, column_name):
                    return "This field is not required for this broker"
        return None

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if index.isValid():
            if role == Qt.EditRole:
                self.data_list[index.row()][index.column()] = value
                self.dataChanged.emit(index, index, [role])
                return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_labels[section]
        return None

    # --------- custom functions ---------
    def get_data(self, index: int) -> typing.Any:
        return self.data_list[index]

    def set_data(self, data: typing.List[typing.List]):
        self.beginResetModel()
        self.data_list = data
        self.endResetModel()

    def get_all_row_data(self) -> typing.List[typing.List[typing.Any]]:
        """
        Returns the data of all rows in the model.
        :return:
        """
        return self.data_list

    def get_data_by_row(self, row: int) -> typing.Any:
        return self.data_list[row]

    def delete_row(self, row_num):
        self.beginRemoveRows(QtCore.QModelIndex(), row_num, row_num)
        del self.data_list[row_num]
        self.endRemoveRows()

    def append_empty_row(self) -> None:
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self.data_list.append([""] * self.columnCount())
        self.endInsertRows()
