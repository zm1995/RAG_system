@echo off
echo ========================================
echo   统一知识库 RAG 系统
echo ========================================
echo 1. 启动 Web 界面 (DeepSeek 问答)
echo 2. 全量重建向量索引 (Obsidian + AI 助教)
echo 3. 启动 Obsidian 自动同步监听
echo 4. 生成 AI 助教导出 JSON
echo 5. 退出
echo ========================================

set /p choice="请选择 (1-5): "

if "%choice%"=="1" goto app
if "%choice%"=="2" goto index
if "%choice%"=="3" goto sync
if "%choice%"=="4" goto export
if "%choice%"=="5" exit

:app
cd /d %~dp0..
call venv\Scripts\activate.bat
set PYTHONUTF8=1
streamlit run web\app.py
goto end

:index
cd /d %~dp0..
call venv\Scripts\activate.bat
python src\vector_db\index_unified.py
pause
goto end

:sync
cd /d %~dp0..
call venv\Scripts\activate.bat
python scripts\auto_sync.py
goto end

:export
cd /d %~dp0..
call venv\Scripts\activate.bat
python -m src.pipelines.generate_export --source all
pause
goto end

:end
