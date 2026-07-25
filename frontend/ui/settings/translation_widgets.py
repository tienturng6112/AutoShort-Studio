import logging
from PySide6.QtWidgets import (QWidget, QGroupBox, QFormLayout, QLineEdit, 
                               QComboBox, QPushButton, QHBoxLayout, QLabel, QVBoxLayout)
from PySide6.QtCore import Signal
from backend.services.localization_service import LocalizationService

loc = LocalizationService()
logger = logging.getLogger(__name__)

class BaseTranslationSettingsWidget(QWidget):
    """Base class for Translation Provider settings widgets."""
    
    test_requested = Signal()
    refresh_models_requested = Signal()

    def __init__(self, provider_id: str, title_key: str):
        super().__init__()
        self.provider_id = provider_id
        
        self.group_box = QGroupBox(loc.translate(title_key))
        self.layout = QFormLayout()
        self.group_box.setLayout(self.layout)
        
        self.test_btn = QPushButton(loc.translate("btn_test_connection"))
        self.test_btn.clicked.connect(self._on_test_clicked)
        self.test_status_label = QLabel("")
        self.test_layout = QHBoxLayout()
        self.test_layout.addWidget(self.test_btn)
        self.test_layout.addWidget(self.test_status_label)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.group_box)
        main_layout.addStretch()

    def _on_refresh_models_clicked(self):
        if hasattr(self, "refresh_btn"):
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("...")
        self.refresh_models_requested.emit()
        
    def _on_test_clicked(self):
        self.test_requested.emit()

    def _on_test_finished(self, res: dict):
        self.test_btn.setEnabled(True)
        self.test_btn.setText(loc.translate("btn_test_connection"))
        
        success = res.get("success", False) or res.get("status") == "Success" or res.get("status") == "Connected"
        if success:
            self.test_status_label.setText(f"✓ Connected")
            self.test_status_label.setStyleSheet("color: #059669; font-weight: bold;")
        else:
            err = res.get("error", res.get("message", "Unknown error"))
            self.test_status_label.setText(f"✗ Failed: {err}")
            self.test_status_label.setStyleSheet("color: #DC2626; font-weight: bold;")

    def load_config(self, data: dict):
        pass

    def save_config(self) -> dict:
        return {}

    def _on_refresh_models_finished(self, res: dict):
        if hasattr(self, "refresh_btn"):
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText(loc.translate("btn_refresh_models"))
            
        success = res.get("success", False) or res.get("status") == "Success"
        models = res.get("models", []) or res.get("data", [])
        
        print(f"\n[UI SLOT MODEL REFRESH AUDIT - {self.__class__.__name__}]")
        print(f"  Slot received success: {success}")
        print(f"  Received models count: {len(models)}")
        
        if success and models and hasattr(self, "model_combo"):
            curr = self.model_combo.currentText()
            self.model_combo.clear()
            self.model_combo.addItems(models)
            print(f"  combo.clear() executed: True")
            print(f"  addItems(models) executed with {len(models)} items.")
            
            if curr in models:
                self.model_combo.setCurrentText(curr)
            elif curr:
                self.model_combo.addItem(curr)
                self.model_combo.setCurrentText(curr)
            print(f"  Active selected model: {self.model_combo.currentText()}")
        print("=============================================\n")


class ChatAnywhereSettingsWidget(BaseTranslationSettingsWidget):
    def __init__(self):
        super().__init__("chatanywhere", "chatanywhere_config")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.base_url_edit = QLineEdit()
        
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        
        self.refresh_btn = QPushButton(loc.translate("btn_refresh_models"))
        self.refresh_btn.clicked.connect(self._on_refresh_models_clicked)
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_combo, 1)
        model_layout.addWidget(self.refresh_btn)
        
        self.timeout_edit = QLineEdit("30")
        self.max_tokens_edit = QLineEdit("2048")
        self.temperature_edit = QLineEdit("0.7")
        
        self.layout.addRow(loc.translate("lbl_api_key"), self.api_key_edit)
        self.layout.addRow(loc.translate("lbl_base_url"), self.base_url_edit)
        self.layout.addRow(loc.translate("lbl_model_name"), model_layout)
        self.layout.addRow(loc.translate("lbl_timeout"), self.timeout_edit)
        self.layout.addRow(loc.translate("lbl_max_tokens"), self.max_tokens_edit)
        self.layout.addRow(loc.translate("lbl_temperature"), self.temperature_edit)
        self.layout.addRow(self.test_layout)

    def load_config(self, data: dict):
        ca_config = data.get("chatanywhere", {})
        self.api_key_edit.setText(ca_config.get("api_key", ""))
        self.base_url_edit.setText(ca_config.get("base_url", "https://api.chatanywhere.tech/v1"))
        
        model = ca_config.get("model", "gpt-4o-mini")
        if self.model_combo.findText(model) == -1:
            self.model_combo.addItem(model)
        self.model_combo.setCurrentText(model)
        
        self.timeout_edit.setText(str(ca_config.get("timeout", 30)))
        self.max_tokens_edit.setText(str(ca_config.get("max_tokens", 2048)))
        self.temperature_edit.setText(str(ca_config.get("temperature", 0.7)))

    def save_config(self) -> dict:
        return {
            "api_key": self.api_key_edit.text(),
            "base_url": self.base_url_edit.text(),
            "model": self.model_combo.currentText(),
            "timeout": int(self.timeout_edit.text() or 30),
            "max_tokens": int(self.max_tokens_edit.text() or 2048),
            "temperature": float(self.temperature_edit.text() or 0.7)
        }


class DeepLSettingsWidget(BaseTranslationSettingsWidget):
    def __init__(self):
        super().__init__("deepl", "deepl_config")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["default"])
        self.model_combo.setEditable(True)
        
        self.layout.addRow(loc.translate("lbl_api_key"), self.api_key_edit)
        self.layout.addRow(loc.translate("lbl_model_name"), self.model_combo)
        self.layout.addRow(self.test_layout)

    def load_config(self, data: dict):
        dl_config = data.get("deepl", {})
        self.api_key_edit.setText(dl_config.get("api_key", ""))
        model = dl_config.get("model", "default")
        self.model_combo.setCurrentText(model)

    def save_config(self) -> dict:
        return {
            "api_key": self.api_key_edit.text(),
            "model": self.model_combo.currentText()
        }


class GoogleSettingsWidget(BaseTranslationSettingsWidget):
    def __init__(self):
        super().__init__("google", "lbl_google_config")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.layout.addRow(loc.translate("lbl_api_key"), self.api_key_edit)
        self.layout.addRow(self.test_layout)

    def load_config(self, data: dict):
        g_config = data.get("google", {})
        self.api_key_edit.setText(g_config.get("api_key", ""))

    def save_config(self) -> dict:
        return {"api_key": self.api_key_edit.text()}


class GeminiSettingsWidget(BaseTranslationSettingsWidget):
    def __init__(self):
        super().__init__("gemini", "lbl_gemini_config")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gemini-1.5-flash", "gemini-1.5-pro"])
        self.model_combo.setEditable(True)
        
        self.layout.addRow(loc.translate("lbl_api_key"), self.api_key_edit)
        self.layout.addRow(loc.translate("lbl_model_name"), self.model_combo)
        self.layout.addRow(self.test_layout)

    def load_config(self, data: dict):
        g_config = data.get("gemini", {})
        self.api_key_edit.setText(g_config.get("api_key", ""))
        self.model_combo.setCurrentText(g_config.get("model", "gemini-1.5-flash"))

    def save_config(self) -> dict:
        return {
            "api_key": self.api_key_edit.text(),
            "model": self.model_combo.currentText()
        }


class OpenAISettingsWidget(BaseTranslationSettingsWidget):
    def __init__(self):
        super().__init__("openai", "lbl_openai_config")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o-mini", "gpt-4o"])
        self.model_combo.setEditable(True)
        
        self.layout.addRow(loc.translate("lbl_api_key"), self.api_key_edit)
        self.layout.addRow(loc.translate("lbl_model_name"), self.model_combo)
        self.layout.addRow(self.test_layout)

    def load_config(self, data: dict):
        o_config = data.get("openai", {})
        self.api_key_edit.setText(o_config.get("api_key", ""))
        self.model_combo.setCurrentText(o_config.get("model", "gpt-4o-mini"))

    def save_config(self) -> dict:
        return {
            "api_key": self.api_key_edit.text(),
            "model": self.model_combo.currentText()
        }
