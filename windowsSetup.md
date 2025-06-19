pyinstaller --noconsole --onefile --add-data="venv\Lib\site-packages\customtkinter;customtkinter" --add-data="venv\Lib\site-packages\cv2;cv2" --add-data="venv\Lib\site-packages\torch\lib;torch\lib" --add-data="assets\logo.ico;assets" --add-data="monitor;monitor" --hidden-import=transformers --hidden-import=pystray --hidden-import=mss main.py

pip install customtkinter psutil mss opencv-python pyttsx3 transformers==4.41.2 pillow torch pyautogui pystray
