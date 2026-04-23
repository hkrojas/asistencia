import * as SecureStore from 'expo-secure-store';

const KEYS = {
  DEVICE_TOKEN: 'device_token',
};

/**
 * Guarda el token de dispositivo en almacenamiento SEGURO.
 * @param {string} token
 */
export async function saveDeviceToken(token) {
  try {
    await SecureStore.setItemAsync(KEYS.DEVICE_TOKEN, token);
  } catch (error) {
    console.error('[Storage] Error guardando device_token:', error);
    throw error;
  }
}

/**
 * Lee el token de dispositivo desde almacenamiento SEGURO.
 * @returns {Promise<string|null>}
 */
export async function getDeviceToken() {
  try {
    return await SecureStore.getItemAsync(KEYS.DEVICE_TOKEN);
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
    await SecureStore.deleteItemAsync(KEYS.DEVICE_TOKEN);
  } catch (error) {
    console.error('[Storage] Error eliminando device_token:', error);
  }
}
