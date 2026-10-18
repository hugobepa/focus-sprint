#!/usr/bin/env python3
"""
Sprint de concentración v3.0 — Optimizado según evidencia científica.
- 10 actividades preconfiguradas (frecuencia + beat + ruido + duración).
- WAV de 30 min reproducido en loop con pygame.mixer (NO abre reproductor externo).
- Generación vía API de binaural-generator (sin subprocess, sin shell).
- Sample rate selectivo por tipo de ruido (8000 / 16000 / 22050 Hz).
- Recomendación automática Binaural vs Monaural según actividad.
- Recordatorio de última actividad entre sesiones.
- Reutilización de WAV si la configuración coincide.

Requiere: pip install numpy soundfile pygame binaural-generator

Referencias:
- Basu et al. (2023) meta-análisis BB memoria/atención.
- Engelbregt et al. (2021) BB vs MB en atención y EEG.
- Chaieb et al. (2015) revisión ABS.
"""

import ctypes
import glob
import json
import os
import subprocess
import sys
import time

# ---------------------------------------------------------------
# CONFIGURACIÓN GLOBAL
# ---------------------------------------------------------------

# Sample rate óptimo por tipo de ruido
SAMPLE_RATES = {
    "brown": 8000,  # Graves puros — sobra
    "ocean": 8000,  # Graves suaves — sobra
    "none": 8000,  # Solo binaural — sobra
    "pink": 16000,  # Medios — suficiente
    "rain": 16000,  # Medios + agudos de gotas
    "white": 22050,  # Agudos — necesario
}

# Duración fija del WAV en loop (30 minutos)
LOOP_DURATION_SEC = 1800

# Volúmenes fijos (recomendados por literatura)
VOL_BINAURAL = 0.40  # 40%
VOL_RUIDO = 0.15  # 15%

# Archivo de configuración persistente
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".sprint_focus_config.json")

# ---------------------------------------------------------------
# CATÁLOGO DE ACTIVIDADES
# ---------------------------------------------------------------

ACTIVIDADES = {
    1: {
        "nombre": "Programación / Debugging",
        "freq": 40,
        "tipo_beat": "binaural",
        "ruido": "brown",
        "duracion_rec": 50,
        "justificacion": "Gamma 40 Hz: atención sostenida y flexibilidad cognitiva.",
    },
    2: {
        "nombre": "Estudio / Memorización",
        "freq": 10,
        "tipo_beat": "binaural",
        "ruido": "brown",
        "duracion_rec": 30,
        "justificacion": "Alpha 10 Hz: mejora memoria de trabajo (Engelbregt 2021).",
    },
    3: {
        "nombre": "Escritura / Redacción",
        "freq": 14,
        "tipo_beat": "monaural",
        "ruido": "pink",
        "duracion_rec": 45,
        "justificacion": "Beta 14 Hz: mejora vigilancia y fluidez verbal.",
    },
    4: {
        "nombre": "Diseño / Creatividad",
        "freq": 6,
        "tipo_beat": "binaural",
        "ruido": "ocean",
        "duracion_rec": 40,
        "justificacion": "Theta 6 Hz: creatividad y pensamiento divergente.",
    },
    5: {
        "nombre": "Lectura / Comprensión",
        "freq": 40,
        "tipo_beat": "binaural",
        "ruido": "brown",
        "duracion_rec": 45,
        "justificacion": "Gamma 40 Hz: precisión en comprensión lectora.",
    },
    6: {
        "nombre": "Análisis de Datos",
        "freq": 20,
        "tipo_beat": "monaural",
        "ruido": "pink",
        "duracion_rec": 50,
        "justificacion": "Beta 20 Hz: detección de señales y patrones.",
    },
    7: {
        "nombre": "Reuniones / Escucha Activa",
        "freq": 10,
        "tipo_beat": "monaural",
        "ruido": "ocean",
        "duracion_rec": 30,
        "justificacion": "Alpha 10 Hz: alerta relajado, ideal para escuchar.",
    },
    8: {
        "nombre": "Tareas Administrativas",
        "freq": 14,
        "tipo_beat": "monaural",
        "ruido": "pink",
        "duracion_rec": 25,
        "justificacion": "Beta 14 Hz: arousal moderado para tareas repetitivas.",
    },
    9: {
        "nombre": "Meditación / Reset",
        "freq": 6,
        "tipo_beat": "binaural",
        "ruido": "ocean",
        "duracion_rec": 15,
        "justificacion": "Theta 6 Hz: relajación profunda y reset mental.",
    },
    10: {
        "nombre": "Aprendizaje de Idiomas",
        "freq": 10,
        "tipo_beat": "binaural",
        "ruido": "brown",
        "duracion_rec": 30,
        "justificacion": "Alpha 10 Hz: memoria de trabajo verbal.",
    },
}

# ---------------------------------------------------------------
# CONFIG PERSISTENTE
# ---------------------------------------------------------------


def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  No se pudo guardar config: {e}")


# ---------------------------------------------------------------
# UI — MENÚ Y SELECCIÓN
# ---------------------------------------------------------------


def mostrar_menu():
    print("\n" + "=" * 62)
    print("  🎯  SPRINT DE CONCENTRACIÓN — Selecciona actividad")
    print("=" * 62)
    for k, v in ACTIVIDADES.items():
        beat_icon = "🎧" if v["tipo_beat"] == "binaural" else "🔊"
        print(
            f"  {k:>2}) {v['nombre']:<28} {v['freq']:>3} Hz  {beat_icon} {v['tipo_beat']}"
        )
    print("=" * 62)
    while True:
        try:
            op = int(input("👉 Actividad (1-10): "))
            if op in ACTIVIDADES:
                return op
        except ValueError:
            pass
        print("❌ Opción inválida. Elige entre 1 y 10.")


def mostrar_detalle(act):
    print("\n" + "─" * 62)
    print(f"  📌 Actividad: {act['nombre']}")
    print(f"  🧠 Frecuencia:   {act['freq']} Hz")
    print(f"  🎧 Tipo de beat: {act['tipo_beat'].upper()}")
    print(f"  🌫️  Ruido fondo:  {act['ruido']}")
    print(f"  ⏱️  Duración rec.: {act['duracion_rec']} min")
    print(f"  💡 {act['justificacion']}")
    print("─" * 62)


def ajustar_configuracion(act):
    """Permite cambiar frecuencia, tipo beat, ruido y duración."""
    freq = act["freq"]
    tipo_beat = act["tipo_beat"]
    ruido = act["ruido"]

    print("\n🔧 Modo avanzado (Enter = mantener valor actual)")

    # Frecuencia
    while True:
        try:
            v = input(f"  Frecuencia binaural Hz [{freq}]: ").strip()
            if v == "":
                break
            freq = int(v)
            if freq > 0:
                break
        except ValueError:
            pass
        print("  ❌ Introduce un número entero positivo.")

    # Tipo de beat
    while True:
        v = input(f"  Tipo de beat (binaural/monaural) [{tipo_beat}]: ").strip().lower()
        if v == "":
            break
        if v in ("binaural", "monaural"):
            tipo_beat = v
            break
        if v in ("b", "bi"):
            tipo_beat = "binaural"
            break
        if v in ("m", "mo"):
            tipo_beat = "monaural"
            break
        print("  ❌ Escribe 'binaural' o 'monaural'.")

    # Ruido
    opciones_ruido = list(SAMPLE_RATES.keys())
    while True:
        v = input(f"  Ruido {opciones_ruido} [{ruido}]: ").strip().lower()
        if v == "":
            break
        if v in opciones_ruido:
            ruido = v
            break
        print(f"  ❌ Opciones válidas: {opciones_ruido}")

    return freq, tipo_beat, ruido


def preguntar_duracion(rec):
    while True:
        v = input(f"⏱️  Duración del sprint en minutos [{rec}]: ").strip()
        if v == "":
            return rec
        try:
            mins = int(v)
            if mins > 0:
                return mins
        except ValueError:
            pass
        print("❌ Introduce un número entero positivo.")


def verificar_cascos(tipo_beat):
    if tipo_beat != "binaural":
        return "monaural"
    print("\n⚠️  Esta configuración recomienda BINAURAL (requiere cascos).")
    print("   Los binaural beats pierden su efecto con altavoces.")
    while True:
        v = input("🎧 ¿Tienes cascos? (s/n): ").strip().lower()
        if v == "s":
            return "binaural"
        if v == "n":
            print("   → Cambiando a MONAURAL automáticamente.")
            return "monaural"
        print("❌ Responde 's' o 'n'.")


# ---------------------------------------------------------------
# AUDIO — GENERACIÓN, MONO, VOLUMEN
# ---------------------------------------------------------------


def convertir_a_mono(wav_file):
    try:
        import numpy as np
        import soundfile as sf

        data, fs = sf.read(wav_file, dtype="float32")
        if data.ndim == 1:
            return True
        data_mono = np.mean(data, axis=1)
        sf.write(wav_file, data_mono, fs, subtype="PCM_16")
        return True
    except ImportError:
        print("⚠️  Instala soundfile y numpy: pip install soundfile numpy")
        return False
    except Exception as e:
        print(f"⚠️  Error convirtiendo a mono: {e}")
        return False


def aplicar_volumen(wav_file, factor):
    if factor >= 1.0:
        return True
    try:
        import numpy as np
        import soundfile as sf

        data, fs = sf.read(wav_file, dtype="float32")
        data = np.clip(data * factor, -1.0, 1.0)
        sf.write(wav_file, data, fs, subtype="PCM_16")
        return True
    except ImportError:
        print("⚠️  Instala soundfile y numpy: pip install soundfile numpy")
        return False
    except Exception as e:
        print(f"⚠️  Error aplicando volumen: {e}")
        return False


def ruta_wav(freq, tipo_beat, ruido, sample_rate):
    """Nombre determinista según la configuración."""
    nombre = f"sprint_audio_{freq}Hz_{tipo_beat}_{ruido}_{sample_rate}Hz.wav"
    return os.path.join(os.path.expanduser("~"), nombre)


def limpiar_wavs_antiguos(wav_objetivo):
    """Borra otros sprint_audio_*.wav que no sean el objetivo."""
    patron = os.path.join(os.path.expanduser("~"), "sprint_audio_*.wav")
    for f in glob.glob(patron):
        if os.path.abspath(f) != os.path.abspath(wav_objetivo):
            try:
                os.remove(f)
                print(f"🗑️  WAV antiguo borrado: {os.path.basename(f)}")
            except Exception:
                pass


def generar_wav(freq, tipo_beat, ruido, sample_rate, wav_file, yaml_file):
    """
    Genera el WAV usando la API de Python de binaural-generator.
    Sin subprocess → sin cmd.exe → sin reproductor externo.
    Con fallback defensivo a subprocess sin shell si la API cambia.
    """
    wav_yaml = wav_file.replace("\\", "/")

    if ruido == "none":
        noise_block = 'background_noise:\n  type: "none"\n'
    else:
        noise_block = (
            f'background_noise:\n  type: "{ruido}"\n  amplitude: {VOL_RUIDO:.3f}\n'
        )

    yaml_content = f"""title: "Sprint Focus {freq} Hz"
base_frequency: 200
sample_rate: {sample_rate}
output_filename: '{wav_yaml}'

{noise_block}
steps:
  - type: stable
    frequency: {freq}
    duration: {LOOP_DURATION_SEC}
    fade_in_duration: 5
    fade_out_duration: 5
"""

    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    # --- Intento 1: API de Python (sin subprocess) ---
    try:
        from binaural_generator.cli import AudioConfig, generate_audio
        from binaural_generator.core.constants import (
            DEFAULT_BASE_FREQUENCY,
            DEFAULT_SAMPLE_RATE,
        )
        from binaural_generator.core.tone_generator import save_audio_file
        from binaural_generator.core.utils import load_yaml_config

        cfg = load_yaml_config(yaml_file)
        audio_config = AudioConfig(
            sample_rate=cfg.get("sample_rate", DEFAULT_SAMPLE_RATE),
            base_freq=cfg.get("base_frequency", DEFAULT_BASE_FREQUENCY),
            steps=cfg["steps"],
            noise_config=cfg.get("noise_config"),
            title=cfg.get("title", "Binaural Beat"),
        )
        result = generate_audio(audio_config)
        save_audio_file(
            filename=wav_file,
            sample_rate=audio_config.sample_rate,
            left=result.left_channel,
            right=result.right_channel,
            total_duration_sec=result.total_duration,
        )
        return  # Éxito por API
    except (ImportError, AttributeError, TypeError) as e:
        print(f"ℹ️  API directa no disponible ({type(e).__name__}), usando CLI interno…")

    # --- Fallback: CLI en el mismo proceso (sin shell=True) ---
    subprocess.run(
        [sys.executable, "-m", "binaural_generator.cli", yaml_file, "-o", wav_file],
        check=True,
    )


# ---------------------------------------------------------------
# NOTIFICACIONES
# ---------------------------------------------------------------


def mostrar_popup(titulo, mensaje, icono="info"):
    try:
        MB_OK = 0x00000000
        MB_SYSTEMMODAL = 0x00001000
        MB_SETFOREGROUND = 0x00010000
        MB_TOPMOST = 0x00040000
        iconos = {"info": 0x40, "warning": 0x30, "error": 0x10}
        flags = (
            MB_OK
            | MB_SYSTEMMODAL
            | MB_SETFOREGROUND
            | MB_TOPMOST
            | iconos.get(icono, 0x40)
        )

        def _popup():
            ctypes.windll.user32.MessageBoxW(0, mensaje, titulo, flags)

        import threading

        threading.Thread(target=_popup, daemon=True).start()
    except Exception as e:
        print(f"⚠️  Popup: {e}")


def mostrar_toast(titulo, mensaje):
    ps = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$template = @"
<toast><visual><binding template="ToastGeneric">
<text>{titulo}</text><text>{mensaje}</text>
</binding></visual></toast>
"@
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Sprint Focus").Show($toast)
"""
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
    except Exception:
        pass


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------


def main():
    print("\n🎯  Sprint de Concentración v3.0")
    print("─" * 62)

    config = cargar_config()
    actividad_id = None

    # Recordar última actividad
    if config.get("last_activity") and config["last_activity"] in ACTIVIDADES:
        ultima = ACTIVIDADES[config["last_activity"]]
        print(f"💾 Última actividad: #{config['last_activity']} — {ultima['nombre']}")
        resp = input("¿Repetir la última actividad? (s/n): ").strip().lower()
        if resp == "s":
            actividad_id = config["last_activity"]

    if actividad_id is None:
        actividad_id = mostrar_menu()

    act = ACTIVIDADES[actividad_id]
    mostrar_detalle(act)

    # Config recomendada o ajuste
    resp = input("\n¿Usar configuración recomendada? (s/n) [s]: ").strip().lower()
    if resp == "n":
        freq, tipo_beat, ruido = ajustar_configuracion(act)
    else:
        freq = act["freq"]
        tipo_beat = act["tipo_beat"]
        ruido = act["ruido"]

    # Verificar cascos si binaural
    tipo_beat = verificar_cascos(tipo_beat)

    # Duración elegida por el usuario
    mins = preguntar_duracion(act["duracion_rec"])

    # Resumen final
    sample_rate = SAMPLE_RATES.get(ruido, 8000)
    print("\n" + "═" * 62)
    print("  📋 RESUMEN DEL SPRINT")
    print("═" * 62)
    print(f"  Actividad:    {act['nombre']}")
    print(f"  Frecuencia:   {freq} Hz")
    print(f"  Tipo beat:    {tipo_beat.upper()}")
    print(f"  Ruido fondo:  {ruido}")
    print(f"  Sample rate:  {sample_rate} Hz")
    print(f"  Duración:     {mins} min")
    print(f"  Loop WAV:     {LOOP_DURATION_SEC // 60} min")
    print("═" * 62)

    resp = input("\n¿Comenzar sprint? (s/n): ").strip().lower()
    if resp != "s":
        print("Cancelado.")
        return

    # Rutas
    wav_file = ruta_wav(freq, tipo_beat, ruido, sample_rate)
    yaml_file = os.path.join(os.path.expanduser("~"), "focus_temp.yaml")

    # 1️⃣ FocusCLI
    procesos = []
    try:
        p = subprocess.Popen(
            ["focuscli", "timer", str(mins)],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        procesos.append(p)
        print("✅ FocusCLI iniciado")
    except FileNotFoundError:
        try:
            p = subprocess.Popen(
                [sys.executable, "-m", "focuscli.main", "timer", str(mins)],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            procesos.append(p)
            print("✅ FocusCLI iniciado (via python -m)")
        except Exception as e:
            print(f"⚠️  FocusCLI no disponible: {e}")

        # 2️⃣ Samaya — DESACTIVADO (abre el reproductor por defecto en Windows)
        # Descomenta si algún día lo arreglan o lo sustituyes por otra herramienta.
        #
        # try:
        #     p = subprocess.Popen(
        #         ["samaya", "--time", str(mins)],
        #         shell=True,
        #         stdout=subprocess.DEVNULL,
        #         stderr=subprocess.DEVNULL,
        #     )
        #     procesos.append(p)
        #     print("✅ Samaya iniciado")
        # except FileNotFoundError:
        #     print("⚠️  Samaya no encontrado.")
        print("ℹ️  Samaya desactivado (usamos audio binaural propio)")

    # 3️⃣ Audio (generar o reutilizar)
    audio_listo = False
    if os.path.exists(wav_file):
        print(f"♻️  Reutilizando WAV existente: {os.path.basename(wav_file)}")
        audio_listo = True
    else:
        print(f"🎼 Generando WAV ({LOOP_DURATION_SEC // 60} min) a {sample_rate} Hz...")
        limpiar_wavs_antiguos(wav_file)
        try:
            generar_wav(freq, tipo_beat, ruido, sample_rate, wav_file, yaml_file)
            print(f"✅ WAV generado: {os.path.basename(wav_file)}")
            audio_listo = True
        except FileNotFoundError:
            print("⚠️  'binaural-generator' no encontrado.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error generando WAV: {e}")

        # Convertir a mono si aplica
        if audio_listo and tipo_beat == "monaural":
            print("🔊 Convirtiendo a mono...")
            convertir_a_mono(wav_file)

        # Aplicar volumen
        if audio_listo:
            aplicar_volumen(wav_file, VOL_BINAURAL)

        # Tamaño real
        if audio_listo and os.path.exists(wav_file):
            mb = os.path.getsize(wav_file) / (1024 * 1024)
            print(f"📦 Tamaño WAV: {mb:.1f} MB")

    # 4️⃣ Reproducir en loop con pygame.mixer (NO abre reproductor externo)
    mixer_iniciado = False
    if audio_listo and os.path.exists(wav_file):
        try:
            import pygame

            # Inicializar mixer con defaults; SDL2 hace resampling si hace falta
            pygame.mixer.init()
            pygame.mixer.music.load(wav_file)
            pygame.mixer.music.set_volume(1.0)  # el WAV ya tiene el volumen aplicado
            pygame.mixer.music.play(loops=-1)  # -1 = loop infinito
            mixer_iniciado = True
            print(f"🎵 Reproduciendo en loop (volumen {int(VOL_BINAURAL * 100)}%)")
        except ImportError:
            print("⚠️  pygame no instalado. Ejecuta: pip install pygame")
        except Exception as e:
            print(f"⚠️  No se pudo reproducir con pygame: {e}")

    # 5️⃣ Esperar duración del sprint
    print(f"\n🚀 Sprint de {mins} min iniciado. ⌛ (Ctrl+C para cancelar)\n")
    try:
        time.sleep(mins * 60)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupción manual.")
    finally:
        print("\n🧹 Deteniendo...")

        # Detener audio con pygame
        if mixer_iniciado:
            try:
                import pygame

                pygame.mixer.music.stop()
                pygame.mixer.quit()
                print("🔇 Audio detenido")
            except Exception:
                pass

        for p in procesos:
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

        # Borrar YAML siempre
        if os.path.exists(yaml_file):
            try:
                os.remove(yaml_file)
                print("🗑️  YAML borrado")
            except Exception:
                pass

        # Guardar actividad
        config["last_activity"] = actividad_id
        guardar_config(config)

        print(f"\n💾 WAV conservado para reutilizar: {os.path.basename(wav_file)}")
        print("\n✅ Sprint finalizado. ¡Buen trabajo!")

        # Notificaciones
        detalle = f"{freq} Hz | {tipo_beat} | {ruido} | {mins} min"
        mostrar_toast("✅ Sprint completado", f"{act['nombre']} — {detalle}")
        mostrar_popup(
            "✅ Sprint completado",
            f"¡Buen trabajo!\n\n"
            f"Actividad: {act['nombre']}\n"
            f"Duración: {mins} min\n"
            f"Config: {detalle}\n\n"
            f"Toma un descanso real: camina, estira, mira lejos.\n"
            f"Nada de pantallas durante 5-10 minutos.",
            icono="info",
        )


if __name__ == "__main__":
    main()
