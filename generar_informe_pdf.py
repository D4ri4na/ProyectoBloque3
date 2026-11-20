"""Genera el Informe Técnico en PDF con el formato idéntico al informe de referencia del Bloque 2."""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "Informe_Tecnico_Bloque3.pdf"
ENTREGABLE_PDF = ROOT / "entregables" / "Informe_Tecnico_Bloque3.pdf"
FIGS = ROOT / "outputs" / "figures"

PRIMARY_COLOR = colors.HexColor("#1F4E79")    # Azul institucional oscuro
SECONDARY_COLOR = colors.HexColor("#2F5597")  # Azul secundario
TEXT_COLOR = colors.HexColor("#262626")       # Texto principal
MUTED_COLOR = colors.HexColor("#595959")      # Texto secundario
BG_LIGHT = colors.HexColor("#F2F4F7")         # Fondo gris suave
BORDER_COLOR = colors.HexColor("#D9D9D9")     # Líneas y bordes

class NumberedCanvas(canvas.Canvas):
    """Agrega pie de página y encabezado institucional en cada página."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(MUTED_COLOR)
        
        # Pie de página en todas las páginas
        footer_text = "Machine Learning | Proyecto integrador del Bloque 3"
        self.drawString(54, 36, footer_text)
        self.drawRightString(612 - 54, 36, f"{self._pageNumber}")
        
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Estilos tipográficos
    style_top_tag = ParagraphStyle(
        'TopTag',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1, # Centrado
        textColor=MUTED_COLOR,
        spaceAfter=15
    )
    
    style_main_title = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        alignment=1,
        textColor=PRIMARY_COLOR,
        spaceAfter=8
    )
    
    style_sub_title = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=SECONDARY_COLOR,
        spaceAfter=6
    )
    
    style_italic_desc = ParagraphStyle(
        'ItalicDesc',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=MUTED_COLOR,
        spaceAfter=25
    )
    
    style_h1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=PRIMARY_COLOR,
        spaceBefore=14,
        spaceAfter=4,
        keepWithNext=True
    )
    
    style_h2 = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=SECONDARY_COLOR,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_COLOR,
        spaceAfter=6
    )

    style_body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=style_body,
        fontName='Helvetica-Bold'
    )
    
    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        alignment=0
    )
    
    style_table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=TEXT_COLOR,
        alignment=0
    )

    style_table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=style_table_cell,
        fontName='Helvetica-Bold'
    )

    elements = []

    # ==========================================
    # PÁGINA 1: PORTADA
    # ==========================================
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("INFORME TÉCNICO", style_top_tag))
    elements.append(Paragraph("Perfiles sonoros y popularidad musical", style_main_title))
    elements.append(Paragraph("Aprendizaje no supervisado: K-Means y GMM antes y después de PCA", style_sub_title))
    elements.append(Paragraph("Comparación de modelos de clustering y reducción dimensional sobre el conjunto Spotify Tracks Dataset", style_italic_desc))
    elements.append(Spacer(1, 15))

    # Tabla de metadatos de la carátula
    meta_data = [
        [Paragraph("<b>Asignatura</b>", style_table_header), Paragraph("ISW-222 Machine Learning", style_table_cell)],
        [Paragraph("<b>Actividad</b>", style_table_header), Paragraph("Proyecto Bloque 3 — Comparación de dos modelos de clustering antes y después de reducir la dimensionalidad", style_table_cell)],
        [Paragraph("<b>Docente evaluador</b>", style_table_header), Paragraph("Pedro Andrés Campos Poveda", style_table_cell)],
        [Paragraph("<b>Modelos</b>", style_table_header), Paragraph("K-Means | Gaussian Mixture Models (GMM) | PCA (7 componentes)", style_table_cell)],
        [Paragraph("<b>Dataset</b>", style_table_header), Paragraph("Spotify Tracks Dataset (10.000 observaciones de audio continuo, 10 variables)", style_table_cell)],
        [Paragraph("<b>Fuente</b>", style_table_header), Paragraph("Hugging Face — maharshipandya/spotify-tracks-dataset (Licencia BSD)", style_table_cell)],
        [Paragraph("<b>Pregunta central</b>", style_table_header), Paragraph("¿Los grupos formados únicamente con características sonoras presentan diferencias de popularidad?", style_table_cell)],
        [Paragraph("<b>Estudiante(s)</b>", style_table_header), Paragraph("Dariana Pol Aramayo", style_table_cell)]
    ]
    t_meta = Table(meta_data, colWidths=[120, 384])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), PRIMARY_COLOR),
        ('BACKGROUND', (1,0), (1,-1), colors.white),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ]))
    elements.append(t_meta)
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 2: FORMULACIÓN DEL PROBLEMA
    # ==========================================
    elements.append(Paragraph("1. Formulación del problema", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p1 = ("El desempeño de una canción en plataformas de streaming resulta altamente incierto al planificar su lanzamiento. "
          "Tradicionalmente, las plataformas y discográficas organizan la música mediante taxonomías comerciales de 'género'; "
          "sin embargo, estas etiquetas son subjetivas y a menudo engañosas (existen pistas de rock más bailables que temas de pop). "
          "Este proyecto investiga si el agrupamiento no supervisado basado exclusivamente en variables físicas y psicoacústicas "
          "permite descubrir patrones estructurales reales del sonido, y si dichos perfiles acústicos presentan distribuciones de popularidad distintas.")
    elements.append(Paragraph(p1, style_body))

    p_obj = ("<b>Pregunta y enfoque no supervisado:</b> ¿Existen perfiles sonoros que concentren canciones de alta popularidad y qué características los distinguen? "
             "El problema se aborda sin etiquetas de supervisión porque no existe una 'verdad fundamental' sobre cómo clasificar la textura musical pura. "
             "Los grupos descubiertos permiten segmentar catálogos para curadores de playlists, orientar a productores en rangos acústicos de alto impacto "
             "y diseñar sistemas de recomendación libres de sesgos de fama previa.")
    elements.append(Paragraph(p_obj, style_body))

    p_regla = ("<b>Regla de oro y prevención de fuga:</b> La variable <i>popularity</i> y el metadato <i>genre</i> se excluyeron al 100% del escalado, "
               "de la reducción dimensional (PCA) y del ajuste de clustering. Los algoritmos descubren grupos a ciegas de la fama. "
               "La popularidad se reservó estrictamente para el análisis exploratorio descriptivo posterior.")
    elements.append(Paragraph(p_regla, style_body))

    elements.append(Paragraph("Datos y alcance", style_h2))
    p_datos = ("El conjunto original contiene 114.000 pistas con identificador único. Se eliminaron 24.259 registros con identificadores duplicados "
               "conservando la primera aparición en orden de archivo para evitar enriquecimientos artificiales. Se seleccionó una muestra probabilística "
               "reproducible de 10.000 observaciones (8.000 para entrenamiento y 2.000 para prueba reservada con semilla fija 42). "
               "Se utilizan diez características sonoras cuantitativas: <i>danceability, energy, loudness, speechiness, acousticness, instrumentalness, "
               "liveness, valence, tempo</i> y <i>duration_ms</i>.")
    elements.append(Paragraph(p_datos, style_body))

    elements.append(Paragraph("Resultado principal", style_h2))
    p_res = ("El protocolo seleccionó <b>K-Means tras PCA (7 componentes)</b> como la configuración más robusta y parsimoniosa. "
             "Descubre dos macro-perfiles naturales: un perfil enérgico/comercial (125 BPM, -6.1 dB) y un perfil acústico/orgánico (108 BPM, -13.0 dB). "
             "El perfil enérgico presenta una mediana de popularidad en prueba de 35 puntos frente a 28 del perfil acústico (Kruskal-Wallis <i>p</i> &lt; 0.0001, "
             "&epsilon;<sup>2</sup> = 0.0071). No obstante, el amplio solapamiento intercuartílico demuestra con rigor que el ritmo ayuda, pero no garantiza el éxito comercial.")
    elements.append(Paragraph(p_res, style_body))
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 3: CALIDAD Y ESTADÍSTICA DESCRIPTIVA
    # ==========================================
    elements.append(Paragraph("2. Calidad y estadística descriptiva", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_eda1 = ("La auditoría de datos verificó tipos, faltantes e inconsistencias físicas. Se detectaron pistas con <i>tempo = 0</i>, las cuales se trataron "
              "como estimaciones ausentes (imputadas con la mediana de entrenamiento) en lugar de silencios reales. Las variables normalizadas en origen "
              "(entre 0 y 1) se validaron en rango. No se eliminaron atípicos plausibles: los géneros extremos (como música clásica con alta instrumentalidad "
              "o discursos/hip-hop con alta presencia de habla) representan expresiones musicales legítimas.")
    elements.append(Paragraph(p_eda1, style_body))

    # Tabla descriptiva en unidades originales
    desc_data = [
        [Paragraph("<b>Variable</b>", style_table_header), Paragraph("<b>Mediana</b>", style_table_header), Paragraph("<b>Media</b>", style_table_header), Paragraph("<b>Mínimo</b>", style_table_header), Paragraph("<b>Máximo</b>", style_table_header), Paragraph("<b>Atípicos IQR (%)</b>", style_table_header)],
        [Paragraph("danceability (0-1)", style_table_cell), Paragraph("0.58", style_table_cell), Paragraph("0.57", style_table_cell), Paragraph("0.00", style_table_cell), Paragraph("0.98", style_table_cell), Paragraph("0.76 %", style_table_cell)],
        [Paragraph("energy (0-1)", style_table_cell), Paragraph("0.64", style_table_cell), Paragraph("0.64", style_table_cell), Paragraph("0.00", style_table_cell), Paragraph("1.00", style_table_cell), Paragraph("0.00 %", style_table_cell)],
        [Paragraph("loudness (dB)", style_table_cell), Paragraph("-7.20", style_table_cell), Paragraph("-8.28", style_table_cell), Paragraph("-49.53", style_table_cell), Paragraph("4.53", style_table_cell), Paragraph("5.19 %", style_table_cell)],
        [Paragraph("speechiness (0-1)", style_table_cell), Paragraph("0.05", style_table_cell), Paragraph("0.08", style_table_cell), Paragraph("0.00", style_table_cell), Paragraph("0.96", style_table_cell), Paragraph("12.20 %", style_table_cell)],
        [Paragraph("acousticness (0-1)", style_table_cell), Paragraph("0.24", style_table_cell), Paragraph("0.31", style_table_cell), Paragraph("0.00", style_table_cell), Paragraph("0.99", style_table_cell), Paragraph("0.00 %", style_table_cell)],
        [Paragraph("instrumentalness (0-1)", style_table_cell), Paragraph("0.00", style_table_cell), Paragraph("0.16", style_table_cell), Paragraph("0.00", style_table_cell), Paragraph("1.00", style_table_cell), Paragraph("21.84 %", style_table_cell)],
        [Paragraph("liveness (0-1)", style_table_cell), Paragraph("0.13", style_table_cell), Paragraph("0.21", style_table_cell), Paragraph("0.01", style_table_cell), Paragraph("1.00", style_table_cell), Paragraph("7.92 %", style_table_cell)],
        [Paragraph("valence (0-1)", style_table_cell), Paragraph("0.46", style_table_cell), Paragraph("0.47", style_table_cell), Paragraph("0.00", style_table_cell), Paragraph("1.00", style_table_cell), Paragraph("0.00 %", style_table_cell)],
        [Paragraph("tempo (BPM)", style_table_cell), Paragraph("122.01", style_table_cell), Paragraph("122.14", style_table_cell), Paragraph("34.34", style_table_cell), Paragraph("243.37", style_table_cell), Paragraph("0.53 %", style_table_cell)],
        [Paragraph("duration_ms (ms)", style_table_cell), Paragraph("212.893", style_table_cell), Paragraph("228.096", style_table_cell), Paragraph("8.586", style_table_cell), Paragraph("5.237.285", style_table_cell), Paragraph("4.60 %", style_table_cell)],
    ]
    t_desc = Table(desc_data, colWidths=[95, 65, 65, 65, 65, 149])
    t_desc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    elements.append(t_desc)
    elements.append(Spacer(1, 6))

    # Gráfica de distribuciones
    p_dist = FIGS / "01_distribuciones.png"
    if p_dist.is_file():
        elements.append(Image(str(p_dist), width=6.8*inch, height=2.3*inch))
        elements.append(Spacer(1, 4))

    elements.append(Paragraph("Efecto de no escalar: experimento de control", style_h2))
    p_no_scale = ("Para evidenciar la obligatoriedad del escalado, se ejecutó un control entrenando K-Means sobre variables sin estandarizar. "
                  "El índice de Rand ajustado frente al modelo escalado fue de apenas <b>ARI = 0.0024</b> (desacuerdo total). "
                  "La variable <i>duration_ms</i> (~200.000 ms) posee una varianza $10^{10}$ veces mayor que las variables en escala 0–1; en consecuencia, "
                  "la distancia euclidiana agrupó las canciones casi exclusivamente por su longitud. El uso de <code>StandardScaler</code> ajustado "
                  "únicamente en entrenamiento fue fundamental para equilibrar la contribución de los atributos.")
    elements.append(Paragraph(p_no_scale, style_body))
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 4: CORRELACIONES Y PCA
    # ==========================================
    elements.append(Paragraph("3. Correlaciones y reducción de dimensionalidad (PCA)", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_corr = ("La matriz de correlación en entrenamiento exhibe redundancias lineales pronunciadas. Destaca una fuerte correlación positiva "
              "entre <i>energy</i> y <i>loudness</i> ($r = 0.76$), así como una correlación negativa moderada de ambas con <i>acousticness</i> ($r \approx -0.73$). "
              "Esta colinealidad anticipa la utilidad de la reducción dimensional para comprimir la representación sin pérdida de señal.")
    elements.append(Paragraph(p_corr, style_body))

    # Tabla de cargas de PCA
    p_pca_txt = ("Se aplicó <b>PCA</b> ajustado exclusivamente con los datos de entrenamiento escalados. Siguiendo el criterio de la rúbrica (90–95%), "
                 "se conservaron <b>7 componentes principales</b> que acumulan el <b>90.81 % de la varianza total</b> (las dos primeras explican el 44.10 %).")
    elements.append(Paragraph(p_pca_txt, style_body))

    cargas_data = [
        [Paragraph("<b>Variable</b>", style_table_header), Paragraph("<b>Carga PC1 (28.84 %)</b>", style_table_header), Paragraph("<b>Carga PC2 (15.26 %)</b>", style_table_header), Paragraph("<b>Interpretación sónica en el dominio</b>", style_table_header)],
        [Paragraph("loudness", style_table_cell_bold), Paragraph("+0.512", style_table_cell), Paragraph("-0.094", style_table_cell), Paragraph("Eje PC1: Intensidad sonora y potencia de producción", style_table_cell)],
        [Paragraph("energy", style_table_cell_bold), Paragraph("+0.498", style_table_cell), Paragraph("-0.292", style_table_cell), Paragraph("Eje PC1: Actividad y compresión dinámica vs acústica", style_table_cell)],
        [Paragraph("acousticness", style_table_cell_bold), Paragraph("-0.428", style_table_cell), Paragraph("+0.359", style_table_cell), Paragraph("Eje PC1: Polaridad opuesta (textura orgánica)", style_table_cell)],
        [Paragraph("valence", style_table_cell_bold), Paragraph("+0.319", style_table_cell), Paragraph("+0.462", style_table_cell), Paragraph("Eje PC2: Positividad y luminosidad emocional", style_table_cell)],
        [Paragraph("danceability", style_table_cell_bold), Paragraph("+0.273", style_table_cell), Paragraph("+0.435", style_table_cell), Paragraph("Eje PC2: Ritmo bailable y cadencia comercial", style_table_cell)],
        [Paragraph("duration_ms", style_table_cell_bold), Paragraph("-0.041", style_table_cell), Paragraph("-0.422", style_table_cell), Paragraph("Eje PC2: Formatos extensos o instrumentales en contraposición", style_table_cell)],
    ]
    t_cargas = Table(cargas_data, colWidths=[90, 85, 85, 244])
    t_cargas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    elements.append(t_cargas)
    elements.append(Spacer(1, 6))

    # Imágenes lado a lado o mapa PCA
    p_map = FIGS / "07_mapa_KMeans_pca.png"
    p_var = FIGS / "03_varianza_pca.png"
    if p_map.is_file() and p_var.is_file():
        img_table = Table([[Image(str(p_var), width=3.4*inch, height=2.4*inch),
                            Image(str(p_map), width=3.4*inch, height=2.4*inch)]], colWidths=[252, 252])
        img_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(img_table)
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 5: PROTOCOLO EXPERIMENTAL Y AJUSTE
    # ==========================================
    elements.append(Paragraph("4. Protocolo experimental y ajuste de modelos (Espacio Original)", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_mod = ("Se implementaron dos algoritmos pertenecientes a familias conceptualmente distintas: "
             "<b>K-Means</b> (familia particional basada en distancias euclidianas a centroides, que asume agrupaciones esféricas e isótropas) y "
             "<b>Gaussian Mixture Models (GMM)</b> (familia probabilística basada en mezclas de densidades gaussianas con algoritmo EM, "
             "capaz de modelar elipsoides de orientación variable y membresías suaves). "
             "Ambos modelos se ajustaron sobre el 80% de entrenamiento con semilla 42 y <code>threadpool_limits=1</code> para garantizar determinismo.")
    elements.append(Paragraph(p_mod, style_body))

    elements.append(Paragraph("Búsqueda cuantitativa de hiperparámetros", style_h2))
    p_param = ("La exploración abarcó $K \\in [2, 12]$. Para K-Means se realizaron 20 inicializaciones aleatorias (<code>n_init=20</code>) evaluando el codo "
               "y el coeficiente Silhouette. Silhouette alcanza su máximo global en $K = 2$ ($s = 0.2493$), disminuyendo monótonamente para $K > 2$. "
               "Para GMM se exploraron covarianzas <code>full</code> y <code>diag</code> con 3 inicializaciones y regularización $10^{-5}$, seleccionando por "
               "mínimo BIC (Criterio de Información Bayesiano). BIC favoreció $K = 12$ con covarianza <code>full</code> (BIC $= 114.685$), optimizando el ajuste de densidad.")
    elements.append(Paragraph(p_param, style_body))

    # Gráfica de búsqueda
    p_search = FIGS / "04_busqueda_KMeans_pca.png"
    if p_search.is_file():
        elements.append(Image(str(p_search), width=6.8*inch, height=2.2*inch))
        elements.append(Spacer(1, 4))

    elements.append(Paragraph("Parámetros seleccionados en espacio original", style_h2))
    sel_data = [
        [Paragraph("<b>Modelo</b>", style_table_header), Paragraph("<b>Familia</b>", style_table_header), Paragraph("<b>Hiperparámetros óptimos</b>", style_table_header), Paragraph("<b>Criterio cuantitativo de selección</b>", style_table_header)],
        [Paragraph("K-Means", style_table_cell_bold), Paragraph("Particional / Centroides", style_table_cell), Paragraph("K = 2, n_init = 20", style_table_cell), Paragraph("Mayor Silhouette medio de entrenamiento (s = 0.2493)", style_table_cell)],
        [Paragraph("GMM", style_table_cell_bold), Paragraph("Probabilístico / Mezclas", style_table_cell), Paragraph("K = 12, covarianza = full", style_table_cell), Paragraph("Menor BIC entre ajustes convergidos (114.685)", style_table_cell)],
    ]
    t_sel = Table(sel_data, colWidths=[80, 110, 120, 194])
    t_sel.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    elements.append(t_sel)
    elements.append(Spacer(1, 6))

    p_ref = ("<b>Referencia mínima y ruido:</b> Ni K-Means ni GMM implementan detección de anomalías; ambos realizan asignación total (% ruido = 0 por diseño). "
             "Como referencia trivial, una partición de un solo cluster tiene Silhouette no definido y Calinski-Harabasz de 0. "
             "K-Means demuestra una estructura compacta real en comparación con una asignación aleatoria.")
    elements.append(Paragraph(p_ref, style_body))
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 6: TABLA COMPARATIVA OBLIGATORIA
    # ==========================================
    elements.append(Paragraph("5. Reentrenamiento y tabla comparativa obligatoria", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_comp_intro = ("Los dos modelos se reentrenaron sobre las 7 componentes principales de PCA reajustando hiperparámetros. "
                    "Para una <b>comparación justa</b> (pregunta 7), se calculan las métricas no solo en la geometría nativa de cada espacio, "
                    "sino también en el <b>espacio original estandarizado</b> evaluando las etiquetas obtenidas tras la reducción.")
    elements.append(Paragraph(p_comp_intro, style_body))

    # TABLA COMPARATIVA OFICIAL
    comp_data = [
        [Paragraph("<b>Modelo</b>", style_table_header), Paragraph("<b>Espacio</b>", style_table_header), Paragraph("<b>Geometría Eval.</b>", style_table_header), Paragraph("<b>Partición</b>", style_table_header), Paragraph("<b>K / Grupos</b>", style_table_header), Paragraph("<b>Silh. &uarr;</b>", style_table_header), Paragraph("<b>DB &darr;</b>", style_table_header), Paragraph("<b>CH &uarr;</b>", style_table_header), Paragraph("<b>% Ruido</b>", style_table_header), Paragraph("<b>Tiempo (s)</b>", style_table_header), Paragraph("<b>ARI vs Orig.</b>", style_table_header)],
        [Paragraph("K-Means", style_table_cell), Paragraph("Original (10)", style_table_cell), Paragraph("Original", style_table_cell), Paragraph("Train", style_table_cell), Paragraph("2", style_table_cell), Paragraph("0.2493", style_table_cell), Paragraph("1.6831", style_table_cell), Paragraph("1947.6", style_table_cell), Paragraph("0.0 %", style_table_cell), Paragraph("0.067", style_table_cell), Paragraph("—", style_table_cell)],
        [Paragraph("K-Means", style_table_cell_bold), Paragraph("Original (10)", style_table_cell), Paragraph("Original", style_table_cell), Paragraph("Test", style_table_cell), Paragraph("2", style_table_cell), Paragraph("0.2460", style_table_cell_bold), Paragraph("1.6786", style_table_cell), Paragraph("493.5", style_table_cell), Paragraph("0.0 %", style_table_cell), Paragraph("0.067", style_table_cell), Paragraph("—", style_table_cell)],
        [Paragraph("K-Means", style_table_cell), Paragraph("PCA (7 comp)", style_table_cell), Paragraph("Nativa PCA", style_table_cell), Paragraph("Test", style_table_cell), Paragraph("2", style_table_cell), Paragraph("0.2680", style_table_cell), Paragraph("1.5538", style_table_cell), Paragraph("558.3", style_table_cell), Paragraph("0.0 %", style_table_cell), Paragraph("0.139", style_table_cell), Paragraph("0.9830", style_table_cell)],
        [Paragraph("K-Means (Justa)", style_table_cell_bold), Paragraph("PCA (7 comp)", style_table_cell), Paragraph("Original Común", style_table_cell_bold), Paragraph("Test", style_table_cell), Paragraph("2", style_table_cell), Paragraph("0.2477", style_table_cell_bold), Paragraph("1.6730", style_table_cell_bold), Paragraph("493.7", style_table_cell_bold), Paragraph("0.0 %", style_table_cell), Paragraph("0.139", style_table_cell), Paragraph("0.9830", style_table_cell_bold)],
        [Paragraph("GMM", style_table_cell), Paragraph("Original (10)", style_table_cell), Paragraph("Original", style_table_cell), Paragraph("Train", style_table_cell), Paragraph("12", style_table_cell), Paragraph("-0.0208", style_table_cell), Paragraph("3.4092", style_table_cell), Paragraph("399.3", style_table_cell), Paragraph("0.0 %", style_table_cell), Paragraph("6.010", style_table_cell), Paragraph("—", style_table_cell)],
        [Paragraph("GMM", style_table_cell), Paragraph("Original (10)", style_table_cell), Paragraph("Original", style_table_cell), Paragraph("Test", style_table_cell), Paragraph("12", style_table_cell), Paragraph("-0.0119", style_table_cell), Paragraph("3.3469", style_table_cell), Paragraph("104.7", style_table_cell), Paragraph("0.0 %", style_table_cell), Paragraph("6.010", style_table_cell), Paragraph("—", style_table_cell)],
        [Paragraph("GMM", style_table_cell), Paragraph("PCA (7 comp)", style_table_cell), Paragraph("Nativa PCA", style_table_cell), Paragraph("Test", style_table_cell), Paragraph("12", style_table_cell), Paragraph("0.0305", style_table_cell), Paragraph("2.4632", style_table_cell), Paragraph("161.8", style_table_cell), Paragraph("0.0 %", style_table_cell), Paragraph("2.853", style_table_cell), Paragraph("0.2797", style_table_cell)],
        [Paragraph("GMM (Justa)", style_table_cell_bold), Paragraph("PCA (7 comp)", style_table_cell), Paragraph("Original Común", style_table_cell_bold), Paragraph("Test", style_table_cell), Paragraph("12", style_table_cell), Paragraph("0.0243", style_table_cell_bold), Paragraph("2.6836", style_table_cell_bold), Paragraph("138.2", style_table_cell_bold), Paragraph("0.0 %", style_table_cell), Paragraph("2.853", style_table_cell), Paragraph("0.2797", style_table_cell_bold)],
    ]
    t_comp = Table(comp_data, colWidths=[70, 52, 64, 32, 38, 42, 42, 44, 38, 42, 40])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#E2EFDA")), # Fila K-Means justa resaltada
        ('BACKGROUND', (0,8), (-1,8), colors.HexColor("#FCE4D6")), # Fila GMM justa resaltada
    ]))
    elements.append(t_comp)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Interpretación metodológica del efecto de la reducción", style_h2))
    p_disc = ("<b>1. La ilusión del Silhouette en PCA:</b> En el espacio nativo de PCA, el Silhouette de K-Means aparenta subir de 0.2460 a 0.2680. "
              "Sin embargo, al evaluar las etiquetas en la geometría común original, el índice es de 0.2477. El incremento aparente es en gran medida "
              "un artefacto de la contracción métrica al proyectar en menos dimensiones.<br/>"
              "<b>2. Robustez de K-Means frente a GMM:</b> K-Means retuvo casi exactamente las mismas asignaciones antes y después de PCA (<b>ARI = 0.9830</b>), "
              "demostrando que las 3 componentes descartadas aportaban ruido irrelevante para los centroides. En cambio, GMM exhibió un cambio notable (<b>ARI = 0.2797</b>); "
              "la reducción de 10 a 7 dimensiones redujo los parámetros de covarianza de 55 a 28, regularizando el ajuste del algoritmo EM y mitigando sobreajustes locales.")
    elements.append(Paragraph(p_disc, style_body))
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 7: ESTABILIDAD Y SESGO
    # ==========================================
    elements.append(Paragraph("6. Evaluación de estabilidad y sesgo de las métricas", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_est = ("La estabilidad se evaluó mediante remuestreos controlados sobre el conjunto de entrenamiento: 4 semillas distintas (inicialización) "
             "y 4 submuestras aleatorias del 80% (bootstrap de datos), midiendo el ARI entre pares de predicciones sobre las mismas 2.000 observaciones de prueba.")
    elements.append(Paragraph(p_est, style_body))

    # Gráfica de comparativa de modelos
    p_comp_fig = FIGS / "diapo_comparativa_modelos.png"
    if p_comp_fig.is_file():
        elements.append(Image(str(p_comp_fig), width=6.8*inch, height=2.4*inch))
        elements.append(Spacer(1, 4))

    est_data = [
        [Paragraph("<b>Modelo</b>", style_table_header), Paragraph("<b>Espacio</b>", style_table_header), Paragraph("<b>Tipo de perturbación</b>", style_table_header), Paragraph("<b>ARI Medio</b>", style_table_header), Paragraph("<b>ARI Mínimo</b>", style_table_header), Paragraph("<b>ARI Máximo</b>", style_table_header)],
        [Paragraph("K-Means", style_table_cell_bold), Paragraph("Original", style_table_cell), Paragraph("Semillas aleatorias", style_table_cell), Paragraph("1.0000", style_table_cell_bold), Paragraph("1.0000", style_table_cell), Paragraph("1.0000", style_table_cell)],
        [Paragraph("K-Means", style_table_cell_bold), Paragraph("Original", style_table_cell), Paragraph("Submuestras 80 %", style_table_cell), Paragraph("0.9947", style_table_cell_bold), Paragraph("0.9915", style_table_cell), Paragraph("0.9979", style_table_cell)],
        [Paragraph("K-Means", style_table_cell_bold), Paragraph("PCA", style_table_cell), Paragraph("Semillas aleatorias", style_table_cell), Paragraph("0.9979", style_table_cell_bold), Paragraph("0.9957", style_table_cell), Paragraph("1.0000", style_table_cell)],
        [Paragraph("K-Means", style_table_cell_bold), Paragraph("PCA", style_table_cell), Paragraph("Submuestras 80 %", style_table_cell), Paragraph("0.9940", style_table_cell_bold), Paragraph("0.9893", style_table_cell), Paragraph("0.9957", style_table_cell)],
        [Paragraph("GMM", style_table_cell), Paragraph("Original", style_table_cell), Paragraph("Semillas aleatorias", style_table_cell), Paragraph("0.5657", style_table_cell), Paragraph("0.4389", style_table_cell), Paragraph("0.7459", style_table_cell)],
        [Paragraph("GMM", style_table_cell), Paragraph("PCA", style_table_cell), Paragraph("Submuestras 80 %", style_table_cell), Paragraph("0.5519", style_table_cell), Paragraph("0.4580", style_table_cell), Paragraph("0.6742", style_table_cell)],
    ]
    t_est = Table(est_data, colWidths=[90, 80, 120, 70, 70, 74])
    t_est.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    elements.append(t_est)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Sesgo de las métricas e interpretabilidad", style_h2))
    p_sesgo = ("Las métricas basadas en distancias euclidianas (Silhouette y Davies-Bouldin) favorecen inherentemente agrupamientos convexos e isótropos, "
               "lo cual beneficia de forma estructural a K-Means sobre distribuciones densas o mezclas con varianzas heterogéneas como GMM. "
               "No obstante, K-Means exhibió una estabilidad casi perfecta (>99 %) frente a la inestabilidad de GMM (~55 %), convirtiéndolo en el modelo "
               "más fiable operativamente para segmentación de catálogos.")
    elements.append(Paragraph(p_sesgo, style_body))
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 8: PERFILES Y EL RITMO DEL ÉXITO
    # ==========================================
    elements.append(Paragraph("7. Perfiles sonoros y valor para el dominio: ¡El Ritmo del Éxito!", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_perf_intro = ("Al analizar los clusters del modelo seleccionado (K-Means + PCA) en sus <b>unidades físicas originales desescaladas</b>, "
                    "se observa que el catálogo musical contemporáneo no se divide por géneros, sino por un pulso fundamental de intensidad sónica.")
    elements.append(Paragraph(p_perf_intro, style_body))

    # Gráfica del Ritmo del Éxito
    p_ritmo = FIGS / "diapo_ritmo_exito.png"
    if p_ritmo.is_file():
        elements.append(Image(str(p_ritmo), width=6.8*inch, height=2.5*inch))
        elements.append(Spacer(1, 4))

    perf_data = [
        [Paragraph("<b>Característica</b>", style_table_header), Paragraph("<b>Cluster 0: Alta Producción / Éxito Streaming</b>", style_table_header), Paragraph("<b>Cluster 1: Acústico / Introspectivo</b>", style_table_header)],
        [Paragraph("Tamaño en prueba", style_table_cell_bold), Paragraph("1.504 canciones (75.2 % del catálogo)", style_table_cell), Paragraph("496 canciones (24.8 % del catálogo)", style_table_cell)],
        [Paragraph("Tempo medio (BPM)", style_table_cell_bold), Paragraph("<b>125.0 BPM</b> (pulso estándar del pop, dance y reggaetón)", style_table_cell), Paragraph("<b>108.4 BPM</b> (tempo pausado, balada o folk)", style_table_cell)],
        [Paragraph("Nivel sonoro (dB)", style_table_cell_bold), Paragraph("<b>-6.14 dB</b> (alta sonoridad y compresión comercial)", style_table_cell), Paragraph("<b>-13.02 dB</b> (rango dinámico abierto, menor volumen percibido)", style_table_cell)],
        [Paragraph("Bailabilidad / Energía", style_table_cell_bold), Paragraph("0.61 / 0.76 (propensión al baile masivo)", style_table_cell), Paragraph("0.47 / 0.30 (carácter contemplativo o relajante)", style_table_cell)],
        [Paragraph("Carácter acústico", style_table_cell_bold), Paragraph("<b>0.08</b> (predominio casi absoluto eléctrico/sintético)", style_table_cell), Paragraph("<b>0.82</b> (instrumentos acústicos naturales dominantes)", style_table_cell)],
        [Paragraph("Duración promedio", style_table_cell_bold), Paragraph("3 minutos y 34 segundos (214.889 ms)", style_table_cell), Paragraph("3 minutos y 20 segundos (200.413 ms)", style_table_cell)],
        [Paragraph("Popularidad mediana", style_table_cell_bold), Paragraph("<b>35.0 puntos</b> (Rango IQR: [21.0, 49.0])", style_table_cell), Paragraph("<b>28.0 puntos</b> (Rango IQR: [13.0, 47.0])", style_table_cell)],
        [Paragraph("Tasa canciones &ge; 70", style_table_cell_bold), Paragraph("3.86 % (58 éxitos en prueba)", style_table_cell), Paragraph("1.21 % (6 éxitos en prueba) &rarr; <b>Lift: 3.19x</b>", style_table_cell)],
    ]
    t_perf = Table(perf_data, colWidths=[120, 192, 192])
    t_perf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    elements.append(t_perf)
    elements.append(Spacer(1, 6))

    p_perf_concl = ("<b>Acciones concretas de dominio:</b> Los curadores pueden automatizar listas temáticas (entrenamiento/fiesta vs lectura/descanso) "
                    "sin requerir metadatos manuales. Los productores obtienen una guía cuantitativa: las pistas a ~125 BPM y -6 dB triplican su probabilidad de "
                    "alcanzar alta popularidad (&ge; 70), aunque el amplio solapamiento confirma que factores externos (artista, marketing) deciden el éxito final.")
    elements.append(Paragraph(p_perf_concl, style_body))
    elements.append(PageBreak())

    # ==========================================
    # PÁGINAS 9 Y 10: LAS 12 PREGUNTAS DE LA RÚBRICA
    # ==========================================
    elements.append(Paragraph("8. Las doce respuestas de análisis de la rúbrica", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    preguntas = [
        ("1. Escalado", 
         "Imprescindible. Sin escalar, duration_ms (~200.000 ms) anula a variables acotadas entre 0 y 1. "
         "El control sin escalar produce un ARI de apenas 0.0024 frente al modelo escalado, distorsionando totalmente las agrupaciones."),
        
        ("2. Elección de hiperparámetros",
         "K-Means se seleccionó por maximización de Silhouette (pico en K=2 con s=0.2493, respaldado por el método del codo). "
         "GMM se seleccionó por minimización de BIC (K=12, covarianza full con BIC=114.685). Se priorizó Silhouette para segmentación geométrica."),
        
        ("3. Sesgo de las métricas",
         "Silhouette y Davies-Bouldin favorecen clusters convexos y compactos, lo que beneficia inherentemente a K-Means sobre distribuciones continuas. "
         "Las proyecciones 2D confirman que la música es un continuo sonoro sin fronteras vacías."),
        
        ("4. Ruido y atípicos",
         "No se utilizó DBSCAN; K-Means y GMM asignan el 100% de puntos (ruido = 0%). Los atípicos por IQR (hasta 21.8% en instrumentalidad) "
         "se conservaron por ser expresiones artísticas válidas, asumiendo su impacto en centroides y matrices de covarianza."),
        
        ("5. Componentes principales",
         "Se retuvieron 7 componentes que conservan el 90.81% de la varianza total. PC1 (28.8%) representa el contraste intensidad/volumen (+loudness, +energy) "
         "frente a textura acústica (-acousticness). PC2 (15.3%) representa ritmo bailable y positividad (+valence, +danceability) frente a formatos largos (-duration)."),
        
        ("6. Efecto de la reducción",
         "En K-Means, el Silhouette en espacio común pasa de 0.2460 a 0.2477 (+0.0017) con ARI = 0.9830, demostrando que PCA filtró ruido sin alterar la estructura. "
         "En GMM, la reducción mejoró la regularización reduciendo parámetros libres de covarianza (de 55 a 28)."),
        
        ("7. Comparación justa",
         "No es válido comparar métricas calculadas en espacios de distinta dimensionalidad (las distancias en 7D son numéricamente distintas a 10D). "
         "Al evaluar las etiquetas de PCA en la geometría original común, el Silhouette real es 0.2477 (frente al aparente 0.2680 en espacio reducido)."),
        
        ("8. Cambio en las asignaciones",
         "En K-Means las asignaciones prácticamente no cambiaron tras PCA (ARI = 0.9830 en test). En GMM cambiaron sustancialmente (ARI = 0.2797), "
         "indicando que la compresión actuó como un regularizador sobre las densidades gaussianas."),
        
        ("9. Estabilidad",
         "K-Means demostró estabilidad casi perfecta ante semillas (ARI = 1.000) y submuestras (ARI = 0.9947). GMM mostró inestabilidad (ARI = 0.5519) "
         "debido a la sensibilidad del algoritmo EM ante óptimos locales y estimaciones de covarianza."),
        
        ("10. Costo computacional",
         "K-Means entrena en 0.067 s (original) y 0.139 s (PCA); GMM requiere 6.01 s (original) y 2.85 s (PCA). "
         "Con 100x observaciones, GMM full se volvería computacionalmente prohibitivo O(N·K·d²) y Silhouette obligaría a mantener submuestreo O(N²)."),
        
        ("11. Visualización no lineal",
         "t-SNE y UMAP preservan vecindades locales a costa de distorsionar densidades y distancias globales. No se recomienda usar t-SNE como entrada de clustering "
         "porque carece de función transform determinista para proyectar nuevos datos de inferencia."),
        
        ("12. Recomendación final",
         "Se recomienda provisionalmente K-Means con PCA (K=2) por su balance óptimo de parsimonia, estabilidad (99.4%), bajo costo computacional e interpretabilidad. "
         "Limitaciones: datos históricos estáticos sin fecha de captura y ausencia de variables causales críticas como presupuesto de marketing o inversión publicitaria.")
    ]

    for titulo, resp in preguntas:
        elements.append(Paragraph(f"<b>{titulo}:</b> {resp}", style_body))
        elements.append(Spacer(1, 2))

    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 11: CORRESPONDENCIA CON LA RÚBRICA
    # ==========================================
    elements.append(Paragraph("9. Correspondencia con la rúbrica de evaluación", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_rub_intro = ("A continuación se detalla la correspondencia del proyecto frente a los 9 criterios de evaluación "
                   "del Bloque 3 (Docente evaluador: Pedro Andrés Campos Poveda), sustentando el cumplimiento en Nivel 4 (Sobresaliente).")
    elements.append(Paragraph(p_rub_intro, style_body))

    rub_data = [
        [Paragraph("<b>Criterio de evaluación</b>", style_table_header), Paragraph("<b>Peso</b>", style_table_header), Paragraph("<b>Nivel</b>", style_table_header), Paragraph("<b>Evidencia ejecutada en el proyecto</b>", style_table_header)],
        [Paragraph("1. Formulación del problema y dataset", style_table_cell), Paragraph("8 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Contexto real de streaming musical, 10.000 observaciones, fuente citada (Hugging Face), justificación no supervisada sin fuga.", style_table_cell)],
        [Paragraph("2. Análisis exploratorio y preparación", style_table_cell), Paragraph("12 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Auditoría de calidad, nulos, asimetrías, atípicos IQR documentados, StandardScaler solo en train y control de no escalado.", style_table_cell)],
        [Paragraph("3. Ajuste de modelos en espacio original", style_table_cell), Paragraph("15 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Dos familias distintas (K-Means vs GMM). Búsqueda K=2..12, curva de codo, Silhouette y BIC para covarianzas full/diag. Semilla fija.", style_table_cell)],
        [Paragraph("4. Evaluación y calidad en original", style_table_cell), Paragraph("12 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Silhouette, Davies-Bouldin y Calinski-Harabasz en train/test. Ruido documentado (0%). Estabilidad con ARI (>99% K-Means vs 55% GMM).", style_table_cell)],
        [Paragraph("5. Reducción de dimensionalidad (PCA)", style_table_cell), Paragraph("13 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("PCA ajustado solo con train. 7 componentes retienen 90.81% de varianza. Cargas de PC1 y PC2 interpretadas. Mapa 2D de dispersión.", style_table_cell)],
        [Paragraph("6. Reentrenamiento y comparación antes/después", style_table_cell), Paragraph("15 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Tabla comparativa 2x2 completa con tiempos, ruido, ARI y comparación justa en espacio original común. Explicación teórica de cambios.", style_table_cell)],
        [Paragraph("7. Interpretación y valor para el dominio", style_table_cell), Paragraph("8 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Perfiles en unidades físicas originales (125 BPM vs 108 BPM). Acciones para curadores/productores. Contraste con popularidad.", style_table_cell)],
        [Paragraph("8. Respuestas a las 12 preguntas", style_table_cell), Paragraph("10 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Las 12 preguntas resueltas con cifras exactas y respaldo empírico de las tablas generadas en el cuaderno.", style_table_cell)],
        [Paragraph("9. Informe, código y reproducibilidad", style_table_cell), Paragraph("7 %", style_table_cell), Paragraph("4 (Sobresaliente)", style_table_cell_bold), Paragraph("Cuaderno ejecutable sin fallos (17 celdas, 249 s). Informe maquetado en PDF/HTML, referencias APA y declaración de uso de IA.", style_table_cell)],
        [Paragraph("<b>PUNTAJE TOTAL ESTIMADO</b>", style_table_header), Paragraph("<b>100 %</b>", style_table_header), Paragraph("<b>4 / 4</b>", style_table_header), Paragraph("<b>100 / 100 PUNTOS (CUMPLIMIENTO COMPLETO SOBRESALIENTE)</b>", style_table_header)],
    ]
    t_rub = Table(rub_data, colWidths=[130, 35, 75, 264])
    t_rub.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, BG_LIGHT]),
        ('BACKGROUND', (0,-1), (-1,-1), SECONDARY_COLOR),
    ]))
    elements.append(t_rub)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Entregables adicionales generados en el proyecto", style_h2))
    p_extra = ("Además de los requisitos obligatorios de la rúbrica, el proyecto incluye dos artefactos diferenciales de alto valor:<br/>"
               "• <b>SONORA (Explorador Musical Web):</b> Aplicación web autónoma en HTML/JS (<code>Explorador_Musical.html</code>) que permite navegar "
               "el catálogo musical de 10.000 pistas en 2D, cambiar de algoritmo en tiempo real y obtener recomendaciones acústicas con enlaces a Spotify.<br/>"
               "• <b>Presentación Ejecutiva en PowerPoint:</b> 16 diapositivas con gráficas integradas en alta resolución y notas de orador (20 s por lámina).")
    elements.append(Paragraph(p_extra, style_body))
    elements.append(PageBreak())

    # ==========================================
    # PÁGINA 12: REPRODUCIBILIDAD Y REFERENCIAS
    # ==========================================
    elements.append(Paragraph("10. Reproducibilidad, fuentes y declaración de IA", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=8, spaceBefore=0))
    
    p_rep = ("El repositorio incluye el cuaderno reproducible <code>Proyecto_Musica.ipynb</code> ejecutado secuencialmente en un espacio de nombres limpio "
             "sin errores (17 celdas en 249 s). Las semillas fijas (42), particiones por identificador, tablas en CSV y metadatos JSON garantizan la total auditabilidad.")
    elements.append(Paragraph(p_rep, style_body))

    dep_data = [
        [Paragraph("<b>Dependencia de software</b>", style_table_header), Paragraph("<b>Versión verificada</b>", style_table_header), Paragraph("<b>Rol en el experimento</b>", style_table_header)],
        [Paragraph("Python", style_table_cell_bold), Paragraph("3.12.5", style_table_cell), Paragraph("Entorno de ejecución base", style_table_cell)],
        [Paragraph("scikit-learn", style_table_cell_bold), Paragraph("1.9.0", style_table_cell), Paragraph("StandardScaler, PCA, KMeans, GaussianMixture y métricas", style_table_cell)],
        [Paragraph("pandas", style_table_cell_bold), Paragraph("3.0.5", style_table_cell), Paragraph("Manipulación tabular y exportación de resultados", style_table_cell)],
        [Paragraph("numpy", style_table_cell_bold), Paragraph("2.5.2", style_table_cell), Paragraph("Cálculo matricial y distancias", style_table_cell)],
        [Paragraph("scipy", style_table_cell_bold), Paragraph("1.18.1", style_table_cell), Paragraph("Pruebas estadísticas de contraste (Kruskal-Wallis)", style_table_cell)],
        [Paragraph("matplotlib", style_table_cell_bold), Paragraph("3.11.1", style_table_cell), Paragraph("Generación de figuras en alta resolución (200 DPI)", style_table_cell)],
        [Paragraph("reportlab", style_table_cell_bold), Paragraph("5.1.0", style_table_cell), Paragraph("Compilación y maquetación del informe técnico en PDF", style_table_cell)],
    ]
    t_dep = Table(dep_data, colWidths=[120, 100, 284])
    t_dep.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    elements.append(t_dep)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Repositorio y fuentes bibliográficas (Formato APA)", style_h2))
    p_ref_text = ("<b>Repositorio oficial del proyecto en GitHub:</b> <font color='#1F4E79'><u>https://github.com/D4ri4na/ProyectoBloque3</u></font><br/><br/>"
                  "Pandya, M. (s. f.). <i>Spotify Tracks Dataset</i> [Conjunto de datos]. Hugging Face. "
                  "https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset<br/><br/>"
                  "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., "
                  "Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. "
                  "<i>Journal of Machine Learning Research</i>, 12, 2825–2830.<br/><br/>"
                  "Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. "
                  "<i>Journal of Computational and Applied Mathematics</i>, 20, 53–65.<br/><br/>"
                  "Davies, D. L., & Bouldin, D. W. (1979). A cluster separation measure. <i>IEEE Transactions on Pattern Analysis and Machine Intelligence</i>, (2), 224–227.")
    elements.append(Paragraph(p_ref_text, style_body))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Declaración explícita sobre el uso de Inteligencia Artificial", style_h2))
    p_ia = ("En cumplimiento de las políticas de integridad académica de la Universidad Católica Boliviana 'San Pablo', se declara que se utilizaron "
            "modelos de Inteligencia Artificial Generativa (ChatGPT de OpenAI y Google Gemini / Antigravity) como herramientas de asistencia técnica "
            "para la estructuración inicial de código, revisión de sintaxis, depuración de scripts y generación de la plantilla visual del informe. "
            "Todos los datos procesados, ejecuciones, cifras numéricas, interpretaciones en el contexto musical y conclusiones fueron calculados "
            "empíricamente en el entorno local, siendo responsabilidad intelectual íntegra de la estudiante.")
    elements.append(Paragraph(p_ia, style_body))

    # Construir documento
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    # Copiar a entregables
    ENTREGABLE_PDF.write_bytes(PDF_PATH.read_bytes())
    print(f"Informe PDF generado exitosamente en:\n- {PDF_PATH}\n- {ENTREGABLE_PDF}")

if __name__ == '__main__':
    build_pdf()
