import os
from tkinter import Tk, Toplevel, Listbox, Button, Label, Scrollbar, StringVar, Radiobutton, END, messagebox, filedialog
import threading
from tkinter import Tk, Toplevel, Listbox, Button, Label, Scrollbar, StringVar, DoubleVar, Radiobutton, END, messagebox, filedialog
from tkinter.ttk import Progressbar
from pypdf import PdfWriter, PdfReader

class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unidor y Compresor de PDFs")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
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
        ventana.geometry("340x230")
        ventana.resizable(False, False)
        ventana.grab_set()

        seleccion = StringVar(value="medio")

        Label(ventana, text="Selecciona el nivel de compresión:", font=("Arial", 10, "bold")).pack(pady=10)

        Radiobutton(ventana, text="Sin compresión (Máxima calidad)", variable=seleccion, value="ninguna").pack(anchor="w", padx=30, pady=2)
        Radiobutton(ventana, text="Compresión baja (Calidad alta)", variable=seleccion, value="baja").pack(anchor="w", padx=30, pady=2)
        Radiobutton(ventana, text="Compresión media (Recomendado)", variable=seleccion, value="medio").pack(anchor="w", padx=30, pady=2)
        Radiobutton(ventana, text="Compresión alta (Menor calidad / Más ligero)", variable=seleccion, value="alta").pack(anchor="w", padx=30, pady=2)

        resultado = {"nivel": None}

        def confirmar():
            resultado["nivel"] = seleccion.get()
            ventana.destroy()

        Button(ventana, text="Aceptar", command=confirmar, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=12).pack(pady=12)
        
        ventana.wait_window()
        return resultado["nivel"]

    def merge_pdfs(self):
        pdfs = self.pdf_files

        if not pdfs:
            messagebox.showwarning("Advertencia", "No hay archivos PDF seleccionados para unir.")
            return

        # Pedir nivel de compresión mediante ventana emergente

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

        # Crear ventana emergente de carga (Progress Dialog)
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

        # Desactivar botones principales
        self.btn_merge.config(state="disabled")
        self.btn_select.config(state="disabled")

        # Lanzar el proceso en segundo plano
        threading.Thread(
            target=self.process_pdfs, 
            args=(output_file, nivel, es_unico_archivo, progress_dialog, progress_var, lbl_percent), 
            daemon=True
        ).start()

    def process_pdfs(self, output_file, nivel, es_unico_archivo, progress_dialog, progress_var, lbl_percent):
        try:
            merger = PdfWriter()

            # 1. Primero unimos todos los PDFs normalmente al writer
            for pdf in pdfs:
                reader = PdfReader(pdf)
                for page in reader.pages:
                    merger.add_page(page)

            # 2. Una vez que las páginas ya forman parte del writer, aplicamos la compresión
            if nivel != "ninguna":
                for page in merger.pages:
                    page.compress_content_streams() # Comprime flujos de texto/vectores

            # Fase 1: Lectura y conteo de páginas
            readers = []
            total_pages = 0
            for pdf in self.pdf_files:
                reader = PdfReader(pdf)
                readers.append(reader)
                total_pages += len(reader.pages)

            if total_pages == 0:
                raise Exception("Los archivos PDF seleccionados están vacíos o son inválidos.")

            processed_pages = 0

            # Fase 2: Agregar páginas al writer
            for reader in readers:
                for page in reader.pages:
                    merger.add_page(page)
                    processed_pages += 1
                    current_pct = int((processed_pages / total_pages) * 40)
                    progress_var.set(current_pct)
                    lbl_percent.config(text=f"{current_pct}%")

            # Fase 3: Compresión (si aplica)
            if nivel != "ninguna":
                compression_processed = 0
                for page in merger.pages:
                    page.compress_content_streams()

                    if nivel in ["medio", "alta"]:
                        for img in page.images:
                            try:
                                img.replace(img.image, quality=(50 if nivel == "medio" else 25))
                            except Exception:
                                pass
            # 3. Guardamos el archivo final resultante
                    compression_processed += 1
                    current_pct = 40 + int((compression_processed / total_pages) * 50)
                    progress_var.set(current_pct)
                    lbl_percent.config(text=f"{current_pct}%")
            else:
                progress_var.set(90)
                lbl_percent.config(text="90%")

            # Fase 4: Guardado final en disco
            with open(output_file, "wb") as f:
                merger.write(f)
            merger.close()

            messagebox.showinfo("Éxito", f"¡PDFs unidos y comprimidos correctamente!\nGuardado en:\n{output_file}")
            self.clear_list()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al procesar los PDFs:\n{str(e)}")

            progress_var.set(100)
            lbl_percent.config(text="100%")

            msg_exito = (
                f"¡PDF comprimido correctamente!\nGuardado en:\n{output_file}"
                if es_unico_archivo
                else f"¡PDFs unidos y comprimidos correctamente!\nGuardado en:\n{output_file}"
            )
            
            self.root.after(0, lambda: [
                progress_dialog.destroy(),
                messagebox.showinfo("Éxito", msg_exito),
                self.clear_list(),
                self.reset_ui()
            ])

        except Exception as e:
            self.root.after(0, lambda: [
                progress_dialog.destroy(),
                messagebox.showerror("Error", f"Ocurrió un error al procesar el/los PDF(s):\n{str(e)}"),
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