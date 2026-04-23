import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Pressable,
  Modal,
  TextInput,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme';
import { getDeviceToken, saveDeviceToken } from '../utils/storage';
import { checkDeviceToken, fetchCurrentState, sendAttendance, syncOfflinePunches, getPendingSyncCount, pairDevice } from '../services/api';
import MyTimesheetScreen from './MyTimesheetScreen';

export default function AttendanceScreen() {
  const cameraRef = useRef(null);
  const [permission, requestPermission] = useCameraPermissions();

  const [loading, setLoading] = useState(true);
  const [linked, setLinked] = useState(false);
  const [employeeName, setEmployeeName] = useState('');
  const [currentAction, setCurrentAction] = useState('check_in');
  const [isProcessing, setIsProcessing] = useState(false);
  const [pendingSyncCount, setPendingSyncCount] = useState(0);

  // ── Estado del modal de emparejamiento ──
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [pairingCode, setPairingCode] = useState('');
  const [showSummary, setShowSummary] = useState(false);

  useEffect(() => {
    initializeDevice();

    // Motor de sincronización offline
    const syncInterval = setInterval(async () => {
      const synced = await syncOfflinePunches();
      if (synced > 0) {
        console.log(`[Sync] Se sincronizaron ${synced} registros.`);
      }
      const pending = await getPendingSyncCount();
      setPendingSyncCount(pending);
    }, 30000); // 30 segundos

    return () => clearInterval(syncInterval);
  }, []);

  async function initializeDevice() {
    try {
      const token = await getDeviceToken();

      if (!token) {
        setLinked(false);
        setLoading(false);
        return;
      }

      const verification = await checkDeviceToken(token);

      if (!verification.valid) {
        // Si no hay conexión (verification set valid: false but with error), 
        // no desvinculamos, solo permitimos modo offline si ya estaba vinculado.
        if (verification.error && verification.error.includes('No se pudo conectar')) {
           setLinked(true);
           setEmployeeName('Modo Offline');
        } else {
           setLinked(false);
        }
        setLoading(false);
        return;
      }

      setLinked(true);
      setEmployeeName(verification.employeeName || '');

      const state = await fetchCurrentState(token);
      setCurrentAction(state.action);
      
      const pending = await getPendingSyncCount();
      setPendingSyncCount(pending);
    } catch (error) {
      console.error('[Attendance] Error en inicialización:', error);
      setLinked(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdminLink() {
    if (pairingCode.length === 6) {
      setShowAdminModal(false);
      setLoading(true);

      try {
        const response = await pairDevice(pairingCode);
        await saveDeviceToken(response.device_token);
        
        Alert.alert('✅ Vinculado', 'Dispositivo vinculado a la sede.');
        setPairingCode('');
        await initializeDevice();
      } catch (error) {
        Alert.alert('Error', 'Código inválido, expirado o error de red.');
        setLoading(false);
        setPairingCode('');
      }
    } else {
      Alert.alert('Código incompleto', 'Por favor ingrese los 6 dígitos del código.');
    }
  }

  async function handleTakePicture() {
    if (isProcessing) return;

    setIsProcessing(true);

    try {
      // Capturar foto
      let photoBase64 = null;
      if (cameraRef.current) {
        try {
          const photo = await cameraRef.current.takePictureAsync({
            base64: true,
            quality: 0.5, // Reducimos calidad para offline storage
          });
          photoBase64 = photo?.base64 || null;
        } catch (e) {
          console.warn('[Camera] No se pudo capturar foto:', e);
        }
      }

      // Enviar al backend
      const token = await getDeviceToken();
      const result = await sendAttendance(photoBase64, currentAction, token);

      if (result.success) {
        const actionLabel = currentAction === 'check_in' ? 'Ingreso' : 'Salida';
        const offlineMsg = result.offline ? '\n(Sin conexión - Guardado localmente)' : '';

        Alert.alert(
          result.offline ? '⚠️ Guardado Offline' : '✅ Asistencia registrada',
          `${actionLabel} registrado con éxito.${offlineMsg}\n${new Date().toLocaleTimeString()}`,
          [{ text: 'OK' }]
        );

        // Actualizar contador de pendientes si fue offline
        if (result.offline) {
          const pending = await getPendingSyncCount();
          setPendingSyncCount(pending);
        }

        // Alternar acción para la próxima vez
        setCurrentAction((prev) =>
          prev === 'check_in' ? 'check_out' : 'check_in'
        );
      } else {
        Alert.alert('Error', result.error || 'No se pudo registrar la asistencia.');
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo conectar con el servidor.');
      console.error('[Attendance] Error al registrar:', error);
    } finally {
      setIsProcessing(false);
    }
  }

  // ── Estado: Cargando ──
  if (loading) {
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color={Colors.checkIn} />
        <Text style={styles.loadingText}>Verificando dispositivo...</Text>
      </View>
    );
  }

  // ── Estado: Dispositivo NO vinculado ──
  if (!linked) {
    return (
      <View style={styles.centeredContainer}>
        <View style={styles.unlinkedCard}>
          <Pressable
            onLongPress={() => setShowAdminModal(true)}
            delayLongPress={3000}
          >
            <Ionicons name="warning-outline" size={56} color={Colors.textSecondary} />
          </Pressable>
          <Text style={styles.unlinkedTitle}>Dispositivo no vinculado</Text>
          <Text style={styles.unlinkedSubtitle}>
            Contacte al administrador para vincular este equipo al sistema de asistencia.
          </Text>
        </View>

        {/* ── Modal oculto de administrador ── */}
        <Modal
          visible={showAdminModal}
          transparent
          animationType="fade"
          onRequestClose={() => { setShowAdminModal(false); setPairingCode(''); }}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalCard}>
              <Ionicons name="shield-checkmark-outline" size={40} color={Colors.todayAccent} />
              <Text style={styles.modalTitle}>Vincular Dispositivo</Text>
              <Text style={styles.modalSubtitle}>Ingrese el código de 6 dígitos generado en el panel web</Text>

              <TextInput
                style={styles.pinInput}
                value={pairingCode}
                onChangeText={setPairingCode}
                placeholder="000000"
                placeholderTextColor={Colors.tabInactive}
                secureTextEntry
                keyboardType="number-pad"
                maxLength={6}
                autoFocus
              />

              <TouchableOpacity style={styles.linkButton} onPress={handleAdminLink}>
                <Text style={styles.linkButtonText}>Vincular Equipo</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => { setShowAdminModal(false); setPairingCode(''); }}
              >
                <Text style={styles.cancelButtonText}>Cancelar</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </View>
    );
  }

  // ── Estado: Sin permiso de cámara ──
  if (!permission) {
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color={Colors.checkIn} />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.centeredContainer}>
        <View style={styles.unlinkedCard}>
          <Ionicons name="camera-outline" size={56} color={Colors.textSecondary} />
          <Text style={styles.unlinkedTitle}>Permiso de cámara requerido</Text>
          <Text style={styles.unlinkedSubtitle}>
            Para registrar tu asistencia necesitamos acceso a la cámara.
          </Text>
          <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
            <Text style={styles.permissionButtonText}>Permitir cámara</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // ── Estado: Vinculado + Cámara activa ──
  const isCheckIn = currentAction === 'check_in';
  const buttonColor = isCheckIn ? Colors.checkIn : Colors.checkOut;
  const buttonLabel = isCheckIn ? 'MARCAR INGRESO' : 'MARCAR SALIDA';
  const buttonIcon = isCheckIn ? 'log-in-outline' : 'log-out-outline';

  return (
    <View style={styles.container}>
      {/* Cámara frontal como fondo completo */}
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFillObject}
        facing="front"
      />

      {/* Overlay oscuro sutil para legibilidad */}
      <View style={styles.overlay} />

      {/* Encabezado superior */}
      <View style={styles.topBar}>
        <Text style={styles.greetingText}>Hola, {employeeName}</Text>
        <Text style={styles.instructionText}>
          {isCheckIn
            ? 'Posiciona tu rostro y marca tu ingreso'
            : 'Posiciona tu rostro y marca tu salida'}
        </Text>

        {pendingSyncCount > 0 && (
          <View style={styles.syncIndicator}>
            <Ionicons name="cloud-offline-outline" size={16} color={Colors.warning} />
            <Text style={styles.syncText}>
              {pendingSyncCount} marcación{pendingSyncCount > 1 ? 'es' : ''} pendiente{pendingSyncCount > 1 ? 's' : ''} (Sin conexión)
            </Text>
          </View>
        )}

        {linked && (
          <TouchableOpacity 
            style={styles.summaryButton} 
            onPress={() => setShowSummary(true)}
          >
            <Ionicons name="stats-chart" size={16} color={Colors.textLight} />
            <Text style={styles.summaryButtonText}>Ver Mi Semana</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Guía visual: marco facial */}
      <View style={styles.faceGuideContainer}>
        <View style={styles.faceGuide} />
      </View>

      {/* Botón de acción en la parte inferior */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: buttonColor }]}
          onPress={handleTakePicture}
          disabled={isProcessing}
          activeOpacity={0.8}
        >
          {isProcessing ? (
            <ActivityIndicator size="large" color={Colors.textLight} />
          ) : (
            <>
              <Ionicons name={buttonIcon} size={36} color={Colors.textLight} />
              <Text style={styles.actionButtonText}>{buttonLabel}</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* ── Modal de Resumen Semanal ── */}
      <Modal
        visible={showSummary}
        animationType="slide"
        onRequestClose={() => setShowSummary(false)}
      >
        <MyTimesheetScreen onClose={() => setShowSummary(false)} />
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  centeredContainer: {
    flex: 1,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },

  // ── Overlay ──
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.25)',
  },

  // ── Top bar ──
  topBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingHorizontal: 24,
    paddingBottom: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    alignItems: 'center',
  },
  greetingText: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.textLight,
    marginBottom: 4,
  },
  instructionText: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
  },
  syncIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 152, 0, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginTop: 10,
    borderWidth: 1,
    borderColor: 'rgba(255, 152, 0, 0.3)',
  },
  syncText: {
    fontSize: 12,
    color: Colors.warning || '#FF9800',
    fontWeight: '600',
    marginLeft: 6,
  },
  summaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginTop: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  summaryButtonText: {
    color: Colors.textLight,
    fontSize: 14,
    fontWeight: '700',
    marginLeft: 8,
  },

  // ── Guía facial ──
  faceGuideContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  faceGuide: {
    width: 220,
    height: 280,
    borderRadius: 110,
    borderWidth: 2.5,
    borderColor: 'rgba(255,255,255,0.5)',
    borderStyle: 'dashed',
  },

  // ── Bottom bar ──
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingBottom: Platform.OS === 'ios' ? 40 : 30,
    paddingTop: 20,
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  actionButton: {
    width: 180,
    height: 180,
    borderRadius: 90,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 10,
  },
  actionButtonText: {
    color: Colors.textLight,
    fontSize: 16,
    fontWeight: '800',
    marginTop: 8,
    letterSpacing: 0.8,
    textAlign: 'center',
  },

  // ── Loading ──
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.textSecondary,
  },

  // ── No vinculado / Permisos ──
  unlinkedCard: {
    alignItems: 'center',
    backgroundColor: Colors.cardBackground,
    borderRadius: 20,
    padding: 40,
    maxWidth: 340,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  unlinkedTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginTop: 16,
    textAlign: 'center',
  },
  unlinkedSubtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    marginTop: 10,
    textAlign: 'center',
    lineHeight: 22,
  },
  permissionButton: {
    marginTop: 24,
    backgroundColor: Colors.checkIn,
    borderRadius: 12,
    paddingHorizontal: 28,
    paddingVertical: 14,
  },
  permissionButtonText: {
    color: Colors.textLight,
    fontSize: 16,
    fontWeight: '700',
  },

  // ── Modal de administrador ──
  modalOverlay: {
    flex: 1,
    backgroundColor: Colors.overlay,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  modalCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 20,
    padding: 32,
    width: '100%',
    maxWidth: 340,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 8,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginTop: 12,
    textAlign: 'center',
  },
  modalSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 6,
    textAlign: 'center',
  },
  pinInput: {
    width: '100%',
    marginTop: 24,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: Colors.border,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 20,
    fontWeight: '600',
    textAlign: 'center',
    letterSpacing: 6,
    color: Colors.textPrimary,
  },
  linkButton: {
    marginTop: 20,
    backgroundColor: Colors.todayAccent,
    borderRadius: 12,
    paddingHorizontal: 28,
    paddingVertical: 14,
    width: '100%',
    alignItems: 'center',
  },
  linkButtonText: {
    color: Colors.textLight,
    fontSize: 16,
    fontWeight: '700',
  },
  cancelButton: {
    marginTop: 12,
    paddingVertical: 10,
  },
  cancelButtonText: {
    color: Colors.textSecondary,
    fontSize: 15,
    fontWeight: '600',
  },
});
