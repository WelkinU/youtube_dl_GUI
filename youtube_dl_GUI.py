import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

import threading
import youtube_dl
import json

GUI_STATE_JSON_FILE = './youtube_dl_GUI_state.json'

class App(QMainWindow):

    def __init__(self):
        super().__init__()

        gui_state = self.loadGUIState() #load GUI state from file, load default state if save file not found
        self.download_folder_list = gui_state['DownloadFolderList']
        self.default_video_formats_menu_items=['Video - Best Quality','Audio Only - Best Quality','Detect All Available Formats']
        
        #initialize window dimensions
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 100
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
        self.urlEntryText.textChanged.connect(self.resetVideoFormats) #set up callback to update video formats when URL is changed

        #create output folder button and entry textbox
        outputFolderButton = QPushButton('Select Output Folder')
        outputFolderButton.setToolTip('Select output folder')
        outputFolderButton.clicked.connect(self.updateOutputFolder)
        self.outputEntryCombobox = QComboBox()
        self.outputEntryCombobox.setEditable(True)

        for item in self.download_folder_list:
            self.outputEntryCombobox.addItem(item) #set default output folder to be downloads folder
        #self.outputEntryCombobox.editTextChanged[str].connect(self.downloadTextChanged)

        #add combobox for video download format and detect formats button
        detectFormatsLabel = QLabel('Download Format:')

        self.videoFormatCombobox = QComboBox()
        self.populateVideoFormatCombobox(self.default_video_formats_menu_items) #set default values for format select combobox
        self.videoFormatCombobox.activated[str].connect(self.videoFormatChange)
        

        #add download button
        downloadButton = QPushButton('Download')
        downloadButton.clicked.connect(self.downloadVideo_callback)

        #create grid layout
        layout = QGridLayout()

        #add widgets to the layout
        layout.addWidget(urlEntryLabel,1,0)
        layout.addWidget(self.urlEntryText,1,1)
        layout.addWidget(outputFolderButton,2,0)
        layout.addWidget(self.outputEntryCombobox,2,1)
        layout.addWidget(detectFormatsLabel,3,0)
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

        #make sure a valid output directory was entered
        if not os.path.isdir(self.outputEntryCombobox.currentText()):
            self.statusBar().showMessage('Invalid download directory!')
            return

        #make sure the Download Folder List combobox is populated with the latest entry
        #this covers the case where the user uses the edittext portion of the combobox
        self.addItemToDownloadsCombobox(self.outputEntryCombobox.currentText())

        #set output path/format
        outtmpl = os.path.join(self.outputEntryCombobox.currentText(),r'%(title)s.%(ext)s')

        #create the youtube downloader options based on video format combobox selection
        if self.videoFormatCombobox.currentText() == self.default_video_formats_menu_items[0]:
            #download best video quality
            ydl_opts = {
                'format': 'best',
                'outtmpl': outtmpl,
            }
        elif self.videoFormatCombobox.currentText() == self.default_video_formats_menu_items[1]:
            #for downloading best audio and converting to mp3
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192', #not actually best quality...
                }],
            }
        else:
            #grab video format from the dropdown string: ie. "135 - some video metadata here" -> "135"
            video_format = self.videoFormatCombobox.currentText()[0:self.videoFormatCombobox.currentText().find('-')-1]
            ydl_opts = {
                'format': video_format,
                'outtmpl': outtmpl,
            }

        #download the video in daemon thread
        self.statusBar().showMessage('Downloading Video...') #update status bar
        thread = threading.Thread(target = downloadVideo_thread_helper, args = (self,ydl_opts,) )
        thread.daemon = True
        thread.start()

    def updateVideoFormats(self):
        ''' Grabs the list of available video formats in background thread and populates
        video format combobox with results when complete.
        '''

        def getVideoFormats_thread_helper(self,url):
            ''' Grabs the available video formats. Intended to be run as background thread.
            '''
            self.options = {
                            'noplaylist': True, # only download single song, not playlist
                            }
            with youtube_dl.YoutubeDL(self.options) as ydl:
                meta = ydl.extract_info(url, download=False)
                formats = meta.get('formats', [meta])

            #add formats to combobox
            item_list=self.default_video_formats_menu_items[0:2]
            item_list.extend([ f['format'] +' ' +f['ext'] for f in formats])
            self.populateVideoFormatCombobox(item_list)
            self.statusBar().showMessage('Finished Downloading Video Formats')
            self.videoFormatCombobox.setCurrentIndex(0)

        url = self.urlEntryText.text()
        #check if is valid url
        #should probably be reworked to be compatible with non-YouTube websites
        if not url.startswith('https://www.youtube.com/watch?'): 
            #invalid url
            self.populateVideoFormatCombobox(self.default_video_formats_menu_items)
            return

        else:
            #valid url - fetch the video formats in background daemon thread
            self.statusBar().showMessage('Downloading Video Formats')
            thread = threading.Thread(target = getVideoFormats_thread_helper, args = (self,url,) )
            thread.daemon = True
            thread.start()

    def videoFormatChange(self,text):
        if text == self.default_video_formats_menu_items[2]:
            #detect video formats was selected

            #update statusbar to let user know something is happening
            self.statusBar().showMessage('Loading available formats...')
            #update video formats
            self.updateVideoFormats()
    
    def populateVideoFormatCombobox(self,labels):
        '''Populate the video format combobox with video formats. Clear the previous labels.

        labels {list} -- list of strings representing the video format combobox options
        '''
        self.videoFormatCombobox.clear()

        for label in labels:
            self.videoFormatCombobox.addItem(label)

    def resetVideoFormats(self):
        idx = self.videoFormatCombobox.currentIndex()

        self.populateVideoFormatCombobox(self.default_video_formats_menu_items)

        #preserve combobox index if possible
        if idx>1:
            self.videoFormatCombobox.setCurrentIndex(0)
        else:
            self.videoFormatCombobox.setCurrentIndex(idx)

    @pyqtSlot()
    def updateOutputFolder(self):
        ''' Callback for "Update Output Folder" button. Allows user to select
        output directory via standard UI.
        '''
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if len(file)>0:
            self.addItemToDownloadsCombobox(file)
        else:
            self.statusBar().showMessage('Select a folder!')

    def downloadTextChanged(self,text):
        #function not used right now
        if text not in self.download_folder_list and os.path.isdir(text):
            self.addItemToDownloadsCombobox(text)

    def addItemToDownloadsCombobox(self,text):
        if text not in self.download_folder_list:
            #if it's not in the list, add it to the list
            self.download_folder_list = [text]+self.download_folder_list
        else:
            #if it's in the list already, move it to the top of the list
            self.download_folder_list = [text]+[folder for folder in self.download_folder_list if not folder == text]

        #maximum download folder history of 5
        if len(self.download_folder_list)>5:
            self.download_folder_list = self.download_folder_list[0:6]

        #update the combobox
        self.outputEntryCombobox.clear()
        for item in self.download_folder_list:
            self.outputEntryCombobox.addItem(item)

        self.outputEntryCombobox.setCurrentIndex(0) #reset index - just in case

    def saveGUIState(self):
        save_dict= {'DownloadFolderList': self.download_folder_list,
                    }

        with open(GUI_STATE_JSON_FILE,'w') as file:
            json.dump(save_dict,file)

    def loadGUIState(self):
        if os.path.isfile(GUI_STATE_JSON_FILE):
            with open(GUI_STATE_JSON_FILE, 'r') as file:
                save_data = json.load(file)

            if isinstance(save_data['DownloadFolderList'],str):
                save_data['DownloadFolderList'] = [save_data['DownloadFolderList']] #convert to list

        else:
            save_data = {'DownloadFolderList': [get_default_download_path()],
                        }

        return save_data

    def closeEvent(self, event):
        '''This function gets called when the user closes the GUI. It saves the GUI state to the json file
        GUI_STATE_JSON_FILE.
        '''
        self.saveGUIState()
        if True:
            event.accept() # let the window close
        else:
            event.ignore()


def get_default_download_path():
    """Returns the path for the "Downloads" folder on Linux or Windows.
    Used as default directory for videos to be saved to.
    #From: https://stackoverflow.com/questions/35851281/python-finding-the-users-downloads-folder
    """
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