<template>
  <div>
    <nav class="nav">
      <div class="nav-container">
        <router-link to="/dashboard" class="nav-figure">
          <img src="../../imagenes/logo.png" class="nav-logo" alt="Logo Cronos" />
        </router-link>
        <label class="nav-toggle" for="menu-input">
          <input type="checkbox" id="menu-input" class="nav-input" />
        </label>
        <ul class="nav-list">
          <li class="nav-item"><router-link to="/dashboard" class="nav-link">Panel de control</router-link></li>
          <li class="nav-item"><router-link :to="{ name: 'perfil-admin' }" class="nav-link">Perfil</router-link></li>
        </ul>
      </div>
    </nav>

    <main class="horarios-main">
      <!-- HEADER CON BOTÓN REGRESAR -->
      <div class="horarios-header">
        <button @click="goBack" class="btn-back-icon" title="Volver al Dashboard">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div class="header-text">
          <h1>Gestión de Horarios</h1>
          <p>Genera, publica y administra los horarios académicos</p>
        </div>
        <div class="header-spacer"></div>
      </div>

      <div class="horarios-card">
        <!-- HEADER CON CONTROLES -->
        <div class="header-actions">
          <button @click="generarHorarios" :disabled="isLoading" class="btn-primary">
            <i class="fas fa-sync-alt"></i>
            <span v-if="isLoading">Procesando...</span>
            <span v-else>Generar Nuevos Horarios</span>
          </button>

          <button @click="togglePublicarTodos" :disabled="!horariosGenerados || isLoading" class="btn-secondary">
            <i class="fas fa-globe"></i>
            <span v-if="todosPublicados">Dar de baja todos</span>
            <span v-else>Publicar todos</span>
          </button>

          <button @click="generarPDFMasivo" :disabled="datosFiltrados.length === 0 || !horariosGenerados || isLoading" class="btn-secondary">
            <i class="fas fa-download"></i>
            Descargar Todos (PDF)
          </button>
        </div>

        <!-- SELECTOR DE VISTA CON PESTAÑAS -->
        <div class="vista-selector">
          <button class="vista-tab" :class="{ active: vistaActual === 'grupos' }" @click="vistaActual = 'grupos'">
            Grupos
          </button>
          <button class="vista-tab" :disabled="!horariosGenerados || isLoading" :class="{ active: vistaActual === 'profesores' }" @click="vistaActual = 'profesores'">
            Profesores
          </button>
        </div>

        <!-- FILTRO DE BÚSQUEDA -->
        <div class="search-container">
          <i class="fas fa-search search-icon"></i>
          <input type="text" v-model="searchTerm" :placeholder="vistaActual === 'grupos' 
            ? 'Buscar por grupo, tutor, materia o profesor...' 
            : 'Buscar por profesor, materia, aula o grupo...'" class="search-input" />
        </div>

        <!-- MENSAJE INICIAL (Sin datos) -->
        <div v-if="!horariosGenerados && !isLoading" class="empty-state">
          <div class="empty-content">
            <i class="fas fa-calendar-times"></i>
            <h3>No hay horarios generados</h3>
            <p>Haz clic en <strong>"Generar Nuevos Horarios"</strong> para crear los horarios del período.</p>
          </div>
        </div>

        <!-- LOADING -->
        <div v-if="isLoading" class="loading-container">
          <div class="spinner"></div>
          <p>Cargando horarios... Por favor espera.</p>
        </div>

        <!-- ERROR -->
        <div v-if="error" class="error-state">
          <i class="fas fa-exclamation-triangle"></i>
          <p>{{ error }}</p>
          <button @click="cargarHorarios" class="btn-primary">Reintentar</button>
        </div>

        <!-- CONTENIDO: HORARIOS -->
        <template v-if="horariosGenerados && !isLoading && !error">
          <p v-if="datosFiltrados.length === 0 && searchTerm" class="no-results-text">
            No se encontraron resultados para "{{ searchTerm }}"
          </p>

          <div class="horarios-cards-wrapper">
            <div v-for="item in datosFiltrados" :key="item.id" class="horario-item" :class="{ 'horario-publicado': item.publicado }" :id="`horario-card-${item.id}`">
              
              <!-- HEADER DE LA TARJETA -->
              <div class="horario-item-header">
                <div class="horario-item-info">
                  <p class="school-info">
                    <b>{{ nombreEscuela }}</b> | Período: <b>{{ periodoCuatrimestral }}</b>
                  </p>
                  <h3 v-if="vistaActual === 'grupos'" class="horario-item-title">
                    Grupo: {{ item.nombre }}
                  </h3>
                  <h3 v-else class="horario-item-title">Profesor: {{ item.nombre }}</h3>
                  
                  <p class="tutor-info" v-if="vistaActual === 'grupos'">
                    Tutor: <b>{{ item.tutor }}</b>
                  </p>
                  <p class="division-info">{{ divisionUniforme }}</p>
                </div>
                
                <div class="horario-item-actions">
                  <button @click="generarPDFIndividual(item.id, item.nombre)" class="btn-pdf">
                    <i class="fas fa-file-pdf"></i> PDF
                  </button>

                  <button v-if="vistaActual === 'grupos'" @click="togglePublicarGrupo(item.id, item.publicado)" class="btn-publicar" :class="item.publicado ? 'btn-publicado' : 'btn-no-publicado'">
                    <i :class="item.publicado ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                    <span v-if="item.publicado">Dar de baja</span>
                    <span v-else>Publicar</span>
                  </button>
                </div>
              </div>

              <!-- LEYENDA DE COLORES -->
              <div class="leyenda-colores">
                <span class="leyenda-label">{{ vistaActual === 'grupos' ? 'Materias:' : 'Grupos:' }}</span>
                <div class="leyenda-items">
                  <div v-for="leyendaItem in getLeyendaIndividual(item)" :key="leyendaItem.nombre" class="leyenda-item">
                    <div class="leyenda-color" :style="{ backgroundColor: leyendaItem.color }"></div>
                    <span>{{ leyendaItem.nombre }}</span>
                  </div>
                </div>
              </div>

              <!-- TABLA DE HORARIO -->
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
                      
                      <td v-for="dia in dias" :key="dia" class="clase-cell" :style="getCeldaStyle(item, dia, hora)">
                        <template v-if="vistaActual === 'grupos'">
                          <div v-if="item.data[dia] && item.data[dia][hora]" class="clase-info">
                            <div class="clase-materia">{{ item.data[dia][hora].materia }}</div>
                            <div class="clase-profesor">{{ item.data[dia][hora].profesor.split(' ')[0] }}</div>
                            <div class="clase-aula">{{ item.data[dia][hora].aula }}</div>
                          </div>
                        </template>

                        <template v-else>
                          <div v-if="item.data[dia] && item.data[dia][hora]" v-for="(clase, idx) in item.data[dia][hora]" :key="idx" class="clase-info" :class="{ 'clase-multiple': idx > 0 }">
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
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import '../../assets/styles.css';

const router = useRouter()

const goBack = () => {
  router.back()
}

const nombreEscuela = ref('UTEQ');
const periodoCuatrimestral = ref('AGO-DIC 2025');
const divisionUniforme = ref('INGENIERÍA');
const dias = ref(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']);
const horas = ref(['17:00', '18:00', '19:00', '20:00', '21:00']);

const vistaActual = ref('grupos');
const searchTerm = ref('');
const isLoading = ref(false);
const error = ref(null);
const horariosGenerados = ref(false);
const horariosGruposData = ref([]);

// Apuntando directo al puerto 8000 de tu servicio Python
const SOLVER_API = `http://localhost:8000`;

const todosPublicados = computed(() => {
  if (!horariosGruposData.value.length) return false;
  return horariosGruposData.value.every(grupo => grupo.publicado === true);
});

const togglePublicarTodos = async () => {
  const nuevoEstado = !todosPublicados.value;
  // Nota: Si la funcionalidad de publicar requiere endpoints específicos que mantenías en NestJS, 
  // asegúrate de ajustar esa URL. De lo contrario, puedes gestionarlo de manera local o con su respectivo servicio.
  horariosGruposData.value = horariosGruposData.value.map(grupo => ({ ...grupo, publicado: nuevoEstado }));
};

const togglePublicarGrupo = async (id_grupo, estadoActual) => {
  const nuevoEstado = !estadoActual;
  const index = horariosGruposData.value.findIndex(g => g.id === id_grupo);
  if (index !== -1) horariosGruposData.value[index].publicado = nuevoEstado;
};

const getTextColor = (bgColor) => {
  if (!bgColor || bgColor === 'transparent') return '#213547';
  const color = bgColor.replace('#', '');
  const r = parseInt(color.substr(0, 2), 16);
  const g = parseInt(color.substr(2, 2), 16);
  const b = parseInt(color.substr(4, 2), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? '#213547' : '#FFFFFF';
};

const getCeldaStyle = (item, dia, hora) => {
  const clase = item.data[dia]?.[hora];
  if (!clase) return {};
  if (vistaActual.value === 'grupos') {
    return {
      backgroundColor: clase.colorMateria || '#F0F4F8',
      borderLeft: `4px solid ${clase.colorGrupo || '#88B7F3'}`,
      color: getTextColor(clase.colorMateria || '#F0F4F8')
    };
  }
  if (Array.isArray(clase) && clase.length > 0) {
    const primeraClase = clase[0];
    return {
      backgroundColor: primeraClase.colorGrupo || '#F0F4F8',
      borderLeft: `4px solid ${primeraClase.colorMateria || '#88B7F3'}`,
      color: getTextColor(primeraClase.colorGrupo || '#F0F4F8')
    };
  }
  return {};
};

const getLeyendaIndividual = (item) => {
  const itemsMap = new Map();
  if (vistaActual.value === 'grupos') {
    Object.values(item.data).forEach(dia => {
      Object.values(dia).forEach(clase => {
        if (clase && clase.materia && clase.colorMateria) {
          itemsMap.set(clase.materia, { nombre: clase.materia, color: clase.colorMateria });
        }
      });
    });
  } else {
    Object.values(item.data).forEach(dia => {
      Object.values(dia).forEach(clases => {
        if (Array.isArray(clases)) {
          clases.forEach(clase => {
            if (clase && clase.grupo && clase.colorGrupo) {
              itemsMap.set(clase.grupo, { nombre: clase.grupo, color: clase.colorGrupo });
            }
          });
        }
      });
    });
  }
  return Array.from(itemsMap.values()).sort((a, b) => a.nombre.localeCompare(b.nombre));
};

const generarHorarios = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    // 1. Llama a Python para generar y guardar en base de datos
    await fetch(`${SOLVER_API}/generate`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({}) 
    });
    
    // 2. Consulta los datos formateados directamente desde el nuevo endpoint de Python
    const response = await fetch(`${SOLVER_API}/horario-profesor-asignatura/grupos/formateados`);
    const data = await response.json();
    
    horariosGruposData.value = data;
    horariosGenerados.value = data.length > 0;
    if (data.length === 0) error.value = 'No se generaron horarios.';
  } catch (err) {
    error.value = `Error: ${err.message}`;
  } finally {
    isLoading.value = false;
  }
};

const cargarHorarios = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const response = await fetch(`${SOLVER_API}/horario-profesor-asignatura/grupos/formateados`);
    const data = await response.json();
    horariosGruposData.value = data;
    horariosGenerados.value = data.length > 0;
  } catch (err) {
    console.error('Error al cargar:', err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => cargarHorarios());

const horariosProfesores = computed(() => {
  const map = new Map();
  horariosGruposData.value.forEach(grupo => {
    Object.keys(grupo.data).forEach(dia => {
      Object.keys(grupo.data[dia]).forEach(hora => {
        const clase = grupo.data[dia][hora];
        if (!clase) return;
        const clases = Array.isArray(clase) ? clase : [clase];
        clases.forEach(c => {
          const nombre = c.profesor;
          if (!map.has(nombre)) {
            map.set(nombre, { nombre, id: nombre.replace(/\s/g, '_').replace(/[^\w]/g, ''), data: {} });
          }
          const prof = map.get(nombre);
          if (!prof.data[dia]) prof.data[dia] = {};
          if (!prof.data[dia][hora]) prof.data[dia][hora] = [];
          prof.data[dia][hora].push({
            materia: c.materia, aula: c.aula, grupo: grupo.nombre,
            colorMateria: c.colorMateria, colorGrupo: c.colorGrupo
          });
        });
      });
    });
  });
  return Array.from(map.values()).sort((a, b) => a.nombre.localeCompare(b.nombre));
});

const datosActuales = computed(() => vistaActual.value === 'grupos' ? horariosGruposData.value : horariosProfesores.value);

const datosFiltrados = computed(() => {
  if (!searchTerm.value.trim()) return datosActuales.value;
  const q = searchTerm.value.toLowerCase().trim();
  return datosActuales.value.filter(item => {
    if (item.nombre.toLowerCase().includes(q)) return true;
    if (item.tutor?.toLowerCase().includes(q)) return true;
    for (const dia of Object.values(item.data)) {
      for (const hora in dia) {
        const clases = Array.isArray(dia[hora]) ? dia[hora] : [dia[hora]];
        if (clases.some(c => c?.materia?.toLowerCase().includes(q) || c?.profesor?.toLowerCase().includes(q) || c?.aula?.toLowerCase().includes(q) || c?.grupo?.toLowerCase().includes(q))) return true;
      }
    }
    return false;
  });
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
  const actionsContainer = el.querySelector('.horario-item-actions');
  if (actionsContainer) actionsContainer.style.display = 'none';
  try {
    await new Promise(resolve => setTimeout(resolve, 100));
    const canvas = await html2canvas(el, { scale: 3, useCORS: true, backgroundColor: '#ffffff' });
    const pdf = new jsPDF('l', 'mm', 'a4');
    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 297, 210);
    pdf.save(`Horario_${nombre}.pdf`);
  } finally {
    if (actionsContainer) actionsContainer.style.display = '';
  }
};

const generarPDFMasivo = async () => {
  if (!datosFiltrados.value.length) return;
  const pdf = new jsPDF('l', 'mm', 'a4');
  const allActions = document.querySelectorAll('.horario-item-actions');
  const originalStates = Array.from(allActions).map(el => ({ element: el, display: el.style.display }));
  allActions.forEach(el => el.style.display = 'none');
  try {
    await new Promise(resolve => setTimeout(resolve, 100));
    let firstPage = true;
    for (const item of datosFiltrados.value) {
      const el = document.getElementById(`horario-card-${item.id}`);
      if (!el) continue;
      const canvas = await html2canvas(el, { scale: 3, useCORS: true, backgroundColor: '#ffffff' });
      if (!firstPage) pdf.addPage();
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 297, 210);
      firstPage = false;
    }
    pdf.save(`Horarios_${vistaActual.value === 'grupos' ? 'Grupos' : 'Profesores'}.pdf`);
  } finally {
    originalStates.forEach(state => state.element.style.display = state.display);
  }
};
</script>

<style scoped>
/* =======================
   GESTIÓN DE HORARIOS - CON BOTÓN REGRESAR
======================= */

.horarios-main {
  max-width: 1400px;
  margin: 40px auto;
  padding: 0 20px;
}

/* Header con botón a la izquierda y título centrado */
.horarios-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  position: relative;
}

.btn-back-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: white;
  color: #3abef9;
  border-radius: 50%;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  cursor: pointer;
  flex-shrink: 0;
}

.btn-back-icon i {
  font-size: 1rem;
  transition: transform 0.3s ease;
}

.btn-back-icon:hover {
  background: #3abef9;
  color: white;
  border-color: #3abef9;
  transform: translateX(-3px);
  box-shadow: 0 4px 10px rgba(58, 190, 249, 0.25);
}

.btn-back-icon:hover i {
  transform: translateX(-2px);
}

.header-text {
  flex: 1;
  text-align: center;
}

.header-text h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 5px;
}

.header-text p {
  color: #7f8c8d;
  margin: 0;
}

.header-spacer {
  width: 40px;
  flex-shrink: 0;
}

.horarios-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  padding: 30px;
  border: 1px solid #eef2f6;
}

/* HEADER ACTIONS */
.header-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eef2f6;
}

.header-actions button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

/* VISTA SELECTOR */
.vista-selector {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 25px;
}

.vista-tab {
  padding: 10px 30px;
  background: #f1f5f9;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  font-weight: 600;
  color: #64748b;
  transition: all 0.2s;
}

.vista-tab.active {
  background: #88B7F3;
  color: white;
}

.vista-tab:hover:not(.active) {
  background: #e2e8f0;
}

/* BÚSQUEDA */
.search-container {
  position: relative;
  max-width: 400px;
  margin: 0 auto 30px;
}

.search-icon {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
}

.search-input {
  width: 100%;
  padding: 12px 15px 12px 45px;
  border: 1px solid #e2e8f0;
  border-radius: 30px;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #88B7F3;
  box-shadow: 0 0 0 3px rgba(136, 183, 243, 0.1);
}

/* HORARIOS CARDS */
.horarios-cards-wrapper {
  display: flex;
  flex-direction: column;
  gap: 30px;
  margin-top: 20px;
}

.horario-item {
  background: #f8fafc;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #eef2f6;
  transition: all 0.2s;
}

.horario-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.horario-publicado {
  border-left: 4px solid #88B7F3;
}

/* HEADER DEL HORARIO */
.horario-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eef2f6;
}

.horario-item-info {
  flex: 1;
}

.school-info {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 8px;
}

.horario-item-title {
  font-size: 1.3rem;
  color: #2c3e50;
  margin: 5px 0;
}

.tutor-info, .division-info {
  font-size: 0.85rem;
  color: #64748b;
  margin: 3px 0;
}

.horario-item-actions {
  display: flex;
  gap: 10px;
}

.btn-pdf {
  background: #E54848;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-pdf:hover {
  background: #C93F3F;
}

.btn-publicar {
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
}

.btn-no-publicado {
  background: #88B7F3;
  color: white;
}

.btn-no-publicado:hover {
  background: #6a9fd8;
}

.btn-publicado {
  background: #e2e8f0;
  color: #475569;
}

.btn-publicado:hover {
  background: #cbd5e1;
}

/* LEYENDA */
.leyenda-colores {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 12px;
  background: white;
  border-radius: 12px;
  border: 1px solid #eef2f6;
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
  gap: 6px;
  font-size: 0.75rem;
  color: #475569;
}

.leyenda-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

/* TABLA HORARIO */
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
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.horario-tabla td {
  padding: 10px 6px;
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

.clase-info {
  text-align: center;
}

.clase-materia {
  font-weight: 700;
  font-size: 0.75rem;
}

.clase-profesor, .clase-grupo, .clase-aula {
  font-size: 0.7rem;
  opacity: 0.8;
}

.clase-multiple {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* ESTADOS */
.empty-state, .error-state {
  text-align: center;
  padding: 50px 20px;
}

.empty-state i, .error-state i {
  font-size: 3rem;
  color: #cbd5e1;
  margin-bottom: 15px;
}

.error-state i {
  color: #E54848;
}

.empty-state h3 {
  margin-bottom: 8px;
  color: #2c3e50;
}

.no-results-text {
  text-align: center;
  padding: 30px;
  color: #64748b;
}

.loading-container {
  text-align: center;
  padding: 50px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #88B7F3;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* RESPONSIVE */
@media (max-width: 768px) {
  .horarios-main {
    padding: 0 15px;
  }
  
  .horarios-card {
    padding: 20px;
  }
  
  .horario-item-header {
    flex-direction: column;
  }
  
  .horario-item-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .vista-tab {
    padding: 8px 20px;
    font-size: 0.85rem;
  }
  
  .header-actions {
    flex-direction: column;
  }
  
  .header-actions button {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .horarios-header {
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
  }
  
  .header-spacer {
    display: none;
  }
  
  .btn-back-icon {
    position: absolute;
    left: 0;
    top: 0;
  }
  
  .header-text {
    flex: none;
    width: 100%;
    margin-top: 10px;
  }
  
  .header-text h1 {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .horario-tabla th,
  .horario-tabla td {
    padding: 6px 3px;
    font-size: 0.7rem;
  }
  
  .hora-col {
    width: 70px;
  }
  
  .clase-materia {
    font-size: 0.65rem;
  }
  
  .leyenda-colores {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>