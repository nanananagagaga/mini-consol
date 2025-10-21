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
        
    def process_block_models(self, csv_files, solido_labels, column_mapping, capping_rules, log_callback=None):
        """
        Procesar múltiples archivos CSV de block models
        
        Args:
            csv_files: Lista de rutas de archivos CSV
            solido_labels: Diccionario {archivo: etiqueta_solido}
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
                
                # Agregar columna de sólido
                solido_label = solido_labels.get(csv_path, f"solido_{i}")
                df_mapped['solido'] = solido_label
                
                log(f"  - Filas leídas: {len(df_mapped)}")
                log(f"  - Sólido asignado: {solido_label}")
                
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
        
        # Crear DataFrame final con datos LIMPIOS (sin metadata) + columnas calculadas
        log("Creando resultado final...")
        
        # Los consolidated_dfs ya contienen solo datos válidos (sin metadata)
        # Obtener datos originales limpios de cada archivo
        all_clean_data = []
        
        for i, csv_path in enumerate(csv_files):
            # Leer archivo (ya limpio porque _read_csv_safe salta filas 2-4)
            df_clean = self._read_csv_safe(csv_path, log)
            if df_clean is None or df_clean.empty:
                continue
                
            # Mapear columnas a nombres estándar
            df_mapped = self._map_columns(df_clean, column_mapping, log)
            if not df_mapped.empty:
                all_clean_data.append(df_mapped)
        
        # Concatenar datos originales limpios
        if all_clean_data:
            result_df = pd.concat(all_clean_data, ignore_index=True)
            
            # Agregar las 3 columnas calculadas al final
            result_df['SOLIDO'] = consolidated_df['solido']
            result_df['CUT_PLAN'] = consolidated_df['cut_plan'] 
            result_df['CUS_PLAN'] = consolidated_df['cus_plan']
        else:
            raise Exception("No se pudieron limpiar los datos originales")
        
        log("Procesamiento completado exitosamente")
        return result_df
    
    def _read_csv_safe(self, csv_path, log_callback):
        """
        Leer CSV de forma segura, saltando SIEMPRE las filas 2, 3, 4 que contienen metadata Vulcan
        Estructura esperada:
        - Fila 1: Headers (columnas)
        - Filas 2-4: Metadata Vulcan (#VULCAN_EXPORT, #UNITS:, #RANGES:) 
        - Fila 5+: Datos reales
        """
        try:
            # Saltar SIEMPRE las filas 2, 3, 4 (skiprows es 0-indexed, así que [1,2,3])
            df = pd.read_csv(csv_path, skiprows=[1, 2, 3])
            log_callback(f"  - CSV leído saltando filas metadata (2-4)")
            return df
                
        except Exception as e:
            log_callback(f"  - Error leyendo CSV: {str(e)}")
            return None
    
    def _map_columns(self, df, column_mapping, log_callback):
        """
        Mapear columnas del usuario a nombres estándar MANTENIENDO las originales
        """
        # Crear copia del DataFrame
        df_mapped = df.copy()
        
        # Crear columnas estándar como COPIAS de las originales (no renombrar)
        mapped_cols = []
        for std_name, user_col in column_mapping.items():
            if user_col in df.columns:
                # Crear nueva columna estándar copiando la original
                df_mapped[std_name] = df_mapped[user_col].copy()
                mapped_cols.append(f"{user_col} -> {std_name}")
            else:
                raise Exception(f"Columna '{user_col}' no encontrada en el archivo")
        
        # Verificar que las columnas críticas existen
        required_cols = ['cut_op', 'rst_op', 'pas_cut']
        missing_cols = [col for col in required_cols if col not in df_mapped.columns]
        if missing_cols:
            raise Exception(f"Columnas faltantes después del mapeo: {missing_cols}")
        
        # Convertir a numérico las columnas críticas (copias estándar)
        for col in ['cut_op', 'rst_op']:
            df_mapped[col] = pd.to_numeric(df_mapped[col], errors='coerce')
        
        # pas_cut puede ser categórico, convertir a string (copia estándar)
        df_mapped['pas_cut'] = df_mapped['pas_cut'].astype(str)
        
        log_callback(f"  - Columnas mapeadas: {', '.join(mapped_cols)}")
        log_callback(f"  - Columnas originales preservadas en resultado final")
        
        return df_mapped
    
    def _apply_capping_rules(self, df, capping_rules, log_callback):
        """
        Aplicar reglas de capping para generar cut_plan
        """
        # Inicializar cut_plan como copia de cut_op
        df['cut_plan'] = df['cut_op'].copy()
        
        rules_applied = 0
        
        for rule in capping_rules:
            solido = rule['solido']
            pas_cut = str(rule['pas_cut'])
            rango_min = rule['rango_min']
            rango_max = rule['rango_max']
            multiplicador = rule['multiplicador']
            
            # Crear máscara para aplicar la regla
            mask = (
                (df['solido'] == solido) & 
                (df['pas_cut'] == pas_cut) &
                (df['cut_op'] >= rango_min) & 
                (df['cut_op'] < rango_max)
            )
            
            # Aplicar multiplicador
            affected_rows = mask.sum()
            if affected_rows > 0:
                df.loc[mask, 'cut_plan'] = df.loc[mask, 'cut_op'] * multiplicador
                rules_applied += 1
                log_callback(f"  - Regla aplicada: solido={solido}, pas_cut={pas_cut}, "
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
    
    def process_individual_file(self, csv_path, solido_label, column_mapping, capping_rules, log_callback=None):
        """
        Procesar un solo archivo CSV agregando las columnas calculadas
        
        Args:
            csv_path: Ruta del archivo CSV
            solido_label: Etiqueta de sólido para este archivo
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
            
            # Agregar columna de sólido
            df_work['solido'] = solido_label
            
            log(f"Filas leídas: {len(df_work)}")
            
            # Aplicar reglas de capping (genera cut_plan)
            df_work = self._apply_capping_rules(df_work, capping_rules, log)
            
            # Calcular CUS_PLAN
            df_work = self._calculate_cus_plan(df_work, log)
            
            # Agregar solo las nuevas columnas al DataFrame original
            df['SOLIDO'] = df_work['solido']
            df['CUT_PLAN'] = df_work['cut_plan']
            df['CUS_PLAN'] = df_work['cus_plan']
            
            log(f"Nuevas columnas agregadas: SOLIDO, CUT_PLAN, CUS_PLAN")
            
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