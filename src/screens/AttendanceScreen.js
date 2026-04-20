import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme';
import { getDeviceToken } from '../utils/storage';
import { checkDeviceToken, fetchCurrentState } from '../services/api';

export default function AttendanceScreen() {
  const cameraRef = useRef(null);
  const [permission, requestPermission] = useCameraPermissions();

  const [loading, setLoading] = useState(true);
  const [linked, setLinked] = useState(false);
  const [employeeName, setEmployeeName] = useState('');
  const [currentAction, setCurrentAction] = useState('check_in');
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    initializeDevice();
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
        setLinked(false);
        setLoading(false);
        return;
      }

      setLinked(true);
      setEmployeeName(verification.employeeName || '');

      const state = await fetchCurrentState(token);
      setCurrentAction(state.action);
    } catch (error) {
      console.error('[Attendance] Error en inicialización:', error);
      setLinked(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleTakePicture() {
    if (isProcessing) return;

    setIsProcessing(true);

    try {
      // Capturar foto (en web no disponible, se simula)
      let photoBase64 = null;
      if (cameraRef.current) {
        try {
          const photo = await cameraRef.current.takePictureAsync({
            base64: true,
            quality: 0.7,
          });
          photoBase64 = photo?.base64 || null;
        } catch (e) {
          console.warn('[Camera] No se pudo capturar foto:', e);
        }
      }

      // Simular envío al backend (2 segundos de espera)
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const actionLabel = currentAction === 'check_in' ? 'Ingreso' : 'Salida';

      Alert.alert(
        '✅ Asistencia registrada',
        `${actionLabel} registrado con éxito.\n${new Date().toLocaleTimeString()}`,
        [{ text: 'OK' }]
      );

      // Alternar acción para la próxima vez
      setCurrentAction((prev) =>
        prev === 'check_in' ? 'check_out' : 'check_in'
      );
    } catch (error) {
      Alert.alert('Error', 'No se pudo registrar la asistencia. Intente de nuevo.');
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
          <Ionicons name="warning-outline" size={56} color={Colors.textSecondary} />
          <Text style={styles.unlinkedTitle}>Dispositivo no vinculado</Text>
          <Text style={styles.unlinkedSubtitle}>
            Contacte al administrador para vincular este equipo al sistema de asistencia.
          </Text>
        </View>
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
});
