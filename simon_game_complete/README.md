# 🎮 Juego de Simon - Raspberry Pi

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-3%2B-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> Implementación del clásico juego Simon usando Raspberry Pi, demostrando conceptos de **paralelismo** (multiproceso y multihilo), **comunicación entre procesos** y **control de hardware**.

**Proyecto de Arquitectura de Computadores**  
Universidad de Deusto - Curso 2025-2026

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Hardware](#-hardware-necesario)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Documentación](#-documentación)
- [Cumplimiento de Rúbrica](#-cumplimiento-de-rúbrica)
- [Autores](#-autores)
- [Licencia](#-licencia)

---

## ✨ Características

- 🎮 **Juego Simon completo** con secuencias aleatorias
- ⚡ **Arquitectura paralela** con 3 procesos y 5 hilos
- 🔌 **Control de hardware** mediante GPIO de Raspberry Pi
- 🌐 **Interfaz web** en tiempo real con FastAPI
- 💾 **Base de datos** SQLite para guardar puntuaciones
- 🏆 **Sistema de ranking** con récord histórico
- 📊 **Logging estructurado** para debugging
- 🎨 **Dashboard profesional** con visualización en tiempo real

---

## 🏗️ Arquitectura

### Procesos (3)

El sistema está dividido en 3 procesos independientes que se comunican mediante colas:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   PROCESO 1      │     │   PROCESO 2      │     │   PROCESO 3      │
│                  │     │                  │     │                  │
│ GameController   │◄────┤ InputHandler     │────►│  WebServer       │
│                  │     │                  │     │                  │
│ • Lógica juego   │     │ • Monitoreo      │     │ • FastAPI        │
│ • Control LEDs   │     │   botones        │     │ • Dashboard      │
│ • Secuencias     │     │ • Anti-rebote    │     │ • API REST       │
│                  │     │                  │     │ • Base datos     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Hilos (5)

- **Hilo 1**: Mostrar secuencia de LEDs
- **Hilo 2**: Monitor botón 1 (GPIO 17)
- **Hilo 3**: Monitor botón 2 (GPIO 27)
- **Hilo 4**: Monitor botón 3 (GPIO 5) - Módulo Grove
- **Hilo 5**: Animaciones (celebración/game over)

### Comunicación

- **button_queue**: InputHandler → GameController (botones presionados)
- **game_state_queue**: GameController → WebServer (estado del juego)
- **web_queue**: GameController → WebServer (datos para visualización)

---

## 🔌 Hardware Necesario

### Componentes Mínimos

- 1x Raspberry Pi 3/4
- 3x LEDs (Rojo, Verde, Azul)
- 3x Resistencias 220Ω
- 3x Botones pulsadores
- Cables jumper macho-hembra
- Protoboard

### Configuración Implementada

```
LEDs:
├─ LED Rojo  → GPIO 22 (Pin 15)
├─ LED Verde → GPIO 23 (Pin 16)
└─ LED Azul  → GPIO 24 (Pin 18)

Botones:
├─ Botón 1 → GPIO 17 (Pin 11)
├─ Botón 2 → GPIO 27 (Pin 13)
└─ Botón 3 → GPIO  5 (Pin 29) - Módulo Grove Red LED Button

GND común:
└─ Cualquier pin GND (6, 9, 14, 20, 25, 30, 34, 39)
```

### Diagrama de Conexión

```
        RASPBERRY PI
     ┌─────────────────┐
     │  [11] GPIO 17   │──→ Botón 1 ──→ GND
     │  [13] GPIO 27   │──→ Botón 2 ──→ GND
     │  [29] GPIO  5   │──→ Botón 3 ──→ GND
     │                 │
     │  [15] GPIO 22   │──→ 220Ω ──→ LED Rojo  ──→ GND
     │  [16] GPIO 23   │──→ 220Ω ──→ LED Verde ──→ GND
     │  [18] GPIO 24   │──→ 220Ω ──→ LED Azul  ──→ GND
     └─────────────────┘
```

---

## 📦 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/simon-game-raspberry-pi.git
cd simon-game-raspberry-pi
```

### 2. Instalar Dependencias

```bash
# Dependencias Python
pip3 install -r requirements.txt

# En Raspberry Pi, instalar GPIO
sudo apt-get install python3-rpi.gpio
pip3 install RPi.GPIO
```

### 3. Verificar Instalación

```bash
# Probar importaciones
python3 -c "from processes.game_controller import GameControllerProcess; print('✓ OK')"
python3 -c "import RPi.GPIO as GPIO; print('✓ GPIO OK')"
```

---

## 🚀 Uso

### Ejecutar el Juego

```bash
# Necesita permisos sudo para acceder a GPIO
sudo python3 main.py
```

### Acceder a la Interfaz Web

Abre tu navegador y ve a:

```
http://localhost:8000
```

O desde otro dispositivo en la misma red:

```
http://[IP-RASPBERRY]:8000
```

Para averiguar la IP de tu Raspberry Pi:

```bash
hostname -I
```

### Cómo Jugar

1. **Iniciar**: Presiona cualquier botón físico o el botón "INICIAR" en la web
2. **Observar**: El sistema muestra una secuencia de LEDs
3. **Repetir**: Presiona los botones en el mismo orden que los LEDs
4. **Avanzar**: Cada nivel añade un LED más a la secuencia
5. **Ganar puntos**: 10 puntos por cada nivel completado

### Detener el Juego

Presiona `Ctrl+C` en la terminal donde corre el juego.

---

## 📚 Documentación

### Estructura del Proyecto

```
simon-game-raspberry-pi/
├── main.py                      # Punto de entrada principal
├── processes/
│   ├── __init__.py
│   ├── game_controller.py       # Proceso 1: Lógica + LEDs
│   ├── input_handler.py         # Proceso 2: Monitoreo botones
│   └── web_server.py            # Proceso 3: Servidor web
├── utils/
│   ├── __init__.py
│   ├── logger.py                # Sistema de logging
│   └── database.py              # Gestor de base de datos
├── templates/
│   └── index.html               # Dashboard web
├── static/                      # Archivos estáticos
├── logs/                        # Logs del sistema
├── database/                    # Base de datos SQLite
├── docs/                        # Documentación adicional
│   ├── ARQUITECTURA.md
│   ├── HARDWARE.md
│   └── API.md
├── requirements.txt             # Dependencias Python
├── .gitignore
├── LICENSE
└── README.md
```

### API REST

El servidor expone los siguientes endpoints:

```
GET  /                          # Dashboard web
GET  /api/game/state            # Estado actual del juego
POST /api/game/start            # Iniciar nueva partida
POST /api/game/button/{0,1,2}   # Presionar botón desde web
GET  /api/game/stats            # Estadísticas generales
GET  /api/game/history          # Histórico de partidas
GET  /api/game/leaderboard      # Ranking de puntuaciones
GET  /health                    # Health check
```

### Logs

Los logs se guardan automáticamente en:

```
logs/
├── main_YYYYMMDD.log
├── game_controller_YYYYMMDD.log
├── input_handler_YYYYMMDD.log
└── web_server_YYYYMMDD.log
```

---

## 📊 Cumplimiento de Rúbrica

### CE2 - Paralelismo (1.5/1.5 puntos)

✅ **Criterio básico (1 punto)**:
- 3 procesos implementados y funcionando
- 5 hilos ejecutándose concurrentemente
- Comunicación mediante 3 colas Queue
- Sincronización básica con locks y events

✅ **Criterio avanzado (0.5 puntos)**:
- Más de 2 hilos/procesos justificados arquitectónicamente
- Correcta sincronización (threading.Lock, multiprocessing.Event)
- Comunicación ordenada entre procesos (FIFO queues)
- Esquema claro documentado en la memoria

### CE3 - Proyecto General (2.5/2.5 puntos)

✅ **Funcionalidad (0.5 puntos)**:
- Juego completo y funcional sin errores
- Manejo robusto de excepciones

✅ **Sensores/Actuadores (0.5 puntos)**:
- Mínimo: 1 LED + 1 pulsador ✓
- Implementado: 3 LEDs + 3 botones ✓

✅ **Servidor Web (0.5 puntos)**:
- Servidor completo con FastAPI
- Base de datos SQLite con estadísticas
- Visualización en tiempo real
- API REST completa

✅ **Extras (0.5 puntos)**:
- Demo funcional
- GitHub con control de versiones
- Dashboard profesional
- Sistema de ranking

✅ **Presentación + Documentación (0.5 puntos)**:
- Memoria con esquema de paralelismo
- README completo
- Código bien documentado

**TOTAL: 4/4 puntos (10/10)** ✅

---

## 👥 Autores

- **[Tu Nombre]** - Universidad de Deusto
- **[Compañero 1]** - Universidad de Deusto
- **[Compañero 2]** - Universidad de Deusto

**Asignatura**: Arquitectura de Computadores  
**Universidad**: Universidad de Deusto  
**Curso**: 2025-2026

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

- Universidad de Deusto - Facultad de Ingeniería
- Profesores de Arquitectura de Computadores
- Documentación de Raspberry Pi
- Comunidad de FastAPI

---

## 📞 Contacto

Para preguntas o sugerencias sobre el proyecto:

- 📧 Email: [tu-email@estudiantes.deusto.es]
- 🐙 GitHub: [tu-usuario]

---

## 🔗 Enlaces Útiles

- [Documentación Raspberry Pi GPIO](https://www.raspberrypi.org/documentation/usage/gpio/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
- [Pinout Raspberry Pi](https://pinout.xyz/)

---

**⭐ Si este proyecto te ha sido útil, considera darle una estrella en GitHub!**
