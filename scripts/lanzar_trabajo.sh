#!/bin/bash
#SBATCH --job-name=contador_inmortal  # Nombre del trabajo
#SBATCH --output=salida_trabajo.log   # Archivo donde se guardarán los prints
#SBATCH --error=error_trabajo.log     # Archivo donde se guardarán los errores
#SBATCH --partition=all               # Partición del clúster Avignon a usar
#SBATCH --nodes=1                     # Número de nodos que necesitamos
#SBATCH --ntasks=1                    # Número de tareas (procesos)
#SBATCH --cpus-per-task=1             # Cores por tarea
#SBATCH --time=00:10:00               # Tiempo máximo de ejecución (30 mins)

echo "=========================================================="
echo "Iniciando trabajo en el clúster (HPC)"
echo "Fecha de inicio: $(date)"
echo "Nodo asignado por Slurm: $SLURM_JOB_NODELIST"
echo "=========================================================="

# Cargamos el entorno de Python si hace falta (depende del cluster, a veces no es necesario)
# module load python/3.x 

# Nos aseguramos de estar en el directorio correcto
cd /home/alumnos/a0499612/multirm/scripts/

# Ejecutamos nuestro script paciente
python3 -u contador.py

echo "=========================================================="
echo "Trabajo finalizado o interrumpido."
echo "Fecha de fin: $(date)"
echo "=========================================================="