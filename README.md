# Dashboard Analítico de Visualización de Datos

Dashboard interactivo hecho con Streamlit para analizar el costo asociado a incumplimientos de SLA en quejas ciudadanas de NYC 311.

## Requisitos

- Windows
- Python instalado
- Entorno virtual `.venv` en la raíz del proyecto

## Instalación local

1. Abre una terminal en la carpeta del proyecto.
2. Activa el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Instala las dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecución

```powershell
streamlit run dashboard.py
```

Streamlit abrirá automáticamente una URL local en el navegador. Si no ocurre, revisa la terminal — normalmente `http://localhost:8501`.

## Estructura esperada

```text
dashboard.py
requirements.txt
.venv/
data/datos_combinados.parquet
```

## Hipótesis

**¿Qué pasaría con el costo total por incumplimiento del NYPD si se aumentara su tiempo límite de respuesta de 0.33 días (8 horas) a un umbral mayor?**

El NYPD tiene el SLA más estricto del sistema y es la agencia con mayor costo absoluto en penalidades (~$985M). La hipótesis plantea que flexibilizar ese umbral reduciría drásticamente la cantidad de casos clasificados como breach y, con ello, el costo estimado.

El dashboard incluye una sección interactiva con un slider que permite simular distintos umbrales de SLA y observar en tiempo real el impacto en la tasa de incumplimiento, los casos recuperados y el ahorro estimado en millones de USD.

> Esta hipótesis no busca justificar una peor calidad de servicio, sino entender qué tan sensible es el costo al umbral definido y si el SLA actual refleja la capacidad operativa real del NYPD.

## Notas

- El archivo `data/datos_combinados.parquet` debe existir para que el dashboard cargue correctamente.
- Si recreas el entorno virtual, vuelve a ejecutar `pip install -r requirements.txt`.