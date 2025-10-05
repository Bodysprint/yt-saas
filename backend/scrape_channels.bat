@echo off
title Scrape YouTube channel -> urls.txt
echo ==============================================
echo   Scraping channels list into urls.txt
echo ==============================================
python scrape_channel_videos.py
echo.
echo Terminé ! Vérifie urls.txt
pause
