import os
import platform
import sys
import threading
import urllib.error
from pathlib import Path
import customtkinter as ctk
from tkinter import PhotoImage
import pymupdf
from app_version import APP_VERSION
from version_utils import is_newer_version
from update_manager import (
    download_update,
    install_update,
    latest_release,
    select_release_asset,
)

# Configuración inicial del tema global
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    # Obtiene la ruta absoluta al recurso, compatible con desarrollo y con PyInstaller
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unidor y Compresor de PDFs")
        self.root.geometry("520x540")
        self.root.resizable(False, False)

        self.app_icon = PhotoImage(
            file=resource_path(os.path.join("assets", "logo_png.png"))
        )
        self.root.iconphoto(True, self.app_icon)
        system = platform.system().casefold()
        if system == "windows":
            self.root.iconbitmap(
                resource_path(os.path.join("assets", "logo_ico.ico"))
            )
        elif system == "linux":
            self.root.tk.call("wm", "class", self.root._w, "UnidorPDFs")

        self.pdf_files = []
        self.file_widgets = []
        self.file_labels = []
        self.selected_file_index = None
        self.drag_widget = None

        # --- CONTENEDOR PRINCIPAL ---
        self.main_frame = ctk.CTkFrame(root, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título principal
        self.label = ctk.CTkLabel(
            self.main_frame, 
            text="Gestor y Compresor de PDFs", 
            font=ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        )
        self.label.pack(anchor="w", pady=(0, 10))

        # --- ÁREA DE LISTA DE ARCHIVOS (Tarjeta con scroll) ---
        self.list_container = ctk.CTkScrollableFrame(
            self.main_frame, 
            width=480, 
            height=220, 
            corner_radius=10,
            border_width=1,
            border_color=("#d1d5db", "#374151")
        )
        self.list_container.pack(pady=(0, 15))
        
        # Etiqueta de estado vacío dentro del contenedor
        self.placeholder_label = ctk.CTkLabel(
            self.list_container, 
            text="No hay archivos seleccionados.\nHaz clic en 'Agregar PDFs' para comenzar.",
            text_color=("gray50", "gray50")
        )
        self.placeholder_label.pack(pady=70)

        # --- BOTONERA ---
        self.btn_select = ctk.CTkButton(
            self.main_frame, 
            text="+ Agregar PDFs", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb", hover_color="#1d4ed8",
            corner_radius=8, height=38,
            command=self.select_files
        )
        self.btn_select.pack(fill="x", pady=(0, 8))

        # Fila de botones secundarios (Eliminar / Limpiar)
        self.sub_buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.sub_buttons_frame.pack(fill="x", pady=(0, 15))

        self.btn_remove = ctk.CTkButton(
            self.sub_buttons_frame, 
            text="Eliminar selección", 
            font=ctk.CTkFont(size=12),
            fg_color="#dc2626", hover_color="#b91c1c",
            corner_radius=8, height=32,
            command=self.remove_selected
        )
        self.btn_remove.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_clear = ctk.CTkButton(
            self.sub_buttons_frame, 
            text="Limpiar lista", 
            font=ctk.CTkFont(size=12),
            fg_color="#6b7280", hover_color="#4b5563",
            corner_radius=8, height=32,
            command=self.clear_list
        )
        self.btn_clear.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Botón de acción principal (Procesar)
        self.btn_merge = ctk.CTkButton(
            self.main_frame, 
            text="🚀 Procesar PDF(s)", 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#16a34a", hover_color="#15803d",
            corner_radius=8, height=42,
            command=self.start_processing_workflow
        )
        self.btn_merge.pack(fill="x")

        # Lanzar comprobación de actualizaciones automática en segundo plano al iniciar
        if APP_VERSION != "dev":
            threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        """Consulta la API de GitHub para verificar si hay una nueva versión."""
        try:
            release = latest_release()
            latest_version = release["tag_name"]
            if is_newer_version(latest_version, APP_VERSION):
                self.root.after(
                    0,
                    lambda: self.show_update_dialog(release),
                )
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as error:
            self.root.after(
                0,
                lambda message=str(error): self.show_message(
                    "Comprobación de actualizaciones",
                    f"No se pudo comprobar si hay una nueva versión:\n{message}",
                    kind="warning",
                ),
            )

    def show_update_dialog(self, release):
        latest_version = release["tag_name"]
        if self.show_message(
            "Actualización disponible", 
            f"¡Hay una nueva versión disponible ({latest_version})!\n\n"
            "¿Deseas descargarla e instalarla ahora? La aplicación se reiniciará.",
            kind="question",
        ):
            self.show_message(
                "Actualización",
                "La actualización se está descargando. La aplicación se cerrará "
                "y volverá a abrirse cuando termine la instalación.",
            )
            threading.Thread(
                target=self.install_latest_update,
                args=(release,),
                daemon=True,
            ).start()

    def install_latest_update(self, release):
        staged_path = None
        try:
            asset = select_release_asset(release)
            executable_path = Path(sys.executable).resolve()
            staged_path = download_update(asset, executable_path)
            install_update(staged_path, executable_path, os.getpid())
        except Exception as error:
            if staged_path is not None:
                staged_path.unlink(missing_ok=True)
            self.root.after(
                0,
                lambda message=str(error): self.show_message(
                    "Error de actualización",
                    f"No se pudo instalar la actualización:\n{message}",
                    kind="error",
                ),
            )
            return

        self.root.after(0, self.root.destroy)

    def show_message(self, title, message, kind="info", parent=None):
        parent = parent or self.root
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=22)

        icon, color = {
            "info": ("i", "#2563eb"),
            "warning": ("!", "#d97706"),
            "error": ("×", "#dc2626"),
            "question": ("?", "#2563eb"),
        }.get(kind, ("i", "#2563eb"))
        ctk.CTkLabel(
            content,
            text=icon,
            width=38,
            height=38,
            corner_radius=19,
            fg_color=color,
            text_color="white",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=(0, 16), anchor="n")

        message_label = ctk.CTkLabel(
            content,
            text=message,
            justify="left",
            wraplength=380,
            font=ctk.CTkFont(size=13),
        )
        message_label.pack(side="left", fill="both", expand=True)

        result = {"confirmed": False}
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(0, 20))

        def finish(confirmed):
            result["confirmed"] = confirmed
            dialog.destroy()

        if kind == "question":
            ctk.CTkButton(
                buttons,
                text="No",
                fg_color="transparent",
                border_width=1,
                command=lambda: finish(False),
                width=100,
            ).pack(side="right", padx=(8, 0))
            ctk.CTkButton(
                buttons,
                text="Sí",
                command=lambda: finish(True),
                width=100,
            ).pack(side="right")
        else:
            ctk.CTkButton(
                buttons,
                text="Aceptar",
                command=lambda: finish(True),
                width=100,
            ).pack(side="right")

        dialog.update_idletasks()
        height = max(170, min(440, message_label.winfo_reqheight() + 105))
        self._center_dialog(dialog, parent, 480, height)
        dialog.wait_window()
        return result["confirmed"]

    @staticmethod
    def _center_dialog(dialog, parent, width, height):
        dialog.geometry(f"{width}x{height}")
        dialog.update_idletasks()
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        dialog.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def _show_pdf_file_dialog(self, title, save=False):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("680x520")
        dialog.minsize(560, 400)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

        selected_files = set()
        result = {"value": None}
        current_directory = Path.home()
        current_path = ctk.StringVar(value=str(current_directory))
        filename = ctk.StringVar()

        heading = ctk.CTkLabel(
            dialog,
            text=title,
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        )
        heading.pack(fill="x", padx=20, pady=(18, 12))

        navigation = ctk.CTkFrame(dialog, fg_color="transparent")
        navigation.pack(fill="x", padx=20, pady=(0, 10))
        path_entry = ctk.CTkEntry(navigation, textvariable=current_path)
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        list_frame = ctk.CTkScrollableFrame(
            dialog,
            corner_radius=10,
            border_width=1,
            border_color=("#d1d5db", "#374151"),
        )
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        status = ctk.CTkLabel(dialog, text="", anchor="w", text_color=("gray40", "gray70"))
        status.pack(fill="x", padx=22, pady=(0, 8))

        if save:
            filename_row = ctk.CTkFrame(dialog, fg_color="transparent")
            filename_row.pack(fill="x", padx=20, pady=(0, 10))
            ctk.CTkLabel(filename_row, text="Nombre del archivo:").pack(
                side="left", padx=(0, 8)
            )
            filename_entry = ctk.CTkEntry(filename_row, textvariable=filename)
            filename_entry.pack(side="left", fill="x", expand=True)
        else:
            filename_entry = None

        def finish():
            if save:
                name = filename.get().strip()
                if (
                    not name
                    or name in {".", ".."}
                    or any(char in name for char in '<>:"/\\|?*')
                    or any(ord(char) < 32 for char in name)
                ):
                    self.show_message(
                        "Nombre no válido",
                        "Escribe un nombre de archivo válido.",
                        kind="warning",
                        parent=dialog,
                    )
                    return
                if Path(name).suffix.casefold() != ".pdf":
                    name += ".pdf"
                output_path = current_directory / name
                if output_path.exists() and not self.show_message(
                    "Confirmar reemplazo",
                    f"El archivo ya existe:\n{output_path}\n\n¿Quieres reemplazarlo?",
                    kind="question",
                    parent=dialog,
                ):
                    return
                result["value"] = str(output_path)
            elif selected_files:
                result["value"] = tuple(str(path) for path in sorted(selected_files))
            dialog.destroy()

        def render_directory(directory):
            nonlocal current_directory
            try:
                directory = directory.expanduser().resolve()
                if not directory.is_dir():
                    raise NotADirectoryError(f"No es una carpeta: {directory}")
                entries = sorted(
                    directory.iterdir(),
                    key=lambda item: (not item.is_dir(), item.name.casefold()),
                )
            except OSError as error:
                self.show_message(
                    "No se puede abrir la carpeta",
                    str(error),
                    kind="error",
                    parent=dialog,
                )
                return

            current_directory = directory
            current_path.set(str(directory))
            for widget in list_frame.winfo_children():
                widget.destroy()

            folders = [entry for entry in entries if entry.is_dir()]
            pdfs = [
                entry for entry in entries
                if entry.is_file() and entry.suffix.casefold() == ".pdf"
            ]
            for entry in folders:
                button = ctk.CTkButton(
                    list_frame,
                    text=f"📁  {entry.name}",
                    anchor="w",
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("#e5e7eb", "#334155"),
                    command=lambda item=entry: render_directory(item),
                )
                button.pack(fill="x", pady=2, padx=2)

            for entry in pdfs:
                if save:
                    command = lambda item=entry: filename.set(item.name)
                    text = f"📄  {entry.name}"
                    fg_color = "transparent"
                else:
                    selected = entry in selected_files
                    command = lambda item=entry: toggle_file(item)
                    text = f"{'✓' if selected else '□'}  {entry.name}"
                    fg_color = ("#dbeafe", "#1e3a5f") if selected else "transparent"
                ctk.CTkButton(
                    list_frame,
                    text=text,
                    anchor="w",
                    fg_color=fg_color,
                    text_color=("gray10", "gray90"),
                    hover_color=("#e5e7eb", "#334155"),
                    command=command,
                ).pack(fill="x", pady=2, padx=2)

            if not folders and not pdfs:
                ctk.CTkLabel(
                    list_frame,
                    text="No hay carpetas ni archivos PDF en esta ubicación.",
                    text_color=("gray45", "gray65"),
                ).pack(pady=24)
            update_status()

        def update_status():
            if save:
                status.configure(text="Selecciona una carpeta y escribe el nombre del PDF.")
            else:
                status.configure(text=f"{len(selected_files)} archivo(s) seleccionado(s)")

        def toggle_file(path):
            if path in selected_files:
                selected_files.remove(path)
            else:
                selected_files.add(path)
            render_directory(current_directory)

        def navigate_to_path():
            render_directory(Path(current_path.get()))

        def navigate_up():
            if current_directory.parent != current_directory:
                render_directory(current_directory.parent)

        ctk.CTkButton(
            navigation, text="Subir", width=72, command=navigate_up
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            navigation, text="Ir", width=58, command=navigate_to_path
        ).pack(side="left")
        path_entry.bind("<Return>", lambda _event: navigate_to_path())

        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkButton(
            actions,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            command=dialog.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            actions,
            text="Guardar" if save else "Agregar selección",
            fg_color="#16a34a",
            hover_color="#15803d",
            command=finish,
        ).pack(side="right")

        if filename_entry is not None:
            filename_entry.bind("<Return>", lambda _event: finish())

        render_directory(current_directory)
        self._center_dialog(dialog, self.root, 680, 520)
        dialog.wait_window()
        return result["value"]

    def select_files(self):
        files = self._show_pdf_file_dialog("Seleccionar archivos PDF")
        if not files:
            return
        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
        self.refresh_file_list()

    def remove_selected(self):
        if self.selected_file_index is not None and 0 <= self.selected_file_index < len(self.pdf_files):
            del self.pdf_files[self.selected_file_index]
            self.selected_file_index = None
            self.refresh_file_list()

    def clear_list(self):
        self.pdf_files.clear()
        self.selected_file_index = None
        self.refresh_file_list()

    def select_item_in_ui(self, index):
        self.selected_file_index = index
        for i, w in enumerate(self.file_widgets):
            if i == index:
                w.configure(fg_color=("#e2e8f0", "#334155"))
            else:
                w.configure(fg_color="transparent")

    def refresh_file_list(self):
        for w in self.file_widgets:
            w.destroy()
        self.file_widgets.clear()
        self.file_labels.clear()
        self.drag_widget = None

        if not self.pdf_files:
            self.placeholder_label.pack(pady=70)
            return
        
        self.placeholder_label.pack_forget()

        for idx, pdf in enumerate(self.pdf_files):
            file_name = os.path.basename(pdf)
            
            item_frame = ctk.CTkFrame(self.list_container, fg_color="transparent", corner_radius=6, height=35)
            item_frame.pack(fill="x", pady=2, padx=2)
            
            lbl = ctk.CTkLabel(item_frame, text=f"{idx + 1}. {file_name}", anchor="w", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=10, fill="x", expand=True)

            for widget in (item_frame, lbl):
                widget.bind(
                    "<Button-1>",
                    lambda event, row=item_frame: self.start_drag(event, row)
                )
                widget.bind("<B1-Motion>", self.drag_item)
                widget.bind("<ButtonRelease-1>", self.end_drag)

            self.file_widgets.append(item_frame)
            self.file_labels.append(lbl)

    def start_drag(self, _event, row):
        self.drag_widget = row
        self.select_item_in_ui(self.file_widgets.index(row))
        return "break"

    def drag_item(self, event):
        if self.drag_widget not in self.file_widgets:
            return "break"

        source_index = self.file_widgets.index(self.drag_widget)
        target_index = len(self.file_widgets) - 1
        for index, row in enumerate(self.file_widgets):
            midpoint = row.winfo_rooty() + row.winfo_height() / 2
            if event.y_root < midpoint:
                target_index = index
                break

        if target_index == source_index:
            return "break"

        pdf = self.pdf_files.pop(source_index)
        self.pdf_files.insert(target_index, pdf)
        row = self.file_widgets.pop(source_index)
        self.file_widgets.insert(target_index, row)
        label = self.file_labels.pop(source_index)
        self.file_labels.insert(target_index, label)
        self.selected_file_index = target_index

        for row in self.file_widgets:
            row.pack_forget()
        for index, row in enumerate(self.file_widgets):
            row.pack(fill="x", pady=2, padx=2)
            self.file_labels[index].configure(
                text=f"{index + 1}. {os.path.basename(self.pdf_files[index])}"
            )
        self.select_item_in_ui(target_index)
        return "break"

    def end_drag(self, _event):
        self.drag_widget = None

    def pedir_nivel_compresion(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Nivel de Compresión")
        dialog.geometry("380x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Selecciona el nivel de compresión:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

        seleccion = ctk.StringVar(value="medio")

        options = [
            ("Sin compresión (Máxima calidad)", "ninguna"),
            ("Compresión baja (Calidad alta)", "baja"),
            ("Compresión media (Recomendado)", "medio"),
            ("Compresión alta (Más ligero)", "alta")
        ]

        for text, val in options:
            rb = ctk.CTkRadioButton(dialog, text=text, variable=seleccion, value=val, font=ctk.CTkFont(size=12))
            rb.pack(anchor="w", padx=40, pady=5)

        resultado = {"nivel": None}

        def confirmar():
            resultado["nivel"] = seleccion.get()
            dialog.destroy()

        btn_aceptar = ctk.CTkButton(
            dialog, 
            text="Aceptar", 
            command=confirmar, 
            fg_color="#16a34a", 
            hover_color="#15803d", 
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        btn_aceptar.pack(pady=20)
        
        self._center_dialog(dialog, self.root, 380, 300)
        dialog.wait_window()
        return resultado["nivel"]

    def start_processing_workflow(self):
        if not self.pdf_files:
            self.show_message(
                "Advertencia",
                "No hay archivos PDF seleccionados para procesar.",
                kind="warning",
            )
            return

        nivel = self.pedir_nivel_compresion()
        if not nivel:
            return

        es_unico_archivo = len(self.pdf_files) == 1
        titulo_dialogo = "Guardar PDF comprimido como..." if es_unico_archivo else "Guardar PDF unido como..."

        output_file = self._show_pdf_file_dialog(titulo_dialogo, save=True)

        if not output_file:
            return

        progress_dialog = ctk.CTkToplevel(self.root)
        progress_dialog.title("Procesando...")
        progress_dialog.geometry("360x140")
        progress_dialog.resizable(False, False)
        progress_dialog.transient(self.root)
        progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        progress_dialog.grab_set()

        ctk.CTkLabel(progress_dialog, text="Optimizando y procesando archivo...", font=ctk.CTkFont(size=12)).pack(pady=15)

        progress_bar = ctk.CTkProgressBar(progress_dialog, orientation="horizontal", width=300)
        progress_bar.pack(pady=5)
        progress_bar.set(0)

        lbl_percent = ctk.CTkLabel(progress_dialog, text="0%", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_percent.pack(pady=5)
        self._center_dialog(progress_dialog, self.root, 360, 140)

        self.btn_merge.configure(state="disabled")
        self.btn_select.configure(state="disabled")

        threading.Thread(
            target=self.process_pdfs_pymupdf, 
            args=(output_file, nivel, es_unico_archivo, progress_dialog, progress_bar, lbl_percent), 
            daemon=True
        ).start()

    def process_pdfs_pymupdf(self, output_file, nivel, es_unico_archivo, progress_dialog, progress_bar, lbl_percent):
        try:
            doc_salida = pymupdf.open()
            documentos = []
            total_paginas = 0

            for pdf in self.pdf_files:
                doc = pymupdf.open(pdf)
                documentos.append(doc)
                total_paginas += len(doc)

            if total_paginas == 0:
                raise Exception("Los archivos PDF seleccionados están vacíos o son inválidos.")

            paginas_procesadas = 0

            for doc in documentos:
                doc_salida.insert_pdf(doc)
                paginas_procesadas += len(doc)
                current_pct = (paginas_procesadas / total_paginas) * 0.7
                progress_bar.set(current_pct)
                lbl_percent.configure(text=f"{int(current_pct * 100)}%")

            progress_bar.set(0.8)
            lbl_percent.configure(text="80% (Optimización final...)")

            garbage_val = 0
            deflate_val = False
            deflate_images_val = False

            if nivel == "baja":
                garbage_val = 2
                deflate_val = True
                deflate_images_val = True
            elif nivel == "medio":
                garbage_val = 4
                deflate_val = True
                deflate_images_val = True
            elif nivel == "alta":
                garbage_val = 4
                deflate_val = True
                deflate_images_val = True

            progress_bar.set(0.9)
            lbl_percent.configure(text="90% (Guardando en disco...)")

            doc_salida.save(
                output_file,
                garbage=garbage_val,
                deflate=deflate_val,
                deflate_images=deflate_images_val
            )
            
            doc_salida.close()
            for doc in documentos:
                doc.close()

            progress_bar.set(1.0)
            lbl_percent.configure(text="100%")

            msg_exito = (
                f"¡PDF comprimido correctamente!\nGuardado en:\n{output_file}"
                if es_unico_archivo
                else f"¡PDFs unidos y comprimidos correctamente!\nGuardado en:\n{output_file}"
            )
            
            self.root.after(0, lambda m=msg_exito, pd=progress_dialog: [
                pd.destroy(),
                self.show_message("Éxito", m),
                self.clear_list(),
                self.reset_ui()
            ])

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda err=error_msg, pd=progress_dialog: [
                pd.destroy(),
                self.show_message(
                    "Error",
                    f"Ocurrió un error al procesar el archivo:\n{err}",
                    kind="error",
                ),
                self.reset_ui()
            ])

    def reset_ui(self):
        self.btn_merge.configure(state="normal")
        self.btn_select.configure(state="normal")

if __name__ == "__main__":
    root = ctk.CTk()
    app = PDFMergerApp(root)
    root.mainloop()