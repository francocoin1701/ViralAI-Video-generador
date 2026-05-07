# main.py
import sys

def menu():
    print("\n🤖 CVA - Creación de Video Automático")
    print("="*60)
    print("  1. ✍️  Generar guión")
    print("  2. 🎙️  Generar voces")
    print("  3. 🎬  Generar videos  (próximamente)")
    print("  4. 👋  Salir")
    print("="*60)
    return input("Elige una opción: ").strip()

if __name__ == "__main__":
    while True:
        opcion = menu()
        if opcion == "1":
            from src.generator.script_generator import generar_guion, mostrar_guion, listar_guiones
            todos = listar_guiones()
            if todos:
                print(f"\n📂 Guiones existentes ({len(todos)}):")
                for g in todos:
                    print(f"  [{g.get('estado','?')}] {g['tema']} — {g['titulo']}")
            tema = input("\n📌 Tema del nuevo guión: ").strip()
            if tema:
                guion = generar_guion(tema=tema)
                mostrar_guion(guion)
        elif opcion == "2":
            from src.generator.voice_generator import generar_audio
            from src.generator.script_generator import listar_guiones
            pendientes = listar_guiones(estado="sin_voz")
            if not pendientes:
                print("\n✅ No hay guiones pendientes de voz.")
                continue
            print(f"\n📂 Guiones sin voz ({len(pendientes)}):")
            for i, g in enumerate(pendientes, 1):
                print(f"  {i}. {g['tema']} — {g['titulo']}")
            print(f"  0. Generar TODOS")
            opcion2 = input("\n¿Cuál generar?: ").strip()
            if opcion2 == "0":
                seleccionados = pendientes
            elif opcion2.isdigit() and 1 <= int(opcion2) <= len(pendientes):
                seleccionados = [pendientes[int(opcion2) - 1]]
            else:
                print("❌ Opción inválida")
                continue
            for g in seleccionados:
                print(f"\n⏳ Generando voz para: {g['tema']}...")
                generar_audio(g)
            print("\n✅ Listo!")
        elif opcion == "3":
            from src.editor.video_editor import generar_video
            from src.generator.script_generator import listar_guiones
            pendientes = listar_guiones(estado="sin_video")
            if not pendientes:
                print("\n✅ No hay guiones con voz pendientes de video.")
                continue
            print(f"\n📂 Guiones listos para video ({len(pendientes)}):")
            for i, g in enumerate(pendientes, 1):
                print(f"  {i}. {g['tema']} — {g['titulo']}")
            print(f"  0. Generar TODOS")
            opcion2 = input("\n¿Cuál generar?: ").strip()
            if opcion2 == "0":
                seleccionados = pendientes
            elif opcion2.isdigit() and 1 <= int(opcion2) <= len(pendientes):
                seleccionados = [pendientes[int(opcion2) - 1]]
            else:
                print("❌ Opción inválida")
                continue
            for g in seleccionados:
                generar_video(g)
            print("\n✅ Videos generados!")
        elif opcion == "4":
            print("👋 Hasta luego!")
            break