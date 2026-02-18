import subprocess

def obtener_nodos_libres():
    try:
        # CORRECCIÓN IMPORTANTE: Pasamos el comando como lista.
        # Así aseguramos que "-o" recibe "%n %t" como un único bloque.
        # %n = NodeHostName, %t = StateCompact
        comando = ["sinfo", "-h", "-o", "%n %t"]
        
        # Ejecutamos el comando
        resultado = subprocess.check_output(comando, text=True)
        
        # Filtramos líneas vacías
        lineas = [l.strip() for l in resultado.strip().split('\n') if l.strip()]
        
        nodos_libres = 0
        nodos_ocupados = 0
        
        print(f"--- DEBUG: Analizando {len(lineas)} líneas detectadas ---")
        
        for linea in lineas:
            # Dividimos por espacios
            partes = linea.split()
            
            # Aseguramos que hay al menos nombre y estado
            if len(partes) >= 2:
                nombre_nodo = partes[0]
                estado_nodo = partes[1].lower() # Convertimos a minúsculas para comparar
                
                # Slurm a veces devuelve 'idle*' o 'idle~', así que buscamos 'idle' dentro del texto
                if 'idle' in estado_nodo:
                    nodos_libres += 1
                    # Descomenta la siguiente línea si quieres ver cada nodo libre
                    # print(f"  [OK] Nodo {nombre_nodo} está LIBRE ({estado_nodo})")
                else:
                    nodos_ocupados += 1
                    print(f"  [X]  Nodo {nombre_nodo} está OCUPADO/NO DISPONIBLE ({estado_nodo})")
            else:
                print(f"  [ERROR DE FORMATO] Línea extraña: '{linea}'")

        print(f"\n--- INFORME FINAL ---")
        print(f"Total Nodos: {len(lineas)}")
        print(f"Nodos Libres (idle): {nodos_libres}")
        print(f"Nodos Ocupados/Otros: {nodos_ocupados}")

        # Lógica de decisión
        if nodos_libres >= 6:
            print(">>> ESTADO: AHORRO POSIBLE. Iniciar migración a Raspberry Pi.")
        else:
            print(">>> ESTADO: CARGA ALTA. Mantener en x86.")
            
    except Exception as e:
        print(f"Error crítico: {e}")

if __name__ == "__main__":
    obtener_nodos_libres()