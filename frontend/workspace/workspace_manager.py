import os
import json
import logging
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from PySide6.QtWidgets import QWidget, QStackedWidget

logger = logging.getLogger(__name__)

class WorkspaceManager(QObject):
    """Manages workspace pages within a QStackedWidget instead of independent windows."""
    
    _instance = None
    language_changed = Signal()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config_path: str = "config/workspace.json"):
        if WorkspaceManager._instance is not None:
            raise RuntimeError("WorkspaceManager is a singleton. Use get_instance().")
        super().__init__()
        self.config_path = os.path.abspath(config_path)
        self._pages = {}
        self._layout_data = {}
        self.main_workspace: QStackedWidget = None
        
        # Debounce timer for saving layout to avoid spamming I/O
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._flush_save)
        
        self.load_layout()

    def set_main_workspace(self, workspace_stack: QStackedWidget):
        self.main_workspace = workspace_stack

    def load_layout(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._layout_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load workspace layout: {e}")
                self._layout_data = {}

    def _flush_save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._layout_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workspace layout: {e}")

    def save_layout_deferred(self):
        self._save_timer.start(1000)

    def trigger_language_change(self):
        self.language_changed.emit()

    def show_window(self, page_key: str, *args, **kwargs) -> QWidget:
        if not self.main_workspace:
            logger.error("Main workspace not set in WorkspaceManager")
            return None
            
        page_class = None
        
        import os
        from backend.services.project_repository import ProjectRepository
        
        project_dir = kwargs.pop('project_dir', '')
        
        if page_key == 'settings':
            from frontend.ui.settings_window import SettingsWindow
            page_class = SettingsWindow

        if not page_class:
            logger.error(f'Unknown page key for show_window: {page_key}')
            return None

        return self.open_page(page_key, page_class, *args, **kwargs)

    def open_page(self, page_key: str, page_class, *args, **kwargs) -> QWidget:
        if page_key in self._pages:
            page = self._pages[page_key]
            self.main_workspace.setCurrentWidget(page)
            return page
        
        # Instantiate and add to stack
        page = page_class(*args, **kwargs)
        self._pages[page_key] = page
        self.main_workspace.addWidget(page)
        
        if hasattr(page, 'retranslate_ui'):
            self.language_changed.connect(page.retranslate_ui)
            
        self.main_workspace.setCurrentWidget(page)
        return page
