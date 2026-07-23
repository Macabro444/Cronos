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

    <div v-if="cargandoAccion" class="action-loading">
      <div class="spinner"></div>
      <p>Procesando...</p>
    </div>

    <main class="asignaciones-main">
      <!-- HEADER CON BOTÓN REGRESAR -->
      <div class="asignaciones-header">
        <button @click="goBack" class="btn-back-icon" title="Volver al Dashboard">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div class="header-text">
          <h1>Asignación de Profesores</h1>
          <p>Asigna profesores a asignaturas, grupos y períodos</p>
        </div>
        <div class="header-spacer"></div>
      </div>

      <div v-if="cargando" class="loading-container">
        <div class="spinner"></div>
        <p>Cargando información...</p>
      </div>

      <div class="asignaciones-card" v-else-if="asignaciones.length > 0">
        <div class="table-container">
          <table class="styled-table">
            <thead>
              <tr>
                <th>Profesor</th>
                <th>Asignatura</th>
                <th>División</th>
                <th>Aula</th>
                <th>Edificio</th>
                <th>Periodo</th>
                <th>Grupos</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="asig in currentAsignaciones" :key="'asig-' + asig.id">
                <td :data-label="'Profesor'">{{ asig.nombreProfesor }}</td>
                <td :data-label="'Asignatura'">{{ asig.asignatura || '-' }}</td>
                <td :data-label="'División'">{{ asig.division || '-' }}</td>
                <td :data-label="'Aula'">{{ asig.aula || '-' }}</td>
                <td :data-label="'Edificio'">{{ asig.edificio || '-' }}</td>
                <td :data-label="'Periodo'">{{ asig.periodo || '-' }}</td>
                <td :data-label="'Grupos'">{{ asig.grupos || '-' }}</td>
                <td :data-label="'Acciones'">
                  <button class="btn-secondary btn-accion" @click="editarAsignacion(asig)">Editar</button>
                  <button class="btn-danger btn-accion" @click="eliminarAsignacion(asig.id)">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="pagination">
            <button 
              v-for="pageNumber in totalPages" 
              :key="pageNumber" 
              @click="currentPage = pageNumber"
              :class="{ active: pageNumber === currentPage }"
            >
              {{ pageNumber }}
            </button>
          </div>
        </div>

        <div class="btn-div">
          <button class="btn-primary" @click="abrirFormularioNuevo">
            <i class="fas fa-plus"></i> Agregar Asignación
          </button>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-content">
          <i class="fas fa-chalkboard-user"></i>
          <h3>No hay asignaciones registradas</h3>
          <p>Comienza agregando tu primera asignación de profesor</p>
        </div>
      </div>
    </main>

    <!-- MODAL -->
    <div v-if="mostrarFormulario" class="form-overlay" @click.self="cerrarFormulario">
      <div class="form-modal">
        <div class="modal-header">
          <h2>{{ modoEdicion ? 'Editar Asignación' : 'Agregar Asignación' }}</h2>
          <button class="close-btn" @click="cerrarFormulario">&times;</button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="guardarAsignacion">
            <div class="form-grid-layout">
              <div class="input-group">
                <label>Profesor</label>
                <select v-model="form.id_profesor" required>
                  <option disabled value="">Selecciona un profesor</option>
                  <option v-for="prof in profesores" :key="prof.id" :value="prof.id">
                    {{ prof.nombreCompleto }} - {{ prof.titulo || 'Sin título' }}
                  </option>
                </select>
              </div>

              <div class="input-group">
                <label>Asignatura</label>
                <select v-model="form.id_asignatura" required>
                  <option disabled value="">Selecciona una asignatura</option>
                  <option v-for="asig in asignaturas" :key="asig.id" :value="asig.id">
                    {{ asig.nombre }}<template v-if="obtenerNombreDivisionDeAsignatura(asig.id)"> - {{ obtenerNombreDivisionDeAsignatura(asig.id) }}</template>
                  </option>
                </select>
              </div>

              <div class="input-group">
                <label>Aula (opcional)</label>
                <select v-model="form.id_aula">
                  <option value="">Sin aula</option>
                  <option v-for="aula in aulas" :key="aula.id" :value="aula.id">
                    {{ aula.nombre }}<template v-if="obtenerNombreEdificioDeAula(aula.id)"> - {{ obtenerNombreEdificioDeAula(aula.id) }}</template>
                  </option>
                </select>
              </div>

              <div class="input-group">
                <label>Periodo</label>
                <select v-model="form.id_periodo" required>
                  <option disabled value="">Selecciona un periodo</option>
                  <option v-for="per in periodos" :key="per.id" :value="per.id">
                    {{ per.nombre }}
                  </option>
                </select>
              </div>

              <div class="input-group full-width">
                <label>Grupos (múltiples)</label>
                <div class="checkbox-group">
                  <div v-for="grupo in grupos" :key="grupo.id" class="checkbox-item">
                    <input 
                      type="checkbox" 
                      :id="'grupo-' + grupo.id" 
                      :value="grupo.id" 
                      v-model="form.id_grupos" 
                    />
                    <label :for="'grupo-' + grupo.id">{{ grupo.nombre }}</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="submit" class="btn-primary">Guardar</button>
              <button type="button" class="btn-secondary" @click="cerrarFormulario">Cancelar</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from '../../utils/axios-config'
import '../../assets/styles.css'
import Swal from 'sweetalert2'

const router = useRouter()

const goBack = () => {
  router.back()
}

// ✅ URLs usando el API Gateway (puerto 8080)
const API_ASIGNACIONES = 'http://localhost:8080/api/profesor-asignatura'
const API_ASIGNACIONES_AULAS = 'http://localhost:8080/api/profesor-aula'
const API_PROFESORES = 'http://localhost:8080/api/profesores'
const API_ASIGNATURAS = 'http://localhost:8080/api/curriculum'
const API_PERIODOS = 'http://localhost:8080/api/periodos'
const API_GRUPOS = 'http://localhost:8080/api/v1/grupos'

// 🔥 IMPORTANTE: Rutas SIN /api para estos servicios (según configuración del Gateway)
const API_AULAS = 'http://localhost:8080/aulas'
const API_EDIFICIOS = 'http://localhost:8080/edificios'
const API_DIVISIONES = 'http://localhost:8080/divisiones'

// ==================== ESTADO ====================
const asignaciones = ref([])
const profesores = ref([])
const asignaturas = ref([])
const periodos = ref([])
const grupos = ref([])
const aulas = ref([])
const edificios = ref([])   // 👈 NUEVO: catálogo completo de edificios
const divisiones = ref([])  // 👈 NUEVO: catálogo completo de divisiones

const usuariosCache = ref({})
const profesoresMap = ref({})

const itemsPerPage = 5
const currentPage = ref(1)

const mostrarFormulario = ref(false)
const modoEdicion = ref(false)
const itemEditando = ref(null)

const cargando = ref(false)
const cargandoAccion = ref(false)

const form = ref({
  id_profesor: '',
  id_asignatura: '',
  id_aula: '',
  id_periodo: '',
  id_grupos: []
})

// ==================== COMPUTED ====================
const totalPages = computed(() => Math.ceil(asignaciones.value.length / itemsPerPage))
const indexOfLast = computed(() => currentPage.value * itemsPerPage)
const indexOfFirst = computed(() => indexOfLast.value - itemsPerPage)
const currentAsignaciones = computed(() =>
  asignaciones.value.slice(indexOfFirst.value, indexOfLast.value)
)

// ==================== FUNCIONES AUXILIARES ====================
const obtenerNombreUsuario = async (idUsuario) => {
  if (!idUsuario) return 'N/A'
  if (usuariosCache.value[idUsuario]) return usuariosCache.value[idUsuario]

  try {
    const res = await axios.get(`/api/usuario/perfil/${idUsuario}`)
    const u = res.data.usuario
    const nombreCompleto = u ? `${u.nombre} ${u.apellidoPaterno}` : 'N/A'
    usuariosCache.value[idUsuario] = nombreCompleto
    return nombreCompleto
  } catch (err) {
    console.error('Error obteniendo usuario:', err)
    return 'N/A'
  }
}

// ✅ Obtener nombre completo del profesor desde el DTO
const obtenerNombreProfesor = async (idProfesor) => {
  // Primero buscar en el cache
  if (profesoresMap.value[idProfesor]) {
    return profesoresMap.value[idProfesor]
  }
  
  // Buscar en la lista de profesores
  const profesor = profesores.value.find(p => p.id === idProfesor)
  if (!profesor) return 'N/A'
  
  // Si tiene nombreCompleto en el DTO, usarlo directamente
  if (profesor.nombreCompleto) {
    profesoresMap.value[idProfesor] = profesor.nombreCompleto
    return profesor.nombreCompleto
  }
  
  // Si no, obtener del usuario
  const nombre = await obtenerNombreUsuario(profesor.idUsuario)
  profesoresMap.value[idProfesor] = nombre
  return nombre
}

const obtenerNombreAsignatura = (idAsignatura) => {
  const asig = asignaturas.value.find(a => a.id === idAsignatura)
  return asig ? asig.nombre : '-'
}

const obtenerNombreGrupo = (idGrupo) => {
  const grupo = grupos.value.find(g => g.id === idGrupo)
  return grupo ? grupo.nombre : null
}

const obtenerNombrePeriodo = (idPeriodo) => {
  const periodo = periodos.value.find(p => p.id === idPeriodo)
  return periodo ? periodo.nombre : '-'
}

const obtenerAula = (idAula) => {
  const aula = aulas.value.find(a => a.id === idAula)
  return aula || null
}

// 👈 El aula ya trae el nombre del edificio directamente en "nombreEdificio"
const obtenerNombreEdificioDeAula = (idAula) => {
  if (!idAula) return null
  const aulaIdNum = typeof idAula === 'string' ? parseInt(idAula) : idAula
  const aula = aulas.value.find(a => a.id === aulaIdNum)
  if (!aula) return null

  return aula.nombreEdificio || null
}

// 👈 NUEVO: Obtener el nombre de la división a partir del id de una asignatura (para el <select> del formulario)
// ⚠️ Asume que cada objeto "asignatura" trae el campo idDivision. Si tu API usa otro nombre
//    (por ejemplo id_division o divisionId), ajusta la línea de abajo.
const obtenerNombreDivisionDeAsignatura = (idAsignatura) => {
  if (!idAsignatura) return null
  const asig = asignaturas.value.find(a => a.id === idAsignatura)
  if (!asig) return null

  const idDivision = asig.idDivision ?? asig.id_division ?? asig.divisionId
  if (!idDivision) return null

  const division = divisiones.value.find(d => d.id === idDivision)
  return division ? division.nombre : null
}

// ✅ Obtener división y edificio desde las relaciones (usado en la tabla, vía aula asignada)
const obtenerDivisionYEdificio = async (idAula) => {
  if (!idAula) return { division: '-', edificio: '-' }
  
  try {
    const aulaId = typeof idAula === 'string' ? parseInt(idAula) : idAula
    const response = await axios.get(`${API_AULAS}/${aulaId}`)
    const idEdificio = response.data.idEdificio
    
    if (idEdificio) {
      try {
        const edificioId = typeof idEdificio === 'string' ? parseInt(idEdificio) : idEdificio
        const edificioResponse = await axios.get(`${API_EDIFICIOS}/${edificioId}`)
        const idDivision = edificioResponse.data.idDivision
        
        if (idDivision) {
          try {
            const divisionId = typeof idDivision === 'string' ? parseInt(idDivision) : idDivision
            const divisionResponse = await axios.get(`${API_DIVISIONES}/${divisionId}`)
            return {
              division: divisionResponse.data.nombre || '-',
              edificio: edificioResponse.data.nombre || '-'
            }
          } catch (err) {
            console.error('Error obteniendo división:', err)
            return { division: '-', edificio: edificioResponse.data.nombre || '-' }
          }
        }
        return { division: '-', edificio: edificioResponse.data.nombre || '-' }
      } catch (err) {
        console.error('Error obteniendo edificio:', err)
        return { division: '-', edificio: '-' }
      }
    }
    return { division: '-', edificio: '-' }
  } catch (err) {
    console.error('Error obteniendo aula:', err)
    return { division: '-', edificio: '-' }
  }
}

// ==================== CARGAR DATOS ====================
const cargarCatalogos = async () => {
  try {
    const [profRes, asigRes, perRes, gruposRes, aulasRes, edificiosRes, divisionesRes] = await Promise.all([
      axios.get(API_PROFESORES),
      axios.get(API_ASIGNATURAS),
      axios.get(API_PERIODOS),
      axios.get(API_GRUPOS),
      axios.get(API_AULAS),
      axios.get(API_EDIFICIOS),   // 👈 NUEVO
      axios.get(API_DIVISIONES)   // 👈 NUEVO
    ])
    
    profesores.value = profRes.data
    asignaturas.value = asigRes.data
    periodos.value = perRes.data
    grupos.value = gruposRes.data
    aulas.value = aulasRes.data
    edificios.value = edificiosRes.data   // 👈 NUEVO
    divisiones.value = divisionesRes.data // 👈 NUEVO
    
    // ✅ Precargar nombres de profesores en caché usando nombreCompleto del DTO
    for (const prof of profesores.value) {
      if (prof.nombreCompleto) {
        profesoresMap.value[prof.id] = prof.nombreCompleto
      } else if (prof.idUsuario) {
        const nombre = await obtenerNombreUsuario(prof.idUsuario)
        profesoresMap.value[prof.id] = nombre
      }
    }
  } catch (err) {
    console.error('Error cargando catálogos:', err)
    await Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'No se pudieron cargar los catálogos. Verifica que el Gateway esté corriendo.',
      confirmButtonColor: '#3ABEF9',
      background: '#ffffff',
      color: '#213547',
      iconColor: '#E54848',
      width: '450px',
    })
  }
}

const cargarAsignaciones = async () => {
  cargando.value = true
  try {
    const res = await axios.get(API_ASIGNACIONES)
    const aulasRes = await axios.get(API_ASIGNACIONES_AULAS)
    const aulasAsignadas = aulasRes.data

    const asignacionesConDatos = await Promise.all(
      res.data.map(async (asig) => {
        const aulaAsignada = aulasAsignadas.find(
          a => a.idProfesor === asig.idProfesor && a.idPeriodo === asig.idPeriodo
        )
        const aulaInfo = aulaAsignada ? obtenerAula(aulaAsignada.idAula) : null
        
        const { division, edificio } = await obtenerDivisionYEdificio(aulaAsignada?.idAula)

        const nombresGrupos = (asig.idGrupos || [])
          .map(id => obtenerNombreGrupo(id))
          .filter(Boolean)
          .join(', ')

        // ✅ Obtener nombre completo del profesor
        const nombreProfesor = await obtenerNombreProfesor(asig.idProfesor)

        return {
          id: asig.id,
          nombreProfesor: nombreProfesor,
          asignatura: obtenerNombreAsignatura(asig.idAsignatura),
          division: division,
          aula: aulaInfo ? aulaInfo.nombre : '-',
          edificio: edificio,
          periodo: obtenerNombrePeriodo(asig.idPeriodo),
          grupos: nombresGrupos || '-',
          datosOriginales: asig
        }
      })
    )

    asignaciones.value = asignacionesConDatos
  } catch (err) {
    console.error('Error cargando asignaciones:', err)
    await Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'No se pudieron cargar las asignaciones',
      confirmButtonColor: '#3ABEF9',
      background: '#ffffff',
      color: '#213547',
      iconColor: '#E54848',
      width: '450px',
    })
  } finally {
    cargando.value = false
  }
}

// ==================== CRUD ====================
const abrirFormularioNuevo = () => {
  modoEdicion.value = false
  itemEditando.value = null
  form.value = {
    id_profesor: '',
    id_asignatura: '',
    id_aula: '',
    id_periodo: '',
    id_grupos: []
  }
  mostrarFormulario.value = true
}

const editarAsignacion = async (asig) => {
  modoEdicion.value = true
  itemEditando.value = asig.id

  let idAula = ''
  try {
    const aulasRes = await axios.get(API_ASIGNACIONES_AULAS)
    const aulaAsignada = aulasRes.data.find(
      a => a.idProfesor === asig.datosOriginales.idProfesor &&
        a.idPeriodo === asig.datosOriginales.idPeriodo
    )
    if (aulaAsignada) idAula = aulaAsignada.idAula
  } catch (err) {
    console.error('Error buscando aula:', err)
  }

  form.value = {
    id_profesor: asig.datosOriginales.idProfesor,
    id_asignatura: asig.datosOriginales.idAsignatura,
    id_aula: idAula,
    id_periodo: asig.datosOriginales.idPeriodo,
    id_grupos: asig.datosOriginales.idGrupos || []
  }

  mostrarFormulario.value = true
}

const guardarAsignacion = async () => {
  cargandoAccion.value = true
  try {
    const payloadAsignatura = {
      idProfesor: form.value.id_profesor,
      idAsignatura: form.value.id_asignatura,
      idPeriodo: form.value.id_periodo,
      idGrupos: form.value.id_grupos
    }

    if (modoEdicion.value) {
      await axios.patch(`${API_ASIGNACIONES}/${itemEditando.value}`, payloadAsignatura)
    } else {
      await axios.post(API_ASIGNACIONES, payloadAsignatura)
    }

    if (form.value.id_aula) {
      const payloadAula = {
        idProfesor: form.value.id_profesor,
        idAula: form.value.id_aula,
        idPeriodo: form.value.id_periodo
      }

      try {
        const aulasRes = await axios.get(API_ASIGNACIONES_AULAS)
        const aulaExistente = aulasRes.data.find(
          a => a.idProfesor === form.value.id_profesor &&
            a.idPeriodo === form.value.id_periodo
        )

        if (aulaExistente) {
          await axios.patch(`${API_ASIGNACIONES_AULAS}/${aulaExistente.id}`, payloadAula)
        } else {
          await axios.post(API_ASIGNACIONES_AULAS, payloadAula)
        }
      } catch (err) {
        console.error('Error gestionando aula:', err)
      }
    }

    cargandoAccion.value = false
    await Swal.fire({
      icon: 'success',
      title: modoEdicion.value ? '¡Actualizado!' : '¡Agregado!',
      text: `Asignación ${modoEdicion.value ? 'actualizada' : 'agregada'} correctamente`,
      showConfirmButton: false,
      timer: 2000,
      background: '#ffffff',
      color: '#213547',
      iconColor: '#3ABEF9',
      width: '450px',
    })

    cerrarFormulario()
    await cargarAsignaciones()
  } catch (err) {
    cargandoAccion.value = false
    console.error('Error guardando asignación:', err)
    await Swal.fire({
      icon: 'error',
      title: 'Error',
      text: err.response?.data?.message || 'Error guardando asignación',
      confirmButtonColor: '#3ABEF9',
      background: '#ffffff',
      color: '#213547',
      iconColor: '#E54848',
      width: '450px',
    })
  } finally {
    cargandoAccion.value = false
  }
}

const eliminarAsignacion = async (id) => {
  const confirm = await Swal.fire({
    title: '¿Eliminar asignación?',
    text: 'Esta acción no se puede deshacer',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
    confirmButtonColor: '#E54848',
    cancelButtonColor: '#88B7F3',
    background: '#ffffff',
    color: '#213547',
    iconColor: '#E54848',
    width: '500px',
  })

  if (confirm.isConfirmed) {
    cargandoAccion.value = true
    try {
      await axios.delete(`${API_ASIGNACIONES}/${id}`)
      cargandoAccion.value = false

      await Swal.fire({
        icon: 'success',
        title: 'Eliminado',
        text: 'Asignación eliminada correctamente',
        showConfirmButton: false,
        timer: 2000,
        background: '#ffffff',
        color: '#213547',
        iconColor: '#3ABEF9',
        width: '450px',
      })

      await cargarAsignaciones()

      if (currentAsignaciones.value.length === 0 && currentPage.value > 1) {
        currentPage.value--
      }
    } catch (err) {
      cargandoAccion.value = false
      console.error('Error eliminando:', err)
      await Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'No se pudo eliminar la asignación',
        confirmButtonColor: '#3ABEF9',
        background: '#ffffff',
        color: '#213547',
        iconColor: '#E54848',
        width: '450px',
      })
    } finally {
      cargandoAccion.value = false
    }
  }
}

const cerrarFormulario = () => {
  mostrarFormulario.value = false
  modoEdicion.value = false
  itemEditando.value = null
}

// ==================== LIFECYCLE ====================
onMounted(async () => {
  await cargarCatalogos()
  await cargarAsignaciones()
})
</script>

<style scoped>
/* =======================
   ASIGNACIÓN DE PROFESORES - CON BOTÓN REGRESAR
======================= */

.asignaciones-main {
  max-width: 1400px;
  margin: 40px auto;
  padding: 0 20px;
}

/* Header con botón a la izquierda y título centrado */
.asignaciones-header {
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

.asignaciones-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  padding: 30px;
  border: 1px solid #f0f0f0;
}

.table-container {
  width: 100%;
  overflow-x: auto;
}

.styled-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.styled-table thead tr {
  background-color: #88B7F3;
  color: white;
  text-align: left;
}

.styled-table th,
.styled-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #e2e8f0;
}

.styled-table tbody tr:hover {
  background-color: #f8fafc;
}

.btn-accion {
  width: auto;
  padding: 6px 12px;
  margin: 0 4px;
  font-size: 0.75rem;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 25px;
  flex-wrap: wrap;
}

.pagination button {
  background: #f1f5f9;
  color: #334155;
  border: none;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.pagination button:hover {
  background: #3abef9;
  color: white;
}

.pagination button.active {
  background: #3abef9;
  color: white;
}

.btn-div {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.btn-primary i {
  margin-right: 8px;
}

/* ===== FORMULARIO ===== */
.checkbox-group {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  background: #f8fafc;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #88B7F3;
}

.checkbox-item label {
  margin: 0;
  cursor: pointer;
  font-size: 0.85rem;
  color: #334155;
}

.form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.form-modal {
  background: white;
  width: 90%;
  max-width: 750px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  padding: 20px 25px;
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #94a3b8;
}

.close-btn:hover {
  color: #ef4444;
}

.modal-body {
  padding: 25px;
  max-height: 70vh;
  overflow-y: auto;
}

.form-grid-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.input-group {
  display: flex;
  flex-direction: column;
  text-align: left;
}

.input-group.full-width {
  grid-column: span 2;
}

.input-group label {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: #475569;
}

.input-group select {
  padding: 10px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.2s;
  background: white;
}

.input-group select:focus {
  outline: none;
  border-color: #3abef9;
  box-shadow: 0 0 0 3px rgba(58, 190, 249, 0.1);
}

.modal-footer {
  padding: 20px 25px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.btn-secondary {
  background: white;
  color: #64748b;
  border: 1px solid #e2e8f0;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #f1f5f9;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .asignaciones-main {
    padding: 0 15px;
  }

  .asignaciones-card {
    padding: 20px;
  }

  .form-grid-layout {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .input-group.full-width {
    grid-column: span 1;
  }

  .styled-table th,
  .styled-table td {
    padding: 10px 8px;
    font-size: 0.75rem;
  }

  .btn-accion {
    margin: 2px;
    font-size: 0.7rem;
    padding: 4px 8px;
  }
}

@media (max-width: 600px) {
  .asignaciones-header {
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
  .styled-table thead {
    display: none;
  }

  .styled-table tbody tr {
    display: block;
    margin-bottom: 15px;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 10px;
  }

  .styled-table td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px;
    border-bottom: 1px solid #e2e8f0;
    text-align: right;
  }

  .styled-table td::before {
    content: attr(data-label);
    font-weight: 600;
    color: #334155;
    text-align: left;
    width: 40%;
  }

  .styled-table td:last-child {
    border-bottom: none;
  }

  .btn-accion {
    width: auto;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-footer button {
    width: 100%;
  }

  .checkbox-item {
    padding: 6px 0;
  }
}

/* ===== LOADING ===== */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #e2e8f0;
  border-top-color: #3abef9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-container p {
  margin-top: 15px;
  color: #64748b;
}

.action-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.action-loading .spinner {
  width: 40px;
  height: 40px;
}

.action-loading p {
  margin-top: 15px;
  font-weight: 500;
  color: #475569;
}

/* ===== EMPTY STATE ===== */
.empty-state {
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  padding: 60px 20px;
  text-align: center;
  border: 1px solid #f0f0f0;
}

.empty-content i {
  font-size: 4rem;
  color: #cbd5e1;
  margin-bottom: 20px;
}

.empty-content h3 {
  color: #334155;
  margin-bottom: 10px;
}

.empty-content p {
  color: #94a3b8;
}
</style>