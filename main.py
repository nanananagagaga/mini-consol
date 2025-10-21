"""
Mini Consola para Procesamiento de Block Models
===============================================

Esta aplicación permite:
1. Leer múltiples archivos CSV (block models cortados)
2. Asignar etiquetas de fase a cada archivo
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
        self.fase_labels = {}
        self.rules_manager = RulesManager()
        self.processor = BlockModelProcessor()
        
        # Variables para datos detectados automáticamente
        self.available_fases = []
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
        
        # Pestaña 4: Procesamiento y resultados
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
        
        # Treeview para mostrar archivos y asignar etiquetas de fase
        columns = ('archivo', 'etiqueta_fase')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=10)
        self.files_tree.heading('archivo', text='Archivo CSV')
        self.files_tree.heading('etiqueta_fase', text='Etiqueta de Fase')
        self.files_tree.column('archivo', width=400)
        self.files_tree.column('etiqueta_fase', width=200)
        
        scrollbar_files = ttk.Scrollbar(files_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar_files.set)
        
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar_files.pack(side='right', fill='y')
        
        # Botón para editar etiqueta
        edit_frame = ttk.Frame(files_frame)
        edit_frame.pack(fill='x', pady=5)
        ttk.Button(edit_frame, text="Editar Etiqueta de Fase", command=self.edit_fase_label).pack()
    
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
        
        columns = ('fase', 'pas_cut', 'rango_min', 'rango_max', 'multiplicador')
        self.rules_tree = ttk.Treeview(rules_frame, columns=columns, show='headings', height=12)
        
        self.rules_tree.heading('fase', text='Fase')
        self.rules_tree.heading('pas_cut', text='Pas Cut')
        self.rules_tree.heading('rango_min', text='Rango Mín')
        self.rules_tree.heading('rango_max', text='Rango Máx')
        self.rules_tree.heading('multiplicador', text='Multiplicador')
        
        # Ajustar anchos de columnas
        self.rules_tree.column('fase', width=80)
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
    
    def setup_processing_tab(self, notebook):
        """Configurar pestaña de procesamiento"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="4. Procesamiento")
        
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
            self.fase_labels[str(file_path)] = default_label
            
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
        # Actualizar fases disponibles
        self.available_fases = list(set(self.fase_labels.values()))
        
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
        
        # Log de fases disponibles
        if self.available_fases:
            self.log(f"Fases configuradas: {', '.join(self.available_fases)}")
        
        # Actualizar info en pestaña de reglas
        self.update_rules_info()
    
    def update_rules_info(self):
        """Actualizar información mostrada en pestaña de reglas"""
        try:
            fases_count = len(self.available_fases)
            pas_cut_count = len(self.available_pas_cut_values)
            
            if fases_count == 0:
                info_text = "⚠️ Configura archivos y etiquetas de fase primero"
            elif pas_cut_count == 0:
                info_text = f"✅ {fases_count} fases | ⚠️ Mapea columna PAS_CUT"
            else:
                info_text = f"✅ {fases_count} fases | ✅ {pas_cut_count} valores PAS_CUT detectados"
            
            self.rules_info_label.config(text=info_text)
            
        except Exception:
            pass
    
    def edit_fase_label(self):
        """Editar etiqueta de fase del archivo seleccionado"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return
        
        item = selection[0]
        filename, current_label = self.files_tree.item(item, 'values')
        
        new_label = simpledialog.askstring("Editar Etiqueta de Fase", 
                                            f"Nueva etiqueta para {filename}:", 
                                            initialvalue=current_label)
        if new_label:
            # Encontrar el path completo
            for csv_path in self.csv_files:
                if Path(csv_path).name == filename:
                    self.fase_labels[csv_path] = new_label
                    self.files_tree.item(item, values=(filename, new_label))
                    # Actualizar valores disponibles cuando se cambia una fase
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
        
        info_text = f"Fases disponibles: {len(self.available_fases)} configuradas\n"
        info_text += f"Valores PAS_CUT: {len(self.available_pas_cut_values)} detectados"
        ttk.Label(info_frame, text=info_text, font=('Arial', 9)).pack()
        
        # Frame principal para los campos
        main_frame = ttk.LabelFrame(main_container, text="Configurar Regla", padding=15)
        main_frame.pack(fill='x', pady=(0, 10))
        
        # Variables
        fase_var = tk.StringVar(value=existing_values[0] if existing_values else "")
        pas_cut_var = tk.StringVar(value=existing_values[1] if existing_values else "")
        rango_min_var = tk.DoubleVar(value=float(existing_values[2]) if existing_values else 0.0)
        rango_max_var = tk.DoubleVar(value=float(existing_values[3]) if existing_values else 1.0)
        multiplicador_var = tk.DoubleVar(value=float(existing_values[4]) if existing_values else 1.0)
        
        # Campos del formulario con comboboxes
        ttk.Label(main_frame, text="Fase:").grid(row=0, column=0, sticky='w', padx=5, pady=8)
        fase_combo = ttk.Combobox(main_frame, textvariable=fase_var, width=20, state='readonly')
        fase_combo['values'] = self.available_fases if self.available_fases else ["⚠️ Configura archivos primero"]
        fase_combo.grid(row=0, column=1, padx=5, pady=8, sticky='w')
        
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
        
        example_text = "Ejemplo: Fase='10', PAS_CUT='3', Min=0.5, Max=1.0, Mult=0.9\n"
        example_text += "→ Si CUT_OP está entre 0.5 y 1.0, CUT_PLAN = CUT_OP × 0.9"
        ttk.Label(example_frame, text=example_text, font=('Arial', 8), foreground='gray').pack()
        
        # Botones - IMPORTANTE: Usar pack para que sean siempre visibles
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill='x', pady=(10, 0), side='bottom')
        
        def save_rule():
            try:
                fase = fase_var.get()
                pas_cut = pas_cut_var.get()
                rango_min = rango_min_var.get()
                rango_max = rango_max_var.get()
                multiplicador = multiplicador_var.get()
                
                if not fase:
                    messagebox.showerror("Error", "Debe seleccionar una Fase")
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
                self.rules_manager.add_rule(fase, pas_cut, rango_min, rango_max, multiplicador)
                
                # Actualizar vista
                self.refresh_rules_tree()
                
                # Mensaje de confirmación
                self.log(f"✅ Regla agregada: Fase '{fase}', PAS_CUT '{pas_cut}', "
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
                rule['fase'], rule['pas_cut'], rule['rango_min'], 
                rule['rango_max'], rule['multiplicador']
            ))
    
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
                    fase_labels=self.fase_labels,
                    column_mapping=column_mapping,
                    capping_rules=self.rules_manager.get_all_rules(),
                    log_callback=self.log
                )
                
                output_path = os.path.join(os.path.dirname(self.csv_files[0]), "blockmodel_capeado.csv")
                result_df.to_csv(output_path, index=False)
                
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
                            fase_label=self.fase_labels.get(csv_path, "unknown"),
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
                        
                        # Guardar archivo
                        file_df.to_csv(output_path, index=False)
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
        summary_window.title("Resumen de Procesamiento - Archivo Consolidado")
        summary_window.geometry("600x400")
        summary_window.transient(self.root)
        
        text_widget = tk.Text(summary_window, wrap='word', font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(summary_window, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Generar resumen
        summary = f"""RESUMEN DE PROCESAMIENTO CONSOLIDADO
===================================

Total de filas procesadas: {len(df):,}

Distribución por fase:
{df['fase'].value_counts().to_string()}

Estadísticas de CUT_PLAN:
{df['cut_plan'].describe().to_string()}

Estadísticas de CUS_PLAN:
{df['cus_plan'].describe().to_string()}

Columnas en el resultado final:
{', '.join(df.columns)}
"""
        
        text_widget.insert('1.0', summary)
        text_widget.config(state='disabled')
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def show_individual_processing_summary(self, processed_files, total_rows, save_mode):
        """Mostrar resumen del procesamiento de archivos individuales"""
        summary_window = tk.Toplevel(self.root)
        mode_text = "Actualización de Originales" if save_mode == "update_original" else "Archivos Duplicados"
        summary_window.title(f"Resumen de Procesamiento - {mode_text}")
        summary_window.geometry("700x500")
        summary_window.transient(self.root)
        
        text_widget = tk.Text(summary_window, wrap='word', font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(summary_window, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Generar resumen detallado
        summary = f"""RESUMEN DE PROCESAMIENTO POR ARCHIVOS
====================================

Modo de guardado: {mode_text}
Archivos procesados: {len(processed_files)}
Total de filas procesadas: {total_rows:,}

DETALLE POR ARCHIVO:
"""
        
        # Analizar cada archivo procesado para obtener estadísticas
        for file_path in processed_files:
            try:
                file_name = Path(file_path).name
                # Leer solo las columnas que nos interesan para estadísticas rápidas
                df_stats = pd.read_csv(file_path, usecols=['FASE', 'CUT_PLAN', 'CUS_PLAN'])
                
                fase = df_stats['FASE'].iloc[0] if not df_stats['FASE'].empty else 'N/A'
                filas = len(df_stats)
                cut_plan_min = df_stats['CUT_PLAN'].min()
                cut_plan_max = df_stats['CUT_PLAN'].max()
                cut_plan_mean = df_stats['CUT_PLAN'].mean()
                cus_plan_mean = df_stats['CUS_PLAN'].mean()
                
                summary += f"""
📄 {file_name}
   Fase: {fase}
   Filas: {filas:,}
   CUT_PLAN: min={cut_plan_min:.4f}, max={cut_plan_max:.4f}, promedio={cut_plan_mean:.4f}
   CUS_PLAN: promedio={cus_plan_mean:.4f}
"""
                
            except Exception as e:
                summary += f"""
❌ {Path(file_path).name}
   Error leyendo estadísticas: {str(e)[:60]}
"""
        
        # Agregar información adicional
        summary += f"""

ESTADÍSTICAS GLOBALES:
======================
- Promedio de filas por archivo: {total_rows / len(processed_files):.0f}
- Archivos exitosos: {len(processed_files)}

COLUMNAS AGREGADAS A CADA ARCHIVO:
==================================
✅ FASE - Etiqueta de fase configurada
✅ CUT_PLAN - CUT_OP con reglas de capping aplicadas  
✅ CUS_PLAN - Calculado con fórmula: {self.processor.cus_plan_formula}

UBICACIÓN DE ARCHIVOS:
=====================
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