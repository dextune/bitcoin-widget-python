from PyQt5.QtWidgets import QVBoxLayout, QComboBox, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QSlider, QCheckBox, QHeaderView, QDialog, QLabel
from PyQt5.QtCore import Qt
import json

class SettingsDialog(QDialog):
    def __init__(self, parent=None, btc_widget=None):
        super().__init__(parent)
        self.btc_widget = btc_widget
        self.load_language()  # 언어 파일 로드
        
        self.setWindowTitle(self.get_text('settings'))
        
        # 부모 위젯의 위치를 가져와서 설정 창의 위치 계산
        if parent:
            parent_pos = parent.pos()
            self.setGeometry(parent_pos.x(), parent_pos.y(), 300, 200)
        else:
            self.setGeometry(400, 400, 300, 200)

        # 레이아웃 설정
        settings_layout = QVBoxLayout()
        
        # 언어 선택 콤보박스 추가
        self.language_selector = QComboBox(self)
        self.language_selector.addItem("한국어", "kr")
        self.language_selector.addItem("English", "en")
        settings_layout.addWidget(QLabel(self.get_text('language')))
        settings_layout.addWidget(self.language_selector)
        
        # 검색 입력 생성
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText('Search for coins...')
        
        # 코인 선택기 생성
        self.coin_selector = QComboBox(self)
        
        # Add Coin 버튼 생성
        self.add_button = QPushButton(self.get_text('add_coin'), self)
        
        # 위젯들을 레이아웃에 추가
        settings_layout.addWidget(QLabel(self.get_text('search_coin')))
        settings_layout.addWidget(self.search_input)
        settings_layout.addWidget(QLabel(self.get_text('select_coin')))
        settings_layout.addWidget(self.coin_selector)
        settings_layout.addWidget(self.add_button)
        
        # 투명도 조절 슬라이더 추가
        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        settings_layout.addWidget(self.opacity_slider)

        # 항상 위에 표시 체크박스 추가
        self.always_on_top_checkbox = QCheckBox(self.get_text('always_on_top'), self)
        settings_layout.addWidget(self.always_on_top_checkbox)

        self.setLayout(settings_layout)

        # 이벤트 연결
        self.language_selector.currentIndexChanged.connect(self.change_language)
        self.search_input.textChanged.connect(self.filter_coins)
        self.add_button.clicked.connect(self.add_coin)

        # 슬라이더와 체크박스 이벤트 연결
        self.opacity_slider.valueChanged.connect(self.btc_widget.change_opacity)  # 투명도 변경
        self.always_on_top_checkbox.stateChanged.connect(self.btc_widget.toggle_always_on_top)  # 항상 위에 표시

        # 초기 코인 목록 로드
        self.load_coins()

        # 설정 값 로드
        self.load_settings()

        # 현재 언어 설정을 콤보박스에 반영
        current_lang = self.btc_widget.config.get('language', 'kr')
        index = self.language_selector.findData(current_lang)
        if index >= 0:
            self.language_selector.setCurrentIndex(index)

    def load_settings(self):
        """설정 값을 로드하여 UI에 반영"""
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

    def load_language(self):
        """언어 파일 로드"""
        try:
            with open('language.json', 'r', encoding='utf-8') as f:
                self.languages = json.load(f)
            self.current_language = self.btc_widget.config.get('language', 'kr')
        except Exception as e:
            print(f"Error loading language file: {e}")
            self.languages = {}
            self.current_language = 'kr'

    def get_text(self, key: str) -> str:
        """현재 언어에 따른 텍스트 반환"""
        try:
            return self.languages[self.current_language][key]
        except:
            return key

    def change_language(self):
        """언어 변경"""
        new_language = self.language_selector.currentData()
        self.current_language = new_language
        self.btc_widget.config['language'] = new_language
        
        # UI 텍스트 업데이트
        self.update_texts()
        self.btc_widget.update_texts()  # 메인 창 UI도 업데이트
        
        # 설정 저장
        self.btc_widget.save_config()

    def update_texts(self):
        """UI 텍스트 업데이트"""
        self.setWindowTitle(self.get_text('settings'))
        self.add_button.setText(self.get_text('add_coin'))
        self.always_on_top_checkbox.setText(self.get_text('always_on_top'))
        
        # 레이블 텍스트 업데이트
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                if widget.text() == "언어" or widget.text() == "Language":
                    widget.setText(self.get_text('language'))
                elif widget.text() == "코인 검색" or widget.text() == "Search Coin":
                    widget.setText(self.get_text('search_coin'))
                elif widget.text() == "코인 선택" or widget.text() == "Select Coin":
                    widget.setText(self.get_text('select_coin'))

        # 플레이스홀더 텍스트 업데이트
        self.search_input.setPlaceholderText(self.get_text('search_coin'))

def create_layout(widget):
    layout = QVBoxLayout()

    # 설정 버튼 추가 (테이블 위에 배치)
    settings_button = QPushButton(widget.get_text('settings'), widget)
    layout.addWidget(settings_button)

    # 가격 목록 표시 (QTableWidget 사용)
    price_table = QTableWidget(widget)
    price_table.setColumnCount(2)  # 두 개의 열 (이름, 현재가)
    price_table.setHorizontalHeaderLabels([
        widget.get_text('name'),
        widget.get_text('current_price')
    ])
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

    return layout, price_table, settings_button, None