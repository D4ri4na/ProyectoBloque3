# Perfiles Sonoros y Popularidad Musical en Spotify

> **Proyecto Bloque 3 — Aprendizaje No Supervisado (ISW-222 Machine Learning)**  
> Universidad Católica Boliviana · Semestre 6 · 2026

---

## Pregunta Central

> *¿Los grupos formados únicamente con características acústicas presentan diferencias de popularidad? ¿Existen perfiles sonoros que concentren canciones de alta popularidad y qué características los distinguen?*

---

## Resultados Destacados

| Configuración | Silhouette (espacio común, test) | Estabilidad (ARI) | Tiempo ajuste |
|---|---|---|---|
| **K-Means + PCA** ✅ Recomendada | **0.2477** | **99.4 %** | 0.14 s |
| K-Means Original | 0.2460 | 99.5 % | 0.07 s |
| GMM + PCA | 0.0243 | 55.2 % | 2.85 s |
| GMM Original | −0.0119 | 55.7 % | 6.01 s |

**Hallazgo de popularidad:** El perfil enérgico (Cluster 0) concentra el **4.64 %** de canciones ≥ 70 de popularidad frente al 2.98 % global → **Lift 1.55**, IC95 diferencia [+1.86, +3.83] pp.  
El contraste es estadísticamente significativo pero con amplio solapamiento: el audio no garantiza el éxito comercial.

**El Ritmo del Éxito (Cluster 0 — mayor popularidad):**
- Tempo: **125 BPM** · Loudness: **−6.1 dB** · Bailabilidad: **0.61** · Energía: **0.76**
- Carácter acústico: **0.08** (producción eléctrica/sintética) · Duración: **3 min 34 s**

---

## Estructura del Repositorio

```
ProyectoBloque3/
│
├── Proyecto_Musica.ipynb           # ⭐ Cuaderno principal: código + resultados ejecutados
├── proyecto_musica.py              # Implementación completa del experimento
│
├── Explorador_Musical/
│   ├── Explorador_Musical.html     # ⭐ App interactiva SONORA (abre en navegador, sin servidor)
│   ├── Proyecto_Explorador_Musical.ipynb
│   └── ...                         # Scripts y outputs del explorador
│
├── Proyecto_Final/
│   ├── Proyecto_Mejorado.ipynb     # Ampliación metodológica con K=3-10 y contextos de género
│   ├── mejorar_proyecto.py         # Script principal de la ampliación
│   ├── analizar_contextos.py       # Análisis por contextos musicales (electrónica, rock, pop…)
│   ├── analizar_popularidad.py     # Contraste de popularidad con nuevas 2000 canciones
│   └── resultados/
│       ├── informe.html            # Informe completo con las 12 respuestas de la rúbrica
│       ├── informe.md              # Informe editable en Markdown
│       └── ampliacion/             # Resultados de la ampliación (lift, contextos, figuras)
│
├── outputs/                        # Resultados del experimento principal
│   ├── figures/                    # 21 gráficas generadas (distribuciones, perfiles, mapas 2D…)
│   ├── informe.html                # Informe principal legible en navegador
│   ├── comparativa.csv             # Tabla 2×2 obligatoria con métricas en espacio común
│   ├── estabilidad.csv             # ARI por semillas y submuestras
│   ├── busqueda_*.csv              # Curvas de búsqueda de hiperparámetros
│   ├── perfiles_*.csv              # Medianas por cluster en unidades originales
│   ├── popularidad_*.csv           # Distribución de popularidad post-clustering
│   ├── asignaciones_*.csv          # Asignaciones de canciones (GMM incluye probabilidades)
│   ├── validacion.json             # ✅ 8 comprobaciones de integridad (status: passed)
│   └── versiones.json              # Versiones exactas: Python 3.12.5, sklearn 1.9.0…
│
├── data/raw/
│   ├── spotify_tracks.csv          # Dataset fuente sin modificar (114.000 filas)
│   └── manifest.json               # Procedencia, SHA-256 y huella de los datos
│
├── entregables/
│   ├── Presentacion_Proyecto_Bloque3.pptx  # ⭐ Presentación de 16 diapositivas con gráficas
│   ├── Proyecto_Musica_Bloque3.zip         # ZIP principal de entrega
│   └── ...                                 # Otros ZIPs de versiones anteriores
│
├── descargar_dataset.py            # Descarga y verifica el CSV con SHA-256
├── ejecutar_cuaderno.py            # Verifica todas las celdas sin servidor Jupyter
├── crear_cuaderno.py               # Regenera el .ipynb desde proyecto_musica.py
├── crear_graficas_diapos.py        # Genera las gráficas de la presentación
├── generar_diapositivas.py         # Genera el PowerPoint de 16 diapositivas
├── empaquetar_proyecto.py          # Crea el ZIP de entrega
├── requirements.txt                # Dependencias del proyecto
└── requirements-lock.txt           # Versiones exactas utilizadas en la ejecución verificada
```

---

## Inicio Rápido

### Requisitos
- Python **3.10 o superior** (verificado en 3.12.5)
- Las dependencias listadas en `requirements.txt`

### Instalación y ejecución del experimento principal

```powershell
# 1. Instalar dependencias
python -m pip install -r requirements.txt

# 2. Descargar el dataset (si no está en data/raw/)
python descargar_dataset.py

# 3. Ejecutar el experimento completo
python proyecto_musica.py

# (Alternativa) Abrir el cuaderno en Jupyter / VS Code
# y ejecutar todas las celdas con Run All
```

### Verificar el cuaderno sin servidor Jupyter

```powershell
python ejecutar_cuaderno.py
# → Cuaderno completo: 17 celdas Python, cero errores, ~249 s.
```

### Regenerar la presentación PowerPoint

```powershell
python crear_graficas_diapos.py   # genera gráficas especiales para las diapos
python generar_diapositivas.py    # genera Presentacion_Proyecto_Bloque3.pptx
```

### Ejecutar la ampliación metodológica (Proyecto_Final)

```powershell
cd Proyecto_Final
python -m pip install -r requirements.txt
python mejorar_proyecto.py        # clustering + objetivo de popularidad + contextos
# Solo recalcular contextos con etapas previas ya disponibles:
python analizar_contextos.py
```

### Abrir el Explorador Interactivo SONORA

Haz doble clic en `Explorador_Musical/Explorador_Musical.html` en cualquier navegador moderno.  
No necesita servidor, conexión a internet ni cuenta de Spotify.  
Los enlaces de escucha en Spotify sí requieren conexión.

---

## Configuración del Experimento

| Parámetro | Valor predeterminado |
|---|---|
| Canciones analizadas | **10.000 únicas** |
| División | **80 % train / 20 % test** |
| Semilla | **42** |
| Rango de K explorado | **2 a 12** |
| Varianza retenida PCA | **≥ 90 %** (resultado: 90.81 % con 7 componentes) |
| Criterio K-Means | **Silhouette máximo** |
| Criterio GMM | **BIC mínimo** |

```powershell
# Configuración personalizada
python proyecto_musica.py --muestra 15000 --kmax 20
```

---

## Decisiones Metodológicas Clave

1. **Sin fuga de popularidad ni género:** ambos quedan 100 % fuera del entrenamiento y solo se usan como contraste posterior.
2. **Deduplicación sin sesgo:** las canciones duplicadas por `track_id` se eliminan conservando la primera aparición en orden de archivo, sin seleccionar por popularidad.
3. **Escalado y PCA ajustados solo en entrenamiento:** `StandardScaler`, imputador de medianas y PCA aprenden exclusivamente del conjunto de entrenamiento (80 %).
4. **Hiperparámetros congelados antes de observar popularidad:** K y covarianza se seleccionan por métricas geométricas de validación; no se cambian después de ver las diferencias de popularidad.
5. **Comparación justa:** las métricas en PCA se re-evalúan siempre en el espacio original escalado (`evaluation_space = reference_original`) para evitar comparar geometrías incompatibles.
6. **Silhouette submuestreado:** se usa una muestra fija de máximo 2.000 observaciones con semilla fija para evitar costo cuadrático de memoria.

---

## Interpretación y Límites

Los p-valores de popularidad son **exploratorios**: las canciones pueden compartir artista y no son observaciones independientes.  
Popularidad ≥ 70 en el CSV histórico **no equivale** a ingresos, ventas, calidad ni éxito universal.  
El dataset es de corte transversal; no se conoce la fecha exacta de medición.  
El perfil sonoro influye, pero marketing, nombre del artista y viralidad en redes son factores determinantes que este análisis no captura.

---

## Versiones del Entorno Verificado

| Librería | Versión |
|---|---|
| Python | 3.12.5 |
| scikit-learn | 1.9.0 |
| pandas | 3.0.5 |
| numpy | 2.5.2 |
| scipy | 1.18.1 |
| matplotlib | 3.11.1 |
| threadpoolctl | 3.6.0 |
| python-pptx | 1.0.2 |

---

## Fuente de Datos, Licencia y Declaración de IA

**Dataset:** Pandya, M. (s. f.). *Spotify Tracks Dataset* [Conjunto de datos]. Hugging Face.  
https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset  
La ficha del repositorio declara licencia BSD. Verificar el alcance y los términos originales antes de redistribuir. No se distribuye audio.

**Referencia principal:**  
Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html

**Uso de IA:** Se utilizó ChatGPT/Codex y Google Gemini (Antigravity) para escribir y revisar código, estructurar el trabajo, generar explicaciones y crear la presentación. Las cifras finales provienen de la ejecución real del código. Los autores deben revisar personalmente los resultados, interpretar los perfiles y declarar esta asistencia antes de la entrega final.

> **Antes de entregar:** completar nombre de autores, docente y fecha en la carátula del cuaderno y del informe.
