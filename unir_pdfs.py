import os
import sys
import threading
import urllib.request
import json
import webbrowser
import customtkinter as ctk
from tkinter import messagebox, filedialog
import pymupdf
from app_version import APP_VERSION
from version_utils import versions_match

GITHUB_REPO = "alperonoberto/unidor_pdfs"

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

        # Carga robusta y segura del icono para CustomTkinter
        try:
            icon_path = resource_path(os.path.join("assets", "icon.png"))
            self.root.iconbitmap(icon_path) # Si es .ico en Windows
        except Exception:
            try:
                # Alternativa segura para Linux / PNG
                icon_img = ctk.CTkImage(light_image=None, dark_image=None)
            except Exception:
                pass

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
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "PDFMergerApp-Updater"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data["tag_name"]
                release_url = data["html_url"]

                if not versions_match(latest_version, APP_VERSION):
                    self.root.after(0, lambda: self.show_update_dialog(latest_version, release_url))
        except Exception:
            pass

    def show_update_dialog(self, latest_version, release_url):
        if messagebox.askyesno(
            "Actualización disponible", 
            f"¡Hay una nueva versión disponible ({latest_version})!\n\n¿Deseas abrir la página de descargas en tu navegador?"
        ):
            webbrowser.open(release_url)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
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
        
        dialog.wait_window()
        return resultado["nivel"]

    def start_processing_workflow(self):
        if not self.pdf_files:
            messagebox.showwarning("Advertencia", "No hay archivos PDF seleccionados para procesar.")
            return

        nivel = self.pedir_nivel_compresion()
        if not nivel:
            return

        es_unico_archivo = len(self.pdf_files) == 1
        titulo_dialogo = "Guardar PDF comprimido como..." if es_unico_archivo else "Guardar PDF unido como..."

        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            title=titulo_dialogo
        )

        if not output_file:
            return

        progress_dialog = ctk.CTkToplevel(self.root)
        progress_dialog.title("Procesando...")
        progress_dialog.geometry("360x140")
        progress_dialog.resizable(False, False)
        progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        progress_dialog.grab_set()

        ctk.CTkLabel(progress_dialog, text="Optimizando y procesando archivo...", font=ctk.CTkFont(size=12)).pack(pady=15)

        progress_bar = ctk.CTkProgressBar(progress_dialog, orientation="horizontal", width=300)
        progress_bar.pack(pady=5)
        progress_bar.set(0)

        lbl_percent = ctk.CTkLabel(progress_dialog, text="0%", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_percent.pack(pady=5)

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
                messagebox.showinfo("Éxito", m),
                self.clear_list(),
                self.reset_ui()
            ])

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda err=error_msg, pd=progress_dialog: [
                pd.destroy(),
                messagebox.showerror("Error", f"Ocurrió un error al procesar el archivo:\n{err}"),
                self.reset_ui()
            ])

    def reset_ui(self):
        self.btn_merge.configure(state="normal")
        self.btn_select.configure(state="normal")

if __name__ == "__main__":
    root = ctk.CTk()
    app = PDFMergerApp(root)
    root.mainloop()