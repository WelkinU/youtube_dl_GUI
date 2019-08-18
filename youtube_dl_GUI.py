import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

import threading
import youtube_dl

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 100

        self.default_video_formats_menu_items=['Video - Best Quality','Audio Only - Best Quality']

        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('YouTube DL GUI')
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar().showMessage('Welcome to YouTube Downloader GUI!') #initialize status bar

        #create URL entry buttons and entry textbox
        urlEntryLabel = QLabel('Enter URL:')
        self.urlEntryText = QLineEdit()
        self.urlEntryText.setPlaceholderText('Enter YouTube URL')
        self.urlEntryText.setText('https://www.youtube.com/watch?v=C0DPdy98e4c') #set default video to download
        #self.urlEntryText.textChanged.connect(self.updateVideoFormats) #set up callback to update video formats when URL is changed

        #create output folder button and entry textbox
        outputFolderButton = QPushButton('Select Output Folder')
        outputFolderButton.setToolTip('Select output folder')
        outputFolderButton.clicked.connect(self.updateOutputFolder)
        self.outputEntryText = QLineEdit()
        self.outputEntryText.setPlaceholderText('Enter Download Folder')
        self.outputEntryText.setText(get_default_download_path()) #set default output folder to be downloads folder

        #add combobox for video download format and autodetect formats button
        detectFormatsButton = QPushButton('Detect All Formats')
        detectFormatsButton.clicked.connect(self.updateVideoFormats)

        self.videoFormatCombobox = QComboBox()
        self.populateVideoFormatCombobox(self.default_video_formats_menu_items) #set default values for format select combobox

        #add download button
        downloadButton = QPushButton('Download')
        downloadButton.clicked.connect(self.downloadVideo_callback)

        #create grid layout
        layout = QGridLayout()

        #add widgets to the layout
        layout.addWidget(urlEntryLabel,1,0)
        layout.addWidget(self.urlEntryText,1,1)
        layout.addWidget(outputFolderButton,2,0)
        layout.addWidget(self.outputEntryText,2,1)
        layout.addWidget(detectFormatsButton,3,0)
        layout.addWidget(self.videoFormatCombobox,3,1)
        layout.addWidget(downloadButton,5,0)

        #add grid layout as central widget for main window
        main_widget=QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.show()

    def downloadVideo_callback(self):
        ''' Callback for the "Download Video" button
        '''

        def downloadVideo_thread_helper(self,ydl_opts):
            '''Download the video. Meant to be called in a background daemon thread
            '''
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.urlEntryText.text()])

            self.statusBar().showMessage('Downloading Video... Done.')



        outtmpl = os.path.join(self.outputEntryText.text(),r'%(title)s.%(ext)s')
        if self.videoFormatCombobox.currentText() == self.default_video_formats_menu_items[0]:
            ydl_opts = {
                'format': 'best',
                'outtmpl': outtmpl,
            }
        elif self.videoFormatCombobox.currentText() == self.default_video_formats_menu_items[1]:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            video_format = self.videoFormatCombobox.currentText()[0:self.videoFormatCombobox.currentText().find('-')-1]
            ydl_opts = {
                'format': video_format,
                'outtmpl': outtmpl,
            }

        thread = threading.Thread(target = downloadVideo_thread_helper, args = (self,ydl_opts,) )
        thread.daemon = True
        thread.start()

        self.statusBar().showMessage('Downloading Video...')
        
        

    def updateVideoFormats(self):
        def getVideoFormats_thread_helper(self,url):
            self.options = {
                            'noplaylist': True,          # only download single song, not playlist
                            }
            with youtube_dl.YoutubeDL(self.options) as ydl:
                meta = ydl.extract_info(url, download=False)
                formats = meta.get('formats', [meta])

            #add formats to combobox
            item_list=self.default_video_formats_menu_items
            item_list.extend([ f['format'] +' ' +f['ext'] for f in formats])
            self.populateVideoFormatCombobox(item_list)
            self.statusBar().showMessage('Finished Downloading Video Formats')

        url = self.urlEntryText.text()
        #check if is valid url
        if not url.startswith('https://www.youtube.com/watch?'):
            #invalid url
            self.populateVideoFormatCombobox(self.default_video_formats_menu_items)
            return

        else:
            self.statusBar().showMessage('Downloading Video Formats')
            thread = threading.Thread(target = getVideoFormats_thread_helper, args = (self,url,) )
            thread.daemon = True
            thread.start()
            
    def populateVideoFormatCombobox(self,labels):
        self.videoFormatCombobox.clear()

        for label in labels:
            self.videoFormatCombobox.addItem(label)

    @pyqtSlot()
    def updateOutputFolder(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        print(file)

        if len(file)>0:
            self.outputEntryText.setText(file)
        else:
            self.statusBar().showMessage('Select a folder.')

def get_default_download_path():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = App()
    sys.exit(app.exec_())