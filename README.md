# Mini Consola - Block Model Processor

Aplicación para procesar múltiples archivos CSV de block models, aplicar reglas de capping y calcular variables derivadas.

## 🚀 Cómo usar

### 1. Preparar archivos CSV
- Coloca todos tus block models (.csv) en una carpeta
- **Importante**: Todos los archivos deben tener las mismas columnas principales
- La aplicación maneja automáticamente filas problemáticas de Vulcan (metadata en filas 2-4)

### 2. Ejecutar aplicación
```bash
python main.py
```

### 3. Configurar (4 pasos):

**📁 Pestaña 1 - Archivos:**
- Selecciona carpeta con tus CSVs
- Edita etiquetas de fase para cada archivo (ej: "10", "13A", "15")

**🔧 Pestaña 2 - Columnas:**
- Mapea tus columnas a variables requeridas:
  - `CUT_OP`: Ley de corte original
  - `RST_OP`: Recuperación operacional  
  - `PAS_CUT`: Variable categórica para capping
- Click "Analizar Columnas" para detectar automáticamente

**📋 Pestaña 3 - Reglas de Capping:**
- Agrega reglas por fase + pas_cut + rango de valores
- Ejemplo: Fase "10", PAS_CUT "3", rango 0.5-1.0 → multiplicar por 0.9

**⚙️ Pestaña 4 - Procesar:**
- Elige opción de guardado:
  - **📄 Duplicados** (recomendado): Crea copias `_capeado.csv`
  - **⚠️ Actualizar originales**: Sobrescribe archivos originales
  - **📊 Consolidar**: Todo en un archivo `blockmodel_capeado.csv`

## 📊 Variables calculadas

- **CUT_PLAN**: `CUT_OP` con reglas de capping aplicadas
- **CUS_PLAN**: `RST_OP × CUT_PLAN` (fórmula configurable en código)

## ⚠️ Consideraciones importantes

### Para que funcione correctamente:
1. **Columnas obligatorias**: Todos los CSVs deben tener columnas para CUT_OP, RST_OP y PAS_CUT
2. **Estructura consistente**: Mismos headers en todos los archivos
3. **Datos numéricos**: CUT_OP y RST_OP deben ser valores numéricos
4. **PAS_CUT categórico**: Puede ser texto o números (se convierte a string)

### Archivos problemáticos:
- ✅ Maneja filas de metadata de Vulcan automáticamente
- ✅ Detecta y omite filas con headers duplicados
- ✅ Reporta archivos que no se pueden leer

### Reglas de capping:
- Los rangos son: [mínimo, máximo) - mínimo inclusive, máximo exclusivo
- Multiplicadores deben ser > 0
- Si no hay regla para una combinación fase/pas_cut, CUT_PLAN = CUT_OP

## 🔧 Personalización

**Cambiar fórmula CUS_PLAN:**
Edita línea 21 en `data_processor.py`:
```python
self.cus_plan_formula = "rst_op * cut_plan"  # Cambiar aquí
```

## 📂 Archivos generados

**Opción Duplicados:**
- `archivo_original.csv` → `archivo_original_capeado.csv`
- Agrega columnas: FASE, CUT_PLAN, CUS_PLAN

**Opción Consolidado:**
- Un solo archivo: `blockmodel_capeado.csv`
- Todas las filas de todos los BMs juntas

## 🐛 Solución de problemas

**"No hay columnas comunes":**
- Verifica que todos los CSVs tengan la misma estructura
- Revisa nombres de columnas (sensible a mayúsculas)

**"Error leyendo CSV":**
- Archivo no debe estar abierto en Excel
- Verifica codificación UTF-8
- Revisa que tenga headers válidos

**"No se aplicaron reglas":**
- Etiquetas de fase deben coincidir exactamente
- Valores PAS_CUT son sensibles a mayúsculas/espacios

## 📋 Instalación

```bash
pip install pandas
```

Solo requiere Python 3.7+ y pandas. Tkinter viene incluido con Python.