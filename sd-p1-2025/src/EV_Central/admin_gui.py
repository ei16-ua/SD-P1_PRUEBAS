#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI de Administración de Puntos de Carga
Permite añadir, editar y eliminar CPs desde una interfaz gráfica
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Añadir el path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directo ya que estamos en EV_Central
from database import Database

class AdminCPsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔧 Administración de Puntos de Carga")
        self.root.geometry("1000x600")
        self.root.configure(bg='#1e1e1e')
        
        # Database (ruta relativa al archivo actual)
        db_path = os.path.join(os.path.dirname(__file__), 'central.db')
        self.db = Database(db_path)
        
        # Variables
        self.selected_cp_id = None
        
        # Crear interfaz
        self.create_widgets()
        
        # Cargar datos iniciales
        self.refresh_list()
    
    def create_widgets(self):
        """Crear la interfaz"""
        # Panel superior - Formulario
        form_frame = tk.Frame(self.root, bg='#2d2d2d', padx=20, pady=20)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Título del formulario
        title_label = tk.Label(form_frame, text="📝 Añadir/Editar Punto de Carga", 
                               font=('Arial', 14, 'bold'), bg='#2d2d2d', fg='white')
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        # Campo: ID
        tk.Label(form_frame, text="ID:", font=('Arial', 10), bg='#2d2d2d', fg='white').grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.id_entry = tk.Entry(form_frame, font=('Arial', 10), width=15)
        self.id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Campo: Ubicación
        tk.Label(form_frame, text="Ubicación:", font=('Arial', 10), bg='#2d2d2d', fg='white').grid(row=1, column=2, sticky='e', padx=5, pady=5)
        self.location_entry = tk.Entry(form_frame, font=('Arial', 10), width=30)
        self.location_entry.grid(row=1, column=3, padx=5, pady=5)
        
        # Campo: Precio
        tk.Label(form_frame, text="Precio (€/kWh):", font=('Arial', 10), bg='#2d2d2d', fg='white').grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.price_entry = tk.Entry(form_frame, font=('Arial', 10), width=15)
        self.price_entry.insert(0, "0.35")
        self.price_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Campo: Potencia máxima
        tk.Label(form_frame, text="Potencia (kW):", font=('Arial', 10), bg='#2d2d2d', fg='white').grid(row=2, column=2, sticky='e', padx=5, pady=5)
        self.kw_max_entry = tk.Entry(form_frame, font=('Arial', 10), width=15)
        self.kw_max_entry.insert(0, "11.0")
        self.kw_max_entry.grid(row=2, column=3, padx=5, pady=5, sticky='w')
        
        # Botones de acción
        btn_frame = tk.Frame(form_frame, bg='#2d2d2d')
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)
        
        self.add_btn = tk.Button(btn_frame, text="➕ Añadir", font=('Arial', 10, 'bold'),
                                 bg='#28a745', fg='white', width=12, command=self.add_cp)
        self.add_btn.pack(side=tk.LEFT, padx=5)
        
        self.update_btn = tk.Button(btn_frame, text="💾 Actualizar", font=('Arial', 10, 'bold'),
                                    bg='#ffc107', fg='black', width=12, command=self.update_cp, state=tk.DISABLED)
        self.update_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(btn_frame, text="🔄 Limpiar", font=('Arial', 10),
                                   bg='#6c757d', fg='white', width=12, command=self.clear_form)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = tk.Button(btn_frame, text="🗑️ Eliminar", font=('Arial', 10, 'bold'),
                                    bg='#dc3545', fg='white', width=12, command=self.delete_cp, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Panel inferior - Lista de CPs
        list_frame = tk.Frame(self.root, bg='#1e1e1e')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Título de la lista
        list_title = tk.Label(list_frame, text="📋 Puntos de Carga Registrados", 
                             font=('Arial', 12, 'bold'), bg='#1e1e1e', fg='white')
        list_title.pack(pady=(0, 10))
        
        # Tabla
        columns = ('ID', 'Ubicación', 'Precio (€/kWh)', 'Potencia (kW)', 'Estado')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.tree.heading('ID', text='ID')
        self.tree.heading('Ubicación', text='Ubicación')
        self.tree.heading('Precio (€/kWh)', text='Precio (€/kWh)')
        self.tree.heading('Potencia (kW)', text='Potencia (kW)')
        self.tree.heading('Estado', text='Estado')
        
        self.tree.column('ID', width=100)
        self.tree.column('Ubicación', width=300)
        self.tree.column('Precio (€/kWh)', width=120)
        self.tree.column('Potencia (kW)', width=120)
        self.tree.column('Estado', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Evento de selección
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # Botón de refrescar
        refresh_btn = tk.Button(list_frame, text="🔄 Refrescar Lista", font=('Arial', 10),
                               bg='#17a2b8', fg='white', command=self.refresh_list)
        refresh_btn.pack(pady=10)
        
        # Estilo de la tabla
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#2d2d2d", foreground="white", 
                       fieldbackground="#2d2d2d", borderwidth=0)
        style.configure("Treeview.Heading", background="#3d3d3d", foreground="white", 
                       font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#4d4d4d')])
    
    def refresh_list(self):
        """Actualizar la lista de CPs"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Cargar CPs de la base de datos
        cps = self.db.get_all_cps()
        
        for cp in cps:
            estado = "🟢 Online" if cp.get('connected') else "⚫ Offline"
            self.tree.insert('', tk.END, values=(
                cp['cp_id'],
                cp.get('location', 'Desconocido'),
                f"{cp.get('price_eur_kwh', 0.35):.2f}",
                f"{cp.get('kw_max', 11.0):.1f}",
                estado
            ))
    
    def on_select(self, event):
        """Manejar selección de un CP en la tabla"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        
        # Cargar datos en el formulario
        self.id_entry.delete(0, tk.END)
        self.id_entry.insert(0, values[0])
        self.id_entry.config(state='readonly')  # No permitir cambiar ID en edición
        
        self.location_entry.delete(0, tk.END)
        self.location_entry.insert(0, values[1])
        
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, values[2])
        
        self.kw_max_entry.delete(0, tk.END)
        self.kw_max_entry.insert(0, values[3])
        
        self.selected_cp_id = values[0]
        
        # Activar botones de edición
        self.update_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        self.add_btn.config(state=tk.DISABLED)
    
    def clear_form(self):
        """Limpiar el formulario"""
        self.id_entry.config(state='normal')
        self.id_entry.delete(0, tk.END)
        self.location_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, "0.35")
        self.kw_max_entry.delete(0, tk.END)
        self.kw_max_entry.insert(0, "11.0")
        
        self.selected_cp_id = None
        self.add_btn.config(state=tk.NORMAL)
        self.update_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        
        # Deseleccionar en la tabla
        self.tree.selection_remove(self.tree.selection())
    
    def add_cp(self):
        """Añadir un nuevo CP"""
        cp_id = self.id_entry.get().strip().upper()
        location = self.location_entry.get().strip()
        
        if not cp_id or not location:
            messagebox.showerror("Error", "Debes especificar ID y Ubicación")
            return
        
        try:
            price = float(self.price_entry.get())
            kw_max = float(self.kw_max_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Precio y Potencia deben ser números válidos")
            return
        
        # Verificar si ya existe
        existing = self.db.get_cp(cp_id)
        if existing:
            messagebox.showerror("Error", f"Ya existe un CP con el ID '{cp_id}'")
            return
        
        # Insertar en la base de datos
        self.db.upsert_cp(cp_id, location=location, price_eur_kwh=price, kw_max=kw_max, 
                         connected=False, ok=True, charging=False)
        
        messagebox.showinfo("Éxito", f"✅ CP '{cp_id}' añadido correctamente\n\n"
                                     f"ℹ️ No necesitas crear topics de Kafka\n"
                                     f"   Todos los CPs usan 'cp.commands.all'\n\n"
                                     f"Ya puedes iniciar el ENGINE para este CP.")
        
        self.clear_form()
        self.refresh_list()
    
    def update_cp(self):
        """Actualizar un CP existente"""
        if not self.selected_cp_id:
            messagebox.showerror("Error", "No hay ningún CP seleccionado")
            return
        
        location = self.location_entry.get().strip()
        
        if not location:
            messagebox.showerror("Error", "La ubicación no puede estar vacía")
            return
        
        try:
            price = float(self.price_entry.get())
            kw_max = float(self.kw_max_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Precio y Potencia deben ser números válidos")
            return
        
        # Actualizar en la base de datos
        self.db.upsert_cp(self.selected_cp_id, location=location, 
                         price_eur_kwh=price, kw_max=kw_max)
        
        messagebox.showinfo("Éxito", f"✅ CP '{self.selected_cp_id}' actualizado correctamente")
        
        self.clear_form()
        self.refresh_list()
    
    def delete_cp(self):
        """Eliminar un CP"""
        if not self.selected_cp_id:
            messagebox.showerror("Error", "No hay ningún CP seleccionado")
            return
        
        # Confirmar eliminación
        response = messagebox.askyesno("Confirmar eliminación", 
                                       f"¿Estás seguro de eliminar el CP '{self.selected_cp_id}'?\n\n"
                                       f"Esta acción no se puede deshacer.")
        
        if not response:
            return
        
        # Eliminar de la base de datos
        self.db.delete_cp(self.selected_cp_id)
        
        messagebox.showinfo("Éxito", f"✅ CP '{self.selected_cp_id}' eliminado correctamente\n\n"
                                     f"💡 Puedes eliminar el topic de Kafka con:\n"
                                     f"docker exec kafka kafka-topics --delete --bootstrap-server localhost:9092 "
                                     f"--topic cp.commands.{self.selected_cp_id}")
        
        self.clear_form()
        self.refresh_list()

def main():
    root = tk.Tk()
    app = AdminCPsGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
