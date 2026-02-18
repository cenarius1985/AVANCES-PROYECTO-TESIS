import os
import sys
import shutil
import subprocess
import datetime

# Directorio donde reside este script (raíz del repo)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = SCRIPT_DIR
LOG_FILE = os.path.join(WORK_DIR, "compilation_log.txt")

def command_available(cmd):
    return shutil.which(cmd) is not None

def log_output(title, content):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n=== {title} === {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(content)
            f.write("\n")
    except Exception:
        pass

def get_tex_env():
    env = os.environ.copy()
    sep = ";" if os.name == 'nt' else ":"
    
    # Rutas para TEXINPUTS (fuentes, estilos, imágenes)
    paths = [
        ".",
        os.path.join(WORK_DIR, "Styles"),
        os.path.join(WORK_DIR, "Figures"),
        os.path.join(WORK_DIR, "Content"),
    ]
    
    texinputs = sep.join(paths) + sep
    env["TEXINPUTS"] = texinputs
    
    return env

def run_command(cmd, title="Comando"):
    print(f"> Ejecutando: {' '.join(cmd)}")
    env = get_tex_env()
    try:
        proc = subprocess.run(
            cmd,
            cwd=WORK_DIR,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        log_output(title, proc.stdout + "\n" + proc.stderr)
        if proc.returncode != 0:
            # BibTeX a veces falla si no hay citas, no bloqueamos la compilación por eso
            if "bibtex" in cmd[0].lower():
                print(f"Nota: BibTeX no encontró citas (normal en informes sin bibliografía).")
                return True
            print(f"Error en {title}. Ver log.")
            return False
        return True
    except Exception as e:
        print(f"Excepción ejecutando {title}: {e}")
        return False

def compile_full():
    if not os.path.exists(os.path.join(WORK_DIR, "main.tex")):
        print("Error: No se encuentra main.tex en " + WORK_DIR)
        return

    print("=== Iniciando compilación de Informe de Avances ===")
    
    if command_available("pdflatex"):
        print("Usando PDFLaTeX...")
        # 1. pdflatex inicial
        if not run_command(["pdflatex", "-interaction=nonstopmode", "-file-line-error", "main.tex"], "PDFLaTeX 1"):
            return
            
        # 2. bibtex (opcional, solo si existe .bib y citas)
        # En informes de avance es común no tener .bib aún
        has_bib = any(f.endswith('.bib') for f in os.listdir(WORK_DIR)) or \
                  (os.path.exists("Bibliography") and any(f.endswith('.bib') for f in os.listdir("Bibliography")))
        
        if has_bib:
            run_command(["bibtex", "main"], "BibTeX")
            
        # 3. pdflatex final
        run_command(["pdflatex", "-interaction=nonstopmode", "-file-line-error", "main.tex"], "PDFLaTeX 2")
        run_command(["pdflatex", "-interaction=nonstopmode", "-file-line-error", "main.tex"], "PDFLaTeX 3")

    elif command_available("tectonic"):
        print("PDFLaTeX no encontrado. Usando Tectonic...")
        run_command(["tectonic", "-X", "compile", "main.tex"], "Tectonic")
    else:
        print("Error: No se encontró ni pdflatex ni tectonic.")
        return
    
    print("=== Compilación finalizada ===")
    if os.path.exists(os.path.join(WORK_DIR, "main.pdf")):
        print(f"PDF generado: {os.path.join(WORK_DIR, 'main.pdf')}")
        
        # Lógica de apertura de archivos (solo si es Windows local)
        if os.name == 'nt':
            try:
                # Intenta abrir con Chrome para evitar bloqueos de Adobe
                chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                if os.path.exists(chrome_path):
                     subprocess.Popen([chrome_path, os.path.join(WORK_DIR, "main.pdf")])
                else:
                     # Fallback si no encuentra Chrome en ruta estándar
                     os.startfile("main.pdf")
            except:
                pass

if __name__ == "__main__":
    compile_full()
