# Dashboard Analitico de Visualizacion de Datos

Dashboard interactivo hecho con Streamlit para analizar el costo asociado a incumplimientos de SLA en NYC 311.

## Requisitos

- Windows
- Python instalado
- Entorno virtual `.venv` en la raiz del proyecto

## Instalacion local

1. Abre una terminal en la carpeta del proyecto.
2. Activa el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Instala las dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecucion

Inicia el dashboard con:

```powershell
streamlit run dashboard.py
```

Streamlit abrira automaticamente una URL local en el navegador. Si no ocurre, revisa la terminal para ver la direccion, normalmente `http://localhost:8501`.

## Estructura esperada

El dashboard espera esta estructura basica:

```text
dashboard.py
requirements.txt
.venv/
data/datos_combinados.parquet
```

## Notas

- El archivo `data/datos_combinados.parquet` debe existir para que el dashboard cargue los datos correctamente.
- Si cambias o recreas el entorno virtual, vuelve a ejecutar `pip install -r requirements.txt`.