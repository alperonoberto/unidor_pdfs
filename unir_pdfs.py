import os
import sys
import threading
from tkinter import Tk, Toplevel, Listbox, Button, Label, Scrollbar, StringVar, DoubleVar, Radiobutton, END, messagebox, filedialog, PhotoImage
from tkinter.ttk import Progressbar
import pymupdf

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, compatible con desarrollo y con PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unidor y Compresor de PDFs")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # Carga robusta y segura del icono para cualquier sistema operativo compatible con PyInstaller
        try:
            icon_path = resource_path(os.path.join("assets", "icon.png"))
            icon_img = PhotoImage(file=icon_path)
            self.root.iconphoto(True, icon_img)
        except Exception:
            try:
                # Intento alternativo para Windows (.ico) si estuviera disponible
                ico_path = resource_path(os.path.join("assets", "icon.ico"))
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        self.pdf_files = []
        self.drag_index = None

        # Etiqueta de título
        self.label = Label(root, text="Selecciona los PDFs que deseas procesar:", font=("Arial", 12, "bold"))
        self.label.pack(pady=10)

        # Listbox para mostrar los archivos seleccionados
        self.listbox_frame = Label(root)
        self.listbox_frame.pack(fill="both", expand=True, padx=20)

        self.scrollbar = Scrollbar(self.listbox_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.pdf_listbox = Listbox(self.listbox_frame, selectmode="extended", yscrollcommand=self.scrollbar.set, font=("Arial", 10))
        self.pdf_listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.pdf_listbox.yview)
        self.pdf_listbox.bind("<Button-1>", self.start_drag)
        self.pdf_listbox.bind("<B1-Motion>", self.drag_item)

        # Botones de control
        self.btn_select = Button(root, text="Agregar PDFs", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.select_files)
        self.btn_select.pack(fill="x", padx=20, pady=5)

        self.btn_remove = Button(root, text="Eliminar seleccionado", bg="#f44336", fg="white", font=("Arial", 10), command=self.remove_selected)
        self.btn_remove.pack(fill="x", padx=20, pady=2)

        self.btn_clear = Button(root, text="Limpiar lista", bg="#9e9e9e", fg="white", font=("Arial", 10), command=self.clear_list)
        self.btn_clear.pack(fill="x", padx=20, pady=2)

        self.btn_merge = Button(root, text="Procesar PDF(s)", bg="#2196F3", fg="white", font=("Arial", 11, "bold"), command=self.start_processing_workflow)
        self.btn_merge.pack(fill="x", padx=20, pady=10)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
        self.refresh_listbox()

    def remove_selected(self):
        selected_indices = self.pdf_listbox.curselection()
        for index in reversed(selected_indices):
            del self.pdf_files[index]
        self.refresh_listbox()

    def clear_list(self):
        self.pdf_files.clear()
        self.refresh_listbox()

    def refresh_listbox(self):
        self.pdf_listbox.delete(0, END)
        for index, pdf in enumerate(self.pdf_files, start=1):
            self.pdf_listbox.insert(END, f"{index}. {pdf}")

    def start_drag(self, event):
        index = self.pdf_listbox.nearest(event.y)
        self.drag_index = index if 0 <= index < len(self.pdf_files) else None

    def drag_item(self, event):
        if self.drag_index is None or not self.pdf_files:
            return

        target_index = self.pdf_listbox.nearest(event.y)
        target_index = max(0, min(target_index, len(self.pdf_files) - 1))
        if target_index == self.drag_index:
            return

        pdf = self.pdf_files.pop(self.drag_index)
        self.pdf_files.insert(target_index, pdf)
        self.drag_index = target_index
        self.refresh_listbox()
        self.pdf_listbox.selection_set(target_index)
        self.pdf_listbox.activate(target_index)
        self.pdf_listbox.see(target_index)

    def pedir_nivel_compresion(self):
        """Muestra una ventana emergente modal para elegir el nivel de compresión."""
        ventana = Toplevel(self.root)
        ventana.title("Nivel de Compresión")
        ventana.geometry("360x250")
        ventana.resizable(False, False)
        ventana.grab_set()

        seleccion = StringVar(value="medio")

        Label(ventana, text="Selecciona el nivel de compresión:", font=("Arial", 10, "bold")).pack(pady=12)

        Radiobutton(ventana, text="Sin compresión (Máxima calidad)", variable=seleccion, value="ninguna").pack(anchor="w", padx=30, pady=4)
        Radiobutton(ventana, text="Compresión baja (Calidad alta)", variable=seleccion, value="baja").pack(anchor="w", padx=30, pady=4)
        Radiobutton(ventana, text="Compresión media (Recomendado)", variable=seleccion, value="medio").pack(anchor="w", padx=30, pady=4)
        Radiobutton(ventana, text="Compresión alta (Menor calidad / Más ligero)", variable=seleccion, value="alta").pack(anchor="w", padx=30, pady=4)

        resultado = {"nivel": None}

        def confirmar():
            resultado["nivel"] = seleccion.get()
            ventana.destroy()

        Button(ventana, text="Aceptar", command=confirmar, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=12).pack(pady=12)
        
        ventana.wait_window()
        return resultado["nivel"]

    def start_processing_workflow(self):
        """Gestiona el flujo completo: validación, diálogo de compresión, ruta de guardado y ejecución en hilo."""
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

        progress_dialog = Toplevel(self.root)
        progress_dialog.title("Procesando PDF...")
        progress_dialog.geometry("380x130")
        progress_dialog.resizable(False, False)
        progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        progress_dialog.grab_set()

        Label(progress_dialog, text="Por favor, espere mientras se procesa el archivo...", font=("Arial", 9)).pack(pady=12)

        progress_var = DoubleVar(value=0)
        progress_bar = Progressbar(progress_dialog, orient="horizontal", length=320, mode="determinate", variable=progress_var)
        progress_bar.pack(pady=5)

        lbl_percent = Label(progress_dialog, text="0%", font=("Arial", 10, "bold"))
        lbl_percent.pack(pady=5)

        self.btn_merge.config(state="disabled")
        self.btn_select.config(state="disabled")

        threading.Thread(
            target=self.process_pdfs_pymupdf, 
            args=(output_file, nivel, es_unico_archivo, progress_dialog, progress_var, lbl_percent), 
            daemon=True
        ).start()

    def process_pdfs_pymupdf(self, output_file, nivel, es_unico_archivo, progress_dialog, progress_var, lbl_percent):
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
                current_pct = int((paginas_procesadas / total_paginas) * 70)
                progress_var.set(current_pct)
                lbl_percent.config(text=f"{current_pct}%")

            progress_var.set(80)
            lbl_percent.config(text="80% (Optimizando y comprimiendo...)")

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

            progress_var.set(90)
            lbl_percent.config(text="90% (Guardando en disco...)")

            doc_salida.save(
                output_file,
                garbage=garbage_val,
                deflate=deflate_val,
                deflate_images=deflate_images_val
            )
            
            doc_salida.close()
            for doc in documentos:
                doc.close()

            progress_var.set(100)
            lbl_percent.config(text="100%")

            msg_exito = (
                f"¡PDF comprimido correctamente con PyMuPDF!\nGuardado en:\n{output_file}"
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
                messagebox.showerror("Error", f"Ocurrió un error al procesar el/los PDF(s):\n{err}"),
                self.reset_ui()
            ])

    def reset_ui(self):
        """Restaura los botones principales."""
        self.btn_merge.config(state="normal")
        self.btn_select.config(state="normal")

if __name__ == "__main__":
    root = Tk()
    app = PDFMergerApp(root)
    root.mainloop()