# Laboratorio profesional SONORA

## Demostración
1. Busca una canción y compara sugerencias con y sin PCA.
2. Selecciona una referencia y explica dos diferencias numéricas.
3. Lee la ficha de posicionamiento: perfil, tamaño y popularidad histórica mediana.
4. Distingue esos hechos de las hipótesis editoriales, todavía no validadas.
5. Cambia energía y carácter acústico; observa el perfil y las referencias.
6. Cambia a GMM y explica que pertenencia no significa probabilidad de éxito.
7. Descarga la ficha JSON y restablece el simulador.

## Método
Se conservan entrenamiento/prueba y los cuatro modelos del experimento.
El simulador escala el vector nuevo y lo proyecta con PCA cuando corresponde.
K-Means elige el centro más cercano. GMM maximiza peso por densidad gaussiana
con covarianza completa y calcula pertenencias normalizadas de forma estable.
Candidatas: solo entrenamiento. Los filtros de artista y popularidad usan como
referencia la canción real de partida. Las estadísticas del perfil proceden de
entrenamiento; su mediana excluye valores de popularidad faltantes.

## Hipótesis editoriales manuales
- Actividad física: energía ≥0,70 y bailabilidad ≥0,60.
- Acústica tranquila: carácter acústico ≥0,60 y energía <0,40.
- Referencia instrumental: instrumental ≥0,70.
No son asociaciones aprendidas ni validadas con audiencias. Revisar escuchando.

## Práctica propuesta, todavía no ejecutada
Con voluntarios e identificadores anónimos, comparar a ciegas sugerencias
originales y PCA. Alternar orden, escuchar fragmentos de igual duración y puntuar
similitud y utilidad de 1 a 5. Reportar número de participantes, consultas,
distribuciones y comentarios negativos. Una muestra de conveniencia pequeña
no permite generalizar a todos los oyentes.

## Límites
No se modifica audio. Las combinaciones hipotéticas pueden ser poco realistas.
No se evalúa mezcla, afinación, gusto personal, campañas, audiencia o ventas.
Las características agregadas omiten parte de melodía, letra y estructura.
La revisión visual en navegador quedó pendiente por falta de conexión disponible.
Los informes experimental y del explorador permanecen complementarios y requieren
una revisión editorial conjunta antes de presentar la entrega final.
