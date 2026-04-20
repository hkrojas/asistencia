/**
 * Servicio de API para la app de asistencia.
 * Todas las funciones son stubs preparados para conectar con el backend real.
 */

// TODO: Reemplazar con la URL real del backend
const BASE_URL = 'https://api.example.com/v1';

/**
 * Helper interno para hacer peticiones fetch con headers comunes.
 */
async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const errorBody = await response.text().catch(() => '');
    throw new Error(`API Error ${response.status}: ${errorBody}`);
  }

  return response.json();
}

// ── Stubs de API ───────────────────────────────────────────────

/**
 * Verifica con el backend si el token de dispositivo es válido.
 * @param {string} deviceToken
 * @returns {Promise<{ valid: boolean, employeeName?: string }>}
 */
export async function checkDeviceToken(deviceToken) {
  // TODO: Conectar con endpoint real
  // return request('/device/verify', {
  //   method: 'POST',
  //   body: JSON.stringify({ device_token: deviceToken }),
  // });

  // Mock temporal: simula token válido
  console.log('[API Stub] checkDeviceToken llamado con:', deviceToken);
  return { valid: true, employeeName: 'Juan Pérez' };
}

/**
 * Consulta el estado actual del trabajador (si debe marcar ingreso o salida).
 * @param {string} deviceToken
 * @returns {Promise<{ action: 'check_in' | 'check_out', lastRecord?: string }>}
 */
export async function fetchCurrentState(deviceToken) {
  // TODO: Conectar con endpoint real
  // return request('/attendance/state', {
  //   headers: { 'X-Device-Token': deviceToken },
  // });

  // Mock temporal: alterna entre ingreso/salida
  console.log('[API Stub] fetchCurrentState llamado');
  return { action: 'check_in', lastRecord: null };
}

/**
 * Envía el registro de asistencia con la foto capturada.
 * @param {string} photoBase64 - Foto codificada en base64
 * @param {'check_in' | 'check_out'} actionType
 * @param {string} deviceToken
 * @returns {Promise<{ success: boolean, timestamp: string }>}
 */
export async function sendAttendance(photoBase64, actionType, deviceToken) {
  // TODO: Conectar con endpoint real
  // return request('/attendance/record', {
  //   method: 'POST',
  //   headers: { 'X-Device-Token': deviceToken },
  //   body: JSON.stringify({
  //     photo: photoBase64,
  //     action: actionType,
  //   }),
  // });

  // Mock temporal: simula éxito
  console.log('[API Stub] sendAttendance llamado:', actionType);
  return { success: true, timestamp: new Date().toISOString() };
}

/**
 * Obtiene el horario semanal del trabajador.
 * @param {string} deviceToken
 * @returns {Promise<Array<{ date: string, start: string, end: string }>>}
 */
export async function fetchWeeklySchedule(deviceToken) {
  // TODO: Conectar con endpoint real
  // return request('/schedule/weekly', {
  //   headers: { 'X-Device-Token': deviceToken },
  // });

  // Mock temporal: retorna horario fijo
  console.log('[API Stub] fetchWeeklySchedule llamado');
  return [];
}
