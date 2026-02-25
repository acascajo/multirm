import time
import json
import os
import signal
import sys

# RUTA DEL ARCHIVO DE ESTADO (Simula el NFS)
# Usamos una ruta relativa para que funcione igual en el Cluster y en la RPi
ARCHIVO_ESTADO = "../shared_data/estado_trabajo.json"

def guardar_checkpoint(contador):
    """Guarda el progreso en un archivo JSON."""
    datos = {
        "progreso": contador,
        "timestamp": time.time(),
        "mensaje": "Guardado exitoso"
    }
    with open(ARCHIVO_ESTADO, "w") as f:
        json.dump(datos, f)
    print(f"   [CHECKPOINT] Estado guardado. Contador: {contador}")

def cargar_checkpoint():
    """Intenta recuperar el progreso anterior."""
    if os.path.exists(ARCHIVO_ESTADO):
        try:
            with open(ARCHIVO_ESTADO, "r") as f:
                datos = json.load(f)
            print(f"[RECOVERY] ¡Archivo encontrado! Recuperando desde: {datos['progreso']}")
            return datos["progreso"]
        except Exception as e:
            print(f"[ERROR] Archivo corrupto, empezando de 0. ({e})")
            return 0
    else:
        print("[INIT] No hay estado previo. Empezando desde 0.")
        return 0

def manejar_cierre(signum, frame):
    """Captura Ctrl+C o señales de muerte para guardar antes de morir."""
    print("\n   [SIGNAL] ¡Me están matando! Guardando estado de emergencia...")
    # En un caso real, aquí guardaríamos una última vez.
    sys.exit(0)

# --- PROGRAMA PRINCIPAL ---
if __name__ == "__main__":
    # Capturamos la señal de interrupción
    signal.signal(signal.SIGINT, manejar_cierre)
    signal.signal(signal.SIGTERM, manejar_cierre)

    print("INICIANDO TRABAJO DE LARGA DURACIÓN")
    
    # 1. Recuperamos memoria (si existe)
    contador = cargar_checkpoint()
    
    # 2. Bucle infinito de trabajo
    while True:
        contador += 1
        print(f"Procesando dato número: {contador}...")
        
        # Simulamos trabajo pesado
        time.sleep(2) 
        
        # 3. Guardamos estado cada 3 iteraciones (Simulando checkpoints periódicos)
        if contador % 3 == 0:
            guardar_checkpoint(contador)