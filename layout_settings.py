from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
    QLineEdit, QTableWidget, QTableWidgetItem, QSlider, 
    QCheckBox, QHeaderView, QDialog, QLabel, QWidget
)
from PyQt5.QtCore import Qt
import json

class SettingsDialog(QDialog):
    def __init__(self, parent=None, btc_widget=None):
        super().__init__(parent)
        self.btc_widget = btc_widget
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)  # 프레임 제거
        self.languages = {}  # 언어 데이터 저장용
        self.load_language()  # 언어 파일 먼저 로드
        
        # 설정창 크기 고정
        self.setFixedSize(300, 405)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # 타이틀 바 추가
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
        
        # 타이틀 레이블
        title_label = QLabel(self.get_text('settings'))
        title_label.setStyleSheet("color: #EAECEF; font-weight: bold; font-size: 14px;")
        
        # 닫기 버튼
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
        
        # 메인 레이아웃의 상하 여백을 줄임
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # 기존 설정 레이아웃을 새로운 컨테이너에 추가
        settings_container = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        # 언어 선택 콤박스 추가
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

        # 창 크기 조절 입력 필드 레이아웃 수정
        size_container = QWidget()
        size_layout = QHBoxLayout()  # HBoxLayout으로 변경하여 한 줄에 표시
        
        # 너비 입력
        width_label = QLabel("W:")  # Width 레이블을 W로 변경
        self.width_input = QLineEdit()
        self.width_input.setFixedWidth(60)  # 입력 필드 폭 제한
        self.width_input.setText(str(btc_widget.window_size['width']))
        size_layout.addWidget(width_label)
        size_layout.addWidget(self.width_input)
        size_layout.addWidget(QLabel("px"))  # px 텍스트 추가
        
        # 높이 입력
        height_label = QLabel("H:")  # Height 레이블을 H로 변경
        self.height_input = QLineEdit()
        self.height_input.setFixedWidth(60)  # 입력 필드 폭 제한
        self.height_input.setText(str(btc_widget.window_size['height']))
        size_layout.addWidget(height_label)
        size_layout.addWidget(self.height_input)
        size_layout.addWidget(QLabel("px"))  # px 텍스트 추가
        
        # 레이아웃에 추가
        size_container.setLayout(size_layout)
        settings_layout.addWidget(size_container)

        # Apply Size 버튼 생성
        self.apply_size_button = QPushButton(self.get_text('apply_size'), self)  # 초기화 시 텍스트 설정
        self.apply_size_button.setObjectName("apply_size_button")  # 객체 이름 설정
        self.apply_size_button.clicked.connect(self.apply_window_size)
        settings_layout.addWidget(self.apply_size_button)  # Apply 버튼 추가
        
        # 설정 레이아웃을 메인 레이아웃에 추가
        settings_container.setLayout(settings_layout)
        main_layout.addWidget(settings_container)
        
        self.setLayout(main_layout)
        
        # 이벤트 연결
        self.language_selector.currentIndexChanged.connect(self.change_language)
        self.search_input.textChanged.connect(self.filter_coins)
        self.add_button.clicked.connect(self.add_coin)
        
        # 슬라이더와 체크박스 이벤트 연결
        self.opacity_slider.valueChanged.connect(self.btc_widget.change_opacity)  # 투명도 변경
        self.always_on_top_checkbox.stateChanged.connect(self.btc_widget.toggle_always_on_top)  # 항상 위에 표시
        
        # 초 코인 목록 로드
        self.load_coins()
        
        # 설정 값 로드
        self.load_settings()
        
        # 현재 언어 설정을 콤보박스에 반영
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

    def load_language(self) -> None:
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
        if new_language != self.current_language:
            print(f"Changing language to: {new_language}")  # 디버깅용
            self.current_language = new_language
            self.btc_widget.config['language'] = new_language
            self.btc_widget.languages = self.languages  # 메인 위젯의 언어 데이터도 업데이트
            
            # UI 텍스트 업데이트
            self.update_texts()
            self.btc_widget.update_texts()
            
            # 설정 저장
            self.btc_widget.save_config()

    def update_texts(self) -> None:
        """UI 텍스트 업데이트"""
        # 타이틀 레이블 업데이트
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setText(self.get_text('settings'))
        
        # 버튼 텍스트 업데이트
        self.add_button.setText(self.get_text('add_coin'))
        self.always_on_top_checkbox.setText(self.get_text('always_on_top'))
        # Apply Size 버튼 텍스트 업데이트
        apply_size_btn = self.findChild(QPushButton, "apply_size_button")  # Apply Size 버튼을 찾음
        if apply_size_btn:
            apply_size_btn.setText(self.get_text('apply_size'))  # 언어에 맞게 텍스트 업데이트
        
        # 검색창 플레이스홀더 업데이트
        self.search_input.setPlaceholderText(self.get_text('search_coin'))
        
        # 레이블 텍스트 업데이트
        for widget in self.findChildren(QLabel):
            if widget.text() in ["언어", "Language"]:
                widget.setText(self.get_text('language'))
            elif widget.text() in ["코인 검색", "Search Coin"]:
                widget.setText(self.get_text('search_coin'))
            elif widget.text() in ["코인 선택", "Select Coin"]:
                widget.setText(self.get_text('select_coin'))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def apply_window_size(self):
        """창 크기 적용"""
        try:
            width = int(self.width_input.text())
            height = int(self.height_input.text())
            if width > 0 and height > 0:
                self.btc_widget.resize_window(width, height)
        except ValueError:
            # 잘못된 입력 처리
            self.width_input.setText(str(self.btc_widget.window_size['width']))
            self.height_input.setText(str(self.btc_widget.window_size['height']))

def create_layout(widget):
    layout = QVBoxLayout()
    layout.setContentsMargins(1, 1, 1, 1)
    layout.setSpacing(0)

    # 상단 바 생성
    top_bar = QWidget()
    top_bar.setStyleSheet("background-color: #2B3139;")
    top_bar_layout = QHBoxLayout()
    top_bar_layout.setContentsMargins(5, 5, 5, 5)
    
    # 설정 버튼 추가
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

    # 가격 목록 표시
    price_table = QTableWidget(widget)
    price_table.setColumnCount(2)
    
    # 헤더 완전히 제거
    price_table.horizontalHeader().hide()
    price_table.verticalHeader().hide()
    price_table.horizontalHeader().setVisible(False)
    price_table.horizontalHeader().setHighlightSections(False)
    
    # 테이블 설정
    price_table.setShowGrid(False)
    price_table.setFrameShape(QTableWidget.NoFrame)
    price_table.setSelectionBehavior(QTableWidget.SelectRows)
    price_table.setSelectionMode(QTableWidget.SingleSelection)
    
    # 컬럼 너비 설정
    price_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    price_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    
    layout.addWidget(price_table)

    return layout, price_table, settings_button, None