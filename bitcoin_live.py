from typing import List, Tuple
import sys
import requests
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMenu, QAction, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QVBoxLayout, QHBoxLayout, QLabel,
    QHeaderView
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor
import win32gui # type: ignore
import win32con # type: ignore
from layout_settings import create_layout, SettingsDialog, WINDOW_STYLE, TABLE_STYLE, setup_table, create_title_bar
import json
import webbrowser

# Constants
UPDATE_INTERVAL = 2500  # ms
BINANCE_API_BASE = "https://api.binance.com/api/v3"
WINDOW_GEOMETRY = (300, 300, 270, 300)  # x, y, width, height

class BTCPriceWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_coins: List[str] = []
        self.coins: List[Tuple[str, str]] = []
        self.config = {}  # Dictionary for storing settings
        self.languages = {}  # Dictionary for language data
        self.previous_prices = {}  # Dictionary for storing previous prices
        self.drag_pos = None
        self.window_size = {'width': 270, 'height': 300}  # Default window size
        
        self.load_language()  # Load language file
        self.load_config()  # Load configuration file
        self._init_ui()
        self._init_timer()
        self._load_coins()
        self.update_price()

    def load_language(self) -> None:
        """Load language file"""
        try:
            with open('language.json', 'r', encoding='utf-8') as f:
                self.languages = json.load(f)
        except Exception as e:
            print(f"Error loading language file: {e}")
            self.languages = {}

    def get_text(self, key: str) -> str:
        """Return text based on the current language"""
        current_language = self.config.get('language', 'kr')
        try:
            return self.languages[current_language][key]
        except:
            return key

    def update_texts(self) -> None:
        """Update UI texts"""
        # Update title
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setText("Coin Price")
        
        # Update context menu text for right-click
        self.price_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.price_table.customContextMenuRequested.connect(self.show_context_menu)

    def load_config(self) -> None:
        """Load information from configuration file"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
                self.selected_coins = self.config.get('selected_coins', [])
                self.setWindowOpacity(self.config.get('opacity', 100) / 100)
                always_on_top = self.config.get('always_on_top', 0)
                # Load window size
                window_size = self.config.get('window_size', {'width': 270, 'height': 300})
                self.window_size = window_size
                self.setFixedSize(window_size['width'], window_size['height'])
                QTimer.singleShot(100, lambda: self.apply_always_on_top(always_on_top))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Config load error: {e}")
            self.config = {
                'selected_coins': [],
                'opacity': 100,
                'always_on_top': 0,
                'language': 'kr',
                'window_size': {'width': 270, 'height': 300}
            }
            self.selected_coins = []
            self.setWindowOpacity(1.0)
            self.setFixedSize(270, 300)

    def apply_always_on_top(self, value: int) -> None:
        """Apply always on top setting"""
        is_top = bool(value)
        print(f"Applying always on top: {is_top}")  # For debugging
        self.toggle_always_on_top(is_top)

    def toggle_always_on_top(self, state: bool) -> None:
        """Set always on top"""
        try:
            hwnd = self.winId().__int__()
            
            if state:
                print("Setting window to top most")  # For debugging
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            else:
                print("Setting window to not top most")  # For debugging
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except Exception as e:
            print(f"Error in toggle_always_on_top: {e}")  # For debugging

    def save_config(self) -> None:
        """Save configuration"""
        self.config.update({
            'selected_coins': self.selected_coins,
            'opacity': int(self.windowOpacity() * 100),
            'always_on_top': int(self.isAlwaysOnTop()),
            'language': self.config.get('language', 'kr'),
            'window_size': self.window_size  # Save window size
        })
        
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Config save error: {e}")

    def _init_ui(self) -> None:
        """Initialize UI"""
        self.setWindowTitle('Coin Price')
        self.setGeometry(*WINDOW_GEOMETRY)
        self.setWindowFlags(self.windowFlags() | Qt.Tool | Qt.FramelessWindowHint)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # Add title bar (includes close button)
        title_bar, self.settings_button, close_button = create_title_bar(self)
        main_layout.addWidget(title_bar)
        
        # Connect right-click menu and double-click events
        self.settings_button.clicked.connect(self.open_settings_dialog)
        # Connect close button click event
        close_button.clicked.connect(self.close)
        
        # Set up table widget
        self.price_table = QTableWidget(self)
        setup_table(self.price_table)
        
        # Set up context menu and double-click events
        self.price_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.price_table.customContextMenuRequested.connect(self.show_context_menu)
        self.price_table.cellDoubleClicked.connect(self.open_trading_page)
        
        main_layout.addWidget(self.price_table)
        self.setLayout(main_layout)
        
        # Set overall window style
        self.setStyleSheet(WINDOW_STYLE)

    def _init_timer(self) -> None:
        """Initialize price update timer"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_price)
        self.timer.start(UPDATE_INTERVAL)

    def _load_coins(self) -> None:
        """Load coin list from Binance API"""
        try:
            response = requests.get(f'{BINANCE_API_BASE}/exchangeInfo')
            response.raise_for_status()
            data = response.json()
            
            # Add KRW-USD pair at the beginning
            self.coins = [('KRW-USD', 'KRW-USD')]
            
            # Add existing coin list
            self.coins.extend([
                (symbol['symbol'], symbol['symbol'])
                for symbol in data['symbols']
                if 'USDT' in symbol['symbol']
            ])
        except requests.RequestException as e:
            print(f"Failed to load coin list: {e}")

    def show_context_menu(self, position) -> None:
        """Show right-click context menu"""
        menu = QMenu()
        delete_action = QAction(self.get_text('delete'), self)
        delete_action.triggered.connect(lambda: self.delete_selected_coin())
        menu.addAction(delete_action)
        
        # Show menu at current cursor position
        menu.exec_(self.price_table.viewport().mapToGlobal(position))

    def delete_selected_coin(self) -> None:
        """Delete selected coin"""
        current_row = self.price_table.currentRow()
        if current_row >= 0:
            coin = self.price_table.item(current_row, 0).text()
            if coin in self.selected_coins:
                self.selected_coins.remove(coin)
                self.update_price()
                self.save_config()

    def on_fade_out_finished(self, new_flags):  # new_flags 파라미터 추가
        self.setWindowFlags(new_flags)
        self.show()
        
        # 페이드 인 애니메이션
        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(100)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        fade_in.start()

    def add_coin(self) -> None:
        """Add new coin"""
        selected_coin = self.coin_selector.currentText()
        if selected_coin and selected_coin not in self.selected_coins:
            self.selected_coins.append(selected_coin)
            self.update_price()

    def change_opacity(self, value: int) -> None:
        """Change window opacity"""
        self.setWindowOpacity(value / 100)

    def update_price(self) -> None:
        """Update prices of selected coins"""
        self.price_table.setRowCount(len(self.selected_coins))
        
        for index, coin in enumerate(self.selected_coins):
            self._update_coin_price(index, coin)

    def _update_coin_price(self, index: int, coin: str) -> None:
        """Update individual coin price"""
        try:
            if coin == 'KRW-USD':
                response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
                data = response.json()
                current_price = data['rates']['KRW']
                
                self.price_table.setItem(index, 0, QTableWidgetItem('KRW-USD'))
                price_item = QTableWidgetItem(f'{current_price:.2f}')
            else:
                response = requests.get(f'{BINANCE_API_BASE}/ticker/price?symbol={coin}')
                response.raise_for_status()
                data = response.json()
                current_price = float(data['price'])
                
                self.price_table.setItem(index, 0, QTableWidgetItem(coin))
                price_item = QTableWidgetItem(f'{current_price:.4f}')
            
            # Set default color (white)
            price_item.setForeground(QColor("#EAECEF"))
            price_item.setTextAlignment(Qt.AlignRight)
            self.price_table.setItem(index, 1, price_item)
            
        except requests.RequestException as e:
            self.price_table.setItem(index, 0, QTableWidgetItem(coin))
            error_item = QTableWidgetItem("Error")
            error_item.setForeground(QColor("#F6465D"))  # Error is displayed in red
            self.price_table.setItem(index, 1, error_item)

    def open_trading_page(self, row: int, column: int) -> None:
        """Open exchange page for double-clicked coin"""
        try:
            coin = self.price_table.item(row, 0).text()
            
            if coin == 'KRW-USD':
                url = 'https://www.tradingview.com/chart/?symbol=FX_IDC%3AUSDKRW'
            else:
                # Handle USDT pairs
                base_symbol = coin.replace('USDT', '')
                url = f'https://www.binance.com/en/trade/{base_symbol}_USDT'
            
            print(f"Opening URL: {url}")  # For debugging
            webbrowser.open(url)
        except Exception as e:
            print(f"Failed to open URL: {e}")

    def open_settings_dialog(self) -> None:
        """Open settings dialog"""
        dialog = SettingsDialog(self, self)  # Set current widget as parent
        dialog.exec_()  # Run as modal
        self.save_config()  # Save configuration after changes

    def isAlwaysOnTop(self) -> bool:
        """Return whether the current window is always on top"""
        hwnd = self.winId().__int__()
        return win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST != 0

    def mousePressEvent(self, event):
        """Mouse press event"""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Mouse drag event"""
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            # Calculate new position of the current window
            new_pos = event.globalPos() - self.drag_pos
            screen = QApplication.primaryScreen().geometry()
            
            # Snap distance for magnetic effect (pixels)
            snap_distance = 20
            
            # Window size
            window_width = self.width()
            window_height = self.height()
            
            # Check screen edges and snap
            # Left edge
            if abs(new_pos.x()) < snap_distance:
                new_pos.setX(0)
            # Right edge
            elif abs(screen.width() - (new_pos.x() + window_width)) < snap_distance:
                new_pos.setX(screen.width() - window_width)
            # Top edge
            if abs(new_pos.y()) < snap_distance:
                new_pos.setY(0)
            # Bottom edge
            elif abs(screen.height() - (new_pos.y() + window_height)) < snap_distance:
                new_pos.setY(screen.height() - window_height)
            
            self.move(new_pos)
            event.accept()

    def resize_window(self, width: int, height: int) -> None:
        """Resize window"""
        self.window_size = {'width': width, 'height': height}
        self.setFixedSize(width, height)
        self.save_config()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BTCPriceWidget()
    widget.show()
    sys.exit(app.exec_())