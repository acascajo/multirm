import subprocess
import time
from datetime import datetime

# CONFIGURACION
UMBRAL_NODOS_LIBRES = 6       # Mínimo de nodos libres para considerar migrar (aun no se cuantos es un ejemplo)
TIEMPO_ESPERA_SEGUNDOS = 10   # Cada cuánto miramos Slurm
INTENTOS_PARA_MIGRAR = 3      # Cuántas veces seguidas debe estar libre para actuar
# Como son 3 intentos y 10 segundos por cada uno
# Se requieren 3 * 10 = 30 segundos de estabilidad para migrar


def obtener_metricas_slurm():
    try:
        # Pasamos el comando como lista.
        # Así aseguramos q "-o" recibe "%n %t" como un único bloque.
        comando = ["sinfo", "-h", "-o", "%n %t"]
        
        # Ejecutamos el comando
        resultado = subprocess.check_output(comando, text=True)
        
        # Filtramos líneas vacías
        lineas = [l.strip() for l in resultado.strip().split('\n') if l.strip()]
        nodos_libres = 0
        lista_ocupados = []
        
        for linea in lineas:
            # Dividimos por espacios
            partes = linea.split()

            # Miramos q hay al menos nombre y estado
            if len(partes) >= 2:
                nombre = partes[0]
                estado = partes[1].lower()
                # Slurm a veces devuelve 'idle*' o 'idle~', así que buscamos 'idle' dentro del texto
                if 'idle' in estado:
                    nodos_libres += 1
                
                else:
                    lista_ocupados.append(f"{nombre} ({estado})")
                    
        return len(lineas), nodos_libres, lista_ocupados
        
    except Exception as e:
        print(f"[ERROR] Fallo al consultar Slurm: {e}")
        return 0, 0

def iniciar_agente():
    print(f"--- AGENTE DE DECISIÓN INICIADO ---")
    print(f"Configuración: Esperar {INTENTOS_PARA_MIGRAR} chequeos de {TIEMPO_ESPERA_SEGUNDOS} segundos antes de migrar.")
    
    conteo_estabilidad = 0
    modo_ahorro = False
    
    while True:
        # 1. Obtenemos datos
        total, libres, ocupados = obtener_metricas_slurm()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Generamos el texto de ocupados para mostrarlo si hace falta
        texto_ocupados = ", ".join(ocupados) if ocupados else "Ninguno"

        # 2. Evaluamos la situación
        if libres >= UMBRAL_NODOS_LIBRES:
            conteo_estabilidad += 1
            
            if not modo_ahorro:
                print(f"[{timestamp}] Carga BAJA detectada ({libres}/{total} libres). Ocupados: [{texto_ocupados}]. Estabilidad: {conteo_estabilidad}/{INTENTOS_PARA_MIGRAR}")
            
            # 3. ¿Hemos esperado lo suficiente? (TRIGGER)
            if conteo_estabilidad >= INTENTOS_PARA_MIGRAR:
                if not modo_ahorro:
                    print(f"   >>> ¡CONDICIÓN DE MIGRACIÓN ALCANZADA! <<<")
                    print(f"   >>> Iniciando protocolo de ahorro energético en Raspberry Pi...")
                    # Aquí iría la llamada a la función que despierta a la RPi
                    # resetear_contador() ? O mantenerlo hasta que suba la carga?

                    modo_ahorro = True
                    print(f"   (Sistema entra en modo vigilancia silenciosa de ahorro)")
                
                # Mantenemos el contador al máximo
                conteo_estabilidad = INTENTOS_PARA_MIGRAR # Topeamos el contador

                
        else:
            # Caso: Carga ALTA o NORMAL
            conteo_estabilidad = 0
            
            # Si estábamos en modo ahorro y de repente se llena el cluster...
            if modo_ahorro_activo:
                print(f"[{timestamp}] ¡ATENCIÓN! Carga de trabajo detectada. Desactivando modo ahorro.")
                print(f"   >>> Reactivando nodos x86...")
                modo_ahorro_activo = False
            
            print(f"[{timestamp}] Carga NORMAL/ALTA ({libres}/{total} libres).")
            print(f"   >>> Nodos trabajando: {texto_ocupados}")
            
        # 4. Dormimos hasta el siguiente chequeo
        time.sleep(TIEMPO_ESPERA_SEGUNDOS)

if __name__ == "__main__":
    iniciar_agente()