#!/usr/bin/env python3
"""
Système de logs global pour l'application
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

class GlobalLogger:
    def __init__(self):
        self.log_file = Path("session_log.txt")
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_new_session()
    
    def start_new_session(self):
        """Démarre une nouvelle session de logs"""
        if self.log_file.exists():
            self.log_file.unlink()  # Supprimer l'ancien log
        
        self.log("=" * 80)
        self.log(f"NOUVELLE SESSION DÉMARRÉE - {self.session_id}")
        self.log("=" * 80)
    
    def log(self, message, level="INFO"):
        """Ajoute un message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Afficher dans la console
        print(log_entry)
        
        # Écrire dans le fichier
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def log_error(self, message):
        """Log une erreur"""
        self.log(f"❌ {message}", "ERROR")
    
    def log_success(self, message):
        """Log un succès"""
        self.log(f"✅ {message}", "SUCCESS")
    
    def log_warning(self, message):
        """Log un avertissement"""
        self.log(f"⚠️ {message}", "WARNING")
    
    def log_info(self, message):
        """Log une information"""
        self.log(f"ℹ️ {message}", "INFO")
    
    def log_api_call(self, endpoint, method, data=None):
        """Log un appel API"""
        self.log(f"[API] {method} {endpoint}")
        if data:
            self.log(f"   Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def log_file_operation(self, operation, file_path, details=""):
        """Log une opération sur fichier"""
        self.log(f"[FILE] {operation}: {file_path}")
        if details:
            self.log(f"   {details}")
    
    def log_transcription(self, video_url, status, details=""):
        """Log une opération de transcription"""
        self.log(f"[TRANSCRIPTION] {status}: {video_url}")
        if details:
            self.log(f"   {details}")
    
    def log_scraping(self, channel_url, video_count, status):
        """Log une opération de scraping"""
        self.log(f"[SCRAPING] {status}: {channel_url} ({video_count} videos)")

# Instance globale
logger = GlobalLogger()
