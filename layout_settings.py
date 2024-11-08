from PyQt5.QtWidgets import QVBoxLayout, QComboBox, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QSlider, QCheckBox, QHeaderView, QDialog, QLabel
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None, btc_widget=None):
        super().__init__(parent)
        self.btc_widget = btc_widget
        self.setWindowTitle('설정')
        
        # 부모 위젯의 위치를 가져와서 설정 창의 위치 계산
        if parent:
            parent_pos = parent.pos()
            self.setGeometry(parent_pos.x(), parent_pos.y(), 300, 200)
        else:
            self.setGeometry(400, 400, 300, 200)

        # 레이아웃 설정
        settings_layout = QVBoxLayout()
        
        # 검색 입력 생성
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText('Search for coins...')
        
        # 코인 선택기 생성
        self.coin_selector = QComboBox(self)
        
        # Add Coin 버튼 생성
        self.add_button = QPushButton('Add Coin', self)
        
        # 위젯들을 레이아웃에 추가
        settings_layout.addWidget(QLabel('코인 검색'))
        settings_layout.addWidget(self.search_input)
        settings_layout.addWidget(QLabel('코인 선택'))
        settings_layout.addWidget(self.coin_selector)
        settings_layout.addWidget(self.add_button)
        
        self.setLayout(settings_layout)

        # 이벤트 연결
        self.search_input.textChanged.connect(self.filter_coins)
        self.add_button.clicked.connect(self.add_coin)

        # 초기 코인 목록 로드
        self.load_coins()

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

def create_layout(widget):
    layout = QVBoxLayout()

    # 설정 버튼 추가 (테이블 위에 배치)
    settings_button = QPushButton('설정', widget)
    layout.addWidget(settings_button)

    # 가격 목록 표시 (QTableWidget 사용)
    price_table = QTableWidget(widget)
    price_table.setColumnCount(2)  # 두 개의 열 (이름, 현재가)
    price_table.setHorizontalHeaderLabels(['이름', '현재가'])  # 헤더 설정
    layout.addWidget(price_table)

    # 셀 크기를 꽉 차게 변경
    price_table.horizontalHeader().setStretchLastSection(True)
    price_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    price_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    # 헤더 정렬: 가운데 정렬
    header = price_table.horizontalHeader()
    for i in range(header.count()):
        header.setStyleSheet("QHeaderView::section { text-align: center; }")

    # 본문 셀 내용 왼쪽 정렬
    price_table.setStyleSheet("QTableWidget::item { text-align: left; }")

    # 테이블 가로 스크롤 비활성화
    price_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # 투명도 조절 슬라이더 추가
    opacity_slider = QSlider(Qt.Horizontal, widget)
    opacity_slider.setRange(0, 100)
    opacity_slider.setValue(100)
    layout.addWidget(opacity_slider)

    # 항상 위에 표시 체크박스 추가
    always_on_top_checkbox = QCheckBox('항상 위에 표시', widget)
    layout.addWidget(always_on_top_checkbox)

    # 설정 창 열기 함수
    def open_settings():
        dialog = SettingsDialog(widget, widget)
        dialog.exec_()

    settings_button.clicked.connect(open_settings)

    return layout, price_table, opacity_slider, always_on_top_checkbox