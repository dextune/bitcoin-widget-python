from typing import List, Tuple
import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMenu, QAction, 
    QTableWidgetItem
)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve
import win32gui # type: ignore
import win32con # type: ignore
from layout_settings import create_layout
import json
import webbrowser

# 상수 정의
UPDATE_INTERVAL = 2500  # ms
BINANCE_API_BASE = "https://api.binance.com/api/v3"
WINDOW_GEOMETRY = (300, 300, 250, 300)  # x, y, width, height

class BTCPriceWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_coins: List[str] = []
        self.coins: List[Tuple[str, str]] = []
        
        self._init_ui()
        self._init_timer()
        self._load_coins()
        self.update_price()

    def _init_ui(self) -> None:
        """UI 초기화 및 이벤트 설정"""
        self.setWindowTitle('BTC Price Widget')
        self.setGeometry(*WINDOW_GEOMETRY)
        
        # 초기 윈도우 플래그 설정
        self.setWindowFlags(self.windowFlags() | Qt.Tool)  # Tool 플래그 추가로 작업 표시줄 아이콘 제거

        # 레이아웃 정
        layout, self.price_table, self.opacity_slider, self.always_on_top_checkbox = create_layout(self)
        self.setLayout(layout)

        # 이벤트 연결
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        self.always_on_top_checkbox.stateChanged.connect(self.toggle_always_on_top)
        
        # 컨텍스트 메뉴 설정
        self.price_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.price_table.customContextMenuRequested.connect(self.show_context_menu)

        # 더블클릭 이벤트 연결
        self.price_table.cellDoubleClicked.connect(self.open_trading_page)

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

    def show_context_menu(self, pos) -> None:
        """우클릭 컨텍스트 메뉴 표시"""
        menu = QMenu(self)
        delete_action = QAction('삭제', self)
        delete_action.triggered.connect(lambda: self.delete_row(pos))
        menu.addAction(delete_action)
        menu.exec_(self.price_table.viewport().mapToGlobal(pos))

    def delete_row(self, pos) -> None:
        """선택된 행 삭제"""
        row = self.price_table.rowAt(pos.y())
        if row >= 0:
            self.price_table.removeRow(row)
            self.selected_coins.pop(row)

    def toggle_always_on_top(self, state: int) -> None:
        hwnd = self.winId().__int__()
        
        if state == Qt.Checked:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        else:
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
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
                # 환율 API 호출
                response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
                data = response.json()
                krw_rate = data['rates']['KRW']
                
                self.price_table.setItem(index, 0, QTableWidgetItem('KRW-USD'))
                price_item = QTableWidgetItem(f'{krw_rate:.2f}')
                price_item.setTextAlignment(Qt.AlignRight)
                self.price_table.setItem(index, 1, price_item)
            else:
                # 기존 바이낸스 API 호출
                response = requests.get(f'{BINANCE_API_BASE}/ticker/price?symbol={coin}')
                response.raise_for_status()
                data = response.json()
                
                self.price_table.setItem(index, 0, QTableWidgetItem(coin))
                price_item = QTableWidgetItem(f'{float(data["price"]):.4f}')
                price_item.setTextAlignment(Qt.AlignRight)
                self.price_table.setItem(index, 1, price_item)
            
        except requests.RequestException as e:
            self.price_table.setItem(index, 0, QTableWidgetItem(coin))
            self.price_table.setItem(index, 1, QTableWidgetItem(f'Error: {str(e)}'))

    def open_trading_page(self, row: int, column: int) -> None:
        """더블클릭한 코인의 거래소 페이지 열기"""
        coin = self.price_table.item(row, 0).text()
        
        if coin == 'KRW-USD':
            # 환율 정보 페이지
            url = 'https://www.tradingview.com/chart/?symbol=FX_IDC%3AUSDKRW'
        else:
            # 바이낸스 거래 페이지
            symbol = coin.lower()
            url = f'https://www.binance.com/en/trade/{symbol}'
        
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"URL 열기 실패: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BTCPriceWidget()
    widget.show()
    sys.exit(app.exec_())