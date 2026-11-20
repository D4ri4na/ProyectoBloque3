"""Genera una presentación PPTX profesional, editable y con gráficos integrados en alta resolución."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent
OUTPUT_PPTX = ROOT / "Presentacion_Proyecto_Bloque3.pptx"
FIGS = ROOT / "outputs" / "figures"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

BG_DARK = RGBColor(18, 18, 18)       # #121212
CARD_BG = RGBColor(30, 30, 30)       # #1E1E1E
ACCENT_GREEN = RGBColor(29, 185, 84) # #1DB954
TEXT_WHITE = RGBColor(255, 255, 255) # #FFFFFF
TEXT_MUTED = RGBColor(179, 179, 179) # #B3B3B3
HIGHLIGHT_BG = RGBColor(35, 50, 40)  # Verde tenue

slides_data = [
    {
        "num": "01",
        "tag": "PORTADA · APRENDIZAJE NO SUPERVISADO",
        "title": "La Fórmula Sónica del Éxito Musical",
        "subtitle": "Clustering y Reducción Dimensional (PCA) sobre 10.000 Canciones de Spotify",
        "bullets": [
            "¿Influye el sonido en la popularidad o el éxito depende solo del marketing?",
            "Comparación de dos familias: K-Means (particional) vs. GMM (probabilístico).",
            "Evaluación de impacto antes y después de reducir la dimensionalidad con PCA.",
            "Segmentación acústica pura: el modelo aprende sin ver géneros ni popularidad."
        ],
        "highlight": "Objetivo: descubrir si existen patrones de ritmo y producción asociados al streaming masivo.",
        "script": "«¿Existe un patrón acústico detrás de los éxitos musicales o el éxito depende solo del marketing? Hoy analizamos 10.000 canciones en Spotify para descubrir si el ritmo, la energía y la acústica pueden condicionar la popularidad sin mirar géneros ni nombres de artistas.»",
        "image": None
    },
    {
        "num": "02",
        "tag": "CONTEXTO DEL DOMINIO",
        "title": "El Problema de la Industria Musical Moderna",
        "subtitle": "Catálogos saturados y etiquetas editoriales subjetivas",
        "bullets": [
            "+100.000 canciones nuevas son subidas diariamente a plataformas digitales.",
            "Los 'géneros' son etiquetas comerciales subjetivas (un Rock puede ser bailable).",
            "Los oyentes eligen música por 'estados de ánimo' y energía, no por taxonomías rígidas.",
            "Riesgo: canciones de alta calidad quedan invisibles por falta de etiquetado preciso."
        ],
        "highlight": "Reto: organizar catálogos inmensos analizando la huella de audio física de cada pista.",
        "script": "«Las plataformas de streaming reciben más de 100.000 canciones diarias. Clasificar por género es engañoso: hay canciones de Rock más bailables que temas de Pop. La industria necesita entender la huella sónica real para ordenar su biblioteca sin prejuicios editoriales.»",
        "image": None
    },
    {
        "num": "03",
        "tag": "APLICABILIDAD Y NEGOCIO",
        "title": "¿A Quiénes Ayuda este Proyecto?",
        "subtitle": "Casos de uso reales para la industria del audio y streaming",
        "bullets": [
            "Curadores de Playlists: armar secuencias y mezclas con coherencia sónica fluida.",
            "Productores y Compositores: conocer rangos de energía y tempo de mayor consumo.",
            "Sellos y Cazatalentos (A&R): filtrar catálogos de artistas emergentes sin sesgo de fama.",
            "Algoritmos de Recomendación: sugerir pistas por afinidad tímbrica sin 'efecto burbuja'."
        ],
        "highlight": "Impacto: permite descubrir música por su esencia acústica, no por su presupuesto de prensa.",
        "script": "«Esto ayuda directamente a curadores de playlists para crear transiciones suaves de sonido, a productores musicales para saber en qué rangos de energía mezclar, y a discográficas para descubrir gemas ocultas en catálogos gigantescos que no tuvieron suficiente marketing.»",
        "image": None
    },
    {
        "num": "04",
        "tag": "METODOLOGÍA · REGLA DE ORO",
        "title": "Agrupamiento Acústico Puro (Ciego a la Fama)",
        "subtitle": "Aislamiento estricto de variables para evitar fuga de información",
        "bullets": [
            "10 variables numéricas continuas: danceability, energy, loudness, tempo, acousticness...",
            "Regla de Oro: la 'Popularidad' y el 'Género' quedaron 100% fuera del entrenamiento.",
            "Ningún algoritmo utilizó la fama para decidir cómo segmentar el catálogo.",
            "La popularidad se reservó exclusivamente como contraste estadístico posterior."
        ],
        "highlight": "Principio científico: si el modelo viera la popularidad, el agrupamiento estaría viciado.",
        "script": "«El objetivo fue agrupar las canciones guiándonos únicamente por 10 características acústicas. Para evitar trampas, el modelo jamás vio qué tan famosa era la canción. La popularidad se mantuvo oculta y solo se usó al final para contrastar los resultados.»",
        "image": None
    },
    {
        "num": "05",
        "tag": "PREPARACIÓN DE DATOS",
        "title": "Distribuciones y el Peligro del No-Escalado",
        "subtitle": "StandardScaler y partición 80/20 ajustados exclusivamente con entrenamiento",
        "bullets": [
            "10.000 canciones únicas reproducibles (8.000 train / 2.000 test).",
            "Muestra asimetrías severas en loudness, duración e instrumentalidad.",
            "Control sin escalar: K-Means colapsa con ARI = 0.0024 frente al escalado.",
            "Causa: duration_ms (~200.000) devora a variables acotadas entre 0 y 1."
        ],
        "highlight": "Lección: el escalado estandarizado es obligatorio en aprendizaje basado en distancias.",
        "script": "«Trabajamos con 10.000 pistas únicas divididas en 80% para entrenar y 20% para validar. El escalado se ajustó solo en entrenamiento: si no escalábamos, la duración en milisegundos destruía el análisis al opacar a las variables de ritmo y energía.»",
        "image": FIGS / "01_distribuciones.png"
    },
    {
        "num": "06",
        "tag": "MODELADO NO SUPERVISADO",
        "title": "Dos Familias de Algoritmos en Competencia",
        "subtitle": "K-Means (geométrico particional) vs. GMM (probabilístico mixto)",
        "bullets": [
            "K-Means: optimiza centroides euclidianos (grupos esféricos).",
            "Ajuste K-Means: curva de codo y maximización de Silhouette (óptimo K=2).",
            "GMM: densidades gaussianas mixtas con EM y asignación suave.",
            "Ajuste GMM: minimización estricta del criterio Bayesiano (BIC)."
        ],
        "highlight": "Contraste: ¿la música se organiza en esferas rígidas o en nubes gaussianas solapadas?",
        "script": "«Comparamos dos familias de algoritmos opuestas: K-Means, que busca núcleos esféricos rígidos por distancia euclidiana, y GMM, un modelo probabilístico que entiende la música como mezclas continuas con bordes difusos y probabilidades de pertenencia.»",
        "image": FIGS / "04_busqueda_KMeans_pca.png"
    },
    {
        "num": "07",
        "tag": "REDUCCIÓN DIMENSIONAL",
        "title": "PCA: Condensando el Espacio Sónico",
        "subtitle": "De 10 variables continuas a 7 componentes principales sin fuga",
        "bullets": [
            "PCA ajustado exclusivamente sobre el conjunto de entrenamiento.",
            "7 componentes retienen el 90.81% de la varianza total (estándar 90-95%).",
            "Filtra redundancias: energy y loudness tenían correlación de r = 0.76.",
            "Reduce el costo computacional de cálculo de distancias euclidianas."
        ],
        "highlight": "Varianza acumulada: 90.81% retenida (máxima información con menor dimensionalidad).",
        "script": "«Aplicamos PCA para eliminar redundancias: variables como volumen sonoro y energía decían casi lo mismo. Redujimos de 10 variables a 7 componentes conservando más del 90% de la información sónica original, acelerando los modelos.»",
        "image": FIGS / "03_varianza_pca.png"
    },
    {
        "num": "08",
        "tag": "INTERPRETACIÓN MATEMÁTICA",
        "title": "Los Dos Ejes Maestros de la Música (PC1 y PC2)",
        "subtitle": "Visualización 2D de clusters proyectados en el plano principal",
        "bullets": [
            "PC1 (28.8% var): Loudness (+0.51) y Energy (+0.50) vs Acousticness (-0.43).",
            "-> Eje PC1: Intensidad y Volumen vs. Textura Acústica Pura.",
            "PC2 (15.3% var): Valence (+0.46) y Danceability (+0.44) vs Duration (-0.42).",
            "-> Eje PC2: Bailabilidad Comercial vs. Formato Extenso / Instrumental."
        ],
        "highlight": "El plano PC1/PC2 resume el 44.1% de toda la diversidad acústica del catálogo.",
        "script": "«Los dos primeros componentes revelan los ejes maestros de la música: el eje horizontal contrapone la potencia eléctrica y el volumen contra el sonido acústico orgánico. El eje vertical mide el ritmo bailable y alegre frente a temas instrumentales largos.»",
        "image": FIGS / "07_mapa_KMeans_pca.png"
    },
    {
        "num": "09",
        "tag": "DESCUBRIMIENTO NATURAL",
        "title": "La Gran Polaridad del Catálogo",
        "subtitle": "El agrupamiento óptimo divide la música en dos macro-perfiles",
        "bullets": [
            "Cluster 0 (75% del catálogo): Música moderna, alta producción, enérgica y rítmica.",
            "Cluster 1 (25% del catálogo): Música acústica, introspectiva, dinámica y orgánica.",
            "Esta separación emerge de forma espontánea a partir de las matemáticas del sonido.",
            "Demuestra que el catálogo comercial responde ante todo a un pulso de 'intensidad vital'."
        ],
        "highlight": "Conclusión: la división no es por géneros, sino por nivel de energía y producción.",
        "script": "«Al buscar la estructura óptima, los datos no se dividen por géneros, sino por energía vital: un grupo masivo dominado por la producción enérgica y moderna, frente a un bloque más pequeño de música suave, lenta y acústica.»",
        "image": None
    },
    {
        "num": "10",
        "tag": "HALLAZGO CENTRAL",
        "title": "¡El Ritmo del Éxito! (La Huella Popular)",
        "subtitle": "Parámetros acústicos del Cluster 0 (mayor concentración de hits)",
        "bullets": [
            "Tempo medio: 125.0 BPM (pulso natural del pop, dance y reggaetón).",
            "Loudness: -6.14 dB (alta presencia sonora, compresión moderna).",
            "Bailabilidad: 0.61 / Energía: 0.76 (propensión al baile masivo).",
            "Carácter acústico: apenas 0.08 (instrumentación eléctrica/sintética).",
            "Duración óptima: 3 minutos y 34 segundos (máxima retención)."
        ],
        "highlight": "La receta sónica: 125 BPM, -6 dB, alta bailabilidad y 3.5 minutos de duración.",
        "script": "«Aquí está el hallazgo central: el grupo con mayor éxito comercial se ancla en torno a los 125 golpes por minuto, un volumen sonoro comprimido a -6 decibelios, alta bailabilidad y una duración promedio de 3 minutos y medio. Es el estándar rítmico de la música global contemporánea.»",
        "image": FIGS / "diapo_ritmo_exito.png"
    },
    {
        "num": "11",
        "tag": "COMPARATIVA ACÚSTICA",
        "title": "El Perfil de Menor Consumo en Streaming",
        "subtitle": "Parámetros físicos del Cluster 1 (música acústica / ambiental)",
        "bullets": [
            "Tempo medio: 108.4 BPM (tempo moderado o introspectivo).",
            "Loudness percibido: -13.02 dB (dinámica abierta, menor volumen).",
            "Carácter acústico: 0.82 (instrumentación puramente orgánica).",
            "Bailabilidad: 0.47 / Valencia: 0.26 (ánimo más melancólico o íntimo).",
            "Popularidad mediana: 28 puntos frente a 35 del perfil enérgico."
        ],
        "highlight": "Realidad del streaming: la música orgánica y dinámica tiene menor tracción masiva.",
        "script": "«En contraste, el perfil de baja popularidad promedia 108 BPM, un volumen mucho más bajo (-13 dB) y un 82% de textura acústica. Aunque es música artísticamente valiosa, el consumo masivo en streaming la penaliza en reproducciones.»",
        "image": FIGS / "05_perfiles_KMeans_pca.png"
    },
    {
        "num": "12",
        "tag": "EVALUACIÓN ESTADÍSTICA",
        "title": "¿El Ritmo Garantiza el Éxito? (Honestidad Científica)",
        "subtitle": "Prueba Kruskal-Wallis y solapamiento de distribuciones",
        "bullets": [
            "Contraste significativo: H = 15.21, p < 0.0001 (diferencia medible).",
            "Efecto modesto: epsilon-cuadrado = 0.0071.",
            "Solapamiento intercuartílico: ambos grupos comparten el rango [21 a 49].",
            "Veredicto: sonar a 125 BPM 'ayuda', pero NO garantiza ser un hit."
        ],
        "highlight": "El audio define el terreno de juego; el marketing y el artista definen el gol.",
        "script": "«¿Significa esto que producir a 125 BPM garantiza un hit? No. Estadísticamente hay una ventaja real, pero el rango de éxito es amplísimo: el marketing, el nombre del artista y la viralidad en redes siguen decidiendo qué canción despega.»",
        "image": FIGS / "06_popularidad_KMeans_pca.png"
    },
    {
        "num": "13",
        "tag": "BATALLA DE MODELOS",
        "title": "K-Means vs. GMM: Resultados Técnicos",
        "subtitle": "Métricas internas obligatorias evaluadas en el espacio común",
        "bullets": [
            "K-Means (PCA): Silhouette = 0.2477 | Davies-Bouldin = 1.6730 | Calinski = 493.7.",
            "GMM (PCA): Silhouette bajo (0.024) y Davies-Bouldin alto (2.68).",
            "Estabilidad: K-Means logró 99.4% ante semillas vs. 55.2% de GMM.",
            "Tiempo: K-Means entrenó en 0.14 s frente a 2.85 s de GMM."
        ],
        "highlight": "Ganador técnico: K-Means con PCA por estabilidad, parsimonia y velocidad.",
        "script": "«Técnicamente, K-Means con PCA fue el modelo ganador: logró la mayor separación de grupos, una estabilidad del 99% entre distintas corridas y tardó menos de una décima de segundo en clasificar miles de pistas.»",
        "image": FIGS / "diapo_comparativa_modelos.png"
    },
    {
        "num": "14",
        "tag": "APORTE METODOLÓGICO",
        "title": "La Ilusión de la Reducción Dimensional",
        "subtitle": "Por qué es vital evaluar con una 'Comparación Justa'",
        "bullets": [
            "En el espacio PCA, el Silhouette aparente de K-Means subió a 0.2680.",
            "Trampa: las distancias en 7 dimensiones se contraen frente a 10 dimensiones.",
            "Comparación Justa: evaluando las etiquetas de PCA en el espacio original, da 0.2477.",
            "Conclusión: PCA no inventa estructura; retiene la misma calidad (ARI = 0.983) con menos costo."
        ],
        "highlight": "Rigor: siempre se deben re-evaluar los clusters en el espacio físico original.",
        "script": "«Un aporte clave de nuestro trabajo fue la 'comparación justa': descubrimos que las métricas parecen subir en PCA solo porque las distancias se comprimen; al medir con rigor en el espacio original, la ganancia real es sutil pero filtra ruido.»",
        "image": None
    },
    {
        "num": "15",
        "tag": "ENTREGABLE APLICADO",
        "title": "SONORA: Explorador Musical Interactivo",
        "subtitle": "Herramienta standalone en HTML para navegación de catálogo",
        "bullets": [
            "Aplicación web autónoma (Explorador_Musical.html) que corre sin servidor.",
            "Buscador instantáneo por título o artista sobre las 10.000 pistas analizadas.",
            "Proyección interactiva en 2D (PC1 vs PC2) coloreada por grupos.",
            "Módulo 'Explorar desde aquí': sugiere pistas con sonido similar y enlace directo a Spotify."
        ],
        "highlight": "Transferencia real: un curador puede usar la herramienta hoy mismo en su navegador.",
        "script": "«No nos quedamos en gráficos estáticos: construimos SONORA, una aplicación web interactiva que corre localmente sin servidor, permitiendo a cualquier curador navegar el mapa sónico de 10.000 canciones y escuchar canciones similares en Spotify.»",
        "image": None
    },
    {
        "num": "16",
        "tag": "CONCLUSIONES Y CIERRE",
        "title": "Conclusiones y Trabajo Futuro",
        "subtitle": "Síntesis del proyecto de aprendizaje no supervisado",
        "bullets": [
            "La física del sonido (125 BPM, -6 dB) muestra una asociación medible con la popularidad.",
            "K-Means + PCA ofrece la solución más robusta, limpia y eficiente de segmentación.",
            "Limitaciones: datos estáticos (sin métricas temporales de playlists ni presupuesto de marketing).",
            "Futuro: incorporar análisis de letras (NLP) y descomposición espectral por fragmentos de audio."
        ],
        "highlight": "El aprendizaje no supervisado es la brújula para navegar el océano musical moderno.",
        "script": "«En conclusión: el aprendizaje no supervisado es una brújula potente para ordenar la música por su esencia física. Hay un ritmo preferido por el oyente moderno, pero la emoción y el talento siguen siendo el verdadero misterio. ¡Muchas gracias!»",
        "image": None
    }
]

for item in slides_data:
    slide = prs.slides.add_slide(blank_layout)
    
    # Fondo
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_DARK
    bg.line.fill.background()
    
    # Tag
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf_h = header_box.text_frame
    tf_h.word_wrap = True
    p_h = tf_h.paragraphs[0]
    p_h.text = f"{item['num']}  ·  {item['tag']}"
    p_h.font.size = Pt(11)
    p_h.font.bold = True
    p_h.font.color.rgb = ACCENT_GREEN
    
    # Título y Subtítulo
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(0.9))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = item['title']
    p_t.font.size = Pt(26)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_WHITE
    
    p_sub = tf_t.add_paragraph()
    p_sub.text = item['subtitle']
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = TEXT_MUTED
    p_sub.space_before = Pt(3)
    
    has_img = item['image'] is not None and Path(item['image']).is_file()
    
    if has_img:
        # Layout de 2 columnas: Texto a la izquierda, Gráfico a la derecha
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(6.2), Inches(3.9))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = RGBColor(45, 45, 45)
        card.line.width = Pt(1)
        
        content_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(5.8), Inches(3.6))
        tf_c = content_box.text_frame
        tf_c.word_wrap = True
        for i, bullet in enumerate(item['bullets']):
            p = tf_c.paragraphs[0] if i == 0 else tf_c.add_paragraph()
            p.text = f"•  {bullet}"
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_WHITE
            p.space_after = Pt(8)
            p.line_spacing = 1.15
            
        img_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.2), Inches(1.9), Inches(5.333), Inches(3.9))
        img_card.fill.solid()
        img_card.fill.fore_color.rgb = CARD_BG
        img_card.line.color.rgb = RGBColor(45, 45, 45)
        img_card.line.width = Pt(1)
        
        slide.shapes.add_picture(str(item['image']), Inches(7.35), Inches(2.05), Inches(5.033), Inches(3.6))
        
    else:
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(11.733), Inches(3.9))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = RGBColor(45, 45, 45)
        card.line.width = Pt(1)
        
        content_box = slide.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(11.133), Inches(3.5))
        tf_c = content_box.text_frame
        tf_c.word_wrap = True
        for i, bullet in enumerate(item['bullets']):
            p = tf_c.paragraphs[0] if i == 0 else tf_c.add_paragraph()
            p.text = f"•  {bullet}"
            p.font.size = Pt(15)
            p.font.color.rgb = TEXT_WHITE
            p.space_after = Pt(10)
            p.line_spacing = 1.15
            
    # Takeaway
    hl_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.05), Inches(11.733), Inches(0.9))
    hl_card.fill.solid()
    hl_card.fill.fore_color.rgb = HIGHLIGHT_BG
    hl_card.line.color.rgb = ACCENT_GREEN
    hl_card.line.width = Pt(1.5)
    
    hl_box = slide.shapes.add_textbox(Inches(1.0), Inches(6.1), Inches(11.333), Inches(0.8))
    tf_hl = hl_box.text_frame
    tf_hl.word_wrap = True
    p_hl = tf_hl.paragraphs[0]
    p_hl.text = f"TAKEAWAY:  {item['highlight']}"
    p_hl.font.size = Pt(12)
    p_hl.font.bold = True
    p_hl.font.color.rgb = ACCENT_GREEN
    
    # Speaker Notes
    notes_slide = slide.notes_slide
    notes_tf = notes_slide.notes_text_frame
    notes_tf.text = (
        f"[TIEMPO: 20 SEGUNDOS]\n\n"
        f"GUIÓN ORAL:\n{item['script']}\n\n"
        f"PUNTOS A ENFATIZAR:\n- {item['highlight']}"
    )

prs.save(OUTPUT_PPTX)
entregable_pptx = ROOT / "entregables" / "Presentacion_Proyecto_Bloque3.pptx"
prs.save(entregable_pptx)
print(f"Presentación actualizada con gráficos incrustados:\n- {OUTPUT_PPTX}\n- {entregable_pptx}")
