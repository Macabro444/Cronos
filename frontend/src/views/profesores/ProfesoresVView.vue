<template>
  <div class="perfil-container-full">
    <nav class="nav">
      <div class="nav-container">
        <router-link to="/profesor" class="nav-figure">
          <img src="../../imagenes/logo.png" class="nav-logo" alt="Logo Cronos" />
        </router-link>

        <label class="nav-toggle" for="menu-input">
          <input type="checkbox" id="menu-input" class="nav-input" />
        </label>

        <ul class="nav-list">
          <li class="nav-item">
            <router-link to="/profesor" class="nav-link">Inicio</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/profesor/perfil" class="nav-link">Perfil</router-link>
          </li>
        </ul>
      </div>
    </nav>

    <main class="main-content">
      <div class="header-section">
        <h1>Mi Horario</h1>
        <p>Consulta tu horario de clases y gestiona tus servicios</p>
      </div>

      <div class="accesos-directos">
        <router-link to="/profesor/asesorias" class="btn-acceso-card">
          <div class="acceso-icon"><i class="fas fa-chalkboard-teacher"></i></div>
          <span>Ver Asesorías</span>
        </router-link>

        <router-link v-if="esPsicologo" to="/profesor/psicologia" class="btn-acceso-card">
          <div class="acceso-icon"><i class="fas fa-brain"></i></div>
          <span>Citas Psicología</span>
        </router-link>

        <router-link to="/profesor/disponibilidad" class="btn-acceso-card">
          <div class="acceso-icon"><i class="fas fa-calendar-alt"></i></div>
          <span>Disponibilidad</span>
        </router-link>
      </div>

      <div v-if="isLoading" class="empty-state-container">
        <div class="empty-card">
          <div class="spinner"></div>
          <p>Cargando horario...</p>
        </div>
      </div>

      <div v-else-if="error" class="empty-state-container">
        <div class="empty-card error-card">
          <i class="fas fa-exclamation-triangle"></i>
          <h3>Error al cargar</h3>
          <p>{{ error }}</p>
          <button @click="cargarHorario" class="btn-primary">Reintentar</button>
        </div>
      </div>

      <div v-else-if="!horarioProfesor" class="empty-state-container">
        <div class="empty-card">
          <i class="fas fa-calendar-times"></i>
          <h3>Horario no disponible</h3>
          <p>Tu horario aún no ha sido generado.</p>
          <p class="text-muted">Por favor, contacta con el coordinador académico.</p>
        </div>
      </div>

      <div v-else-if="horarioProfesor && !isLoading && !error" class="horario-card" :id="`horario-card-${horarioProfesor.id}`">
        <div class="horario-header">
          <div class="horario-info">
            <p class="school-info">
              <b>{{ nombreEscuela }}</b> | Período: <b>{{ periodoCuatrimestral }}</b>
            </p>
            <h2 class="horario-title">Profesor: {{ horarioProfesor.nombre }}</h2>
            <p class="division-info">{{ divisionUniforme }}</p>
          </div>

          <div class="horario-actions">
            <button @click="generarPDFIndividual(horarioProfesor.id, horarioProfesor.nombre)" class="btn-pdf-action">
              <i class="fas fa-file-pdf"></i> PDF
            </button>
          </div>
        </div>

        <div class="leyenda-colores">
          <span class="leyenda-label">Grupos:</span>
          <div class="leyenda-items">
            <div v-for="leyendaItem in getLeyendaIndividual(horarioProfesor)" :key="leyendaItem.nombre" class="leyenda-item">
              <div class="leyenda-color" :style="{ backgroundColor: leyendaItem.color }"></div>
              <span>{{ leyendaItem.nombre }}</span>
            </div>
          </div>
        </div>

        <div class="horario-tabla-wrapper">
          <table class="horario-tabla">
            <thead>
              <tr>
                <th class="hora-col">Hora</th>
                <th v-for="dia in dias" :key="dia">{{ dia.substring(0, 3) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="hora in horas" :key="hora">
                <td class="hora-cell">{{ formatTimeRange(hora) }}</td>
                <td v-for="dia in dias" :key="dia" class="clase-cell" :style="getCeldaStyle(horarioProfesor, dia, hora)">
                  <template v-if="horarioProfesor.data[dia] && horarioProfesor.data[dia][hora]">
                    <div v-for="(clase, idx) in horarioProfesor.data[dia][hora]" :key="idx" class="clase-content" :class="{ 'clase-multiple': idx > 0 }">
                      <div class="clase-materia">{{ clase.materia }}</div>
                      <div class="clase-grupo">{{ clase.grupo }}</div>
                      <div class="clase-aula">{{ clase.aula }}</div>
                    </div>
                  </template>
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
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import '../../assets/styles.css';

const router = useRouter();
const nombreEscuela = ref('UTEQ');
const periodoCuatrimestral = ref('AGO-DIC 2025');
const divisionUniforme = ref('INGENIERÍA');
const dias = ref(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']);
const horas = ref(['17:00', '18:00', '19:00', '20:00', '21:00']);

const isLoading = ref(false);
const error = ref(null);
const horarioProfesor = ref(null);
const esPsicologoReal = ref(false);
const esPsicologo = computed(() => esPsicologoReal.value === true);

const NESTJS_API = `http://localhost:8000`; // Apunta al puerto correcto de FastAPI

const obtenerIdProfesor = () => {
  // 1. Prioridad: id_rol del localStorage
  const idRol = localStorage.getItem('id_rol');
  if (idRol) {
    console.log('ID obtenido desde id_rol:', idRol);
    return idRol;
  }

  // 2. Fallback: JWT sub
  const token = localStorage.getItem('access_token');
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload?.sub) {
        console.log('ID obtenido desde JWT (sub):', payload.sub);
        return payload.sub;
      }
    } catch (e) {
      console.warn('No se pudo decodificar el token JWT:', e);
    }
  }

  // 3. Último fallback: id directo
  const id = localStorage.getItem('id');
  if (id) {
    console.log('ID obtenido desde id:', id);
    return id;
  }

  // 4. Fallback de emergencia para pruebas (ej. profesor con ID 3)
  console.warn('No se encontró ID en localStorage, usando ID por defecto (3)');
  return 3; 
};

const cargarHorario = async () => {
  isLoading.value = true;
  error.value = null;

  const idProfesor = obtenerIdProfesor();

  if (!idProfesor) {
    error.value = "No se pudo identificar al profesor. Por favor, inicia sesión nuevamente.";
    isLoading.value = false;
    return;
  }

  try {
    const response = await fetch(`${NESTJS_API}/horario-profesor-asignatura/profesor/${idProfesor}/publicado`);

    if (!response.ok) {
      if (response.status === 404) {
        horarioProfesor.value = null;
        esPsicologoReal.value = false;
      } else {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      return;
    }

    const data = await response.json();
    esPsicologoReal.value = data.es_psicologo || false;

    horarioProfesor.value = {
      id: data.id,
      nombre: data.nombre,
      data: {}
    };

    dias.value.forEach(d => horarioProfesor.value.data[d] = {});

    if (data.data) {
      Object.keys(data.data).forEach(d => {
        Object.keys(data.data[d]).forEach(h => {
          horarioProfesor.value.data[d][h] = Array.isArray(data.data[d][h])
            ? data.data[d][h]
            : [data.data[d][h]];
        });
      });
    }
  } catch (e) {
    console.error('Error al cargar horario:', e);
    error.value = "Error al conectar con el servidor";
    esPsicologoReal.value = false;
  } finally {
    isLoading.value = false;
  }
};

const getCeldaStyle = (item, dia, hora) => {
  const clase = item?.data?.[dia]?.[hora];
  if (!clase || !clase.length) return {};
  const c = clase[0];
  const bgColor = c.colorGrupo || '#88B7F3';
  const r = parseInt(bgColor.slice(1, 3), 16);
  const g = parseInt(bgColor.slice(3, 5), 16);
  const b = parseInt(bgColor.slice(5, 7), 16);
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  return {
    backgroundColor: bgColor,
    borderLeft: `4px solid ${c.colorMateria || '#e2e8f0'}`,
    color: brightness > 125 ? '#1e293b' : '#ffffff'
  };
};

const getLeyendaIndividual = (item) => {
  if (!item || !item.data) return [];
  const itemsMap = new Map();
  Object.values(item.data).forEach(dia => {
    if (dia) {
      Object.values(dia).forEach(clases => {
        if (Array.isArray(clases)) {
          clases.forEach(clase => {
            if (clase && clase.grupo) {
              itemsMap.set(clase.grupo, {
                nombre: clase.grupo,
                color: clase.colorGrupo
              });
            }
          });
        }
      });
    }
  });
  return Array.from(itemsMap.values());
};

onMounted(() => {
  cargarHorario();
});

const formatTimeRange = (startHour) => {
  if (!startHour || !startHour.includes(':')) return startHour;
  const [h, m] = startHour.split(':').map(Number);
  const end = h * 60 + m + 60;
  const eh = String(Math.floor(end / 60) % 24).padStart(2, '0');
  const em = String(end % 60).padStart(2, '0');
  return `${startHour} - ${eh}:${em}`;
};

const generarPDFIndividual = async (id, nombre) => {
  const el = document.getElementById(`horario-card-${id}`);
  if (!el) return;
  const actions = el.querySelector('.horario-actions');
  if (actions) actions.style.visibility = 'hidden';
  try {
    const canvas = await html2canvas(el, { scale: 3, useCORS: true, backgroundColor: '#ffffff' });
    const pdf = new jsPDF('l', 'mm', 'a4');
    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 297, 210);
    pdf.save(`Horario_Profesor_${nombre}.pdf`);
  } finally {
    if (actions) actions.style.visibility = 'visible';
  }
};
</script>

<style scoped>
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

.empty-state-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-card {
  background: white;
  border-radius: 24px;
  padding: 50px 40px;
  text-align: center;
  max-width: 450px;
  width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
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
}

.empty-card .text-muted {
  font-size: 0.85rem;
  color: #94a3b8;
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
}

.horario-card {
  background: white;
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
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
}

.leyenda-colores {
  background: #f8fafc;
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.leyenda-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
}

.leyenda-items {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.leyenda-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
}

.leyenda-color {
  width: 14px;
  height: 14px;
  border-radius: 4px;
}

.horario-tabla-wrapper {
  overflow-x: auto;
}

.horario-tabla {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.horario-tabla th {
  background: #f1f5f9;
  padding: 12px;
  text-align: center;
  font-weight: 600;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.horario-tabla td {
  padding: 10px;
  text-align: center;
  border: 1px solid #e2e8f0;
  vertical-align: middle;
}

.hora-col {
  width: 100px;
}

.hora-cell {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
}

.clase-cell {
  transition: all 0.2s;
}

.clase-content {
  text-align: center;
}

.clase-materia {
  font-weight: 700;
  font-size: 0.75rem;
}

.clase-grupo, .clase-aula {
  font-size: 0.7rem;
  opacity: 0.8;
}

.clase-multiple {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .main-content {
    padding: 20px 15px;
  }

  .btn-acceso-card {
    width: 100%;
  }

  .horario-card {
    padding: 20px;
  }

  .horario-header {
    flex-direction: column;
  }

  .hora-col {
    width: 80px;
  }
}
</style>