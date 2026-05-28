@echo off
echo ========================================
echo   个人知识库 RAG 系统
echo ========================================
echo 1. 启动 Web 界面 (Ollama 本地版)
echo 2. 启动 Web 界面 (DeepSeek API 版)
echo 3. 启动自动同步监听
echo 4. 手动重建索引
echo 5. 退出
echo ========================================

set /p choice="请选择 (1-5): "

if "%choice%"=="1" goto ollama
if "%choice%"=="2" goto deepseek
if "%choice%"=="3" goto sync
if "%choice%"=="4" goto index
if "%choice%"=="5" exit

:ollama
cd /d D:\helen\workspace\repositories\RAG_System
streamlit run app.py
goto end

:deepseek
cd /d D:\helen\workspace\repositories\RAG_System
streamlit run app_deepseek.py
goto end

:sync
cd /d D:\helen\workspace\repositories\RAG_System
python auto_sync.py
goto end

:index
cd /d D:\helen\workspace\repositories\RAG_System
python index_knowledge.py
pause
goto end

:end