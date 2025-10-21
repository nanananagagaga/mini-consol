"""
Gestor de reglas de capping
===========================

Este módulo maneja las reglas de capping de forma flexible y configurable.
Las reglas se definen por:
- Sólido (etiqueta asignada al archivo)
- Pas_cut (valor de la columna pas_cut)
- Rango de valores (min, max) para cut_op
- Multiplicador a aplicar
"""

class RulesManager:
    def __init__(self):
        """
        Inicializar gestor de reglas de capping
        Las reglas se almacenan como una lista de diccionarios
        """
        self.rules = []
        
        # Cargar reglas por defecto como ejemplo
        self._load_default_rules()
    
    def _load_default_rules(self):
        """
        Inicializar sin reglas por defecto
        El usuario configurará sus propias reglas según sus necesidades
        """
        # Iniciar vacío - sin ejemplos
        self.rules = []
    
    def add_rule(self, solido, pas_cut, rango_min, rango_max, multiplicador):
        """
        Agregar nueva regla de capping
        
        Args:
            solido (str): Etiqueta de sólido
            pas_cut (str): Valor de pas_cut
            rango_min (float): Valor mínimo del rango (inclusive)
            rango_max (float): Valor máximo del rango (exclusive)
            multiplicador (float): Factor multiplicativo a aplicar
        """
        # Validaciones básicas
        if rango_max <= rango_min:
            raise ValueError("rango_max debe ser mayor que rango_min")
        
        if multiplicador <= 0:
            raise ValueError("multiplicador debe ser positivo")
        
        new_rule = {
            'solido': str(solido),
            'pas_cut': str(pas_cut),
            'rango_min': float(rango_min),
            'rango_max': float(rango_max),
            'multiplicador': float(multiplicador)
        }
        
        # Verificar si ya existe una regla similar (mismo sólido, pas_cut, y rango solapado)
        existing_rule = self._find_overlapping_rule(new_rule)
        if existing_rule:
            # Preguntar al usuario o reemplazar automáticamente
            # Por ahora, reemplazar
            self.rules.remove(existing_rule)
        
        self.rules.append(new_rule)
    
    def _find_overlapping_rule(self, new_rule):
        """
        Buscar regla existente que tenga solapamiento de rango
        """
        for rule in self.rules:
            if (rule['solido'] == new_rule['solido'] and 
                rule['pas_cut'] == new_rule['pas_cut']):
                
                # Verificar solapamiento de rangos
                existing_min = rule['rango_min']
                existing_max = rule['rango_max']
                new_min = new_rule['rango_min']
                new_max = new_rule['rango_max']
                
                # Hay solapamiento si:
                # - El nuevo rango empieza antes de que termine el existente
                # - Y el nuevo rango termina después de que empiece el existente
                if (new_min < existing_max and new_max > existing_min):
                    return rule
        
        return None
    
    def remove_rule(self, solido, pas_cut, rango_min, rango_max):
        """
        Eliminar regla específica
        """
        rule_to_remove = None
        for rule in self.rules:
            if (rule['solido'] == str(solido) and 
                rule['pas_cut'] == str(pas_cut) and
                rule['rango_min'] == float(rango_min) and
                rule['rango_max'] == float(rango_max)):
                rule_to_remove = rule
                break
        
        if rule_to_remove:
            self.rules.remove(rule_to_remove)
            return True
        return False
    
    def get_all_rules(self):
        """
        Obtener todas las reglas actuales
        
        Returns:
            list: Lista de diccionarios con las reglas
        """
        return self.rules.copy()
    
    def clear_all_rules(self):
        """
        Eliminar todas las reglas
        """
        self.rules = []
    
    def get_rules_for_solido_pascut(self, solido, pas_cut):
        """
        Obtener reglas específicas para una combinación sólido/pas_cut
        
        Args:
            solido (str): Etiqueta de sólido
            pas_cut (str): Valor de pas_cut
            
        Returns:
            list: Lista de reglas aplicables, ordenadas por rango_min
        """
        applicable_rules = []
        
        for rule in self.rules:
            if rule['solido'] == str(solido) and rule['pas_cut'] == str(pas_cut):
                applicable_rules.append(rule)
        
        # Ordenar por rango_min para aplicación secuencial
        applicable_rules.sort(key=lambda x: x['rango_min'])
        
        return applicable_rules
    
    def validate_rules(self):
        """
        Validar que las reglas no tengan conflictos
        
        Returns:
            list: Lista de errores encontrados (vacía si no hay errores)
        """
        errors = []
        
        # Agrupar reglas por sólido/pas_cut
        grouped_rules = {}
        for rule in self.rules:
            key = (rule['solido'], rule['pas_cut'])
            if key not in grouped_rules:
                grouped_rules[key] = []
            grouped_rules[key].append(rule)
        
        # Verificar solapamientos dentro de cada grupo
        for (solido, pas_cut), group_rules in grouped_rules.items():
            # Ordenar por rango_min
            group_rules.sort(key=lambda x: x['rango_min'])
            
            for i in range(len(group_rules) - 1):
                current_rule = group_rules[i]
                next_rule = group_rules[i + 1]
                
                # Verificar solapamiento
                if current_rule['rango_max'] > next_rule['rango_min']:
                    error_msg = (f"Solapamiento detectado en solido='{solido}', pas_cut='{pas_cut}': "
                               f"rango [{current_rule['rango_min']}, {current_rule['rango_max']}) "
                               f"solapa con [{next_rule['rango_min']}, {next_rule['rango_max']})")
                    errors.append(error_msg)
        
        return errors
    
    def export_rules_to_dict(self):
        """
        Exportar reglas a diccionario para serialización
        
        Returns:
            dict: Diccionario con todas las reglas
        """
        return {
            'rules': self.rules,
            'total_rules': len(self.rules)
        }
    
    def import_rules_from_dict(self, rules_dict):
        """
        Importar reglas desde diccionario
        
        Args:
            rules_dict (dict): Diccionario con reglas exportadas
        """
        if 'rules' in rules_dict:
            self.rules = rules_dict['rules']
        else:
            raise ValueError("Formato de reglas inválido")
    
    def get_summary_stats(self):
        """
        Obtener estadísticas resumen de las reglas
        
        Returns:
            dict: Diccionario con estadísticas
        """
        if not self.rules:
            return {'total_rules': 0, 'solidos': [], 'pas_cuts': []}
        
        solidos = list(set(rule['solido'] for rule in self.rules))
        pas_cuts = list(set(rule['pas_cut'] for rule in self.rules))
        
        # Contar reglas por sólido
        rules_por_solido = {}
        for solido in solidos:
            count = sum(1 for rule in self.rules if rule['solido'] == solido)
            rules_por_solido[solido] = count
        
        return {
            'total_rules': len(self.rules),
            'solidos': solidos,
            'pas_cuts': pas_cuts,
            'rules_por_solido': rules_por_solido
        }