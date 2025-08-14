from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
    QLineEdit, QTableWidget, QTableWidgetItem, QSlider, 
    QCheckBox, QHeaderView, QDialog, QLabel, QWidget
)
from PyQt5.QtCore import Qt
import json
from typing import Tuple

# Constants for styling
WINDOW_STYLE = """
    QWidget {
        background-color: #1E2329;
        color: #EAECEF;
    }
"""

TABLE_STYLE = """
    QTableWidget {
        background-color: #1E2329;
        border: none;
    }
    QTableWidget::item {
        color: #EAECEF;
        border-bottom: 1px solid #2B3139;
        padding: 5px;
    }
    QTableWidget::item:selected {
        background-color: #363C45;
    }
"""

class SettingsDialog(QDialog):
    def __init__(self, parent=None, btc_widget=None):
        super().__init__(parent)
        self.btc_widget = btc_widget
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)  # Remove frame
        self.languages = {}  # Store language data
        self.load_language()  # Load language file first
        
        # Fixed window size
        self.setFixedSize(300, 405)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2B3139;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
        """)
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(10, 0, 10, 0)
        title_bar_layout.setSpacing(0)
        
        # Title label
        title_label = QLabel(self.get_text('settings'))
        title_label.setStyleSheet("color: #EAECEF; font-weight: bold; font-size: 14px;")
        
        # Close button
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #848E9C;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #ff4d4d;
            }
        """)
        
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        title_bar.setLayout(title_bar_layout)
        main_layout.addWidget(title_bar)
        
        # Reduce margins and spacing of the main layout
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # Add existing settings layout to a new container
        settings_container = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add language selector combo box
        self.language_selector = QComboBox(self)
        self.language_selector.addItem("한국어", "kr")
        self.language_selector.addItem("English", "en")
        settings_layout.addWidget(QLabel(self.get_text('language')))
        settings_layout.addWidget(self.language_selector)
        
        # Search input
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText('Search for coins...')
        
        # Coin selector
        self.coin_selector = QComboBox(self)
        
        # Add Coin button
        self.add_button = QPushButton(self.get_text('add_coin'), self)
        
        # Add widgets to the layout
        settings_layout.addWidget(QLabel(self.get_text('search_coin')))
        settings_layout.addWidget(self.search_input)
        settings_layout.addWidget(QLabel(self.get_text('select_coin')))
        settings_layout.addWidget(self.coin_selector)
        settings_layout.addWidget(self.add_button)
        
        # Add opacity slider
        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        settings_layout.addWidget(self.opacity_slider)

        # Always on top checkbox
        self.always_on_top_checkbox = QCheckBox(self.get_text('always_on_top'), self)
        settings_layout.addWidget(self.always_on_top_checkbox)

        # Adjust window size input fields layout
        size_container = QWidget()
        size_layout = QHBoxLayout()  # Change to HBoxLayout for single line display
        
        # Width input
        width_label = QLabel("W:")  # Change Width label to W
        self.width_input = QLineEdit()
        self.width_input.setFixedWidth(60)  # Limit input field width
        self.width_input.setText(str(btc_widget.window_size['width']))
        size_layout.addWidget(width_label)
        size_layout.addWidget(self.width_input)
        size_layout.addWidget(QLabel("px"))  # Add px text
        
        # Height input
        height_label = QLabel("H:")  # Change Height label to H
        self.height_input = QLineEdit()
        self.height_input.setFixedWidth(60)  # Limit input field width
        self.height_input.setText(str(btc_widget.window_size['height']))
        size_layout.addWidget(height_label)
        size_layout.addWidget(self.height_input)
        size_layout.addWidget(QLabel("px"))  # Add px text
        
        # Add to the layout
        size_container.setLayout(size_layout)
        settings_layout.addWidget(size_container)

        # Apply Size button
        self.apply_size_button = QPushButton(self.get_text('apply_size'), self)  # Set text when initialized
        self.apply_size_button.setObjectName("apply_size_button")  # Set object name
        self.apply_size_button.clicked.connect(self.apply_window_size)
        settings_layout.addWidget(self.apply_size_button)  # Add Apply button
        
        # Add settings layout to the main layout
        settings_container.setLayout(settings_layout)
        main_layout.addWidget(settings_container)
        
        self.setLayout(main_layout)
        
        # Event connections
        self.language_selector.currentIndexChanged.connect(self.change_language)
        self.search_input.textChanged.connect(self.filter_coins)
        self.add_button.clicked.connect(self.add_coin)
        
        # Slider and checkbox event connections
        self.opacity_slider.valueChanged.connect(self.btc_widget.change_opacity)  # Change opacity
        self.always_on_top_checkbox.stateChanged.connect(self.btc_widget.toggle_always_on_top)  # Always on top
        
        # Load initial coins
        self.load_coins()
        
        # Load settings
        self.load_settings()
        
        # Reflect current language in the combo box
        current_lang = self.btc_widget.config.get('language', 'kr')
        index = self.language_selector.findData(current_lang)
        if index >= 0:
            self.language_selector.setCurrentIndex(index)

        self.setStyleSheet("""
            QDialog {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                border-radius: 5px;
            }
            QLabel {
                color: #848E9C;
            }
            QComboBox {
                background-color: #2B3139;
                color: #EAECEF;
                border: 1px solid #363C45;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
            }
            QLineEdit {
                background-color: #2B3139;
                color: #EAECEF;
                border: 1px solid #363C45;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #F0B90B;
                color: #1E2329;
                border: none;
                border-radius: 3px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F8D12F;
            }
            QCheckBox {
                color: #EAECEF;
            }
            QSlider::groove:horizontal {
                background: #2B3139;
                height: 4px;
            }
            QSlider::handle:horizontal {
                background: #F0B90B;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)

    def load_settings(self):
        """Load settings and reflect them in the UI"""
        self.always_on_top_checkbox.setChecked(self.btc_widget.isAlwaysOnTop())
        self.opacity_slider.setValue(int(self.btc_widget.windowOpacity() * 100))

    def load_coins(self):
        if self.btc_widget:
            self.coin_selector.clear()
            for coin in self.btc_widget.coins:
                self.coin_selector.addItem(coin[0])

    def filter_coins(self):
        search_text = self.search_input.text().lower()
        self.coin_selector.clear()
        filtered_coins = [coin[0] for coin in self.btc_widget.coins if search_text in coin[0].lower()]
        self.coin_selector.addItems(filtered_coins)

    def add_coin(self):
        if self.btc_widget:
            selected_coin = self.coin_selector.currentText()
            if selected_coin and selected_coin not in self.btc_widget.selected_coins:
                self.btc_widget.selected_coins.append(selected_coin)
                self.btc_widget.update_price()

    def load_language(self) -> None:
        """Load language file"""
        try:
            with open('language.json', 'r', encoding='utf-8') as f:
                self.languages = json.load(f)
                self.current_language = self.btc_widget.config.get('language', 'kr')
        except Exception as e:
            print(f"Error loading language file: {e}")
            self.languages = {}
            self.current_language = 'kr'

    def get_text(self, key: str) -> str:
        """Return text based on current language"""
        try:
            return self.languages[self.current_language][key]
        except:
            return key

    def change_language(self):
        """Change language setting"""
        new_language = self.language_selector.currentData()
        if new_language != self.current_language:
            print(f"Changing language to: {new_language}")  # For debugging
            self.current_language = new_language
            self.btc_widget.config['language'] = new_language
            self.btc_widget.languages = self.languages  # Update main widget language data
            
            # Update UI texts
            self.update_texts()
            self.btc_widget.update_texts()
            
            # Save settings
            self.btc_widget.save_config()

    def update_texts(self) -> None:
        """Update UI texts"""
        # Update title label
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setText(self.get_text('settings'))
        
        # Update button texts
        self.add_button.setText(self.get_text('add_coin'))
        self.always_on_top_checkbox.setText(self.get_text('always_on_top'))
        
        # Update Apply Size button text
        apply_size_btn = self.findChild(QPushButton, "apply_size_button")
        if apply_size_btn:
            apply_size_btn.setText(self.get_text('apply_size'))
        
        # Update search placeholder
        self.search_input.setPlaceholderText(self.get_text('search_coin'))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def apply_window_size(self):
        """Apply window size changes"""
        try:
            width = int(self.width_input.text())
            height = int(self.height_input.text())
            if width > 0 and height > 0:
                self.btc_widget.resize_window(width, height)
        except ValueError:
            # Handle invalid input
            self.width_input.setText(str(self.btc_widget.window_size['width']))
            self.height_input.setText(str(self.btc_widget.window_size['height']))

def create_layout(widget):
    layout = QVBoxLayout()
    layout.setContentsMargins(1, 1, 1, 1)
    layout.setSpacing(0)

    # Create top bar
    top_bar = QWidget()
    top_bar.setStyleSheet("background-color: #2B3139;")
    top_bar_layout = QHBoxLayout()
    top_bar_layout.setContentsMargins(5, 5, 5, 5)
    
    # Add settings button
    settings_button = QPushButton("⚙", widget)
    settings_button.setFixedSize(20, 20)
    settings_button.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            color: #848E9C;
            font-size: 14px;
            border: none;
        }
        QPushButton:hover {
            color: #EAECEF;
        }
    """)
    
    top_bar_layout.addStretch()
    top_bar_layout.addWidget(settings_button)
    top_bar.setLayout(top_bar_layout)
    layout.addWidget(top_bar)

    # Price list display
    price_table = QTableWidget(widget)
    price_table.setColumnCount(2)
    
    # Hide header completely
    price_table.horizontalHeader().hide()
    price_table.verticalHeader().hide()
    price_table.horizontalHeader().setVisible(False)
    price_table.horizontalHeader().setHighlightSections(False)
    
    # Table settings
    price_table.setShowGrid(False)
    price_table.setFrameShape(QTableWidget.NoFrame)
    price_table.setSelectionBehavior(QTableWidget.SelectRows)
    price_table.setSelectionMode(QTableWidget.SingleSelection)
    
    # Column width settings
    price_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    price_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    
    layout.addWidget(price_table)

    return layout, price_table, settings_button, None

def setup_table(table: QTableWidget) -> None:
    """Configure table widget settings"""
    # Basic table settings
    table.setColumnCount(3) # Changed to 3 columns
    table.horizontalHeader().hide()
    table.verticalHeader().hide()
    
    # Table style settings
    table.setStyleSheet(TABLE_STYLE)
    
    # Table property settings
    table.setShowGrid(False)
    table.setFrameShape(QTableWidget.NoFrame)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    # Column width settings
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Adjust as needed
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # New column for profit

def create_title_bar(parent: QWidget) -> Tuple[QWidget, QPushButton, QPushButton]:
    """Create title bar with controls"""
    title_bar = QWidget(parent)
    title_bar.setFixedHeight(30)
    title_bar.setStyleSheet("""
        QWidget {
            background-color: #1E2329;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QPushButton {
            background-color: transparent;
            border: none;
            padding: 5px;
            color: #848E9C;
        }
        QPushButton:hover {
            background-color: #2B3139;
        }
    """)
    
    layout = QHBoxLayout(title_bar)
    layout.setContentsMargins(10, 0, 10, 0)
    layout.setSpacing(5)
    
    # Title label
    title_label = QLabel("Coin Price", title_bar)
    title_label.setObjectName("title_label")
    title_label.setStyleSheet("color: #EAECEF; font-weight: bold;")
    
    # Settings button
    settings_button = QPushButton("⚙", title_bar)
    settings_button.setFixedSize(30, 30)
    settings_button.setStyleSheet("font-size: 16px;")
    
    # Close button
    close_button = QPushButton("×", title_bar)
    close_button.setFixedSize(30, 30)
    close_button.setStyleSheet("font-size: 20px;")
    
    layout.addWidget(title_label)
    layout.addStretch()
    layout.addWidget(settings_button)
    layout.addWidget(close_button)
    
    return title_bar, settings_button, close_button