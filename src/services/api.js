import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import uuid from 'react-native-uuid';

// ── URL base del backend ──
const BASE_URL = Platform.select({
  android: 'http://10.0.2.2:5000',
  ios: 'http://localhost:5000',
  default: 'http://localhost:5000', // Web
});

const OFFLINE_PUNCHES_KEY = 'offline_punches';

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
 * Envía el registro de asistencia con la foto capturada.
 * Soporta Offline-First: si falla la red, guarda localmente.
 */
export async function sendAttendance(photoBase64, actionType, deviceToken) {
  const clientUuid = uuid.v4();
  const punchTime = new Date().toISOString();

  const payload = {
    action_type: actionType,
    photo: photoBase64,
    client_uuid: clientUuid,
    punch_time: punchTime,
  };

  try {
    return await request('/attendance/register', {
      method: 'POST',
      headers: { 'X-Device-Token': deviceToken },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    // Si es un error de red (TypeError), guardamos offline
    if (error.message.includes('fetch') || error instanceof TypeError || !BASE_URL) {
      console.log('[API] Red no disponible. Guardando marcación offline...');
      
      try {
        const stored = await AsyncStorage.getItem(OFFLINE_PUNCHES_KEY);
        const punches = stored ? JSON.parse(stored) : [];
        punches.push({ ...payload, deviceToken });
        await AsyncStorage.setItem(OFFLINE_PUNCHES_KEY, JSON.stringify(punches));
        
        return { success: true, offline: true };
      } catch (storageError) {
        console.error('[API] Error guardando en AsyncStorage:', storageError);
        return { success: false, error: 'Error de red y no se pudo guardar localmente.' };
      }
    }
    
    throw error;
  }
}

/**
 * Sincroniza las marcaciones pendientes guardadas localmente.
 */
export async function syncOfflinePunches() {
  try {
    const stored = await AsyncStorage.getItem(OFFLINE_PUNCHES_KEY);
    if (!stored) return 0;

    let punches = JSON.parse(stored);
    if (punches.length === 0) return 0;

    console.log(`[API] Intentando sincronizar ${punches.length} marcaciones...`);
    const remaining = [];

    for (const punch of punches) {
      try {
        const { deviceToken, ...data } = punch;
        await request('/attendance/register', {
          method: 'POST',
          headers: { 'X-Device-Token': deviceToken },
          body: JSON.stringify({ ...data, offline_sync: true }),
        });
        // Si tiene éxito o es 409 (Ya existe), lo eliminamos de la cola
      } catch (error) {
        // Si el error NO es de red (ej. 400, 401), o es 409 Conflict (idempotencia),
        // deberíamos considerar si eliminarlo. Para este MVP, si falla por red, 
        // lo mantenemos para el próximo intento.
        if (error.message.includes('409')) {
           console.log('[API] Punch ya sincronizado (409).');
        } else if (error.message.includes('API Error')) {
           // Error lógico del backend, quizás descartar o loguear
           console.error('[API] Error lógico al sincronizar punch:', error.message);
        } else {
           remaining.push(punch);
        }
      }
    }

    await AsyncStorage.setItem(OFFLINE_PUNCHES_KEY, JSON.stringify(remaining));
    return punches.length - remaining.length;
  } catch (error) {
    console.error('[API] Error en syncOfflinePunches:', error);
    return 0;
  }
}

/**
 * Obtiene el conteo de marcaciones pendientes de sincronizar.
 */
export async function getPendingSyncCount() {
  try {
    const stored = await AsyncStorage.getItem(OFFLINE_PUNCHES_KEY);
    if (!stored) return 0;
    const punches = JSON.parse(stored);
    return punches.length;
  } catch (error) {
    return 0;
  }
}

/**
 * Verifica con el backend si el token de dispositivo es válido.
 */
export async function checkDeviceToken(deviceToken) {
  try {
    return await request('/device/verify', {
      method: 'POST',
      body: JSON.stringify({ device_token: deviceToken }),
    });
  } catch (error) {
    return { valid: false, error: 'Sin conexión para verificar device.' };
  }
}

/**
 * Vincula el dispositivo usando el código de 6 dígitos.
 */
export async function pairDevice(pairingCode) {
  return await request('/devices/pair', {
    method: 'POST',
    body: JSON.stringify({ pairing_code: pairingCode }),
  });
}

/**
 * Consulta el estado actual del trabajador.
 */
export async function fetchCurrentState(deviceToken) {
  try {
    return await request('/attendance/state', {
      headers: { 'X-Device-Token': deviceToken },
    });
  } catch (error) {
    return { action: 'check_in', lastRecord: null, error: 'Offline' };
  }
}

/**
 * Obtiene el horario semanal.
 */
export async function fetchWeeklySchedule(deviceToken) {
  try {
    return await request('/schedule/weekly', {
      headers: { 'X-Device-Token': deviceToken },
    });
  } catch (error) {
    return { employee: '', schedule: [], error: 'Offline' };
  }
}
/**
 * Obtiene el resumen semanal del empleado (transparencia).
 */
export async function getEmployeeSummary(deviceToken) {
  try {
    return await request('/attendance/summary', {
      headers: { 'X-Device-Token': deviceToken },
    });
  } catch (error) {
    throw error;
  }
}
