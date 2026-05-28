@echo off
set BACKUP_DIR=D:\RAG_Backups\%date:~0,4%%date:~5,2%%date:~8,2%
mkdir %BACKUP_DIR%

echo 备份知识库...
xcopy D:\helen\workspace\repositories\MyKnowledge %BACKUP_DIR%\MyKnowledge /E /I

echo 备份向量库...
xcopy D:\helen\workspace\repositories\RAG_System\chroma_db %BACKUP_DIR%\chroma_db /E /I

echo 备份完成！保存位置: %BACKUP_DIR%
pause