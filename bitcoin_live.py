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
from layout_settings import create_layout, SettingsDialog
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
        self.config = {}  # 설정 저장용 딕셔너리
        self.languages = {}  # 언어 데이터 저장
        
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
        # 테이블 헤더 텍스트 업데이트
        self.price_table.setHorizontalHeaderLabels([
            self.get_text('name'),
            self.get_text('current_price')
        ])
        
        # 설정 버튼 텍스트 업데이트
        self.settings_button.setText(self.get_text('settings'))

    def load_config(self) -> None:
        """설정 파일에서 정보를 로드"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
                self.selected_coins = self.config.get('selected_coins', [])
                self.setWindowOpacity(self.config.get('opacity', 100) / 100)
                always_on_top = self.config.get('always_on_top', 0)
                QTimer.singleShot(100, lambda: self.apply_always_on_top(always_on_top))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Config load error: {e}")
            self.config = {
                'selected_coins': [],
                'opacity': 100,
                'always_on_top': 0,
                'language': 'kr'
            }
            self.selected_coins = []
            self.setWindowOpacity(1.0)
            self.toggle_always_on_top(False)

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
        """설정 정보를 파일에 저장"""
        try:
            self.config.update({
                'selected_coins': self.selected_coins,
                'always_on_top': 1 if self.isAlwaysOnTop() else 0,
                'opacity': int(self.windowOpacity() * 100)
            })
            with open('config.json', 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _init_ui(self) -> None:
        """UI 초기화"""
        self.setWindowTitle('BTC Price Widget')
        self.setGeometry(*WINDOW_GEOMETRY)
        
        # 초기 윈도우 플래그 설정
        self.setWindowFlags(self.windowFlags() | Qt.Tool)  # Tool 플래그 추가로 작업 표시줄 아이콘 제거

        # 레이아웃 설정
        layout, self.price_table, self.settings_button, _ = create_layout(self)  # settings_button을 인스턴스 변수로 저장
        self.setLayout(layout)

        # 이벤트 연결
        self.settings_button.clicked.connect(self.open_settings_dialog)  # 설정 버튼 클릭 시 설정 창 열기

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
        delete_action = QAction(self.get_text('delete'), self)
        delete_action.triggered.connect(lambda: self.delete_row(pos))
        menu.addAction(delete_action)
        menu.exec_(self.price_table.viewport().mapToGlobal(pos))

    def delete_row(self, pos) -> None:
        """선택된 행 삭제"""
        row = self.price_table.rowAt(pos.y())
        if row >= 0:
            self.price_table.removeRow(row)
            self.selected_coins.pop(row)

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
            print(f"URL 열기 실패 : {e}")

    def open_settings_dialog(self) -> None:
        """설정 창 열기"""
        dialog = SettingsDialog(self, self)  # 현재 위젯을 부모로 설정
        dialog.exec_()  # 모달로 실행
        self.save_config()  # 설정이 변경된 후 저장

    def isAlwaysOnTop(self) -> bool:
        """현재 창이 항상 위에 표시되는지 여부 반환"""
        hwnd = self.winId().__int__()
        return win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST != 0

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BTCPriceWidget()
    widget.show()
    sys.exit(app.exec_())