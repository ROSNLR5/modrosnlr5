🧬 modrosnlr5 – Linux Kernel LPE PoC (CVE-2026-31431)

<p align="center">
  <img src="assets/modrosnlr5-banner.png" alt="modrosnlr5 banner" width="100%">
</p>

Herramienta de prueba de concepto diseñada para validar la explotación de la vulnerabilidad **CVE-2026-31431** en sistemas Linux.  
El exploit aprovecha la interfaz de sockets `AF_ALG` del kernel para inyectar una carga útil y obtener una shell con privilegios de **root** a partir de una sesión de usuario sin permisos.

> ⚖️ **Uso ético y controlado:** Este código se distribuye exclusivamente con fines de investigación, formación y auditorías autorizadas. Solo debe ejecutarse en entornos sobre los que se tenga permiso explícito.

---

## ✳️ Funciones destacadas

- **Inspección previa de privilegios:** Análisis automático de UID, GID y pertenencia a los grupos `sudo`, `wheel` y `root`.
- **Ingeniería del socket AF_ALG:** PoC que secuestra el flujo de ejecución del binario `su` mediante `os.splice` y descompresión vía `zlib`.
- **Control interactivo:** El teclado permite abortar la operación en cualquier momento (`ESC`), añadiendo una capa de seguridad antes del despliegue real del payload.

---

## 🔬 Mecanismo de explotación

1. **Preparación y análisis**  
   El script examina la identidad del usuario actual, detecta binarios SUID y verifica la configuración del sistema.
2. **Entrega del payload**  
   La carga se descomprime con `zlib` y se inserta en el espacio del proceso objetivo manipulando el flujo de datos del socket.
3. **Elevación a root**  
   Si la inyección tiene éxito, se fuerza un `spawn` de shell con privilegios máximos, estableciendo una sesión persistente.

---

## 🔧 Requisitos y ejecución

### Dependencias
- **Kernel** Linux vulnerable a la familia CVE-2026-31431.
- **Python** ≥ 3.8.
- Acceso de lectura sobre `/usr/bin/su`.

### Comando
```bash
python3 mod_rosnlr5.py
📘 Créditos
Investigación original y PoC base: copy.fail

Adaptación, automatización y desarrollo del repositorio: ROSNLR5

modrosnlr5 – fundamentos de escalada local sobre AF_ALG
