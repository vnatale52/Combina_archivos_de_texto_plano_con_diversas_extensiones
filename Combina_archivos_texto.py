import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import chardet
from datetime import datetime
import shutil
import subprocess
import platform

# ---------------- Funciones ----------------
def detectar_codificacion(ruta):
    with open(ruta, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    return result['encoding'] or 'utf-8'

archivos_validos = []
subcarpetas_excluir = []
carpetas_origen = []

def agregar_carpeta_origen(carpeta):
    if carpeta not in carpetas_origen:
        carpetas_origen.append(carpeta)
    carpeta_origen_var.set("; ".join(carpetas_origen))
    refrescar_archivos()

def cargar_archivos():
    carpeta = filedialog.askdirectory(title="Selecciona carpeta de origen")
    if carpeta:
        agregar_carpeta_origen(carpeta)

def refrescar_archivos():
    global archivos_validos
    ext_permitidas = [e.strip().lower() for e in extensiones_var.get().split(',') if e.strip()]
    archivos_validos = []
    for c in carpetas_origen:
        for root, _, files in os.walk(c):
            if any(os.path.abspath(root) == os.path.abspath(excl) or os.path.abspath(root).startswith(os.path.abspath(excl)+os.sep)
                   for excl in subcarpetas_excluir):
                continue
            for f in files:
                ruta = os.path.join(root,f)
                ext = os.path.splitext(f)[1].lower()
                if ext in ext_permitidas and not f.startswith('_') and 'test' not in f.lower():
                    archivos_validos.append(ruta)
    archivos_validos.sort()
    actualizar_treeview()

def actualizar_treeview():
    for i in tree.get_children(): tree.delete(i)
    for f in archivos_validos:
        nombre = os.path.basename(f)
        carpeta_archivo = os.path.dirname(f)
        extension = os.path.splitext(f)[1]
        tamaño = os.path.getsize(f)/1024
        tree.insert('', 'end', values=(nombre, carpeta_archivo, extension, f"{tamaño:.2f} KB"))
    contador_incluidos_var.set(f"Archivos válidos: {len(archivos_validos)}")

def agregar_subcarpeta_excluir():
    carpeta = filedialog.askdirectory(title="Selecciona subcarpeta a excluir")
    if carpeta and carpeta not in subcarpetas_excluir:
        subcarpetas_excluir.append(carpeta)
        lista_excluir.delete(0, tk.END)
        for s in subcarpetas_excluir: lista_excluir.insert(tk.END, s)
        refrescar_archivos()

def seleccionar_destino():
    carpeta = filedialog.askdirectory(title="Selecciona carpeta destino")
    if carpeta: carpeta_destino_var.set(carpeta)

def combinar_archivos():
    destino = carpeta_destino_var.get()
    seleccion = archivos_validos.copy()
    if not destino:
        messagebox.showwarning("Error", "Selecciona una carpeta destino")
        return
    if not seleccion:
        messagebox.showwarning("Error", "No hay archivos válidos para combinar")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_salida = os.path.join(destino,f"archivo_combinado_{ts}.txt")
    if os.path.exists(archivo_salida):
        shutil.move(archivo_salida, archivo_salida.replace(".txt",f"_backup_{ts}.txt"))

    with open(archivo_salida,'w',encoding='utf-8') as out:
        out.write("=== ARCHIVOS INCLUIDOS ===\n")
        for f in seleccion: out.write(f + "\n")
        out.write("\n\n")
        total = len(seleccion)
        for i, f in enumerate(seleccion,1):
            out.write(f"--- {f} ---\n")
            try:
                enc = detectar_codificacion(f)
                with open(f,'r',encoding=enc) as ff: out.write(ff.read() + "\n\n")
            except Exception as e:
                messagebox.showwarning("Error de lectura", f"No se pudo combinar el archivo:\n{f}\n\nError: {e}")
            progreso_var.set((i/total)*100)
            root.update_idletasks()
    progreso_var.set(100)
    messagebox.showinfo("Completado", f"Archivos combinados en:\n{archivo_salida}")

def abrir_archivo(event):
    item = tree.identify('item', event.x, event.y)
    if not item: return
    ruta = os.path.join(tree.item(item)['values'][1], tree.item(item)['values'][0])
    if os.path.exists(ruta):
        if platform.system() == 'Windows':
            os.startfile(ruta)
        elif platform.system() == 'Darwin':
            subprocess.call(['open', ruta])
        else:
            subprocess.call(['xdg-open', ruta])

def ordenar_treeview(tree, col, reverse):
    data = [(tree.set(k, col), k) for k in tree.get_children('')]
    if col == "Tamaño":
        data = [(float(d[0].split()[0]), d[1]) for d in data]
    data.sort(reverse=reverse)
    for index, (val, k) in enumerate(data):
        tree.move(k, '', index)
    tree.heading(col, command=lambda: ordenar_treeview(tree, col, not reverse))

def drop(event):
    paths = root.tk.splitlist(event.data)
    for p in paths:
        if os.path.isdir(p):
            agregar_carpeta_origen(p)

def on_extensiones_cambio(*args):
    refrescar_archivos()

# ---------------- GUI -----------------
try:
    from tkinterdnd2 import TkinterDnD
    root = TkinterDnD.Tk()
    soporte_dnd = True
except ImportError:
    root = tk.Tk()
    soporte_dnd = False
    print("Drag & drop no disponible. Instala 'tkinterdnd2' para habilitarlo.")

root.title("Combinador de Archivos - Subcarpetas Excluidas")
root.geometry("1050x600")

carpeta_origen_var = tk.StringVar()
carpeta_destino_var = tk.StringVar()
extensiones_var = tk.StringVar(value=".js, .jsx, .html, .json, .css")
contador_incluidos_var = tk.StringVar(value="Archivos válidos: 0")
progreso_var = tk.DoubleVar()

# Refresco dinámico al cambiar extensiones
extensiones_var.trace_add("write", on_extensiones_cambio)

frame_top = tk.Frame(root)
frame_top.pack(pady=5,fill=tk.X)

tk.Label(frame_top,text="Carpetas origen:").grid(row=0,column=0,sticky="w")
tk.Entry(frame_top,textvariable=carpeta_origen_var,width=70).grid(row=0,column=1,padx=5)
tk.Button(frame_top,text="Agregar carpeta",command=cargar_archivos).grid(row=0,column=2)

tk.Label(frame_top,text="Carpeta destino:").grid(row=1,column=0,sticky="w")
tk.Entry(frame_top,textvariable=carpeta_destino_var,width=70).grid(row=1,column=1,padx=5)
tk.Button(frame_top,text="Seleccionar",command=seleccionar_destino).grid(row=1,column=2)

tk.Label(frame_top,text="Extensiones permitidas:").grid(row=2,column=0,sticky="w")
tk.Entry(frame_top,textvariable=extensiones_var,width=70).grid(row=2,column=1,padx=5,columnspan=2)

tk.Label(frame_top,text="Subcarpetas a excluir:").grid(row=3,column=0,sticky="w")
tk.Button(frame_top,text="Agregar subcarpeta",command=agregar_subcarpeta_excluir).grid(row=3,column=1,sticky="w")
lista_excluir = tk.Listbox(frame_top,height=4)
lista_excluir.grid(row=4,column=0,columnspan=2,sticky="we",padx=5)

tk.Label(frame_top,textvariable=contador_incluidos_var,fg="green").grid(row=5,column=0,sticky="w")

frame_tree = tk.Frame(root)
frame_tree.pack(fill=tk.BOTH,expand=True,pady=5)
tree_scroll = tk.Scrollbar(frame_tree)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
tree = ttk.Treeview(frame_tree, columns=("Archivo","Carpeta","Extensión","Tamaño"), show="headings", yscrollcommand=tree_scroll.set)
tree.heading("Archivo", text="Archivo", command=lambda: ordenar_treeview(tree, "Archivo", False))
tree.heading("Carpeta", text="Carpeta", command=lambda: ordenar_treeview(tree, "Carpeta", False))
tree.heading("Extensión", text="Extensión", command=lambda: ordenar_treeview(tree, "Extensión", False))
tree.heading("Tamaño", text="Tamaño", command=lambda: ordenar_treeview(tree, "Tamaño", False))
tree.column("Archivo", width=300)
tree.column("Carpeta", width=500)
tree.column("Extensión", width=80, anchor="center")
tree.column("Tamaño", width=80, anchor="e")
tree.pack(fill=tk.BOTH,expand=True)
tree_scroll.config(command=tree.yview)
tree.bind("<Double-1>", abrir_archivo)

frame_bot = tk.Frame(root)
frame_bot.pack(pady=5)
tk.Button(frame_bot,text="Combinar Archivos",command=combinar_archivos,bg="green",fg="white").grid(row=0,column=0,padx=5)
barra_progreso = ttk.Progressbar(frame_bot,variable=progreso_var,maximum=100,length=300)
barra_progreso.grid(row=0,column=1,padx=10)

if soporte_dnd:
    tree.drop_target_register('*')
    tree.dnd_bind('<<Drop>>', lambda event: [agregar_carpeta_origen(p) for p in root.tk.splitlist(event.data)])

# Mensaje informativo al iniciar
messagebox.showinfo("Información",
                    "Haz doble click sobre un archivo para abrirlo y editar su contenido.\n"
                    "Puedes agregar más extensiones de archivos de texto plano en 'Extensiones permitidas'.")

root.mainloop()
