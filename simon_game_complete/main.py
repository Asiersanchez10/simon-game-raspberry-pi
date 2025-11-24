#!/usr/bin/env python3
"""
Juego de Simon con Raspberry Pi
Proyecto de Arquitectura de Computadores - Universidad de Deusto
Curso 2025-2026

Este sistema implementa paralelismo mediante múltiples procesos e hilos
para un juego interactivo de secuencias de luces y botones.

Autores: [Tu nombre y equipo]
Fecha: Diciembre 2024
"""

import multiprocessing as mp
import signal
import sys
import time
from datetime import datetime

from processes.game_controller import GameControllerProcess
from processes.input_handler import InputHandlerProcess
from processes.web_server import WebServerProcess
from utils.logger import setup_logger

logger = setup_logger('main')


class SimonGameSystem:
    """Clase principal que gestiona todos los procesos del juego"""
    
    def __init__(self):
        # Colas para comunicación entre procesos
        self.game_state_queue = mp.Queue(maxsize=100)
        self.button_queue = mp.Queue(maxsize=50)
        self.web_queue = mp.Queue(maxsize=100)
        
        # Variables compartidas entre procesos
        self.score = mp.Value('i', 0)  # Puntuación actual
        self.high_score = mp.Value('i', 0)  # Récord histórico
        
        # Eventos para sincronización
        self.stop_event = mp.Event()  # Señal de apagado
        self.game_active = mp.Event()  # Indica si hay partida activa
        
        # Lista de procesos activos
        self.processes = []
        
        logger.info("Sistema de Juego Simon inicializado")
        
    def signal_handler(self, signum, frame):
        """Manejador de señales para apagado limpio"""
        logger.info(f"Señal {signum} recibida. Iniciando apagado del sistema...")
        self.stop_event.set()
        
    def start_processes(self):
        """Inicia todos los procesos del sistema"""
        try:
            # Proceso 1: Controlador del juego (lógica y LEDs)
            game_controller = GameControllerProcess(
                game_state_queue=self.game_state_queue,
                button_queue=self.button_queue,
                web_queue=self.web_queue,
                score=self.score,
                high_score=self.high_score,
                stop_event=self.stop_event,
                game_active=self.game_active
            )
            game_controller.start()
            self.processes.append(game_controller)
            logger.info("Proceso GameController iniciado")
            
            # Proceso 2: Manejador de entrada de botones
            input_handler = InputHandlerProcess(
                button_queue=self.button_queue,
                stop_event=self.stop_event,
                game_active=self.game_active
            )
            input_handler.start()
            self.processes.append(input_handler)
            logger.info("Proceso InputHandler iniciado")
            
            # Proceso 3: Servidor Web
            web_server = WebServerProcess(
                game_state_queue=self.game_state_queue,
                web_queue=self.web_queue,
                button_queue=self.button_queue,
                score=self.score,
                high_score=self.high_score,
                stop_event=self.stop_event,
                game_active=self.game_active
            )
            web_server.start()
            self.processes.append(web_server)
            logger.info("Proceso WebServer iniciado")
            
            logger.info("Todos los procesos iniciados correctamente")
            
        except Exception as e:
            logger.error(f"Error al iniciar procesos: {e}")
            self.stop_event.set()
            raise
            
    def monitor_processes(self):
        """Monitorea el estado de los procesos"""
        try:
            while not self.stop_event.is_set():
                # Verificar que todos los procesos estén vivos
                for process in self.processes:
                    if not process.is_alive():
                        logger.warning(f"Proceso {process.name} ha terminado inesperadamente")
                        self.stop_event.set()
                        break
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Interrupción del usuario detectada")
            self.stop_event.set()
            
    def stop_processes(self):
        """Detiene todos los procesos de forma ordenada"""
        logger.info("Deteniendo procesos...")
        self.stop_event.set()
        
        # Esperar a que los procesos terminen
        timeout = 10
        for process in self.processes:
            process.join(timeout=timeout)
            if process.is_alive():
                logger.warning(f"Proceso {process.name} no respondió, terminando forzadamente")
                process.terminate()
                process.join(timeout=2)
                
        logger.info("Todos los procesos detenidos")
        
    def run(self):
        """Método principal para ejecutar el sistema"""
        # Configurar manejadores de señales
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            logger.info("="*60)
            logger.info("🎮 JUEGO DE SIMON - RASPBERRY PI")
            logger.info(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*60)
            
            # Iniciar todos los procesos
            self.start_processes()
            
            # Mostrar información del sistema
            logger.info(f"Número de procesos activos: {len(self.processes)}")
            logger.info(f"Servidor web disponible en: http://localhost:8000")
            logger.info("🎮 ¡El juego está listo!")
            logger.info("Presiona cualquier botón físico para iniciar")
            logger.info("O accede a http://localhost:8000 desde el navegador")
            logger.info("Presiona Ctrl+C para detener el sistema")
            
            # Monitorear procesos
            self.monitor_processes()
            
        except Exception as e:
            logger.error(f"Error crítico en el sistema: {e}", exc_info=True)
            
        finally:
            # Limpieza y apagado
            self.stop_processes()
            logger.info("Sistema apagado correctamente")


def main():
    """Función principal"""
    game_system = SimonGameSystem()
    game_system.run()


if __name__ == "__main__":
    main()
