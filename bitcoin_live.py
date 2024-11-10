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

# 상수 정의
UPDATE_INTERVAL = 2500  # ms
BINANCE_API_BASE = "https://api.binance.com/api/v3"
WINDOW_GEOMETRY = (300, 300, 270, 300)  # x, y, width, height

class BTCPriceWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_coins: List[str] = []
        self.coins: List[Tuple[str, str]] = []
        self.config = {}  # 설정 저장용 딕셔너리
        self.languages = {}  # 언어 데이터 저장
        self.previous_prices = {}  # 이전 가격 저장용
        self.drag_pos = None
        self.window_size = {'width': 270, 'height': 300}  # 기본 창 크기
        
        self.load_language()  # 언어 파일 로드
        self.load_config()  # 설정 파일 로드
        self._init_ui()
        self._init_timer()
        self._load_coins()
        self.update_price()

    def load_language(self) -> None:
        """언어 파일 로드"""
        try:
            with open('language.json', 'r', encoding='utf-8') as f:
                self.languages = json.load(f)
        except Exception as e:
            print(f"Error loading language file: {e}")
            self.languages = {}

    def get_text(self, key: str) -> str:
        """현재 언어에 따른 텍스트 반환"""
        current_language = self.config.get('language', 'kr')
        try:
            return self.languages[current_language][key]
        except:
            return key

    def update_texts(self) -> None:
        """UI 텍스트 업데이트"""
        # 타이틀 업데이트
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setText("Coin Price")
        
        # 테이블 우클릭 메뉴 텍스트 업데이트
        self.price_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.price_table.customContextMenuRequested.connect(self.show_context_menu)

    def load_config(self) -> None:
        """설정 파일에서 정보를 로드"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
                self.selected_coins = self.config.get('selected_coins', [])
                self.setWindowOpacity(self.config.get('opacity', 100) / 100)
                always_on_top = self.config.get('always_on_top', 0)
                # 창 크기 로드
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
        """항상 위에 표시 설정 적용"""
        is_top = bool(value)
        print(f"Applying always on top: {is_top}")  # 디버깅용
        self.toggle_always_on_top(is_top)

    def toggle_always_on_top(self, state: bool) -> None:
        """항상 위에 표시 설정"""
        try:
            hwnd = self.winId().__int__()
            
            if state:
                print("Setting window to top most")  # 디버깅용
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            else:
                print("Setting window to not top most")  # 디버깅용
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except Exception as e:
            print(f"Error in toggle_always_on_top: {e}")  # 디버깅용

    def save_config(self) -> None:
        """설정 저장"""
        self.config.update({
            'selected_coins': self.selected_coins,
            'opacity': int(self.windowOpacity() * 100),
            'always_on_top': int(self.isAlwaysOnTop()),
            'language': self.config.get('language', 'kr'),
            'window_size': self.window_size  # 창 크기 저장
        })
        
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Config save error: {e}")

    def _init_ui(self) -> None:
        """UI 초기화"""
        self.setWindowTitle('Coin Price')
        self.setGeometry(*WINDOW_GEOMETRY)
        self.setWindowFlags(self.windowFlags() | Qt.Tool | Qt.FramelessWindowHint)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # 타이틀 바 추가 (닫기 버튼 포함)
        title_bar, self.settings_button, close_button = create_title_bar(self)
        main_layout.addWidget(title_bar)
        
        # 설정 버튼 클릭 이벤트 연결
        self.settings_button.clicked.connect(self.open_settings_dialog)
        # 닫기 버튼 클릭 이벤트 연결
        close_button.clicked.connect(self.close)
        
        # 테이블 위젯 설정
        self.price_table = QTableWidget(self)
        setup_table(self.price_table)
        
        # 우클릭 메뉴와 더블클릭 이벤트 설정
        self.price_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.price_table.customContextMenuRequested.connect(self.show_context_menu)
        self.price_table.cellDoubleClicked.connect(self.open_trading_page)
        
        main_layout.addWidget(self.price_table)
        self.setLayout(main_layout)
        
        # 전체 창 스타일 설정
        self.setStyleSheet(WINDOW_STYLE)

    def _init_timer(self) -> None:
        """가격 업데이트 타이머 초기화"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_price)
        self.timer.start(UPDATE_INTERVAL)

    def _load_coins(self) -> None:
        """바이낸스 API에서 코인 목록 로드"""
        try:
            response = requests.get(f'{BINANCE_API_BASE}/exchangeInfo')
            response.raise_for_status()
            data = response.json()
            
            # KRW-USD 환율 쌍을 맨 앞에 추가
            self.coins = [('KRW-USD', 'KRW-USD')]
            
            # 기존 코인 목록 추가
            self.coins.extend([
                (symbol['symbol'], symbol['symbol'])
                for symbol in data['symbols']
                if 'USDT' in symbol['symbol']
            ])
        except requests.RequestException as e:
            print(f"코인 목록 로딩 실패: {e}")

    def show_context_menu(self, position) -> None:
        """테이블 우클릭 메뉴 표시"""
        menu = QMenu()
        delete_action = QAction(self.get_text('delete'), self)
        delete_action.triggered.connect(lambda: self.delete_selected_coin())
        menu.addAction(delete_action)
        
        # 현재 커서 위치에서 메뉴 표시
        menu.exec_(self.price_table.viewport().mapToGlobal(position))

    def delete_selected_coin(self) -> None:
        """선택된 코인 삭제"""
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
        """새로운 코인 추가"""
        selected_coin = self.coin_selector.currentText()
        if selected_coin and selected_coin not in self.selected_coins:
            self.selected_coins.append(selected_coin)
            self.update_price()

    def change_opacity(self, value: int) -> None:
        """창 투명도 변경"""
        self.setWindowOpacity(value / 100)

    def update_price(self) -> None:
        """선택된 코인들의 가격 업데이트"""
        self.price_table.setRowCount(len(self.selected_coins))
        
        for index, coin in enumerate(self.selected_coins):
            self._update_coin_price(index, coin)

    def _update_coin_price(self, index: int, coin: str) -> None:
        """개별 코인 가격 업데이트"""
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
            
            # 기본 색상 설정 (흰색)
            price_item.setForeground(QColor("#EAECEF"))
            price_item.setTextAlignment(Qt.AlignRight)
            self.price_table.setItem(index, 1, price_item)
            
        except requests.RequestException as e:
            self.price_table.setItem(index, 0, QTableWidgetItem(coin))
            error_item = QTableWidgetItem("Error")
            error_item.setForeground(QColor("#F6465D"))  # 에러는 빨간색으로 표시
            self.price_table.setItem(index, 1, error_item)

    def open_trading_page(self, row: int, column: int) -> None:
        """더블클릭한 코인의 거래소 페이지 열기"""
        try:
            coin = self.price_table.item(row, 0).text()
            
            if coin == 'KRW-USD':
                url = 'https://www.tradingview.com/chart/?symbol=FX_IDC%3AUSDKRW'
            else:
                # USDT 페어 처리
                base_symbol = coin.replace('USDT', '')
                url = f'https://www.binance.com/en/trade/{base_symbol}_USDT'
            
            print(f"Opening URL: {url}")  # 디버깅용
            webbrowser.open(url)
        except Exception as e:
            print(f"URL 열기 실패: {e}")

    def open_settings_dialog(self) -> None:
        """설정 창 열기"""
        dialog = SettingsDialog(self, self)  # 현재 위젯을 부모로 설정
        dialog.exec_()  # 모달로 실행
        self.save_config()  # 설정이 변경된 후 저장

    def isAlwaysOnTop(self) -> bool:
        """현재 창이 항상 위에 표시되는지 여부 반환"""
        hwnd = self.winId().__int__()
        return win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST != 0

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """마우스 드래그 이벤트"""
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            # 현재 창의 새 위치 계산
            new_pos = event.globalPos() - self.drag_pos
            screen = QApplication.primaryScreen().geometry()
            
            # 자석 효과를 위한 거 임계값 (픽셀)
            snap_distance = 20
            
            # 창의 크기
            window_width = self.width()
            window_height = self.height()
            
            # 화면 가장자리 검사 및 스냅
            # 왼쪽 가장자리
            if abs(new_pos.x()) < snap_distance:
                new_pos.setX(0)
            # 오른쪽 가장자리
            elif abs(screen.width() - (new_pos.x() + window_width)) < snap_distance:
                new_pos.setX(screen.width() - window_width)
            # 위쪽 가장자리
            if abs(new_pos.y()) < snap_distance:
                new_pos.setY(0)
            # 아래쪽 가장자리
            elif abs(screen.height() - (new_pos.y() + window_height)) < snap_distance:
                new_pos.setY(screen.height() - window_height)
            
            self.move(new_pos)
            event.accept()

    def resize_window(self, width: int, height: int) -> None:
        """창 크기 조절"""
        self.window_size = {'width': width, 'height': height}
        self.setFixedSize(width, height)
        self.save_config()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BTCPriceWidget()
    widget.show()
    sys.exit(app.exec_())