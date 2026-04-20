/**
 * Servicio de API para la app de asistencia.
 * Conecta con el backend Flask en /v1/*.
 */
import { Platform } from 'react-native';

// ── URL base del backend ──
// Android Emulator usa 10.0.2.2 para acceder al host.
// iOS Simulator y Web usan localhost directamente.
// En producción: reemplazar con la URL real del servidor.
const BASE_URL = Platform.select({
  android: 'http://10.0.2.2:5000',
  ios: 'http://localhost:5000',
  default: 'http://localhost:5000', // Web
});

/**
 * Helper interno para hacer peticiones fetch con headers comunes.
 */
async function request(endpoint, options = {}) {
  const url = `${BASE_URL}/v1${endpoint}`;
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

// ── Funciones de API ───────────────────────────────────────────

/**
 * Verifica con el backend si el token de dispositivo es válido.
 * @param {string} deviceToken
 * @returns {Promise<{ valid: boolean, employeeName?: string }>}
 */
export async function checkDeviceToken(deviceToken) {
  try {
    return await request('/device/verify', {
      method: 'POST',
      body: JSON.stringify({ device_token: deviceToken }),
    });
  } catch (error) {
    console.error('[API] checkDeviceToken error:', error.message);
    return { valid: false, error: error.message };
  }
}

/**
 * Consulta el estado actual del trabajador (si debe marcar ingreso o salida).
 * @param {string} deviceToken
 * @returns {Promise<{ action: 'check_in' | 'check_out', lastRecord?: string }>}
 */
export async function fetchCurrentState(deviceToken) {
  try {
    return await request('/attendance/state', {
      headers: { 'X-Device-Token': deviceToken },
    });
  } catch (error) {
    console.error('[API] fetchCurrentState error:', error.message);
    return { action: 'check_in', lastRecord: null, error: error.message };
  }
}

/**
 * Envía el registro de asistencia con la foto capturada.
 * @param {string|null} photoBase64 - Foto codificada en base64
 * @param {'check_in' | 'check_out'} actionType
 * @param {string} deviceToken
 * @returns {Promise<{ success: boolean, record?: object }>}
 */
export async function sendAttendance(photoBase64, actionType, deviceToken) {
  try {
    return await request('/attendance/register', {
      method: 'POST',
      headers: { 'X-Device-Token': deviceToken },
      body: JSON.stringify({
        action_type: actionType,
        photo: photoBase64,
      }),
    });
  } catch (error) {
    console.error('[API] sendAttendance error:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Obtiene el horario semanal del trabajador.
 * @param {string} deviceToken
 * @returns {Promise<{ employee: string, schedule: Array }>}
 */
export async function fetchWeeklySchedule(deviceToken) {
  try {
    return await request('/schedule/weekly', {
      headers: { 'X-Device-Token': deviceToken },
    });
  } catch (error) {
    console.error('[API] fetchWeeklySchedule error:', error.message);
    return { employee: '', schedule: [], error: error.message };
  }
}
