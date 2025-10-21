"""
Módulo para procesar block models CSV
====================================

Este módulo contiene la lógica principal para:
1. Leer archivos CSV con manejo de filas problemáticas
2. Aplicar reglas de capping
3. Calcular variables derivadas
4. Consolidar datos
"""

import pandas as pd
import numpy as np
from pathlib import Path

class BlockModelProcessor:
    def __init__(self):
        # Fórmula configurable para CUS_PLAN - CAMBIAR AQUÍ SI ES NECESARIO
        self.cus_plan_formula = "rst_op * cut_plan"  # Fórmula base
        
    def process_block_models(self, csv_files, fase_labels, column_mapping, capping_rules, log_callback=None):
        """
        Procesar múltiples archivos CSV de block models
        
        Args:
            csv_files: Lista de rutas de archivos CSV
            fase_labels: Diccionario {archivo: etiqueta_fase}
            column_mapping: Diccionario {cut_op: col_name, rst_op: col_name, pas_cut: col_name}
            capping_rules: Lista de reglas de capping
            log_callback: Función para logging (opcional)
        
        Returns:
            pandas.DataFrame: DataFrame consolidado con todas las variables calculadas
        """
        def log(msg):
            if log_callback:
                log_callback(msg)
        
        consolidated_dfs = []
        
        # Procesar cada archivo CSV
        for i, csv_path in enumerate(csv_files):
            try:
                log(f"Procesando archivo {i+1}/{len(csv_files)}: {Path(csv_path).name}")
                
                # Leer CSV con manejo de filas problemáticas (skip filas 2, 3, 4 como mencionó tu jefe)
                df = self._read_csv_safe(csv_path, log)
                
                if df is None or df.empty:
                    log(f"Advertencia: No se pudo leer {Path(csv_path).name}")
                    continue
                
                # Mapear columnas a nombres estándar
                df_mapped = self._map_columns(df, column_mapping, log)
                
                # Agregar columna de fase
                fase_label = fase_labels.get(csv_path, f"fase_{i}")
                df_mapped['fase'] = fase_label
                
                log(f"  - Filas leídas: {len(df_mapped)}")
                log(f"  - Fase asignada: {fase_label}")
                
                consolidated_dfs.append(df_mapped)
                
            except Exception as e:
                log(f"Error procesando {Path(csv_path).name}: {str(e)}")
                continue
        
        if not consolidated_dfs:
            raise Exception("No se pudo procesar ningún archivo CSV")
        
        # Consolidar todos los DataFrames
        log("Consolidando DataFrames...")
        consolidated_df = pd.concat(consolidated_dfs, ignore_index=True)
        log(f"Total de filas consolidadas: {len(consolidated_df)}")
        
        # Aplicar reglas de capping
        log("Aplicando reglas de capping...")
        consolidated_df = self._apply_capping_rules(consolidated_df, capping_rules, log)
        
        # Calcular CUS_PLAN
        log("Calculando CUS_PLAN...")
        consolidated_df = self._calculate_cus_plan(consolidated_df, log)
        
        # Reordenar columnas para el resultado final
        final_columns = self._get_final_column_order(consolidated_df)
        consolidated_df = consolidated_df[final_columns]
        
        log("Procesamiento completado exitosamente")
        return consolidated_df
    
    def _read_csv_safe(self, csv_path, log_callback):
        """
        Leer CSV de forma segura, manejando filas problemáticas
        """
        try:
            # Intentar leer normalmente primero
            df = pd.read_csv(csv_path)
            
            # Si tiene pocas filas, no hacer skip
            if len(df) <= 5:
                return df
            
            # Si tiene muchas filas, intentar skip de filas problemáticas (2, 3, 4)
            df_skip = pd.read_csv(csv_path, skiprows=[1, 2, 3])  # skiprows es 0-indexed
            
            # Usar el que tenga más filas válidas
            if len(df_skip) > len(df) * 0.8:  # Si el skip mantiene al menos 80% de los datos
                log_callback(f"  - Aplicado skip de filas problemáticas")
                return df_skip
            else:
                log_callback(f"  - Lectura normal (sin skip)")
                return df
                
        except Exception as e:
            log_callback(f"  - Error leyendo CSV: {str(e)}")
            return None
    
    def _map_columns(self, df, column_mapping, log_callback):
        """
        Mapear columnas del usuario a nombres estándar
        """
        # Crear copia del DataFrame
        df_mapped = df.copy()
        
        # Renombrar columnas según el mapeo
        rename_dict = {}
        for std_name, user_col in column_mapping.items():
            if user_col in df.columns:
                rename_dict[user_col] = std_name
            else:
                raise Exception(f"Columna '{user_col}' no encontrada en el archivo")
        
        df_mapped = df_mapped.rename(columns=rename_dict)
        
        # Verificar que las columnas críticas existen
        required_cols = ['cut_op', 'rst_op', 'pas_cut']
        missing_cols = [col for col in required_cols if col not in df_mapped.columns]
        if missing_cols:
            raise Exception(f"Columnas faltantes después del mapeo: {missing_cols}")
        
        # Convertir a numérico las columnas críticas
        for col in ['cut_op', 'rst_op']:
            df_mapped[col] = pd.to_numeric(df_mapped[col], errors='coerce')
        
        # pas_cut puede ser categórico, convertir a string
        df_mapped['pas_cut'] = df_mapped['pas_cut'].astype(str)
        
        log_callback(f"  - Columnas mapeadas: {list(rename_dict.keys())} -> {list(rename_dict.values())}")
        
        return df_mapped
    
    def _apply_capping_rules(self, df, capping_rules, log_callback):
        """
        Aplicar reglas de capping para generar cut_plan
        """
        # Inicializar cut_plan como copia de cut_op
        df['cut_plan'] = df['cut_op'].copy()
        
        rules_applied = 0
        
        for rule in capping_rules:
            fase = rule['fase']
            pas_cut = str(rule['pas_cut'])
            rango_min = rule['rango_min']
            rango_max = rule['rango_max']
            multiplicador = rule['multiplicador']
            
            # Crear máscara para aplicar la regla
            mask = (
                (df['fase'] == fase) & 
                (df['pas_cut'] == pas_cut) &
                (df['cut_op'] >= rango_min) & 
                (df['cut_op'] < rango_max)
            )
            
            # Aplicar multiplicador
            affected_rows = mask.sum()
            if affected_rows > 0:
                df.loc[mask, 'cut_plan'] = df.loc[mask, 'cut_op'] * multiplicador
                rules_applied += 1
                log_callback(f"  - Regla aplicada: fase={fase}, pas_cut={pas_cut}, "
                           f"rango=[{rango_min}, {rango_max}), mult={multiplicador}, "
                           f"filas afectadas={affected_rows}")
        
        log_callback(f"Total de reglas aplicadas: {rules_applied}")
        return df
    
    def _calculate_cus_plan(self, df, log_callback):
        """
        Calcular CUS_PLAN usando la fórmula configurada
        """
        try:
            # Fórmula configurable - MODIFICAR AQUÍ SI ES NECESARIO
            # Actualmente: cus_plan = rst_op * cut_plan
            
            log_callback(f"  - Fórmula utilizada: {self.cus_plan_formula}")
            
            # Evaluar la fórmula
            if self.cus_plan_formula == "rst_op * cut_plan":
                df['cus_plan'] = df['rst_op'] * df['cut_plan']
            else:
                # Permitir fórmulas más complejas usando eval (con cuidado)
                # Solo permitir operaciones básicas y nombres de columnas conocidos
                allowed_names = {
                    'rst_op': df['rst_op'],
                    'cut_plan': df['cut_plan'],
                    'cut_op': df['cut_op']
                }
                df['cus_plan'] = eval(self.cus_plan_formula, {"__builtins__": {}}, allowed_names)
            
            # Verificar que no hay valores infinitos o NaN
            invalid_count = df['cus_plan'].isna().sum() + np.isinf(df['cus_plan']).sum()
            if invalid_count > 0:
                log_callback(f"  - Advertencia: {invalid_count} valores inválidos en cus_plan")
            
            log_callback(f"  - CUS_PLAN calculado para {len(df)} filas")
            
        except Exception as e:
            log_callback(f"  - Error calculando CUS_PLAN: {str(e)}")
            # Fallback: usar fórmula básica
            df['cus_plan'] = df['rst_op'] * df['cut_plan']
            
        return df
    
    def _get_final_column_order(self, df):
        """
        Definir orden de columnas para el resultado final
        """
        # Columnas principales que siempre deben aparecer primero
        priority_columns = ['fase', 'pas_cut', 'cut_op', 'cut_plan', 'rst_op', 'cus_plan']
        
        # Filtrar columnas que realmente existen
        existing_priority = [col for col in priority_columns if col in df.columns]
        
        # Agregar resto de columnas
        other_columns = [col for col in df.columns if col not in priority_columns]
        
        return existing_priority + other_columns
    
    def process_individual_file(self, csv_path, fase_label, column_mapping, capping_rules, log_callback=None):
        """
        Procesar un solo archivo CSV agregando las columnas calculadas
        
        Args:
            csv_path: Ruta del archivo CSV
            fase_label: Etiqueta de fase para este archivo
            column_mapping: Diccionario {cut_op: col_name, rst_op: col_name, pas_cut: col_name}
            capping_rules: Lista de reglas de capping
            log_callback: Función para logging (opcional)
        
        Returns:
            pandas.DataFrame: DataFrame original con columnas cut_plan y cus_plan agregadas
        """
        def log(msg):
            if log_callback:
                log_callback(f"    {msg}")
        
        try:
            # Leer CSV con manejo de filas problemáticas
            df = self._read_csv_safe(csv_path, log)
            
            if df is None or df.empty:
                log(f"No se pudo leer el archivo")
                return None
            
            # Mapear columnas a nombres estándar (sin renombrar las originales)
            df_work = df.copy()
            
            # Crear mapeo temporal para trabajo interno
            for std_name, user_col in column_mapping.items():
                if user_col in df.columns:
                    df_work[std_name] = pd.to_numeric(df[user_col], errors='coerce')
                else:
                    raise Exception(f"Columna '{user_col}' no encontrada")
            
            # Convertir pas_cut a string para el trabajo interno
            df_work['pas_cut'] = df_work['pas_cut'].astype(str)
            
            # Agregar columna de fase
            df_work['fase'] = fase_label
            
            log(f"Filas leídas: {len(df_work)}")
            
            # Aplicar reglas de capping (genera cut_plan)
            df_work = self._apply_capping_rules(df_work, capping_rules, log)
            
            # Calcular CUS_PLAN
            df_work = self._calculate_cus_plan(df_work, log)
            
            # Agregar solo las nuevas columnas al DataFrame original
            df['FASE'] = df_work['fase']
            df['CUT_PLAN'] = df_work['cut_plan']
            df['CUS_PLAN'] = df_work['cus_plan']
            
            log(f"Nuevas columnas agregadas: FASE, CUT_PLAN, CUS_PLAN")
            
            return df
            
        except Exception as e:
            log(f"Error: {str(e)}")
            return None
    
    def set_cus_plan_formula(self, formula):
        """
        Cambiar la fórmula para calcular CUS_PLAN
        
        Args:
            formula (str): Nueva fórmula (ej: "rst_op * cut_plan * 0.95")
        """
        self.cus_plan_formula = formula