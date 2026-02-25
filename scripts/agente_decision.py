import subprocess
import time
import os
from datetime import datetime

# CONFIGURACION
UMBRAL_NODOS_LIBRES = 6       # Mínimo de nodos libres para considerar migrar (aun no se cuantos es un ejemplo)
TIEMPO_ESPERA_SEGUNDOS = 10   # Cada cuánto miramos Slurm
INTENTOS_PARA_MIGRAR = 3      # Cuántas veces seguidas debe estar libre para actuar
# Como son 3 intentos y 10 segundos por cada uno
# Se requieren 3 * 10 = 30 segundos de estabilidad para migrar

# CONFIGURACIÓN DE RED (mIGRACIÓN)
# Hay q cambiar la IP de las raspberry cuando la sepa
IP_RASPBERRY = "192.168.1.XX"
USUARIO_PI = "pi"
RUTA_REMOTA = "/home/pi/multirm/shared_data/"   # Donde se guardarán los json con los datos en la RPi
SCRIPT_REMOTO = "/home/pi/multirm/scripts/contador.py"

ARCHIVO_ESTADO_LOCAL = "../shared_data/estado_trabajo.json"


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
        return 0, 0, []


def activar_migracion():
    """Función que ejecuta los comandos reales de SCP y SSH"""
    print(f"\n[MIGRACIÓN] Iniciando protocolo de transferencia...")
    
    # 1. Comprobar si existe el archivo de estado
    if not os.path.exists(ARCHIVO_ESTADO_LOCAL):
        print(f"[ERROR] No encuentro el archivo {ARCHIVO_ESTADO_LOCAL}. Comprueba que el trabajo está corriendo")
        return False

    try:
        # 2. ENVIAR DATOS (SCP)
        # Comando: scp ../shared_data/estado.json pi@192.168.1.XX:/home/pi/...
        print(f"[1/2] Enviando Checkpoint a {IP_RASPBERRY}...")
        cmd_scp = [
            "scp", 
            ARCHIVO_ESTADO_LOCAL, 
            f"{USUARIO_PI}@{IP_RASPBERRY}:{RUTA_REMOTA}"
        ]
        # Nota: Esto fallará hasta q no tenga configuradas las claves SSH
        # subprocess.run(cmd_scp, check=True) 
        print(f"[SIMULACIÓN] Copia SCP realizada (Comando preparado).")

        # 3. EJECUTAR EN RASPBERRY (SSH)
        # Comando: ssh pi@192.168.1.XX 'python3 /home/pi/.../job_contador.py'
        print(f"[2/2] Reactivando proceso en nodo ARM...")
        cmd_ssh = [
            "ssh",
            f"{USUARIO_PI}@{IP_RASPBERRY}",
            f"python3 {SCRIPT_REMOTO}"
        ]
        # subprocess.Popen(cmd_ssh) # Usamos Popen para no bloquear este script
        print(f"[SIMULACIÓN] Comando SSH enviado: python3 {SCRIPT_REMOTO}")
        
        return True

    except Exception as e:
        print(f"   [ERROR CRÍTICO] La migración falló: {e}")
        return False


def iniciar_agente():
    print(f"AGENTE DE DECISIÓN INICIADO")
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
                    print(f"¡CONDICIÓN DE MIGRACIÓN ALCANZADA!")

                    exito = activar_migracion()

                    if exito:
                        modo_ahorro = True
                        print(f"(Sistema entra en modo vigilancia silenciosa de ahorro)")

                    else:
                        # Si falla (ej: no encuentra el archivo), seguimos intentándolo en la siguiente vuelta
                        # o ponemos modo_ahorro=True para simular que ha ido bien por ahora
                        print(f"   (Simulación completada / Fallo controlado)")
                        modo_ahorro = True
                
                # Mantenemos el contador al máximo
                conteo_estabilidad = INTENTOS_PARA_MIGRAR # Topeamos el contador

                
        else:
            # Caso: Carga ALTA o NORMAL
            conteo_estabilidad = 0
            
            # Si estábamos en modo ahorro y de repente se llena el cluster...
            if modo_ahorro:
                print(f"[{timestamp}] ¡ATENCIÓN! Carga de trabajo detectada. Desactivando modo ahorro.")
                print(f"Reactivando nodos x86...")
                modo_ahorro = False
            
            print(f"[{timestamp}] Carga NORMAL/ALTA ({libres}/{total} libres).")
            print(f"Nodos trabajando: {texto_ocupados}")
            
        # 4. Dormimos hasta el siguiente chequeo
        time.sleep(TIEMPO_ESPERA_SEGUNDOS)

if __name__ == "__main__":
    iniciar_agente()