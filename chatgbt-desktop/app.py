# from ast import Lambda
import os
import sys 
import markdown
from datetime import datetime
from configparser import ConfigParser
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QSlider,
                            QTabWidget, QTextEdit, QTextBrowser, QMenu, QMenuBar, QSplitter,
                            QToolButton, QStatusBar,
                            QHBoxLayout, QVBoxLayout, QFormLayout, QSizePolicy
                            )

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QEvent, QThread

from PyQt6.QtGui import QIcon, QTextCursor

from chatgbt import ChatGPT
from db import ChatGPTDatabase


def current_timestamp(format_pattern='%y_%m_%d_%H%M%S'):
    return datetime.now().strftime(format_pattern)


class ChatGPTThread(QThread):
    requestFinished = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        
        self._stopped = True
        self.parent = parent
    
    def run(self):
        self._stopped = False
        response = None
        prompt_string = self.parent.message_input.toPlainText()
        
        # ensure to always insert text from the end
        text_cursor = self.parent.conversation_window.textCursor()
        
        text_cursor.movePosition(QTextCursor.MoveOperation.End)
        self.parent.conversation_window.setTextCursor(text_cursor)
        self.parent.conversation_window.insertHtml('<p style="color:#5caa00"> <strong>[User]: </strong><br>')

        self.parent.conversation_window.insertHtml(prompt_string)
        self.parent.conversation_window.insertHtml('<br')
        self.parent.conversation_window.insertHtml('<br')
        
        # make an api call to OpenAI ChatGPT model
        max_tokens = self.parent.max_tokens.value()
        temperature = float('{0:.2f}'.format(self.parent.temperature.value() / 100))
        try:
            while response is None:
                response = self.parent.chatgpt.send_request(prompt_string.strip(), max_tokens, temperature)
                if 'error' in response:
                    self.parent.status.setStyleSheet('''
                        color: red;
                        ''')
                    self.parent.clear_input()
                    self.parent.status.showMessage(response['error'].user_message)
                    return
                else:
                    self.parent .status.setStyleSheet('''
                        color: green;
                    ''')

                markdown_converted = markdown.markdown(response['content'].strip())
                
                # ensure to always isnert text from the end
                text_cursor = self.parent .conversation_window.textCursor ()
                text_cursor.movePosition(QTextCursor.MoveOperation.End)
                self.parent.conversation_window.setTextCursor(text_cursor)
                self.parent.conversation_window.insertHtml('<p style="color:#fd9620"><strong>[assistant]: </strong><br>')
                self.parent.conversation_window.insertHtml(markdown_converted)
                self.parent.conversation_window.insertHtml('<br')
                self.parent.conversation_window.insertHtml('<br')
                self.parent.status.showMessage('Tokens used: {0}'.format(response['usage' ]))
                self.requestFinished.emit()
        except Exception as e:
            print(e)
    
    
class AIAssistant(QWidget):

    def __init__(self, parent=None):
        super().__init__()
        self.chatgpt = ChatGPT(api_key)
        self.t = ChatGPTThread(self)
        
        self.layout = {}
        self.layout['main'] = QVBoxLayout()
        self.setLayout(self.layout['main'])
        
       
        
        self.init_ui() 
        self.init_set_default_settings()
        self.init_configure_signals()
        
         
    def init_ui(self):
        # add sub layout manager
        self.layout['inputs'] = QFormLayout()
        
        
        # add sliders
        self.max_tokens = QSlider(Qt.Orientation.Horizontal, minimum=10, maximum=4996,singleStep=500, pageStep=500, value=200, toolTip= 'Maxium token ChatGPT can consume')
        self.temperature = QSlider(Qt.Orientation.Horizontal, minimum=0, maximum=200, value=10, toolTip='Randomness of the response') 

        
        # organize widgets
        
        #-----------------
        
        # maximum token slider
        self.max_token_value = QLabel('0.0')
        self.layout['slider_layout'] = QHBoxLayout()
        self.layout['slider_layout'].addWidget(self.max_token_value)
        self.layout['slider_layout'].addWidget(self.max_tokens)
        self.layout['inputs'].addRow(QLabel('Token Limit:'),self.layout['slider_layout'])
        
         # temperature slider
        self.temperature_value = QLabel('0.0')
        self.layout['slider_layout2'] = QHBoxLayout()
        self.layout['slider_layout2'].addWidget(self.temperature_value)
        self.layout['slider_layout2'].addWidget(self.temperature)
        self.layout['inputs'].addRow(QLabel('Temperature:'),self.layout['slider_layout2'])
        self.layout['main'].addLayout(self.layout['inputs'])
        
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout['main'].addWidget(splitter)
        
        #conversation window
        self.conversation_window = QTextBrowser(openExternalLinks=True)
        self.conversation_window.setReadOnly(True)
        splitter.addWidget(self.conversation_window)
        
        self.intput_window = QWidget()
        self.layout['input entry'] = QHBoxLayout(self.intput_window)
        self.message_input = QTextEdit(placeholderText= 'Enter your prompt here')
        self.message_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        self.layout['input entry'].addWidget(self.message_input)
        
        # create buttons
        self.btn_submit = QPushButton('&Submit', clicked= self.post_message)


        self.btn_clear = QPushButton('&Clear', clicked=self.reset_input)
        self.layout['buttons'] = QVBoxLayout()
        self.layout['buttons'].addWidget(self.btn_submit)
        self.layout['buttons'].addWidget(self.btn_clear, alignment = Qt.AlignmentFlag.AlignTop) 
        self.layout['input entry'].addLayout(self.layout['buttons']) 
        splitter.addWidget(self.intput_window) 
        splitter.setSizes([800, 200])
       
        # add status bar
        self.status = QStatusBar ()
        self.status.setStyleSheet ('font-size: 12px; color: white;') 
        self.layout['main'].addWidget(self.status)
                
    def init_set_default_settings(self):
        # token slider
        self.max_tokens.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.max_tokens.setTickInterval(500)
        self.max_tokens.setTracking(True)
        self.max_token_value.setText('{0:,}'.format (self.max_tokens.value()))
        
        # temperature slider 
        self.temperature.setTickPosition(QSlider. TickPosition.TicksBelow) 
        self.temperature.setTickInterval(10) 
        self.temperature.setTracking (True)
        self.temperature_value.setText('{0:.2f}'.format(self.temperature.value() / 100))
        
    def init_configure_signals(self):
       
        self.max_tokens.valueChanged.connect(lambda: self.max_token_value.setText('{0: ,}'.format(self.max_tokens.value())))
        self.temperature.valueChanged.connect(lambda: self.temperature_value.setText('{0: .2f}'.format(self.temperature.value())))
        
                    
    def post_message (self) :
        if not self.message_input.toPlainText():
            self.status. showMessage('Prompt feild is empty.') 
            return 
        else:
            self.status.clearMessage()
            
        self.btn_submit.setEnabled(False)
        self.btn_submit.setText('Waiting...')
        
        self.t.requestFinished.connect(self.clear_input)
        self.t.start()
        # self.t.quit()
        
    def clear_input(self):
        self.btn_submit.setEnabled(True)
        self.btn_submit.setText('&Submit')
        self.message_input.clear()
    
    def zoom_in(self) :
        font = self.message_input.font ()
        # increase font size only when current size is less than 30 pixel
        if font.pixelSize() < 30:
            self.message_input.setStyleSheet('font-size: {0}px'.format(font.pixelSize() + 2))
            self.conversation_window.setStyleSheet('font-size: {0}px;'.format (font.pixelSize() + 2))
            
            
    def zoom_out(self):
        font = self.message_input.font()
        # decrease font size only when current size is smaller than  5
        if font.pixelSize() > 5:
            self.message_input.setStyleSheet('font-size:  {0}px'.format(font.pixelSize() - 2))
            self.conversation_window.setStyleSheet('font-size: {0}px;'.format(font.pixelSize() - 2))
                    
        
    def reset_input(self):
        self.message_input.clear()
        self.status.clearMessage() 
        
        
                
class TabManager(QTabWidget):
    # add customized signals
    plusClicked = pyqtSignal()
    
    def __init__(self, parent=None) :
        
        super().__init__(parent)
        # add tab close button
        self.setTabsClosable(True)
        
        
        # Create the add tab button and implement signals
        self.add_tab_button = QToolButton(self, text='+')
        self.add_tab_button.clicked.connect(self.plusClicked)
        self.setCornerWidget(self.add_tab_button)
        
        self.tabCloseRequested.connect(self.closeTab)
        
    def closeTab(self, tab_index):
        if self.count () == 1:
            return 
        self.removeTab(tab_index)

class AppWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.window_width, self.window_height = 720, 720
        self.setMinimumSize(self.window_width, self.window_height)
        self.setWindowIcon(QIcon(os.path.join(os.getcwd(),'robot.png')))
        self.setWindowTitle('ChatGPT AI assistant (By Jacore Baptiste) v1')
        self.setStyleSheet('''
                    QWidget { 
                        font-size: 15px;
                    }        
                    ''')
        self.tab_index_tracker = 1
        self.layout = {}
        
        self.layout['main'] = QVBoxLayout()
        self.setLayout(self.layout['main'])
        
        
        self.layout['main'].insertSpacing(0, 19)
        
        
        self.init_ui()
        self.init_configure_signal()
        self.init_menu()
        
    def init_ui(self):
        # add tab manager
        self.tab_manager = TabManager()
        
        self.layout['main'].addWidget(self.tab_manager)
        
        ai_assistant = AIAssistant()
        self.tab_manager.addTab(AIAssistant(),'Conversation #{0}'.format(self.tab_index_tracker))
        self.set_tab_focus()
    
    
    def init_menu(self):
        self.menu_bar = QMenuBar(self)
        file_menu = QMenu('&File', self.menu_bar)
        file_menu.addAction('&Save output', self.save_output)
        file_menu.addAction('S&ave log do DB', self.save_conversation_log_to_db)
        self.menu_bar.addMenu(file_menu)
        
        # view menu
        view_menu = QMenu('&View', self.menu_bar)
        view_menu.addAction('Zoom &in', self.zoom_in) 
        view_menu.addAction('Zoom &out', self.zoom_out) 
        self.menu_bar.addMenu(view_menu)  
        
    def init_configure_signal(self):
        self.tab_manager.plusClicked.connect(self.add_tab)
        
         
    def set_tab_focus(self) :
        activate_tab = self.tab_manager.currentWidget()
        # activate_tab.message_input.setFocus()
        
        
    def add_tab(self):
        self.tab_index_tracker += 1
        ai_assistant = AIAssistant()
        self.tab_manager.addTab(ai_assistant, 'Conversation #{0}'.format(self.tab_index_tracker)) 
        self.tab_manager.setCurrentIndex(self.tab_manager.count()-1) 
        self.set_tab_focus()
    
    def save_output(self):
        active_tab = self.tab_manager.currentWidget()
        conversation_window_log = active_tab.conversation_window.toPlainText()
        timestamp = current_timestamp()
        with open('{0}_Chat_Log.txt' .format(timestamp), 'w', encoding='UTF-8') as _f:
            _f.write(conversation_window_log)
        active_tab.status.showMessage('''File saved at {0}/ {1} _Chat_Log.txt'''.format(os.getcwd(), timestamp))
    
    def save_conversation_log_to_db(self) :
        timestamp = current_timestamp('%Y-%m-%d %H:%M:%S')
        active_tab = self.tab_manager.currentWidget()
        messages = str(active_tab.chatgpt.messages).replace("'","''")
        values = f"'{messages}', '{timestamp}'"
        
        
        
        db.insert_record('message_logs', 'messages, created', values)
        
    def closeEvent (self, event):
        '''
        QWidget Close event
        '''
        db.close()
        # close threads
        for window in self.findChildren(AIAssistant):
            window.t.quit()
            
        
    def zoom_in(self):
        active_tab = self.tab_manager.currentWidget()
        active_tab.zoom_in() 
        
    def zoom_out(self):
        active_tab = self.tab_manager.currentWidget()
        active_tab.zoom_out() 
    
if __name__ == '__main__':
    
    # load openai API key
    config = ConfigParser()
    config.read('api_key.ini')
    api_key = config.get('openai', 'APIKEY')
    
    
    # init ChatGPT SQLite database
    db = ChatGPTDatabase('chatgpt.db')
    db.create_table(
    'message_logs',
    '''
    message_log_no INTEGER PRIMARY KEY AUTOINCREMENT, 
    messages TEXT, 
    created TEXT
    ''')
    
    # construct application instance
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    
    
    qss_style = open(os.path.join(os.getcwd(), 'css_skins/style.qss'), 'r')
    app.setStyleSheet(qss_style.read())
    
    # launch app window
    app_window = AppWindow()
    app_window.show()
    sys.exit(app.exec())