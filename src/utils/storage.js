import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  DEVICE_TOKEN: '@asistencia/device_token',
};

/**
 * Guarda el token de dispositivo en almacenamiento local.
 * @param {string} token
 */
export async function saveDeviceToken(token) {
  try {
    await AsyncStorage.setItem(KEYS.DEVICE_TOKEN, token);
  } catch (error) {
    console.error('[Storage] Error guardando device_token:', error);
    throw error;
  }
}

/**
 * Lee el token de dispositivo desde almacenamiento local.
 * @returns {Promise<string|null>}
 */
export async function getDeviceToken() {
  try {
    return await AsyncStorage.getItem(KEYS.DEVICE_TOKEN);
  } catch (error) {
    console.error('[Storage] Error leyendo device_token:', error);
    return null;
  }
}

/**
 * Elimina el token de dispositivo (útil para reset/desvinculación).
 */
export async function removeDeviceToken() {
  try {
    await AsyncStorage.removeItem(KEYS.DEVICE_TOKEN);
  } catch (error) {
    console.error('[Storage] Error eliminando device_token:', error);
  }
}
