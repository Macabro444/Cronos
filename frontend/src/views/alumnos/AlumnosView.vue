<template>
  <div class="perfil-container-full">
    <nav class="nav">
      <div class="nav-container">
        <router-link to="/alumno" class="nav-figure">
          <img src="../../imagenes/logo.png" class="nav-logo" alt="Logo Cronos" />
        </router-link>

        <label class="nav-toggle" for="menu-input">
          <input type="checkbox" id="menu-input" class="nav-input" />
        </label>

        <ul class="nav-list">
          <li class="nav-item">
            <router-link to="/alumno" class="nav-link">Inicio</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/alumno/perfil" class="nav-link">Perfil</router-link>
          </li>
        </ul>
      </div>
    </nav>

    <main class="main-content">
      <div class="header-section">
        <h1>Mi Horario</h1>
        <p>Consulta tu horario de clases y accede a servicios académicos</p>
      </div>

      <div class="accesos-directos">
        <router-link to="/alumno/agendar-asesoria" class="btn-acceso-card">
          <div class="acceso-icon"><i class="fas fa-chalkboard-teacher"></i></div>
          <span>Agendar Asesoría</span>
        </router-link>

        <router-link to="/alumno/agendar-psicologia" class="btn-acceso-card">
          <div class="acceso-icon"><i class="fas fa-brain"></i></div>
          <span>Cita Psicología</span>
        </router-link>
      </div>

      <!-- LOADING -->
      <div v-if="isLoading" class="empty-state-container">
        <div class="empty-card">
          <div class="spinner"></div>
          <p>Cargando horario...</p>
        </div>
      </div>

      <!-- ERROR -->
      <div v-else-if="error" class="empty-state-container">
        <div class="empty-card error-card">
          <i class="fas fa-exclamation-triangle"></i>
          <h3>Error al cargar</h3>
          <p>{{ error }}</p>
          <button @click="cargarHorario" class="btn-primary">Reintentar</button>
        </div>
      </div>

      <!-- SIN GRUPO ASIGNADO -->
      <div v-else-if="!grupoAlumno" class="empty-state-container">
        <div class="empty-card">
          <i class="fas fa-users-slash"></i>
          <h3>Sin grupo asignado</h3>
          <p>No tienes un grupo asignado actualmente.</p>
          <p class="text-muted">Por favor, contacta con el departamento de control escolar.</p>
        </div>
      </div>

      <!-- HORARIO NO PUBLICADO -->
      <div v-else-if="!horarioPublicado" class="empty-state-container">
        <div class="empty-card">
          <i class="fas fa-calendar-times"></i>
          <h3>Horario no disponible</h3>
          <p>Tu horario aún no ha sido publicado.</p>
          <p class="text-muted">Por favor, contacta con tu coordinador académico.</p>
        </div>
      </div>

      <!-- HORARIO PUBLICADO -->
      <div v-else-if="horarioPublicado && horarioData" class="horario-card">
        <div class="horario-header">
          <div class="horario-info">
            <p class="school-info">
              <b>{{ nombreEscuela }}</b> | Período: <b>{{ periodoCuatrimestral }}</b>
            </p>
            <h2 class="horario-title">Grupo: {{ horarioData.nombre }}</h2>
            <div class="meta-info">
              <p class="tutor-badge">Tutor: <b>{{ horarioData.tutor }}</b></p>
              <p class="division-badge">{{ divisionUniforme }}</p>
            </div>
          </div>
          
          <div class="horario-actions">
            <button @click="generarPDFIndividual" class="btn-pdf-action">
              <i class="fas fa-file-pdf"></i> PDF
            </button>
          </div>
        </div>

        <div class="leyenda-colores-container">
          <h4 class="leyenda-label">Materias:</h4>
          <div class="leyenda-flex">
            <div v-for="leyendaItem in leyendaMaterias" :key="leyendaItem.nombre" class="leyenda-pill">
              <div class="color-dot" :style="{ backgroundColor: leyendaItem.color }"></div>
              <span class="pill-text">{{ leyendaItem.nombre }}</span>
            </div>
          </div>
        </div>

        <div class="horario-tabla-container">
          <table class="horario-grid">
            <thead>
              <tr>
                <th class="hora-column">Hora</th>
                <th v-for="dia in dias" :key="dia" class="dia-column">{{ dia.substring(0, 3) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="hora in horas" :key="hora">
                <td class="hora-cell">{{ formatTimeRange(hora) }}</td>
                <td 
                  v-for="dia in dias" 
                  :key="dia"
                  class="clase-cell"
                  :style="getCeldaStyle(dia, hora)"
                >
                  <template v-if="horarioData.data[dia] && horarioData.data[dia][hora]">
                    <div class="clase-content">
                      <div class="clase-materia">{{ horarioData.data[dia][hora].materia }}</div>
                      <div class="clase-profesor">{{ horarioData.data[dia][hora].profesor.split(' ')[0] }}</div>
                      <div class="clase-aula"><i class="fas fa-map-marker-alt"></i> {{ horarioData.data[dia][hora].aula }}</div>
                    </div>
                  </template>
                  <div v-else class="clase-empty"></div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import '../../assets/styles.css';

const nombreEscuela = ref('UTEQ');
const periodoCuatrimestral = ref('AGO-DIC 2025');
const divisionUniforme = ref('INGENIERÍA');
const dias = ref(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']);
const horas = ref(['17:00', '18:00', '19:00', '20:00', '21:00']);

const isLoading = ref(false);
const error = ref(null);
const horarioData = ref(null);
const horarioPublicado = ref(false);
const grupoAlumno = ref(null);

// Definimos la URL base de tu API y las rutas
const NESTJS_API = 'http://localhost:8000';// Ajusta el puerto si es necesario
const API_ESTUDIANTES = '/api/estudiantes';
const API_GRUPOS = '/api/v1/grupos';

const obtenerIdAlumnoDesdeLocalStorage = () => {
  const idRol = localStorage.getItem('id_rol');
  if (!idRol) throw new Error('No hay id_rol en localStorage');
  return parseInt(idRol);
};

const obtenerGrupoAlumno = async () => {
  // Asignamos directamente el grupo 7 para que cargue tu horario de inmediato
  const idGrupo = 7; 
  grupoAlumno.value = idGrupo;
  console.log("ID Grupo forzado:", idGrupo);
  return idGrupo;
};

const cargarHorario = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const idGrupo = await obtenerGrupoAlumno();
    console.log("ID Grupo del alumno:", idGrupo);

    if (!idGrupo) { 
      isLoading.value = false; 
      return; 
    }

    const response = await fetch(`${NESTJS_API}/horario-profesor-asignatura/grupos/formateados`);
    if (!response.ok) throw new Error('Error al obtener los horarios formateados');
    
    const todosLosHorarios = await response.json();
    console.log("Todos los horarios recibidos:", todosLosHorarios);

    const horarioGrupo = todosLosHorarios.find(h => Number(h.id) === Number(idGrupo) || Number(h.id_grupo) === Number(idGrupo));

    if (!horarioGrupo) { 
      console.warn("No se encontró un horario para el grupo ID:", idGrupo);
      horarioPublicado.value = false; 
      return; 
    }

    horarioData.value = horarioGrupo;
    horarioPublicado.value = Boolean(horarioGrupo.publicado);

    console.log("Horario data asignado:", horarioData.value);
    console.log("¿Está publicado?:", horarioPublicado.value);

  } catch (err) { 
    console.error(err);
    error.value = `Error al conectar con el servidor`; 
  } finally { 
    isLoading.value = false; 
  }
};

onMounted(() => cargarHorario());

const getCeldaStyle = (dia, hora) => {
  const clase = horarioData.value?.data[dia]?.[hora];
  if (!clase) return {};
  return {
    backgroundColor: clase.colorMateria || '#f1f5f9',
    borderLeft: `6px solid ${clase.colorGrupo || '#88B7F3'}`,
    color: getTextColor(clase.colorMateria || '#f1f5f9')
  };
};

const getTextColor = (bgColor) => {
  const color = bgColor.replace('#', '');
  const r = parseInt(color.substr(0, 2), 16);
  const g = parseInt(color.substr(2, 2), 16);
  const b = parseInt(color.substr(4, 2), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? '#1e293b' : '#FFFFFF';
};

const leyendaMaterias = computed(() => {
  if (!horarioData.value) return [];
  const materiasMap = new Map();
  Object.values(horarioData.value.data).forEach(dia => {
    Object.values(dia).forEach(clase => {
      if (clase?.materia) materiasMap.set(clase.materia, { nombre: clase.materia, color: clase.colorMateria });
    });
  });
  return Array.from(materiasMap.values()).sort((a, b) => a.nombre.localeCompare(b.nombre));
});

const formatTimeRange = (start) => {
  if (!start.includes(':')) return start;
  const [h, m] = start.split(':').map(Number);
  const eh = String(Math.floor((h * 60 + m + 60) / 60) % 24).padStart(2, '0');
  const em = String((h * 60 + m + 60) % 60).padStart(2, '0');
  return `${start} - ${eh}:${em}`;
};

const generarPDFIndividual = async () => {
  const el = document.querySelector('.horario-card');
  if (!el) return;
  const actions = el.querySelector('.horario-actions');
  if (actions) actions.style.visibility = 'hidden';
  try {
    const canvas = await html2canvas(el, { scale: 3, useCORS: true, backgroundColor: '#ffffff' });
    const pdf = new jsPDF('l', 'mm', 'a4');
    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 297, 210);
    pdf.save(`Horario_${horarioData.value.nombre}.pdf`);
  } finally {
    if (actions) actions.style.visibility = 'visible';
  }
};
</script>

<style scoped>
/* =======================
   HOME ALUMNO - CON ESTADOS CENTRADOS
======================= */

.perfil-container-full {
  background: #e3f2fd;
  min-height: 100vh;
  width: 100%;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

.header-section h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 5px;
}

.header-section p {
  color: #7f8c8d;
}

/* ACCESOS DIRECTOS */
.accesos-directos {
  display: flex;
  gap: 20px;
  margin-bottom: 40px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-acceso-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: white;
  padding: 25px;
  border-radius: 20px;
  width: 180px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  text-decoration: none;
  border: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

.btn-acceso-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 30px rgba(58, 190, 249, 0.15);
}

.acceso-icon {
  font-size: 2.5rem;
  color: #3abef9;
  margin-bottom: 12px;
}

.btn-acceso-card span {
  font-weight: 700;
  color: #2c3e50;
  font-size: 0.9rem;
}

/* =======================
   ESTADOS VACÍOS - CENTRADOS Y BONITOS
======================= */

.empty-state-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  width: 100%;
}

.empty-card {
  background: white;
  border-radius: 24px;
  padding: 50px 40px;
  text-align: center;
  max-width: 450px;
  width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
}

.empty-card i {
  font-size: 4rem;
  color: #cbd5e1;
  margin-bottom: 20px;
}

.empty-card h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 12px;
}

.empty-card p {
  color: #7f8c8d;
  margin-bottom: 8px;
}

.empty-card .text-muted {
  font-size: 0.85rem;
  color: #94a3b8;
}

.empty-card.error-card i {
  color: #ef4444;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e2e8f0;
  border-top-color: #3abef9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-primary {
  background: #3abef9;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 20px;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #29a9e0;
}

/* =======================
   TARJETA HORARIO
======================= */

.horario-card {
  background: white;
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
}

.horario-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eef2f6;
}

.horario-info {
  flex: 1;
}

.school-info {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 8px;
}

.horario-title {
  font-size: 1.5rem;
  color: #2c3e50;
  margin: 5px 0;
  font-weight: 700;
}

.meta-info {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.tutor-badge {
  font-size: 0.85rem;
  color: #64748b;
}

.division-badge {
  background: #e1f5fe;
  color: #039be5;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
}

.btn-pdf-action {
  background: #ef4444;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-pdf-action:hover {
  background: #dc2626;
}

/* LEYENDA */
.leyenda-colores-container {
  background: #f8fafc;
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 25px;
}

.leyenda-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  margin-bottom: 10px;
  font-weight: 700;
}

.leyenda-flex {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.leyenda-pill {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 5px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 4px;
}

.pill-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
}

/* TABLA HORARIO */
.horario-tabla-container {
  overflow-x: auto;
  width: 100%;
}

.horario-grid {
  width: 100%;
  border-collapse: separate;
  border-spacing: 6px;
  table-layout: fixed;
}

.hora-column {
  width: 100px;
}

.dia-column {
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.7rem;
  padding: 10px;
  text-align: center;
}

.hora-cell {
  background: #f1f5f9;
  color: #475569;
  font-weight: 600;
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  height: 85px;
}

.clase-cell {
  border-radius: 10px;
  padding: 10px;
  text-align: center;
  vertical-align: middle;
  height: 85px;
}

.clase-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

.clase-materia {
  font-weight: 700;
  font-size: 0.8rem;
  margin-bottom: 3px;
}

.clase-profesor {
  font-size: 0.7rem;
  opacity: 0.8;
}

.clase-aula {
  font-size: 0.65rem;
  margin-top: 3px;
  opacity: 0.7;
}

.clase-empty {
  height: 100%;
}

/* RESPONSIVE */
@media (max-width: 768px) {
  .main-content {
    padding: 20px 15px;
  }
  
  .horario-card {
    padding: 20px;
  }
  
  .horario-header {
    flex-direction: column;
  }
  
  .hora-column {
    width: 80px;
  }
  
  .clase-cell, .hora-cell {
    height: auto;
    min-height: 70px;
  }
  
  .btn-acceso-card {
    width: 100%;
  }
  
  .header-section h1 {
    font-size: 1.5rem;
  }
  
  .empty-card {
    padding: 35px 25px;
  }
  
  .empty-card h3 {
    font-size: 1.25rem;
  }
}
</style>