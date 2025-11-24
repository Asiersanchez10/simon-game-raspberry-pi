#!/usr/bin/env python3
"""
Proceso: Web Server
Servidor web con FastAPI para visualización y control del juego
"""

import multiprocessing as mp
import threading
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from utils.logger import setup_logger
from utils.database import DatabaseManager

logger = setup_logger('web_server')

game_state = {
    'state': 'WAITING',
    'level': 0,
    'score': 0,
    'high_score': 0
}
state_lock = threading.Lock()


class WebServerProcess(mp.Process):
    """Proceso del servidor web"""
    
    def __init__(self, game_state_queue, web_queue, button_queue,
                 score, high_score, stop_event, game_active):
        super().__init__(name='WebServer')
        self.game_state_queue = game_state_queue
        self.web_queue = web_queue
        self.button_queue = button_queue
        self.score = score
        self.high_score = high_score
        self.stop_event = stop_event
        self.game_active = game_active
        
    def run(self):
        logger.info("Proceso WebServer iniciado")
        
        threading.Thread(target=self.update_state_worker, daemon=True).start()
        self.start_server()
    
    def update_state_worker(self):
        """Hilo que actualiza el estado del juego"""
        global game_state
        
        while not self.stop_event.is_set():
            try:
                data = self.web_queue.get(timeout=1)
                with state_lock:
                    game_state.update(data)
                    game_state['score'] = self.score.value
                    game_state['high_score'] = self.high_score.value
            except:
                pass
    
    def start_server(self):
        """Inicia el servidor FastAPI"""
        app = create_app(self.button_queue, self.score, self.high_score)
        
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        try:
            server.run()
        except Exception as e:
            logger.error(f"Error en servidor web: {e}")


def create_app(button_queue, score, high_score) -> FastAPI:
    """Crea y configura la aplicación FastAPI"""
    
    app = FastAPI(title="Juego de Simon", version="1.0.0")
    
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except:
        pass
    
    templates = Jinja2Templates(directory="templates")
    db = DatabaseManager()
    
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/api/game/state")
    async def get_game_state():
        with state_lock:
            return JSONResponse(content=game_state)
    
    @app.post("/api/game/start")
    async def start_game():
        button_data = {
            'button': 0,
            'timestamp': datetime.now().isoformat()
        }
        try:
            button_queue.put(button_data, block=False)
            return JSONResponse(content={"success": True})
        except:
            return JSONResponse(status_code=500, content={"success": False})
    
    @app.post("/api/game/button/{button_index}")
    async def press_button(button_index: int):
        if button_index not in [0, 1, 2]:
            return JSONResponse(status_code=400, content={"success": False})
        
        button_data = {
            'button': button_index,
            'timestamp': datetime.now().isoformat()
        }
        try:
            button_queue.put(button_data, block=False)
            return JSONResponse(content={"success": True, "button": button_index})
        except:
            return JSONResponse(status_code=500, content={"success": False})
    
    @app.get("/api/game/stats")
    async def get_statistics():
        stats = db.get_game_statistics()
        return JSONResponse(content=stats)
    
    @app.get("/api/game/history")
    async def get_history(limit: int = 10):
        history = db.get_game_history(limit)
        return JSONResponse(content={"games": history})
    
    @app.get("/api/game/leaderboard")
    async def get_leaderboard(limit: int = 10):
        leaderboard = db.get_leaderboard(limit)
        return JSONResponse(content={"leaderboard": leaderboard})
    
    @app.get("/health")
    async def health_check():
        return JSONResponse(content={
            "status": "healthy",
            "score": score.value,
            "high_score": high_score.value
        })
    
    return app
