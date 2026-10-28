# Unidor y compresor de PDFs

Aplicación de escritorio para unir varios archivos PDF en uno solo o comprimir un PDF existente. Permite elegir el nivel de compresión, ordenar los documentos antes de procesarlos y seleccionar dónde guardar el resultado.

## Funcionalidades

- **Unir varios PDF** en el orden que elijas.
- **Comprimir un PDF** sin necesidad de combinarlo con otros.
- **Cuatro niveles de compresión:** sin compresión, baja, media y alta.
- **Ordenar documentos** arrastrándolos en la lista antes de procesarlos.
- **Añadir archivos desde el explorador integrado**, navegar por carpetas y seleccionar varios PDF.
- **Elegir la carpeta y el nombre del archivo de salida.** La extensión `.pdf` se añade automáticamente si hace falta y se pide confirmación antes de reemplazar un archivo existente.
- **Indicador de progreso** durante el procesamiento y la descarga de actualizaciones.
- **Interfaz adaptable** al modo claro u oscuro del sistema.
- **Actualizaciones automáticas** en las versiones oficiales para Windows y Linux x86-64.

## Descargar y ejecutar

1. Abre la página de [Releases](https://github.com/alperonoberto/unidor_pdfs/releases).
2. Descarga el archivo correspondiente a tu sistema:
   - Windows: `unir_pdfs-windows-amd64.exe`
   - Linux x86-64: `unir_pdfs-linux-amd64`
3. Ejecuta el archivo descargado. La aplicación es portable y no requiere una instalación tradicional.

En Windows, SmartScreen puede mostrar un aviso al ejecutar un archivo descargado. Asegúrate de obtenerlo desde la página oficial de Releases antes de continuar.

## Cómo usarla

1. Pulsa **Agregar PDFs** y selecciona uno o varios archivos. También puedes navegar entre carpetas desde el explorador integrado.
2. Si seleccionaste varios documentos, arrástralos en la lista para establecer el orden. Usa **Eliminar selección** o **Limpiar lista** si necesitas modificarla.
3. Pulsa **Procesar PDF(s)** y selecciona el nivel de compresión.
4. Elige la carpeta y el nombre del archivo de salida.
5. Espera a que termine el procesamiento; la aplicación indicará el progreso y confirmará dónde guardó el PDF.

Con un único archivo seleccionado, la aplicación genera una versión comprimida. Con varios archivos, los combina y optimiza en un solo PDF.

## Actualizaciones automáticas

Las versiones oficiales para Windows y Linux x86-64 comprueban si hay una actualización al iniciarse. Solo se ofrecen versiones estables; se omiten borradores y versiones preliminares, como `beta` o `rc`. Si hay una actualización disponible, puedes aceptar su descarga e instalación desde la aplicación. Se muestra el progreso y la aplicación se reinicia al finalizar.

Para instalarla automáticamente, la aplicación necesita permiso de escritura en la carpeta donde se encuentra el ejecutable. También puedes descargar manualmente la versión más reciente desde [Releases](https://github.com/alperonoberto/unidor_pdfs/releases).

## Tecnologías

- [Python](https://www.python.org/)
- [CustomTkinter](https://customtkinter.tomschimansky.com/) para la interfaz
- [PyMuPDF](https://pymupdf.readthedocs.io/) para procesar y optimizar documentos PDF
- [PyInstaller](https://pyinstaller.org/) para generar los ejecutables portables

## Desarrollo local

Instala las dependencias con `python -m pip install -r requirements.txt`. Desde la raíz del repositorio, ejecuta la aplicación con:

```bash
PYTHONPATH=src python -m unidor_pdfs.unir_pdfs
```

Las pruebas se ejecutan con `PYTHONPATH=src python -m unittest discover -s tests`.

## Contribuciones

Las contribuciones son bienvenidas. Para informar de un error o proponer una mejora, abre un [Issue](https://github.com/alperonoberto/unidor_pdfs/issues) o envía un Pull Request.
