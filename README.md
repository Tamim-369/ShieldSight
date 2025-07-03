# Guard - AI-Powered Content Protection

🛡️ **Guard** is an AI-powered NSFW content blocker for Windows that closes inappropriate tabs instantly — without your permission.  
Designed for focus, productivity, and digital discipline.

## 🚀 Quick Start

### For Windows Users (Recommended)
1. **Download the latest release** from [GitHub Releases](https://github.com/Tamim-369/ShieldSight/releases/tag/v1.0)
2. Extract and run the executable
3. No installation required - just click and use!

### For Developers (Source Code)
If you want to run from source or contribute:

#### Prerequisites
- Python 3.8 or higher
- Windows 10/11

#### Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/Tamim-369/ShieldSight.git
   cd ShieldSight
   ```

2. Install dependencies:
   ```bash
   pip install customtkinter psutil mss opencv-python pyttsx3 transformers==4.41.2 pillow torch pyautogui pystray fpdf
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## ✨ Features

- **✅ Auto-detects NSFW content** using AI
- **✅ Closes inappropriate tabs instantly**
- **✅ Runs silently in background**
- **✅ Customizable shortcut & sensitivity**
- **✅ Parent Mode** - Track what your child is doing
- **✅ Motivational Redirects** - Opens positive content after blocking
- **✅ Detailed Reports** - PDF reports with screenshots for parents

## 🎯 Usage

### Basic Setup
1. Launch Guard
2. Click "Start" to begin monitoring
3. Adjust sensitivity threshold in Settings if needed
4. The app runs in the background and protects you automatically

### Parent Mode
1. Enable "Parent Mode" in Settings
2. Set a password when prompted
3. Use "Get Report" to view detailed logs and screenshots
4. Reports show all detected events with timestamps

### Settings
- **Sensitivity Threshold**: Adjust detection sensitivity (0-100%)
- **Close Tab Action**: Customize the keyboard shortcut
- **Motivational URL**: Set your preferred redirect URL
- **Parent Mode**: Enable for detailed logging and reports

## 📁 Configuration

The app stores settings in `~/.Guard/config.json`:
- NSFW threshold
- Close tab shortcuts
- Motivational redirect URL
- Parent mode settings

## 🔒 Privacy & Security

- **Local Processing**: All detection happens on your device
- **No Data Collection**: No information is sent to external servers
- **Local Storage**: Screenshots and reports stored locally only
- **Password Protected**: Parent reports require password access

## 📋 Requirements

- Windows 10/11
- Python 3.8+ (for source code)
- 4GB RAM minimum
- Internet connection (for initial model download)

## 🛠️ Troubleshooting

### Common Issues
1. **App not starting**: Check if antivirus is blocking it
2. **False positives**: Adjust sensitivity threshold in settings
3. **Model not loading**: Check internet connection for first run

### Support
- Check the [releases page](https://github.com/Tamim-369/ShieldSight/releases) for latest updates
- Open an issue on GitHub for bugs
- Review settings if detection isn't working as expected

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is provided "as is" without warranty. Use at your own risk. The developers are not responsible for any misuse or damage caused by this software.

## 🙏 Acknowledgments

- Built with Python and CustomTkinter
- Uses Hugging Face transformers for content detection
- Inspired by the need for better digital wellness tools

---

**🛡️ Stay focused. Stay productive. Stay protected.**
