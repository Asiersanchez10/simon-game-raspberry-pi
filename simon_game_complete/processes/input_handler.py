#!/usr/bin/env python3
"""
Proceso: Input Handler
Responsable de detectar las pulsaciones de los 3 botones físicos
"""

import multiprocessing as mp
import threading
import time
from datetime import datetime
from utils.logger import setup_logger

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except (ImportError, RuntimeError):
    RASPBERRY_PI = False

logger = setup_logger('input_handler')


class ButtonMonitor:
    """Clase para monitorear los 3 botones físicos"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.BUTTON_PINS = {0: 17, 1: 27, 2: 5}
        self.last_press_times = {0: 0, 1: 0, 2: 0}
        self.debounce_delay = 0.2
        self.button_presses = []
        
        if RASPBERRY_PI:
            GPIO.setmode(GPIO.BCM)
            # Botones 0 y 1 con pull-up
            GPIO.setup(self.BUTTON_PINS[0], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.BUTTON_PINS[1], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # Botón 2 (módulo Grove) con pull-down
            GPIO.setup(self.BUTTON_PINS[2], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            logger.info("Botones GPIO inicializados")
    
    def monitor_button(self, button_index):
        """Hilo para monitorear un botón específico"""
        pin = self.BUTTON_PINS[button_index]
        
        if button_index == 2:
            # Módulo Grove - detecta HIGH
            last_state = False
            while True:
                if RASPBERRY_PI:
                    current_state = GPIO.input(pin)
                else:
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                
                if current_state and not last_state:
                    if (current_time - self.last_press_times[button_index]) > self.debounce_delay:
                        with self.lock:
                            self.button_presses.append(button_index)
                        logger.info(f"🔴 Botón {button_index} presionado")
                        self.last_press_times[button_index] = current_time
                
                last_state = current_state
                time.sleep(0.01)
        else:
            # Botones normales - detecta LOW
            last_state = True
            while True:
                if RASPBERRY_PI:
                    current_state = GPIO.input(pin)
                else:
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                
                if not current_state and last_state:
                    if (current_time - self.last_press_times[button_index]) > self.debounce_delay:
                        with self.lock:
                            self.button_presses.append(button_index)
                        logger.info(f"🔴 Botón {button_index} presionado")
                        self.last_press_times[button_index] = current_time
                
                last_state = current_state
                time.sleep(0.01)
    
    def get_button_press(self):
        """Obtiene el siguiente botón presionado"""
        with self.lock:
            if self.button_presses:
                return self.button_presses.pop(0)
            return None


class InputHandlerProcess(mp.Process):
    """Proceso de manejo de entrada de botones"""
    
    def __init__(self, button_queue, stop_event, game_active):
        super().__init__(name='InputHandler')
        self.button_queue = button_queue
        self.stop_event = stop_event
        self.game_active = game_active
        
    def run(self):
        logger.info("Proceso InputHandler iniciado")
        button_monitor = ButtonMonitor()
        
        # Iniciar hilos de monitoreo
        threads = []
        for button_index in range(3):
            thread = threading.Thread(
                target=button_monitor.monitor_button,
                args=(button_index,),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        logger.info(f"Iniciados {len(threads)} hilos de monitoreo")
        
        try:
            while not self.stop_event.is_set():
                button = button_monitor.get_button_press()
                
                if button is not None:
                    button_data = {
                        'button': button,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    try:
                        self.button_queue.put(button_data, block=False)
                    except:
                        pass
                
                time.sleep(0.01)
        finally:
            if RASPBERRY_PI:
                GPIO.cleanup()
            logger.info("Proceso InputHandler finalizado")
