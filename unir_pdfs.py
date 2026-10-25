import os
from tkinter import Tk, Listbox, Button, Label, Scrollbar, END, messagebox, filedialog
from pypdf import PdfWriter  # Actualizado a PdfWriter

class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unidor de PDFs")
        self.root.geometry("500x450")
        self.root.resizable(False, False)

        # Etiqueta de título
        self.label = Label(root, text="Selecciona los PDFs que deseas unir:", font=("Arial", 12, "bold"))
        self.label.pack(pady=10)

        # Listbox para mostrar los archivos seleccionados
        self.listbox_frame = Label(root)
        self.listbox_frame.pack(fill="both", expand=True, padx=20)

        self.scrollbar = Scrollbar(self.listbox_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.pdf_listbox = Listbox(self.listbox_frame, selectmode="extended", yscrollcommand=self.scrollbar.set, font=("Arial", 10))
        self.pdf_listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.pdf_listbox.yview)

        # Botones de control
        self.btn_select = Button(root, text="Agregar PDFs", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.select_files)
        self.btn_select.pack(fill="x", padx=20, pady=5)

        self.btn_remove = Button(root, text="Eliminar seleccionado", bg="#f44336", fg="white", font=("Arial", 10), command=self.remove_selected)
        self.btn_remove.pack(fill="x", padx=20, pady=2)

        self.btn_clear = Button(root, text="Limpiar lista", bg="#9e9e9e", fg="white", font=("Arial", 10), command=self.clear_list)
        self.btn_clear.pack(fill="x", padx=20, pady=2)

        self.btn_merge = Button(root, text="Unir y Guardar PDF", bg="#2196F3", fg="white", font=("Arial", 11, "bold"), command=self.merge_pdfs)
        self.btn_merge.pack(fill="x", padx=20, pady=10)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        for file in files:
            if file not in self.pdf_listbox.get(0, END):
                self.pdf_listbox.insert(END, file)

    def remove_selected(self):
        selected_indices = self.pdf_listbox.curselection()
        for index in reversed(selected_indices):
            self.pdf_listbox.delete(index)

    def clear_list(self):
        self.pdf_listbox.delete(0, END)

    def merge_pdfs(self):
        pdfs = self.pdf_listbox.get(0, END)
        
        if not pdfs:
            messagebox.showwarning("Advertencia", "No hay archivos PDF seleccionados para unir.")
            return

        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            title="Guardar PDF unido como..."
        )

        if not output_file:
            return

        try:
            # Usamos PdfWriter en lugar de PdfMerger
            merger = PdfWriter()

            for pdf in pdfs:
                merger.append(pdf)

            merger.write(output_file)
            merger.close()

            messagebox.showinfo("Éxito", f"¡PDFs unidos correctamente!\nGuardado en:\n{output_file}")
            self.clear_list()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al unir los PDFs:\n{str(e)}")

if __name__ == "__main__":
    root = Tk()
    app = PDFMergerApp(root)
    root.mainloop()
