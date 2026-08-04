from sqlalchemy import text
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware 
from db_connector.database import get_db 
from db_connector.data_access import fetch_all_data_for_solver
from solver_service.scheduler import generate_schedule_for_all_groups, ScheduleResult

app = FastAPI(title="Solver Service")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.post("/generate")
async def generate_schedule_endpoint(
    db: Session = Depends(get_db) 
):
    """
    ¡NUEVA ESTRATEGIA! Genera horarios asignando MATERIA POR MATERIA.
    """
    try:
        # 1. CARGAR TODOS LOS DATOS PARA EL SOLVER
        data = fetch_all_data_for_solver(db)
        
        # 2. ASEGURAR AULAS DIRECTAMENTE EN MEMORIA COMO ENTEROS
        if not data.get('professor_rooms') and data.get('professors') and data.get('rooms'):
            first_room_id = data['rooms'][0].id
            data['professor_rooms'] = {p.id: first_room_id for p in data['professors']}
            print("🛠️ Aulas inyectadas correctamente en memoria para el solver.")

        print("\n" + "="*60)
        print("--- INICIANDO GENERACIÓN DE HORARIOS ---")
        print(f"Cursos: {len(data['courses'])}")
        print(f"Aulas: {len(data['rooms'])}")
        print(f"Slots: {len(data['timeslots'])}")
        print(f"Profesores: {len(data['professors'])}")
        print(f"Grupos: {len(data.get('groups', []))}")
        print(f"Asignaciones profesor-materia-grupo: {len(data.get('professor_course_group_assignments', []))}")
        print(f"Aulas asignadas a profesores: {len(data.get('professor_rooms', {}))}")
        print("="*60 + "\n")
        
        if not data.get('professor_course_group_assignments'):
            raise HTTPException(
                status_code=400,
                detail="No hay asignaciones profesor-materia-grupo. Verifica la tabla 'profesor_asignatura_grupo'."
            )
        
        groups_to_process = data.get('groups', [])
        if not groups_to_process:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron grupos en la base de datos"
            )

        professor_map = {p.id: p.name for p in data['professors']}
        course_map = {c.id: c.name for c in data['courses']}
        room_map = {r.id: r.name for r in data['rooms']}
        building_map = {r.id: r.building_name or "N/A" for r in data['rooms']}
        timeslot_map = {ts.id: (ts.day, ts.start_time) for ts in data['timeslots']}
        
        print("🗑️  Limpiando horarios anteriores...")
        group_ids_str = ','.join([str(g.id) for g in groups_to_process])
        db.execute(text(f"DELETE FROM horario_clases WHERE id_grupo IN ({group_ids_str})"))
        db.commit()
        print("✅ Horarios anteriores eliminados\n")
        
        all_schedules = generate_schedule_for_all_groups(
            courses=data['courses'], 
            rooms=data['rooms'], 
            timeslots=data['timeslots'], 
            professors=data['professors'],
            assignments=data['professor_course_group_assignments'],
            professor_rooms=data.get('professor_rooms', {}),
            groups=groups_to_process
        )
        
        print("\n" + "="*60)
        print("💾 GUARDANDO HORARIOS EN BASE DE DATOS")
        print("="*60 + "\n")
        
        final_results = []
        
        for group in groups_to_process:
            group_id = group.id
            schedule = all_schedules.get(group_id, {})
            
            if not schedule:
                print(f"⚠️ No se generó horario para Grupo {group_id}")
                continue
            
            print(f"💾 Guardando horario para {group.name}...")
            
            group_schedule_data = {}
            saved_count = 0
            
            for block_id, (slot_id, room_id, course_id) in schedule.items():
                id_dia = slot_id // 1000
                id_hora_entera = slot_id % 1000 
                
                course = next((c for c in data['courses'] if c.id == course_id), None)
                if not course:
                    continue
                
                assignment = next(
                    (a for a in data['professor_course_group_assignments'] 
                     if a.group_id == group_id and a.course_id == course_id), 
                    None
                )
                
                if not assignment:
                    continue
                
                id_profesor = assignment.professor_id
                id_profesor_asignatura = assignment.professor_asignatura_id
                
                dia_str, hora_str_raw = timeslot_map.get(slot_id, ('Desconocido', 'Desconocida'))
                hora_formateada = str(hora_str_raw)[:5] if hora_str_raw else '00:00'
                
                class_info = {
                    "materia": course_map.get(course_id, "Materia Desconocida"),
                    "profesor": professor_map.get(id_profesor, "Profesor Desconocido"),
                    "aula": room_map.get(room_id, "Aula Desconocida"),
                    "edificio": building_map.get(room_id, "N/A")
                }

                if dia_str not in group_schedule_data:
                    group_schedule_data[dia_str] = {}
                
                group_schedule_data[dia_str][hora_formateada] = class_info
                
                try:
                    insert_query = text("""
                        INSERT INTO horario_clases (
                            id_profesor_asignatura, 
                            id_aula, 
                            id_grupo, 
                            dia, 
                            hora 
                        ) 
                        VALUES (
                            :prof_asig, 
                            :aula, 
                            :grupo, 
                            :dia, 
                            :hora
                        )
                    """)
                    
                    db.execute(
                        insert_query,
                        {
                            "prof_asig": id_profesor_asignatura,
                            "aula": room_id,
                            "grupo": group_id,
                            "dia": id_dia,
                            "hora": f"{id_hora_entera}:00:00"
                        }
                    )
                    saved_count += 1
                except Exception as e:
                    print(f"  ❌ Error al insertar clase: {e}")
                    continue
            
            try:
                db.commit()
                print(f"  ✅ {saved_count} clases guardadas para {group.name}")
            except Exception as e:
                db.rollback()
                print(f"  ❌ Error al guardar grupo {group.name}: {e}")
                continue
            
            final_results.append({
                "id": group_id,
                "nombre": group.name,
                "tutor": getattr(group, 'tutor', 'N/A'), 
                "data": group_schedule_data
            })
        
        return final_results 
        
    except HTTPException as e:
        db.rollback() 
        raise e
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error en generación: {str(e)}"
        )


@app.get("/horario-profesor-asignatura/grupos/formateados")
async def obtener_grupos_formateados(db: Session = Depends(get_db)):
    """
    Endpoint para que el Frontend de Vue obtenga los horarios formateados 
    directamente desde la base de datos sin pasar por NestJS.
    """
    try:
        groups_query = text("SELECT id, nombre FROM grupo")
        groups = db.execute(groups_query).fetchall()
        
        professors_query = text("SELECT p.id, p.abreviatura_nombre FROM profesor p")
        professors = {p.id: p.abreviatura_nombre for p in db.execute(professors_query).fetchall()}

        courses_query = text("SELECT a.id, a.nombre FROM asignatura a")
        courses = {c.id: c.nombre for c in db.execute(courses_query).fetchall()}

        rooms_query = text("SELECT al.id, al.nombre FROM aula al")
        rooms_map = {}
        buildings_map = {}
        for r in db.execute(rooms_query).fetchall():
            rooms_map[r.id] = r.nombre
            buildings_map[r.id] = "N/A"

        dias_map = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado"}

        final_results = []

        for group in groups:
            group_id = group.id
            group_name = group.nombre

            clases_query = text("""
                SELECT hc.dia, hc.hora, hc.id_aula, pa.id_asignatura, pa.id_profesor
                FROM horario_clases hc
                JOIN profesor_asignatura pa ON hc.id_profesor_asignatura = pa.id
                WHERE hc.id_grupo = :grupo_id
            """)
            clases = db.execute(clases_query, {"grupo_id": group_id}).fetchall()

            group_schedule_data = {}
            for clase in clases:
                dia_num = clase.dia
                dia_str = dias_map.get(dia_num, "Desconocido")
                
                hora_str = str(clase.hora)[:5] if clase.hora else "00:00"
                
                materia_nombre = courses.get(clase.id_asignatura, "Materia Desconocida")
                profesor_nombre = professors.get(clase.id_profesor, "Profesor Desconocido")
                aula_nombre = rooms_map.get(clase.id_aula, "Aula Desconocida")
                edificio_nombre = buildings_map.get(clase.id_aula, "N/A")

                class_info = {
                    "materia": materia_nombre,
                    "profesor": profesor_nombre,
                    "aula": aula_nombre,
                    "edificio": edificio_nombre
                }

                if dia_str not in group_schedule_data:
                    group_schedule_data[dia_str] = {}
                
                group_schedule_data[dia_str][hora_str] = class_info

            if group_schedule_data:
                final_results.append({
                    "id": group_id,
                    "nombre": group_name,
                    "tutor": "N/A",
                    "publicado": True,
                    "data": group_schedule_data
                })

        return final_results

    except Exception as e:
        print(f"❌ Error al obtener horarios formateados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/horario-profesor-asignatura/profesor/{profesor_id}/publicado")
async def obtener_horario_profesor_publicado(profesor_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para que el Frontend de Vue obtenga el horario formateado de un profesor específico.
    """
    try:
        # 1. Obtener la información del profesor
        prof_query = text("SELECT id, abreviatura_nombre FROM profesor WHERE id = :prof_id")
        prof = db.execute(prof_query, {"prof_id": profesor_id,}).fetchone()
        
        if not prof:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")

        profesor_nombre = prof.abreviatura_nombre

        # 2. Consultar las clases asignadas a este profesor
        clases_query = text("""
            SELECT hc.dia, hc.hora, hc.id_aula, hc.id_grupo, pa.id_asignatura, g.nombre as grupo_nombre
            FROM horario_clases hc
            JOIN profesor_asignatura pa ON hc.id_profesor_asignatura = pa.id
            JOIN grupo g ON hc.id_grupo = g.id
            WHERE pa.id_profesor = :prof_id
        """)
        clases = db.execute(clases_query, {"prof_id": profesor_id}).fetchall()

        dias_map = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado"}
        
        # Consultas de apoyo para nombres
        courses = {c.id: c.nombre for c in db.execute(text("SELECT id, nombre FROM asignatura")).fetchall()}
        rooms_map = {r.id: r.nombre for r in db.execute(text("SELECT id, nombre FROM aula")).fetchall()}

        prof_schedule_data = {}
        for clase in clases:
            dia_str = dias_map.get(clase.dia, "Desconocido")
            hora_str = str(clase.hora)[:5] if clase.hora else "00:00"
            
            materia_nombre = courses.get(clase.id_asignatura, "Materia Desconocida")
            aula_nombre = rooms_map.get(clase.id_aula, "Aula Desconocida")
            grupo_nombre = clase.grupo_nombre

            class_info = {
                "materia": materia_nombre,
                "grupo": grupo_nombre,
                "aula": aula_nombre,
                "colorGrupo": "#88B7F3", # Puedes ajustar o traer el color de tu BD si lo tienes
                "colorMateria": "#e2e8f0"
            }

            if dia_str not in prof_schedule_data:
                prof_schedule_data[dia_str] = {}
            
            if hora_str not in prof_schedule_data[dia_str]:
                prof_schedule_data[dia_str][hora_str] = []
            
            prof_schedule_data[dia_str][hora_str].append(class_info)

        return {
            "id": profesor_id,
            "nombre": profesor_nombre,
            "es_psicologo": False,
            "publicado": True,
            "data": prof_schedule_data
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Error al obtener horario del profesor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Solver Service - Sistema de Generación de Horarios",
        "version": "2.0"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)