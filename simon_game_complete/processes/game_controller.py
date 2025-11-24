#!/usr/bin/env python3
"""
Proceso: Game Controller
Responsable de la lógica del juego Simon y control de LEDs
"""

import multiprocessing as mp
import threading
import time
import random
from datetime import datetime
from utils.logger import setup_logger
from utils.database import DatabaseManager

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except (ImportError, RuntimeError):
    RASPBERRY_PI = False
    print("⚠️  Modo simulación: GPIO no disponible")

logger = setup_logger('game_controller')


class LEDController:
    """Clase para gestionar los 3 LEDs del juego"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.LED_PINS = {0: 22, 1: 23, 2: 24}
        self.states = {0: False, 1: False, 2: False}
        
        if RASPBERRY_PI:
            GPIO.setmode(GPIO.BCM)
            for pin in self.LED_PINS.values():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            logger.info("LEDs GPIO inicializados")
    
    def turn_on(self, led_index):
        with self.lock:
            if led_index in self.LED_PINS:
                self.states[led_index] = True
                if RASPBERRY_PI:
                    GPIO.output(self.LED_PINS[led_index], GPIO.HIGH)
    
    def turn_off(self, led_index):
        with self.lock:
            if led_index in self.LED_PINS:
                self.states[led_index] = False
                if RASPBERRY_PI:
                    GPIO.output(self.LED_PINS[led_index], GPIO.LOW)
    
    def turn_off_all(self):
        for led_index in self.LED_PINS.keys():
            self.turn_off(led_index)
    
    def flash(self, led_index, duration=0.5):
        self.turn_on(led_index)
        time.sleep(duration)
        self.turn_off(led_index)
    
    def celebration_sequence(self):
        for _ in range(3):
            for led in [0, 1, 2]:
                self.turn_on(led)
                time.sleep(0.1)
                self.turn_off(led)
    
    def game_over_sequence(self):
        for _ in range(5):
            for led in [0, 1, 2]:
                self.turn_on(led)
            time.sleep(0.2)
            self.turn_off_all()
            time.sleep(0.2)
    
    def cleanup(self):
        self.turn_off_all()
        if RASPBERRY_PI:
            GPIO.cleanup()


class GameLogic:
    """Lógica del juego Simon"""
    
    def __init__(self):
        self.sequence = []
        self.player_input = []
        self.level = 0
        self.state = 'WAITING'
        self.lock = threading.Lock()
    
    def start_new_game(self):
        with self.lock:
            self.sequence = []
            self.player_input = []
            self.level = 0
            self.state = 'SHOWING'
            self.add_to_sequence()
            logger.info("🎮 Nuevo juego iniciado")
    
    def add_to_sequence(self):
        new_led = random.randint(0, 2)
        self.sequence.append(new_led)
        self.level += 1
    
    def check_input(self, button_index):
        with self.lock:
            self.player_input.append(button_index)
            current_pos = len(self.player_input) - 1
            
            if self.player_input[current_pos] != self.sequence[current_pos]:
                self.state = 'LOSE'
                return 'GAME_OVER'
            
            if len(self.player_input) == len(self.sequence):
                self.player_input = []
                self.state = 'WIN'
                return 'WIN_LEVEL'
            
            return 'CORRECT'
    
    def next_level(self):
        with self.lock:
            self.add_to_sequence()
            self.player_input = []
            self.state = 'SHOWING'
    
    def reset(self):
        with self.lock:
            self.sequence = []
            self.player_input = []
            self.level = 0
            self.state = 'WAITING'


class GameControllerProcess(mp.Process):
    """Proceso principal del controlador del juego"""
    
    def __init__(self, game_state_queue, button_queue, web_queue, 
                 score, high_score, stop_event, game_active):
        super().__init__(name='GameController')
        self.game_state_queue = game_state_queue
        self.button_queue = button_queue
        self.web_queue = web_queue
        self.score = score
        self.high_score = high_score
        self.stop_event = stop_event
        self.game_active = game_active
        self.db = None
        
    def run(self):
        logger.info("Proceso GameController iniciado")
        self.db = DatabaseManager()
        led_controller = LEDController()
        game_logic = GameLogic()
        
        try:
            while not self.stop_event.is_set():
                try:
                    button_data = self.button_queue.get(timeout=0.1)
                    button_index = button_data['button']
                    
                    if game_logic.state == 'WAITING':
                        game_logic.start_new_game()
                        self.game_active.set()
                        threading.Thread(target=self.show_sequence, 
                                       args=(led_controller, game_logic), 
                                       daemon=True).start()
                        
                    elif game_logic.state == 'PLAYING':
                        led_controller.flash(button_index, 0.3)
                        result = game_logic.check_input(button_index)
                        
                        if result == 'WIN_LEVEL':
                            self.score.value += 10
                            threading.Thread(target=led_controller.celebration_sequence, 
                                           daemon=True).start()
                            time.sleep(0.5)
                            game_logic.next_level()
                            threading.Thread(target=self.show_sequence, 
                                           args=(led_controller, game_logic), 
                                           daemon=True).start()
                            
                        elif result == 'GAME_OVER':
                            if self.score.value > self.high_score.value:
                                self.high_score.value = self.score.value
                            self.db.save_game_result(self.score.value, game_logic.level)
                            threading.Thread(target=led_controller.game_over_sequence, 
                                           daemon=True).start()
                            time.sleep(1)
                            self.score.value = 0
                            game_logic.reset()
                            self.game_active.clear()
                except:
                    pass
                
                try:
                    self.web_queue.put({
                        'state': game_logic.state,
                        'level': game_logic.level,
                        'score': self.score.value,
                        'high_score': self.high_score.value
                    }, block=False)
                except:
                    pass
                
                time.sleep(0.05)
        finally:
            led_controller.cleanup()
    
    def show_sequence(self, led_controller, game_logic):
        time.sleep(1)
        for led_index in game_logic.sequence:
            led_controller.flash(led_index, 0.6)
            time.sleep(0.2)
        with game_logic.lock:
            game_logic.state = 'PLAYING'
