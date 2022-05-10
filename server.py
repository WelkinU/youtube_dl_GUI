from fastapi import FastAPI, Request, Form, File, UploadFile, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError, validator
from typing import List, Optional

import youtube_dl
import os

app = FastAPI()

@app.get("/")
def home(request: Request):
    '''
    Returns barebones HTML form allowing the user to enter a URL and download format
    '''

    html_content = '''
<head>
  <title>YouTube Downloader</title>
</head>

<h2>Enter a YouTube URL and download format</h2>
<form method="post">
  <div>
    <label>Enter YouTube URL </label>
    <input type="text" name="url" style="width:400px" placeholder="https://www.youtube.com/watch?v=C0DPdy98e4c">
    <div>
      <label>Download Format</label>
      <select name="download_format">
        <option>VideoBestQuality</option>
        <option>AudioBestQuality</option>
      </select>
    </div>
  </div>
  <button type="submit">Submit</button>
</form>
'''

    return HTMLResponse(content=html_content, status_code=200)

#mause solution for html forms: https://github.com/tiangolo/fastapi/issues/1989#issuecomment-684799715
def form_body(cls):
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(default=Form(...))
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls

@form_body
class DownloadRequest(BaseModel):
    url: str
    download_format: str

    @validator('url')
    def url_validation(cls, v):
        assert v.startswith('https://www.youtube.com/watch?v='),'Invalid YouTube URL. Expected form: https://www.youtube.com/watch?v=_______________'
        return v

    @validator('download_format')
    def download_format_validation(cls, v):
        assert v in ['VideoBestQuality','AudioBestQuality'], "Invalid download format. Allowed formats: 'VideoBestQuality','AudioBestQuality' "
        return v

    @classmethod
    def as_form(cls, url: str = Form(...), download_format: str = Form(...)):
        return cls(url=url, download_format=download_format)



@app.post("/")
async def download_video(background_tasks: BackgroundTasks, form_data: DownloadRequest = Depends(DownloadRequest)):
    full_filename = download_video(form_data.url, form_data.download_format)

    headers = {'Content-Disposition': f'attachment;filename={os.path.basename(full_filename)}'}
    response = FileResponse(full_filename, headers = headers)

    '''clean up file here as background task'''
    background_tasks.add_task(os.remove,full_filename)
    return response
    

def download_video(url, download_format, download_folder = './downloads/'):
    os.makedirs(download_folder, exist_ok = True)

    outtmpl = os.path.join(download_folder,r'%(title)s.%(ext)s')

    if download_format == 'VideoBestQuality':
        #download best video quality
        ydl_opts = {
            'format': 'best',
            'outtmpl': outtmpl,
        }
    elif download_format == 'AudioBestQuality':
        #for downloading best audio and converting to mp3
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
        #other video format: ie. "135 - some video metadata here" -> "135"
        ydl_opts = {
            'format': download_format,
            'outtmpl': outtmpl,
        }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        meta = ydl.extract_info(url, download=True)

    full_filename = os.path.join(download_folder,f"{meta['title']}.{meta['ext']}")

    return full_filename

#mause solution only works with this exception handler to capture the validation errors
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    error_message = f"Unexpected error occurred: {exc}"
    return JSONResponse(content={'message': exc.errors()}, status_code = 422)


if __name__ == '__main__':
    import uvicorn

    #make the app string equal to whatever the name of this file is
    app_str = 'server:app'
    uvicorn.run(app_str, host='localhost', port=8000, reload=True)