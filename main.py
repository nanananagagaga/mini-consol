"""
Mini Consola para Procesamiento de Block Models
===============================================

Esta aplicación permite:
1. Leer múltiples archivos CSV (block models cortados)
2. Asignar etiquetas de sólido a cada archivo
3. Aplicar reglas de capping configurables
4. Calcular variables derivadas
5. Exportar resultado consolidado
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import os
from pathlib import Path
from data_processor import BlockModelProcessor
from rules_config import RulesManager

class MiniConsolaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Consola - Block Model Processor")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Variables de estado
        self.csv_files = []
        self.folder_path = tk.StringVar()
        self.column_mappings = {}
        self.solido_labels = {}
        self.rules_manager = RulesManager()
        self.processor = BlockModelProcessor()
        
        # Variables para datos detectados automáticamente
        self.available_solidos = []
        self.available_pas_cut_values = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña 1: Configuración de archivos
        self.setup_files_tab(notebook)
        
        # Pestaña 2: Configuración de columnas
        self.setup_columns_tab(notebook)
        
        # Pestaña 3: Reglas de capping
        self.setup_rules_tab(notebook)
        
        # Pestaña 4: Preview antes/después
        self.setup_preview_tab(notebook)
        
        # Pestaña 5: Procesamiento y resultados
        self.setup_processing_tab(notebook)
    
    def setup_files_tab(self, notebook):
        """Configurar pestaña de selección de archivos"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="1. Archivos CSV")
        
        # Sección de selección de carpeta
        folder_frame = ttk.LabelFrame(frame, text="Seleccionar Carpeta de CSVs", padding=10)
        folder_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(folder_frame, text="Carpeta:").grid(row=0, column=0, sticky='w', padx=5)
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(folder_frame, text="Examinar", command=self.select_folder).grid(row=0, column=2, padx=5)
        
        # Lista de archivos CSV encontrados
        files_frame = ttk.LabelFrame(frame, text="Archivos CSV Encontrados", padding=10)
        files_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview para mostrar archivos y asignar etiquetas de sólido
        columns = ('archivo', 'etiqueta_solido')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=10)
        self.files_tree.heading('archivo', text='Archivo CSV')
        self.files_tree.heading('etiqueta_solido', text='Sólido')
        self.files_tree.column('archivo', width=400)
        self.files_tree.column('etiqueta_solido', width=200)
        
        scrollbar_files = ttk.Scrollbar(files_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar_files.set)
        
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar_files.pack(side='right', fill='y')
        
        # Botón para editar etiqueta
        edit_frame = ttk.Frame(files_frame)
        edit_frame.pack(fill='x', pady=5)
        ttk.Button(edit_frame, text="Editar Sólido", command=self.edit_solido_label).pack()
    
    def setup_columns_tab(self, notebook):
        """Configurar pestaña de mapeo de columnas"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="2. Columnas")
        
        info_label = ttk.Label(frame, text="Mapear las columnas de tus CSVs a las variables requeridas:", 
                              font=('Arial', 10, 'bold'))
        info_label.pack(pady=10)
        
        # Frame para mapeo de columnas
        mapping_frame = ttk.LabelFrame(frame, text="Mapeo de Columnas", padding=20)
        mapping_frame.pack(fill='x', padx=20, pady=10)
        
        # Variables para almacenar los mappings
        self.cut_op_var = tk.StringVar()
        self.rst_op_var = tk.StringVar()
        self.pas_cut_var = tk.StringVar()
        
        ttk.Label(mapping_frame, text="Columna para CUT_OP:").grid(row=0, column=0, sticky='w', pady=5)
        self.cut_op_combo = ttk.Combobox(mapping_frame, textvariable=self.cut_op_var, width=30)
        self.cut_op_combo.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(mapping_frame, text="Columna para RST_OP:").grid(row=1, column=0, sticky='w', pady=5)
        self.rst_op_combo = ttk.Combobox(mapping_frame, textvariable=self.rst_op_var, width=30)
        self.rst_op_combo.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(mapping_frame, text="Columna para PAS_CUT:").grid(row=2, column=0, sticky='w', pady=5)
        self.pas_cut_combo = ttk.Combobox(mapping_frame, textvariable=self.pas_cut_var, width=30)
        self.pas_cut_combo.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Button(mapping_frame, text="🔍 Analizar Columnas Comunes en Todos los CSVs", 
                  command=self.auto_detect_columns).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Bind eventos para actualizar cuando cambian las selecciones
        self.cut_op_combo.bind('<<ComboboxSelected>>', lambda e: self.update_available_values())
        self.rst_op_combo.bind('<<ComboboxSelected>>', lambda e: self.update_available_values())
        self.pas_cut_combo.bind('<<ComboboxSelected>>', lambda e: self.update_available_values())
    
    def setup_rules_tab(self, notebook):
        """Configurar pestaña de reglas de capping"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="3. Reglas de Capping")
        
        # Frame de información
        info_frame = ttk.LabelFrame(frame, text="Información de Configuración", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.rules_info_label = ttk.Label(info_frame, text="Configura archivos y mapea columnas primero", 
                                         font=('Arial', 9))
        self.rules_info_label.pack(side='left')
        
        ttk.Button(info_frame, text="🔄 Actualizar", 
                  command=self.update_rules_info).pack(side='right', padx=5)
        
        # Frame de control de reglas
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="➕ Agregar Regla", command=self.add_capping_rule).pack(side='left', padx=5)
        ttk.Button(control_frame, text="✏️ Editar Regla", command=self.edit_capping_rule).pack(side='left', padx=5)
        ttk.Button(control_frame, text="🗑️ Eliminar Regla", command=self.delete_capping_rule).pack(side='left', padx=5)
        
        # Treeview para mostrar reglas
        rules_frame = ttk.LabelFrame(frame, text="Reglas de Capping Configuradas", padding=10)
        rules_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('solido', 'pas_cut', 'rango_min', 'rango_max', 'multiplicador')
        self.rules_tree = ttk.Treeview(rules_frame, columns=columns, show='headings', height=12)
        
        self.rules_tree.heading('solido', text='Sólido')
        self.rules_tree.heading('pas_cut', text='Pas Cut')
        self.rules_tree.heading('rango_min', text='Rango Mín')
        self.rules_tree.heading('rango_max', text='Rango Máx')
        self.rules_tree.heading('multiplicador', text='Multiplicador')
        
        # Ajustar anchos de columnas
        self.rules_tree.column('solido', width=80)
        self.rules_tree.column('pas_cut', width=80)
        self.rules_tree.column('rango_min', width=100)
        self.rules_tree.column('rango_max', width=100)
        self.rules_tree.column('multiplicador', width=120)
        
        scrollbar_rules = ttk.Scrollbar(rules_frame, orient='vertical', command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar_rules.set)
        
        self.rules_tree.pack(side='left', fill='both', expand=True)
        scrollbar_rules.pack(side='right', fill='y')
        
        # Inicializar con reglas por defecto
        self.refresh_rules_tree()
    
    def setup_preview_tab(self, notebook):
        """Configurar pestaña de preview antes/después"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="4. Preview")
        
        # Información superior
        info_frame = ttk.LabelFrame(frame, text="Vista Previa de Cambios", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        info_text = "Aquí puedes ver el antes y después de aplicar las reglas de capping por cada combinación Sólido/PAS_CUT"
        ttk.Label(info_frame, text=info_text, font=('Arial', 9)).pack()
        
        # Botón para generar preview
        button_frame = ttk.Frame(info_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="🔍 Generar Preview", 
                  command=self.generate_preview, 
                  style='Accent.TButton').pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="🔄 Actualizar", 
                  command=self.refresh_preview).pack(side='left', padx=5)
        
        # Área de resultados con scroll
        results_frame = ttk.LabelFrame(frame, text="Comparación Antes/Después", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Text widget con scrollbar para mostrar resultados
        self.preview_text = tk.Text(results_frame, height=20, width=80, font=('Consolas', 9))
        scrollbar_preview = ttk.Scrollbar(results_frame, orient='vertical', command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar_preview.set)
        
        self.preview_text.pack(side='left', fill='both', expand=True)
        scrollbar_preview.pack(side='right', fill='y')
        
        # Agregar texto inicial
        self.preview_text.insert('1.0', "📋 Configura archivos, columnas y reglas, luego haz clic en 'Generar Preview'\n\n")
        self.preview_text.config(state='disabled')
    
    def setup_processing_tab(self, notebook):
        """Configurar pestaña de procesamiento"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="5. Procesamiento")
        
        # Opciones de guardado
        save_options_frame = ttk.LabelFrame(frame, text="Opciones de Guardado", padding=15)
        save_options_frame.pack(fill='x', padx=20, pady=10)
        
        self.save_option = tk.StringVar(value="create_duplicates")
        
        # Opción 1: Guardar duplicados (SEGURO - por defecto)
        opt1_frame = ttk.Frame(save_options_frame)
        opt1_frame.pack(fill='x', pady=5)
        ttk.Radiobutton(opt1_frame, text="� Crear BMs duplicados (Recomendado)", 
                       variable=self.save_option, value="create_duplicates").pack(side='left')
        ttk.Label(opt1_frame, text="(Crea copias con sufijo '_capeado.csv')", 
                 font=('Arial', 8), foreground='darkgreen').pack(side='left', padx=(10, 0))
        
        # Opción 2: Actualizar archivos originales (PELIGROSO)
        opt2_frame = ttk.Frame(save_options_frame)
        opt2_frame.pack(fill='x', pady=5)
        ttk.Radiobutton(opt2_frame, text="⚠️ Actualizar BMs originales", 
                       variable=self.save_option, value="update_original").pack(side='left')
        ttk.Label(opt2_frame, text="(Sobrescribe archivos originales - ¡Cuidado!)", 
                 font=('Arial', 8), foreground='darkorange').pack(side='left', padx=(10, 0))
        
        # Opción 3: Consolidar todo
        opt3_frame = ttk.Frame(save_options_frame)
        opt3_frame.pack(fill='x', pady=5)
        ttk.Radiobutton(opt3_frame, text="📊 Consolidar en un solo archivo", 
                       variable=self.save_option, value="consolidate_all").pack(side='left')
        ttk.Label(opt3_frame, text="(Guarda todo en 'blockmodel_capeado.csv')", 
                 font=('Arial', 8), foreground='darkblue').pack(side='left', padx=(10, 0))
        
        # Botón de procesamiento
        process_frame = ttk.Frame(frame)
        process_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Button(process_frame, text="🚀 PROCESAR BLOCK MODELS", 
                  command=self.process_data, 
                  style='Accent.TButton').pack(pady=10)
        
        # Área de log/resultados
        log_frame = ttk.LabelFrame(frame, text="Log de Procesamiento", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=80)
        scrollbar_log = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar_log.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar_log.pack(side='right', fill='y')
    
    def select_folder(self):
        """Seleccionar carpeta con archivos CSV"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.scan_csv_files()
    
    def scan_csv_files(self):
        """Escanear archivos CSV en la carpeta seleccionada"""
        folder = self.folder_path.get()
        if not folder or not os.path.exists(folder):
            return
        
        # Limpiar lista anterior
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        self.csv_files = []
        
        # Buscar archivos CSV
        for file_path in Path(folder).glob("*.csv"):
            filename = file_path.name
            self.csv_files.append(str(file_path))
            
            # Agregar a la vista con etiqueta por defecto
            default_label = filename.replace('.csv', '')
            self.solido_labels[str(file_path)] = default_label
            
            self.files_tree.insert('', 'end', values=(filename, default_label))
        
        self.log(f"Encontrados {len(self.csv_files)} archivos CSV")
        
        # Auto-detectar columnas del primer archivo
        if self.csv_files:
            self.auto_detect_columns()
    
    def auto_detect_columns(self):
        """Auto-detectar columnas comunes en TODOS los archivos CSV"""
        if not self.csv_files:
            return
        
        try:
            self.log("🔍 Analizando columnas en todos los archivos CSV...")
            
            all_columns_sets = []
            file_columns_info = []
            
            # Leer columnas de cada archivo
            for i, csv_path in enumerate(self.csv_files):
                try:
                    # Intentar lectura normal primero
                    df_normal = pd.read_csv(csv_path, nrows=0)
                    columns_normal = set(df_normal.columns)
                    
                    # Intentar con skip de filas problemáticas
                    df_skip = pd.read_csv(csv_path, nrows=0, skiprows=[1, 2, 3])
                    columns_skip = set(df_skip.columns)
                    
                    # Usar el set de columnas que sea más confiable
                    if len(columns_skip) >= len(columns_normal):
                        file_columns = columns_skip
                        method = "(skip filas problemáticas)"
                    else:
                        file_columns = columns_normal
                        method = "(lectura normal)"
                    
                    all_columns_sets.append(file_columns)
                    file_name = Path(csv_path).name
                    file_columns_info.append({
                        'file': file_name,
                        'columns': file_columns,
                        'count': len(file_columns),
                        'method': method
                    })
                    
                    self.log(f"  📄 {file_name}: {len(file_columns)} columnas {method}")
                    
                except Exception as e:
                    self.log(f"  ❌ Error leyendo {Path(csv_path).name}: {str(e)}")
                    continue
            
            if not all_columns_sets:
                self.log("❌ No se pudieron leer columnas de ningún archivo")
                return
            
            # Encontrar columnas comunes (intersección de todos los sets)
            common_columns = all_columns_sets[0]
            for columns_set in all_columns_sets[1:]:
                common_columns = common_columns.intersection(columns_set)
            
            common_columns_list = sorted(list(common_columns))
            
            # Mostrar información detallada
            self.log(f"📊 Resumen de análisis:")
            self.log(f"  - Archivos analizados: {len(all_columns_sets)}")
            self.log(f"  - Columnas comunes en TODOS: {len(common_columns_list)}")
            
            # Mostrar columnas que NO están en todos los archivos
            all_unique_columns = set()
            for columns_set in all_columns_sets:
                all_unique_columns.update(columns_set)
            
            missing_in_some = all_unique_columns - common_columns
            if missing_in_some:
                self.log(f"  - Columnas que faltan en algunos archivos: {len(missing_in_some)}")
                for col in sorted(missing_in_some):
                    files_with_col = []
                    for info in file_columns_info:
                        if col in info['columns']:
                            files_with_col.append(info['file'])
                    self.log(f"    • '{col}' presente solo en: {', '.join(files_with_col)}")
            
            if not common_columns_list:
                self.log("⚠️ No hay columnas comunes en todos los archivos")
                self.log("💡 Sugerencia: Verifica que todos los CSVs tengan la misma estructura")
                return
            
            # Actualizar comboboxes solo con columnas comunes
            for combo in [self.cut_op_combo, self.rst_op_combo, self.pas_cut_combo]:
                combo['values'] = common_columns_list
            
            # Intentar mapear automáticamente
            mapped_count = 0
            for col in common_columns_list:
                col_lower = col.lower()
                if 'cut' in col_lower and 'op' in col_lower and not self.cut_op_var.get():
                    self.cut_op_var.set(col)
                    mapped_count += 1
                elif 'rst' in col_lower and 'op' in col_lower and not self.rst_op_var.get():
                    self.rst_op_var.set(col)
                    mapped_count += 1
                elif 'pas' in col_lower and 'cut' in col_lower and not self.pas_cut_var.get():
                    self.pas_cut_var.set(col)
                    mapped_count += 1
            
            self.log(f"✅ Columnas comunes disponibles: {', '.join(common_columns_list)}")
            if mapped_count > 0:
                self.log(f"🎯 Mapeo automático realizado para {mapped_count} columnas")
            
            # Actualizar valores disponibles para reglas
            self.update_available_values()
            
        except Exception as e:
            self.log(f"❌ Error al detectar columnas: {str(e)}")
    
    def update_available_values(self):
        """Actualizar listas de valores disponibles para reglas de capping"""
        # Actualizar sólidos disponibles
        self.available_solidos = list(set(self.solido_labels.values()))
        
        # Actualizar valores únicos de pas_cut si tenemos columna mapeada
        self.available_pas_cut_values = []
        
        if self.pas_cut_var.get() and self.csv_files:
            try:
                unique_pas_cut = set()
                files_analyzed = 0
                
                self.log(f"🔍 Analizando valores únicos de {self.pas_cut_var.get()}...")
                
                # Leer cada archivo y extraer valores únicos de pas_cut
                for csv_path in self.csv_files:
                    try:
                        file_name = Path(csv_path).name
                        
                        # Intentar ambos métodos de lectura
                        df = None
                        try:
                            df = pd.read_csv(csv_path, skiprows=[1, 2, 3], nrows=100)
                        except:
                            df = pd.read_csv(csv_path, nrows=100)
                        
                        pas_cut_col = self.pas_cut_var.get()
                        if pas_cut_col in df.columns:
                            # Obtener valores únicos y convertir a string
                            values = df[pas_cut_col].dropna().astype(str).unique()
                            file_unique_count = len(values)
                            unique_pas_cut.update(values)
                            files_analyzed += 1
                            
                            self.log(f"  📄 {file_name}: {file_unique_count} valores únicos")
                        else:
                            self.log(f"  ❌ {file_name}: columna '{pas_cut_col}' no encontrada")
                            
                    except Exception as e:
                        self.log(f"  ❌ {Path(csv_path).name}: error leyendo ({str(e)[:50]})")
                        continue
                
                self.available_pas_cut_values = sorted(list(unique_pas_cut))
                
                if self.available_pas_cut_values:
                    self.log(f"✅ Total valores únicos de {self.pas_cut_var.get()}: "
                           f"{', '.join(self.available_pas_cut_values)} "
                           f"(de {files_analyzed} archivos)")
                else:
                    self.log(f"⚠️ No se encontraron valores válidos de {self.pas_cut_var.get()}")
                
            except Exception as e:
                self.log(f"❌ Error detectando valores de PAS_CUT: {str(e)}")
        
        # Log de sólidos disponibles
        if self.available_solidos:
            self.log(f"Sólidos configurados: {', '.join(self.available_solidos)}")
        
        # Actualizar info en pestaña de reglas
        self.update_rules_info()
    
    def update_rules_info(self):
        """Actualizar información mostrada en pestaña de reglas"""
        try:
            solidos_count = len(self.available_solidos)
            pas_cut_count = len(self.available_pas_cut_values)
            
            if solidos_count == 0:
                info_text = "⚠️ Configura archivos y asigna sólidos primero"
            elif pas_cut_count == 0:
                info_text = f"✅ {solidos_count} sólidos | ⚠️ Mapea columna PAS_CUT"
            else:
                info_text = f"✅ {solidos_count} sólidos | ✅ {pas_cut_count} valores PAS_CUT detectados"
            
            self.rules_info_label.config(text=info_text)
            
        except Exception:
            pass
    
    def edit_solido_label(self):
        """Editar etiqueta de sólido del archivo seleccionado"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return
        
        item = selection[0]
        filename, current_label = self.files_tree.item(item, 'values')
        
        new_label = simpledialog.askstring("Editar Sólido", 
                                            f"Nuevo sólido para {filename}:", 
                                            initialvalue=current_label)
        if new_label:
            # Encontrar el path completo
            for csv_path in self.csv_files:
                if Path(csv_path).name == filename:
                    self.solido_labels[csv_path] = new_label
                    self.files_tree.item(item, values=(filename, new_label))
                    # Actualizar valores disponibles cuando se cambia un sólido
                    self.update_available_values()
                    break
    
    def add_capping_rule(self):
        """Agregar nueva regla de capping"""
        self.show_rule_dialog()
    
    def edit_capping_rule(self):
        """Editar regla de capping seleccionada"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una regla primero")
            return
        
        item = selection[0]
        values = self.rules_tree.item(item, 'values')
        self.show_rule_dialog(values)
    
    def delete_capping_rule(self):
        """Eliminar regla de capping seleccionada"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una regla primero")
            return
        
        if messagebox.askyesno("Confirmar", "¿Eliminar la regla seleccionada?"):
            item = selection[0]
            values = self.rules_tree.item(item, 'values')
            self.rules_manager.remove_rule(values[0], values[1], float(values[2]), float(values[3]))
            self.rules_tree.delete(item)
    
    def show_rule_dialog(self, existing_values=None):
        """Mostrar diálogo para agregar/editar regla"""
        # Actualizar listas disponibles antes de mostrar diálogo
        self.update_available_values()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Regla de Capping")
        dialog.geometry("500x500")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar el diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"500x500+{x}+{y}")
        
        # Crear contenedor principal con scrollbar si es necesario
        main_container = ttk.Frame(dialog)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Información en la parte superior
        info_frame = ttk.LabelFrame(main_container, text="Información", padding=10)
        info_frame.pack(fill='x', pady=(0, 10))
        
        info_text = f"Sólidos disponibles: {len(self.available_solidos)} configurados\n"
        info_text += f"Valores PAS_CUT: {len(self.available_pas_cut_values)} detectados"
        ttk.Label(info_frame, text=info_text, font=('Arial', 9)).pack()
        
        # Frame principal para los campos
        main_frame = ttk.LabelFrame(main_container, text="Configurar Regla", padding=15)
        main_frame.pack(fill='x', pady=(0, 10))
        
        # Variables
        solido_var = tk.StringVar(value=existing_values[0] if existing_values else "")
        pas_cut_var = tk.StringVar(value=existing_values[1] if existing_values else "")
        rango_min_var = tk.DoubleVar(value=float(existing_values[2]) if existing_values else 0.0)
        rango_max_var = tk.DoubleVar(value=float(existing_values[3]) if existing_values else 1.0)
        multiplicador_var = tk.DoubleVar(value=float(existing_values[4]) if existing_values else 1.0)
        
        # Campos del formulario con comboboxes
        ttk.Label(main_frame, text="Sólido:").grid(row=0, column=0, sticky='w', padx=5, pady=8)
        solido_combo = ttk.Combobox(main_frame, textvariable=solido_var, width=20, state='readonly')
        solido_combo['values'] = self.available_solidos if self.available_solidos else ["⚠️ Configura archivos primero"]
        solido_combo.grid(row=0, column=1, padx=5, pady=8, sticky='w')
        
        ttk.Label(main_frame, text="Pas Cut:").grid(row=1, column=0, sticky='w', padx=5, pady=8)
        pas_cut_combo = ttk.Combobox(main_frame, textvariable=pas_cut_var, width=20, state='readonly')
        pas_cut_combo['values'] = self.available_pas_cut_values if self.available_pas_cut_values else ["⚠️ Mapea columnas primero"]
        pas_cut_combo.grid(row=1, column=1, padx=5, pady=8, sticky='w')
        
        ttk.Label(main_frame, text="Rango Mínimo:").grid(row=2, column=0, sticky='w', padx=5, pady=8)
        range_min_entry = ttk.Entry(main_frame, textvariable=rango_min_var, width=22)
        range_min_entry.grid(row=2, column=1, padx=5, pady=8, sticky='w')
        
        ttk.Label(main_frame, text="Rango Máximo:").grid(row=3, column=0, sticky='w', padx=5, pady=8)
        range_max_entry = ttk.Entry(main_frame, textvariable=rango_max_var, width=22)
        range_max_entry.grid(row=3, column=1, padx=5, pady=8, sticky='w')
        
        ttk.Label(main_frame, text="Multiplicador:").grid(row=4, column=0, sticky='w', padx=5, pady=8)
        mult_entry = ttk.Entry(main_frame, textvariable=multiplicador_var, width=22)
        mult_entry.grid(row=4, column=1, padx=5, pady=8, sticky='w')
        
        # Ejemplo de uso
        example_frame = ttk.LabelFrame(main_container, text="Ejemplo", padding=10)
        example_frame.pack(fill='x', pady=(0, 10))
        
        example_text = "Ejemplo: Sólido='10', PAS_CUT='3', Min=0.5, Max=1.0, Mult=0.9\n"
        example_text += "→ Si CUT_OP está entre 0.5 y 1.0, CUT_PLAN = CUT_OP × 0.9"
        ttk.Label(example_frame, text=example_text, font=('Arial', 8), foreground='gray').pack()
        
        # Botones - IMPORTANTE: Usar pack para que sean siempre visibles
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill='x', pady=(10, 0), side='bottom')
        
        def save_rule():
            try:
                solido = solido_var.get()
                pas_cut = pas_cut_var.get()
                rango_min = rango_min_var.get()
                rango_max = rango_max_var.get()
                multiplicador = multiplicador_var.get()
                
                if not solido:
                    messagebox.showerror("Error", "Debe seleccionar un Sólido")
                    return
                
                if not pas_cut:
                    messagebox.showerror("Error", "Debe seleccionar un valor de Pas Cut")
                    return
                
                if rango_max <= rango_min:
                    messagebox.showerror("Error", "Rango Máximo debe ser mayor que Rango Mínimo")
                    return
                
                if multiplicador <= 0:
                    messagebox.showerror("Error", "Multiplicador debe ser mayor que 0")
                    return
                
                # Agregar regla
                self.rules_manager.add_rule(solido, pas_cut, rango_min, rango_max, multiplicador)
                
                # Actualizar vista
                self.refresh_rules_tree()
                
                # Mensaje de confirmación
                self.log(f"✅ Regla agregada: Sólido '{solido}', PAS_CUT '{pas_cut}', "
                        f"rango [{rango_min}, {rango_max}), multiplicador {multiplicador}")
                
                # Cerrar diálogo
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar regla: {str(e)}")
        
        # Separador visual
        ttk.Separator(button_frame, orient='horizontal').pack(fill='x', pady=(0, 10))
        
        # Frame para centrar botones
        btn_center_frame = ttk.Frame(button_frame)
        btn_center_frame.pack(expand=True)
        
        # Botones principales con estilo
        save_btn = ttk.Button(btn_center_frame, text="✅ Guardar Regla", command=save_rule)
        save_btn.pack(side='left', padx=10, pady=10, ipadx=20)
        
        cancel_btn = ttk.Button(btn_center_frame, text="❌ Cancelar", command=dialog.destroy)
        cancel_btn.pack(side='left', padx=10, pady=10, ipadx=20)
        
        # Hacer el botón de guardar el foco por defecto
        save_btn.focus_set()
        dialog.bind('<Return>', lambda e: save_rule())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def refresh_rules_tree(self):
        """Actualizar vista de reglas"""
        # Limpiar vista
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # Agregar reglas actuales
        for rule in self.rules_manager.get_all_rules():
            self.rules_tree.insert('', 'end', values=(
                rule['solido'], rule['pas_cut'], rule['rango_min'], 
                rule['rango_max'], rule['multiplicador']
            ))
    
    def generate_preview(self):
        """Generar preview de antes/después para todas las combinaciones sólido/pas_cut"""
        try:
            # Validaciones
            if not self.csv_files:
                messagebox.showerror("Error", "Primero selecciona archivos CSV")
                return
                
            column_mapping = self._get_current_column_mapping()
            if not column_mapping:
                messagebox.showerror("Error", "Primero configura el mapeo de columnas")
                return
            
            # Limpiar área de preview
            self.preview_text.config(state='normal')
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', "🔄 Generando preview...\n\n")
            self.preview_text.update()
            
            # Obtener datos de muestra de cada archivo
            preview_data = []
            
            for csv_path in self.csv_files:
                try:
                    # Leer archivo (ya sin metadata porque skipea filas 2-4)
                    df = self.processor._read_csv_safe(csv_path, lambda x: None)
                    
                    if df is None or df.empty:
                        continue
                    
                    # Mapear columnas para trabajo interno (ya no necesitamos limpieza adicional)
                    df_work = df.copy()
                    for std_name, user_col in column_mapping.items():
                        if user_col in df.columns:
                            df_work[std_name] = pd.to_numeric(df[user_col], errors='coerce')
                    
                    # Agregar sólido
                    solido_label = self.solido_labels.get(csv_path, "unknown")
                    df_work['solido'] = solido_label
                    df_work['pas_cut'] = df_work['pas_cut'].astype(str)
                    
                    # Crear versión "antes" (sin reglas)
                    df_work['cut_plan_antes'] = df_work['cut_op'].copy()
                    
                    # Crear versión "después" (con reglas)
                    df_work['cut_plan'] = df_work['cut_op'].copy()
                    df_work = self.processor._apply_capping_rules(df_work, self.rules_manager.get_all_rules(), lambda x: None)
                    df_work['cut_plan_despues'] = df_work['cut_plan'].copy()
                    
                    # Agrupar por sólido/pas_cut para estadísticas
                    for (solido, pas_cut), group in df_work.groupby(['solido', 'pas_cut']):
                        # Buscar reglas que realmente se aplican a los datos de este grupo
                        all_rules = self.rules_manager.get_rules_for_solido_pascut(solido, pas_cut)
                        actually_applied_rules = []
                        
                        # Verificar qué reglas realmente afectan a los valores de CUT_OP en este grupo
                        cut_op_values = group['cut_op']
                        min_cut_op = cut_op_values.min()
                        max_cut_op = cut_op_values.max()
                        
                        for rule in all_rules:
                            # Una regla se aplica si hay solapamiento entre el rango de la regla
                            # y el rango de valores CUT_OP en este grupo
                            rule_min = rule['rango_min']
                            rule_max = rule['rango_max']
                            
                            # DEBUG: Mostrar cálculo de solapamiento
                            has_overlap = max_cut_op > rule_min and min_cut_op < rule_max
                            # print(f"DEBUG: {solido}/{pas_cut} - Datos[{min_cut_op:.1f}, {max_cut_op:.1f}] vs Regla[{rule_min:.1f}, {rule_max:.1f}) = {has_overlap}")
                            
                            # Hay solapamiento si: max_datos > rule_min Y min_datos < rule_max
                            if has_overlap:
                                actually_applied_rules.append(rule)
                        
                        preview_data.append({
                            'archivo': Path(csv_path).name,
                            'solido': solido,
                            'pas_cut': pas_cut,
                            'filas': len(group),
                            'cut_op_stats': group['cut_op'].describe(),
                            'antes_stats': group['cut_plan_antes'].describe(),
                            'despues_stats': group['cut_plan_despues'].describe(),
                            'cambios': (group['cut_plan_despues'] != group['cut_plan_antes']).sum(),
                            'reglas_aplicables': actually_applied_rules,
                            'reglas_definidas': all_rules  # Todas las reglas para esta combinación
                        })
                        
                except Exception as e:
                    self.log(f"Error procesando {Path(csv_path).name}: {str(e)}")
                    continue
            
            # Buscar reglas no utilizadas
            all_dataframes = []
            for csv_path in self.csv_files:
                try:
                    column_mapping = self._get_current_column_mapping()
                    df = self.processor._read_csv_safe(csv_path, lambda x: None)
                    df_work = self.processor._map_columns(df, column_mapping, lambda x: None)
                    
                    if not df_work.empty:
                        solido_label = self.solido_labels.get(csv_path, "unknown")
                        df_work['solido'] = solido_label
                        df_work['pas_cut'] = df_work['pas_cut'].astype(str)
                        all_dataframes.append(df_work)
                except:
                    continue
            
            unused_rules = self.rules_manager.get_unused_rules(all_dataframes)
            
            # Mostrar resultados
            self._display_preview_results(preview_data, unused_rules)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando preview: {str(e)}")
            self.preview_text.config(state='normal')
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"❌ Error: {str(e)}\n")
            self.preview_text.config(state='disabled')
    
    def refresh_preview(self):
        """Actualizar preview con datos actuales"""
        self.generate_preview()
    
    def _get_metadata_rows(self, csv_path):
        """Obtener las filas metadata (2, 3, 4) de un archivo CSV original"""
        try:
            # Leer las primeras 5 filas SIN HEADERS para capturar toda la metadata
            df_full = pd.read_csv(csv_path, nrows=5, header=None)
            
            if len(df_full) >= 4:
                # Ahora sí, extraer las filas 2, 3, 4 del archivo (índices 1, 2, 3)
                # índice 0 = header, índice 1,2,3 = metadata filas 2,3,4
                metadata_rows = df_full.iloc[1:4]  # Filas 2, 3, 4 completas
                return metadata_rows
            else:
                return pd.DataFrame()
        except Exception as e:
            self.log(f"Error obteniendo metadata de {os.path.basename(csv_path)}: {str(e)}")
            return pd.DataFrame()
    
    def _save_csv_with_metadata(self, df_data, output_path, reference_csv_path):
        """Guardar CSV con metadata insertada entre headers y datos"""
        try:
            # Obtener filas metadata del archivo de referencia
            metadata_df = self._get_metadata_rows(reference_csv_path)
            
            if metadata_df.empty:
                # Si no hay metadata, guardar normalmente
                df_data.to_csv(output_path, index=False)
                return
            
            # Crear el archivo final con estructura correcta:
            # 1. Headers (nombres de columnas)
            # 2. Filas metadata (2, 3, 4)  
            # 3. Datos procesados
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                # 1. Escribir headers
                headers = ','.join(df_data.columns)
                f.write(headers + '\n')
                
                # 2. Escribir filas metadata
                for _, row in metadata_df.iterrows():
                    # Asegurar que tiene el mismo número de columnas que df_data
                    metadata_values = []
                    for i, col in enumerate(df_data.columns):
                        if i < len(row):
                            metadata_values.append(str(row.iloc[i]))
                        else:
                            metadata_values.append('')  # Rellenar con vacío si falta
                    f.write(','.join(metadata_values) + '\n')
                
                # 3. Escribir datos (sin headers)
                df_data.to_csv(f, header=False, index=False)
                
            self.log(f"  - CSV guardado con metadata incluida")
                
        except Exception as e:
            self.log(f"Error guardando CSV con metadata: {str(e)}")
            # Fallback: guardar sin metadata
            df_data.to_csv(output_path, index=False)
    
    def _clean_vulcan_metadata(self, df, column_mapping):
        """Limpiar filas problemáticas de exportación Vulcan"""
        try:
            # Verificar que las columnas mapeadas existen
            required_cols = list(column_mapping.values())
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return pd.DataFrame()  # Retornar DataFrame vacío si faltan columnas
            
            # Filtrar filas con datos válidos en las columnas principales
            df_clean = df.copy()
            
            # Eliminar filas donde las columnas numéricas no son números
            for std_name, user_col in column_mapping.items():
                if std_name in ['cut_op', 'rst_op']:  # Columnas que deben ser numéricas
                    # Convertir a numérico y eliminar filas con NaN
                    df_clean[user_col] = pd.to_numeric(df_clean[user_col], errors='coerce')
                    df_clean = df_clean.dropna(subset=[user_col])
            
            # Filtrar filas donde pas_cut tiene valores válidos (no vacíos, no metadata)
            pas_cut_col = column_mapping.get('pas_cut')
            if pas_cut_col:
                df_clean = df_clean[df_clean[pas_cut_col].notna()]
                df_clean = df_clean[df_clean[pas_cut_col].astype(str).str.strip() != '']
                # Eliminar filas que parecen metadata (ej: que empiecen con #, Min=, Max=, etc.)
                mask = ~df_clean[pas_cut_col].astype(str).str.contains(r'^(?:#|Min=|Max=|Values=|Codes=)', na=False)
                df_clean = df_clean[mask]
            
            return df_clean
            
        except Exception as e:
            self.log(f"Error limpiando metadata: {str(e)}")
            return df
    
    def _display_preview_results(self, preview_data, unused_rules=None):
        """Mostrar resultados del preview en el text widget"""
        self.preview_text.config(state='normal')
        self.preview_text.delete('1.0', tk.END)
        
        if not preview_data:
            self.preview_text.insert('1.0', "❌ No se encontraron datos válidos para mostrar preview\n")
            self.preview_text.config(state='disabled')
            return
        
        # Título
        header = "PREVIEW DE CAMBIOS POR SÓLIDO/PAS_CUT\n"
        header += "=" * 50 + "\n\n"
        self.preview_text.insert(tk.END, header)
        
        # Agrupar por sólido para mejor organización
        from collections import defaultdict
        data_by_solido = defaultdict(list)
        for item in preview_data:
            data_by_solido[item['solido']].append(item)
        
        for solido, items in data_by_solido.items():
            self.preview_text.insert(tk.END, f"🔸 SÓLIDO: {solido}\n")
            self.preview_text.insert(tk.END, "-" * 40 + "\n")
            
            for item in items:
                # Información básica
                self.preview_text.insert(tk.END, f"\n  📋 PAS_CUT: {item['pas_cut']} | Archivo: {item['archivo']}\n")
                self.preview_text.insert(tk.END, f"  📊 Filas procesadas: {item['filas']} | Filas modificadas: {item['cambios']}\n")
                
                if item['cambios'] > 0:
                    self.preview_text.insert(tk.END, f"  🎯 HAY CAMBIOS - Se aplicaron reglas de capping\n")
                else:
                    self.preview_text.insert(tk.END, f"  ✅ Sin cambios - No hay reglas que afecten este grupo\n")
                
                # Información sobre reglas aplicables y definidas
                reglas_aplicables = item.get('reglas_aplicables', [])
                reglas_definidas = item.get('reglas_definidas', [])
                
                if reglas_aplicables:
                    self.preview_text.insert(tk.END, f"  🎯 REGLAS QUE SE APLICAN ({len(reglas_aplicables)} reglas):\n")
                    for i, regla in enumerate(reglas_aplicables, 1):
                        mult_info = f"x{regla['multiplicador']:.3f}" if regla['multiplicador'] != 1.0 else "sin cambio"
                        self.preview_text.insert(tk.END, f"    [{i}] Rango [{regla['rango_min']:.3f}, {regla['rango_max']:.3f}): {mult_info}\n")
                
                # Mostrar reglas definidas que NO se aplican
                reglas_no_aplicadas = [r for r in reglas_definidas if r not in reglas_aplicables]
                if reglas_no_aplicadas:
                    self.preview_text.insert(tk.END, f"  ℹ️  REGLAS DEFINIDAS PERO NO APLICADAS ({len(reglas_no_aplicadas)} reglas):\n")
                    for i, regla in enumerate(reglas_no_aplicadas, 1):
                        mult_info = f"x{regla['multiplicador']:.3f}" if regla['multiplicador'] != 1.0 else "sin cambio"
                        self.preview_text.insert(tk.END, f"    [{i}] Rango [{regla['rango_min']:.3f}, {regla['rango_max']:.3f}): {mult_info} (fuera del rango de datos)\n")
                
                if not reglas_definidas:
                    self.preview_text.insert(tk.END, f"  ❌ Sin reglas definidas para esta combinación\n")
                
                # Estadísticas de CUT_OP original
                stats_orig = item['cut_op_stats']
                self.preview_text.insert(tk.END, f"  📈 CUT_OP Original: Min={stats_orig['min']:.3f}, Max={stats_orig['max']:.3f}, Media={stats_orig['mean']:.3f}\n")
                
                # Comparación antes/después si hay cambios
                if item['cambios'] > 0:
                    antes = item['antes_stats']
                    despues = item['despues_stats']
                    self.preview_text.insert(tk.END, f"  📉 Antes:   Min={antes['min']:.3f}, Max={antes['max']:.3f}, Media={antes['mean']:.3f}\n")
                    self.preview_text.insert(tk.END, f"  📈 Después: Min={despues['min']:.3f}, Max={despues['max']:.3f}, Media={despues['mean']:.3f}\n")
                    
                    # Calcular impacto
                    impacto = ((despues['mean'] - antes['mean']) / antes['mean']) * 100
                    self.preview_text.insert(tk.END, f"  🎯 Impacto: {impacto:+.1f}% en promedio\n")
                
                self.preview_text.insert(tk.END, "\n")
            
            self.preview_text.insert(tk.END, "\n")
        
        # Resumen general
        total_filas = sum(item['filas'] for item in preview_data)
        total_cambios = sum(item['cambios'] for item in preview_data)
        combinaciones = len(preview_data)
        
        self.preview_text.insert(tk.END, f"📊 RESUMEN GENERAL\n")
        self.preview_text.insert(tk.END, f"=" * 20 + "\n")
        self.preview_text.insert(tk.END, f"Total combinaciones Sólido/PAS_CUT: {combinaciones}\n")
        self.preview_text.insert(tk.END, f"Total filas procesadas: {total_filas:,}\n")
        self.preview_text.insert(tk.END, f"Filas que cambiarán: {total_cambios:,} ({total_cambios/total_filas*100:.1f}%)\n\n")
        
        # Mostrar reglas no utilizadas
        if unused_rules is not None:
            if unused_rules:
                self.preview_text.insert(tk.END, f"⚠️  REGLAS NO UTILIZADAS ({len(unused_rules)} reglas)\n")
                self.preview_text.insert(tk.END, f"=" * 40 + "\n")
                self.preview_text.insert(tk.END, f"Las siguientes reglas no se aplican a ninguna combinación en los datos:\n\n")
                
                for i, regla in enumerate(unused_rules, 1):
                    mult_info = f"x{regla['multiplicador']:.3f}" if regla['multiplicador'] != 1.0 else "sin cambio"
                    self.preview_text.insert(tk.END, f"  [{i}] Sólido: '{regla['solido']}' | PAS_CUT: '{regla['pas_cut']}'\n")
                    self.preview_text.insert(tk.END, f"      Rango: [{regla['rango_min']:.3f}, {regla['rango_max']:.3f}): {mult_info}\n\n")
                
                self.preview_text.insert(tk.END, f"💡 Sugerencia: Revisa si estas reglas tienen errores de tipeo o\n")
                self.preview_text.insert(tk.END, f"   si los datos no contienen las combinaciones esperadas.\n")
            else:
                self.preview_text.insert(tk.END, f"✅ TODAS LAS REGLAS SE UTILIZAN\n")
                self.preview_text.insert(tk.END, f"=" * 30 + "\n")
                self.preview_text.insert(tk.END, f"Todas las reglas definidas se aplican a alguna combinación en los datos.\n")
        
        self.preview_text.config(state='disabled')
        
        # Scroll al inicio
        self.preview_text.see('1.0')
    
    def _get_current_column_mapping(self):
        """Obtener mapeo de columnas actual"""
        if not all([self.cut_op_var.get(), self.rst_op_var.get(), self.pas_cut_var.get()]):
            return None
        
        return {
            'cut_op': self.cut_op_var.get(),
            'rst_op': self.rst_op_var.get(),
            'pas_cut': self.pas_cut_var.get()
        }
    
    def process_data(self):
        """Procesar los datos con las configuraciones actuales"""
        try:
            # Validaciones
            if not self.csv_files:
                messagebox.showerror("Error", "No hay archivos CSV seleccionados")
                return
            
            if not all([self.cut_op_var.get(), self.rst_op_var.get(), self.pas_cut_var.get()]):
                messagebox.showerror("Error", "Debe mapear todas las columnas requeridas")
                return
            
            # Configurar mapeo de columnas
            column_mapping = {
                'cut_op': self.cut_op_var.get(),
                'rst_op': self.rst_op_var.get(),
                'pas_cut': self.pas_cut_var.get()
            }
            
            self.log("Iniciando procesamiento...")
            
            # Obtener opción de guardado seleccionada
            save_mode = self.save_option.get()
            
            if save_mode == "consolidate_all":
                # Opción 3: Consolidar todo (comportamiento original)
                result_df = self.processor.process_block_models(
                    csv_files=self.csv_files,
                    solido_labels=self.solido_labels,
                    column_mapping=column_mapping,
                    capping_rules=self.rules_manager.get_all_rules(),
                    log_callback=self.log
                )
                
                output_path = os.path.join(os.path.dirname(self.csv_files[0]), "blockmodel_capeado.csv")
                
                # Usar el primer archivo como referencia para obtener metadata
                reference_csv = self.csv_files[0]
                self._save_csv_with_metadata(result_df, output_path, reference_csv)
                
                self.log(f"✅ Archivo consolidado guardado: {output_path}")
                self.log(f"📊 Total de filas procesadas: {len(result_df)}")
                
                # Mostrar resumen
                self.show_processing_summary(result_df)
                messagebox.showinfo("Éxito", f"Procesamiento completado.\nArchivo consolidado: {output_path}")
                
            elif save_mode in ["create_duplicates", "update_original"]:
                # Opción 1 y 2: Procesar archivo por archivo
                processed_files = []
                total_rows = 0
                
                for i, csv_path in enumerate(self.csv_files, 1):
                    try:
                        file_name = Path(csv_path).name
                        self.log(f"📄 Procesando {file_name} ({i}/{len(self.csv_files)})...")
                        
                        # Procesar solo este archivo
                        file_df = self.processor.process_individual_file(
                            csv_path=csv_path,
                            solido_label=self.solido_labels.get(csv_path, "unknown"),
                            column_mapping=column_mapping,
                            capping_rules=self.rules_manager.get_all_rules(),
                            log_callback=self.log
                        )
                        
                        if file_df is None or file_df.empty:
                            self.log(f"  ❌ No se pudo procesar {file_name}")
                            continue
                        
                        # Determinar ruta de salida
                        if save_mode == "create_duplicates":
                            # Crear copia con sufijo (SEGURO)
                            base_path = Path(csv_path)
                            output_path = str(base_path.parent / f"{base_path.stem}_capeado{base_path.suffix}")
                        else:  # update_original
                            # Sobrescribir original (PELIGROSO)
                            output_path = csv_path
                        
                        # Guardar archivo con metadata incluida
                        self._save_csv_with_metadata(file_df, output_path, csv_path)
                        processed_files.append(output_path)
                        total_rows += len(file_df)
                        
                        self.log(f"  ✅ Guardado: {Path(output_path).name} ({len(file_df)} filas)")
                        
                    except Exception as e:
                        self.log(f"  ❌ Error procesando {Path(csv_path).name}: {str(e)}")
                        continue
                
                if processed_files:
                    mode_text = "actualizados" if save_mode == "update_original" else "duplicados creados"
                    self.log(f"✅ Procesamiento completado: {len(processed_files)} archivos {mode_text}")
                    self.log(f"📊 Total de filas procesadas: {total_rows}")
                    
                    # Mostrar popup con estadísticas detalladas
                    self.show_individual_processing_summary(processed_files, total_rows, save_mode)
                    
                    # Mensaje de éxito simple
                    summary_text = f"Archivos {mode_text}: {len(processed_files)}\n"
                    summary_text += f"Total de filas: {total_rows}"
                    
                    messagebox.showinfo("Éxito", f"Procesamiento completado.\n\n{summary_text}")
                else:
                    raise Exception("No se pudo procesar ningún archivo")
            
            self.log("🎉 Procesamiento completado exitosamente")
            
        except Exception as e:
            error_msg = f"Error durante el procesamiento: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def show_processing_summary(self, df):
        """Mostrar resumen del procesamiento consolidado"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Estadísticas Detalladas - Archivo Consolidado")
        summary_window.geometry("900x700")
        summary_window.transient(self.root)
        
        text_widget = tk.Text(summary_window, wrap='word', font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(summary_window, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Identificar las columnas originales para CUT_OP, RST_OP, CUS_OP
        column_mapping = self._get_current_column_mapping()
        cut_op_col = column_mapping.get('cut_op', 'CUT_OP') if column_mapping else 'CUT_OP'
        rst_op_col = column_mapping.get('rst_op', 'RST_OP') if column_mapping else 'RST_OP'
        
        # Para CUS_OP, buscar una columna que pueda ser CUS_OP o similar
        cus_op_col = None
        for col in df.columns:
            if 'cus' in col.lower() and 'op' in col.lower() and col != 'CUS_PLAN':
                cus_op_col = col
                break
        
        # Generar resumen detallado
        summary = f"""ESTADÍSTICAS DETALLADAS - PROCESAMIENTO CONSOLIDADO
==================================================

📊 INFORMACIÓN GENERAL:
Total de filas procesadas: {len(df):,}
Distribución por sólido:
{df['SOLIDO'].value_counts().to_string()}

📈 ESTADÍSTICAS GLOBALES:
========================

🔸 SÓLIDO:
{df['SOLIDO'].value_counts().describe()}

🔸 CUT_PLAN:
{df['CUT_PLAN'].describe().to_string()}

🔸 CUT_OP ({cut_op_col}):
{df[cut_op_col].describe().to_string()}

🔸 RST_PLAN:
{df['RST_PLAN'].describe().to_string()}

🔸 RST_OP ({rst_op_col}):
{df[rst_op_col].describe().to_string()}

🔸 CUS_PLAN:
{df['CUS_PLAN'].describe().to_string()}
"""

        # Agregar CUS_OP si existe
        if cus_op_col and cus_op_col in df.columns:
            summary += f"""
🔸 CUS_OP ({cus_op_col}):
{df[cus_op_col].describe().to_string()}
"""
        else:
            summary += f"""
🔸 CUS_OP: (No disponible en datos originales)
"""

        # Estadísticas por sólido
        summary += f"""

📊 ESTADÍSTICAS POR SÓLIDO:
===========================
"""

        for solido in sorted(df['SOLIDO'].unique()):
            df_solido = df[df['SOLIDO'] == solido]
            summary += f"""
🔹 SÓLIDO: {solido} ({len(df_solido):,} filas)
-------------------------------------------

  CUT_PLAN: min={df_solido['CUT_PLAN'].min():.4f}, max={df_solido['CUT_PLAN'].max():.4f}, 
            media={df_solido['CUT_PLAN'].mean():.4f}, std={df_solido['CUT_PLAN'].std():.4f}
  
  CUT_OP:   min={df_solido[cut_op_col].min():.4f}, max={df_solido[cut_op_col].max():.4f}, 
            media={df_solido[cut_op_col].mean():.4f}, std={df_solido[cut_op_col].std():.4f}
  
  RST_PLAN: min={df_solido['RST_PLAN'].min():.4f}, max={df_solido['RST_PLAN'].max():.4f}, 
            media={df_solido['RST_PLAN'].mean():.4f}, std={df_solido['RST_PLAN'].std():.4f}
  
  RST_OP:   min={df_solido[rst_op_col].min():.4f}, max={df_solido[rst_op_col].max():.4f}, 
            media={df_solido[rst_op_col].mean():.4f}, std={df_solido[rst_op_col].std():.4f}
  
  CUS_PLAN: min={df_solido['CUS_PLAN'].min():.4f}, max={df_solido['CUS_PLAN'].max():.4f}, 
            media={df_solido['CUS_PLAN'].mean():.4f}, std={df_solido['CUS_PLAN'].std():.4f}
"""
            
            # Agregar CUS_OP por sólido si existe
            if cus_op_col and cus_op_col in df.columns:
                summary += f"""  
  CUS_OP:   min={df_solido[cus_op_col].min():.4f}, max={df_solido[cus_op_col].max():.4f}, 
            media={df_solido[cus_op_col].mean():.4f}, std={df_solido[cus_op_col].std():.4f}
"""

        summary += f"""

📋 INFORMACIÓN ADICIONAL:
========================
Columnas en el resultado final: {len(df.columns)} columnas
{', '.join(df.columns)}

Fórmula CUS_PLAN utilizada: {self.processor.cus_plan_formula}
"""
        
        text_widget.insert('1.0', summary)
        text_widget.config(state='disabled')
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def show_individual_processing_summary(self, processed_files, total_rows, save_mode):
        """Mostrar resumen del procesamiento de archivos individuales"""
        summary_window = tk.Toplevel(self.root)
        mode_text = "Actualización de Originales" if save_mode == "update_original" else "Archivos Duplicados"
        summary_window.title(f"Estadísticas Detalladas - {mode_text}")
        summary_window.geometry("900x700")
        summary_window.transient(self.root)
        
        text_widget = tk.Text(summary_window, wrap='word', font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(summary_window, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Identificar las columnas originales
        column_mapping = self._get_current_column_mapping()
        cut_op_col = column_mapping.get('cut_op', 'CUT_OP') if column_mapping else 'CUT_OP'
        rst_op_col = column_mapping.get('rst_op', 'RST_OP') if column_mapping else 'RST_OP'
        
        # Generar resumen detallado
        summary = f"""ESTADÍSTICAS DETALLADAS - PROCESAMIENTO POR ARCHIVOS
===================================================

📊 INFORMACIÓN GENERAL:
Modo de guardado: {mode_text}
Archivos procesados: {len(processed_files)}
Total de filas procesadas: {total_rows:,}
Promedio filas por archivo: {total_rows / len(processed_files):.0f}

📋 DETALLE POR ARCHIVO:
======================
"""
        
        # Recopilar todos los datos para estadísticas globales
        all_data = []
        file_details = []
        
        # Analizar cada archivo procesado para obtener estadísticas detalladas
        for file_path in processed_files:
            try:
                file_name = Path(file_path).name
                
                # Leer todas las columnas necesarias
                try:
                    # Intentar leer con las columnas originales también
                    df_file = pd.read_csv(file_path, skiprows=[1,2,3])
                    
                    # Verificar que existan las columnas necesarias
                    required_cols = ['SOLIDO', 'CUT_PLAN', 'RST_PLAN', 'CUS_PLAN']
                    missing_cols = [col for col in required_cols if col not in df_file.columns]
                    
                    if missing_cols:
                        raise Exception(f"Columnas faltantes: {missing_cols}")
                    
                    # Identificar columnas CUS_OP si existe
                    cus_op_col = None
                    for col in df_file.columns:
                        if 'cus' in col.lower() and 'op' in col.lower() and col != 'CUS_PLAN':
                            cus_op_col = col
                            break
                    
                    solido = df_file['SOLIDO'].iloc[0] if not df_file['SOLIDO'].empty else 'N/A'
                    filas = len(df_file)
                    
                    # Estadísticas detalladas del archivo
                    file_stats = {
                        'filename': file_name,
                        'solido': solido,
                        'filas': filas,
                        'cut_plan': df_file['CUT_PLAN'].describe(),
                        'cut_op': df_file[cut_op_col].describe() if cut_op_col in df_file.columns else None,
                        'rst_plan': df_file['RST_PLAN'].describe(),
                        'rst_op': df_file[rst_op_col].describe() if rst_op_col in df_file.columns else None,
                        'cus_plan': df_file['CUS_PLAN'].describe(),
                        'cus_op': df_file[cus_op_col].describe() if cus_op_col and cus_op_col in df_file.columns else None
                    }
                    
                    file_details.append(file_stats)
                    all_data.append(df_file)
                    
                    # Agregar detalle del archivo al resumen
                    summary += f"""
📄 {file_name}
   Sólido: {solido} | Filas: {filas:,}
   
   CUT_PLAN: min={file_stats['cut_plan']['min']:.4f}, max={file_stats['cut_plan']['max']:.4f}, 
             media={file_stats['cut_plan']['mean']:.4f}, std={file_stats['cut_plan']['std']:.4f}
   
   RST_PLAN: min={file_stats['rst_plan']['min']:.4f}, max={file_stats['rst_plan']['max']:.4f}, 
             media={file_stats['rst_plan']['mean']:.4f}, std={file_stats['rst_plan']['std']:.4f}
   
   CUS_PLAN: min={file_stats['cus_plan']['min']:.4f}, max={file_stats['cus_plan']['max']:.4f}, 
             media={file_stats['cus_plan']['mean']:.4f}, std={file_stats['cus_plan']['std']:.4f}
"""
                    
                    if file_stats['cut_op'] is not None:
                        summary += f"""   
   CUT_OP:   min={file_stats['cut_op']['min']:.4f}, max={file_stats['cut_op']['max']:.4f}, 
             media={file_stats['cut_op']['mean']:.4f}, std={file_stats['cut_op']['std']:.4f}
"""
                    
                    if file_stats['rst_op'] is not None:
                        summary += f"""   
   RST_OP:   min={file_stats['rst_op']['min']:.4f}, max={file_stats['rst_op']['max']:.4f}, 
             media={file_stats['rst_op']['mean']:.4f}, std={file_stats['rst_op']['std']:.4f}
"""
                    
                    if file_stats['cus_op'] is not None:
                        summary += f"""   
   CUS_OP:   min={file_stats['cus_op']['min']:.4f}, max={file_stats['cus_op']['max']:.4f}, 
             media={file_stats['cus_op']['mean']:.4f}, std={file_stats['cus_op']['std']:.4f}
"""
                    
                except Exception as read_error:
                    summary += f"""
❌ {file_name}
   Error leyendo estadísticas: {str(read_error)[:80]}
"""
                    continue
                    
            except Exception as e:
                summary += f"""
❌ {Path(file_path).name}
   Error procesando archivo: {str(e)[:60]}
"""
                continue
        
        # Estadísticas globales combinando todos los archivos
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            summary += f"""

📈 ESTADÍSTICAS GLOBALES COMBINADAS:
===================================

🔸 SÓLIDOS:
{combined_df['SOLIDO'].value_counts().to_string()}

🔸 CUT_PLAN (Global):
{combined_df['CUT_PLAN'].describe().to_string()}

🔸 RST_PLAN (Global):
{combined_df['RST_PLAN'].describe().to_string()}

🔸 CUS_PLAN (Global):
{combined_df['CUS_PLAN'].describe().to_string()}
"""
            
            if cut_op_col in combined_df.columns:
                summary += f"""
🔸 CUT_OP ({cut_op_col} - Global):
{combined_df[cut_op_col].describe().to_string()}
"""
            
            if rst_op_col in combined_df.columns:
                summary += f"""
🔸 RST_OP ({rst_op_col} - Global):
{combined_df[rst_op_col].describe().to_string()}
"""
            
            # Buscar CUS_OP
            cus_op_col = None
            for col in combined_df.columns:
                if 'cus' in col.lower() and 'op' in col.lower() and col != 'CUS_PLAN':
                    cus_op_col = col
                    break
            
            if cus_op_col:
                summary += f"""
🔸 CUS_OP ({cus_op_col} - Global):
{combined_df[cus_op_col].describe().to_string()}
"""
            
            # Estadísticas por sólido
            summary += f"""

📊 ESTADÍSTICAS POR SÓLIDO:
===========================
"""
            
            for solido in sorted(combined_df['SOLIDO'].unique()):
                df_solido = combined_df[combined_df['SOLIDO'] == solido]
                summary += f"""
🔹 SÓLIDO: {solido} ({len(df_solido):,} filas)
-------------------------------------------

  CUT_PLAN: min={df_solido['CUT_PLAN'].min():.4f}, max={df_solido['CUT_PLAN'].max():.4f}, 
            media={df_solido['CUT_PLAN'].mean():.4f}, std={df_solido['CUT_PLAN'].std():.4f}
  
  RST_PLAN: min={df_solido['RST_PLAN'].min():.4f}, max={df_solido['RST_PLAN'].max():.4f}, 
            media={df_solido['RST_PLAN'].mean():.4f}, std={df_solido['RST_PLAN'].std():.4f}
  
  CUS_PLAN: min={df_solido['CUS_PLAN'].min():.4f}, max={df_solido['CUS_PLAN'].max():.4f}, 
            media={df_solido['CUS_PLAN'].mean():.4f}, std={df_solido['CUS_PLAN'].std():.4f}
"""
                
                if cut_op_col in df_solido.columns:
                    summary += f"""  
  CUT_OP:   min={df_solido[cut_op_col].min():.4f}, max={df_solido[cut_op_col].max():.4f}, 
            media={df_solido[cut_op_col].mean():.4f}, std={df_solido[cut_op_col].std():.4f}
"""
                
                if rst_op_col in df_solido.columns:
                    summary += f"""  
  RST_OP:   min={df_solido[rst_op_col].min():.4f}, max={df_solido[rst_op_col].max():.4f}, 
            media={df_solido[rst_op_col].mean():.4f}, std={df_solido[rst_op_col].std():.4f}
"""
                
                if cus_op_col and cus_op_col in df_solido.columns:
                    summary += f"""  
  CUS_OP:   min={df_solido[cus_op_col].min():.4f}, max={df_solido[cus_op_col].max():.4f}, 
            media={df_solido[cus_op_col].mean():.4f}, std={df_solido[cus_op_col].std():.4f}
"""

        summary += f"""

📋 INFORMACIÓN ADICIONAL:
========================
COLUMNAS AGREGADAS A CADA ARCHIVO:
✅ SOLIDO - Etiqueta de sólido configurada
✅ CUT_PLAN - CUT_OP con reglas de capping aplicadas
✅ RST_PLAN - RST_OP original (sin modificaciones)
✅ CUS_PLAN - Calculado con fórmula: {self.processor.cus_plan_formula}

UBICACIÓN DE ARCHIVOS:
{Path(processed_files[0]).parent if processed_files else 'N/A'}
"""
        
        text_widget.insert('1.0', summary)
        text_widget.config(state='disabled')
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def log(self, message):
        """Agregar mensaje al log"""
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')
        self.root.update()

def main():
    root = tk.Tk()
    app = MiniConsolaApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()