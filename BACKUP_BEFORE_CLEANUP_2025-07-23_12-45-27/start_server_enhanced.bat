@echo off
echo ========================================
echo  🚀 Trading Optimization Web Server
echo ========================================
echo.
echo 📁 Directory: %cd%
echo 🐍 Using Python: C:/Users/aio/OneDrive/Desktop/DATA TRADINGVIEW/backtest/BTC/.venv_new/Scripts/python.exe
echo.
echo ✅ PowerShell Execution Policy: FIXED (RemoteSigned)
echo ✅ Python Syntax Error: FIXED (duplicate function definitions)
echo ✅ Required packages: Flask, Pandas, Numpy - INSTALLED
echo.
echo 🌐 Starting server at: http://localhost:5000
echo 📊 Access enhanced interface at: http://localhost:5000
echo 📈 Access classic interface at: http://localhost:5000/classic
echo 📋 Monitor progress at: http://localhost:5000/status
echo.
echo ⏹️ Press Ctrl+C to stop the server
echo ========================================
echo.
"C:/Users/aio/OneDrive/Desktop/DATA TRADINGVIEW/backtest/BTC/.venv_new/Scripts/python.exe" web_app.py
pause
