# youtube_dl_GUI

In my (limited) travels on the internet, I couldn't find an easy, reliable, and safe way to download YouTube videos / music. youtube_dl_GUI is intended to fill that void as a basic interface for downloading YouTube videos/audio tracks/playlists that can be easily shared and used by non-programmers. In the future, I will freeze the build into a standalone .exe file for easy sharing / use.

![](images/window.png)

### Usage
1. Enter the URL of the video you want to download into the top "URL" textbox.
1. Then enter the folder to save the video to in the "Output Folder" textbox. 
1. Next choose the video format
    1. To download the highest quality of video, select the video format `Video - Best Quality`
    1. If you only want the audio (saved as .mp3), select `Audio Only - Best Quality`
    1. If you want another video format, click the `Detect All Formats` button, which will fetch the available video formats and populate the dropdown with the available formats.
1. Click the Download button.

### Developer Setup
Just set up Python3 with libraries PyQT5 and youtube_dl (`pip install youtube-dl`), and you should be able to run the code.

### Troubleshooting
Make sure you have the latest version of youtube-dl! Use `pip install --upgrade youtube-dl`in the command line.

### TODO:
- [ ] Build standalone .exe file, equivalent for Mac
- [ ] Additional support for handling YouTube playlists
- [ ] Improve user interface for video formats other than best video/audio.
