#!/usr/bin/env python3
"""
Gestor de base de datos para el juego de Simon
"""

import sqlite3
import threading
from datetime import datetime


class DatabaseManager:
    """Gestor de base de datos SQLite para guardar puntuaciones"""
    
    def __init__(self, db_path='database/simon_game.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos y tabla"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    level INTEGER NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_score 
                ON game_results(score DESC)
            ''')
            
            conn.commit()
            conn.close()
    
    def save_game_result(self, score, level):
        """Guarda el resultado de una partida"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO game_results (timestamp, score, level)
                    VALUES (?, ?, ?)
                ''', (datetime.now().isoformat(), score, level))
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error guardando resultado: {e}")
    
    def get_leaderboard(self, limit=10):
        """Obtiene el ranking de mejores puntuaciones"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT score, level, timestamp
                    FROM game_results
                    ORDER BY score DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [{'score': r[0], 'level': r[1], 'timestamp': r[2]} 
                        for r in rows]
            except:
                return []
    
    def get_game_history(self, limit=10):
        """Obtiene el histórico de partidas"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT score, level, timestamp
                    FROM game_results
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [{'score': r[0], 'level': r[1], 'timestamp': r[2]} 
                        for r in rows]
            except:
                return []
    
    def get_game_statistics(self):
        """Obtiene estadísticas generales"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_games,
                        MAX(score) as best_score,
                        MAX(level) as best_level,
                        AVG(score) as avg_score
                    FROM game_results
                ''')
                
                row = cursor.fetchone()
                conn.close()
                
                return {
                    'total_games': row[0] or 0,
                    'best_score': row[1] or 0,
                    'best_level': row[2] or 0,
                    'avg_score': round(row[3] or 0, 1)
                }
            except:
                return {
                    'total_games': 0,
                    'best_score': 0,
                    'best_level': 0,
                    'avg_score': 0
                }
