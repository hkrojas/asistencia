import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme';
import { getDeviceToken } from '../utils/storage';
import { checkDeviceToken, fetchCurrentState } from '../services/api';

export default function AttendanceScreen() {
  const [loading, setLoading] = useState(true);
  const [linked, setLinked] = useState(false);
  const [employeeName, setEmployeeName] = useState('');
  const [currentAction, setCurrentAction] = useState('check_in');

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

      // Verificar con backend si el token es válido
      const verification = await checkDeviceToken(token);

      if (!verification.valid) {
        setLinked(false);
        setLoading(false);
        return;
      }

      setLinked(true);
      setEmployeeName(verification.employeeName || '');

      // Obtener estado actual (ingreso o salida)
      const state = await fetchCurrentState(token);
      setCurrentAction(state.action);
    } catch (error) {
      console.error('[Attendance] Error en inicialización:', error);
      setLinked(false);
    } finally {
      setLoading(false);
    }
  }

  // ── Estado: Cargando ──
  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={Colors.checkIn} />
        <Text style={styles.loadingText}>Verificando dispositivo...</Text>
      </View>
    );
  }

  // ── Estado: Dispositivo NO vinculado ──
  if (!linked) {
    return (
      <View style={styles.container}>
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

  // ── Estado: Vinculado (placeholder para cámara, próxima fase) ──
  const isCheckIn = currentAction === 'check_in';

  return (
    <View style={styles.container}>
      <Text style={styles.greetingText}>
        Hola, {employeeName}
      </Text>
      <Text style={styles.instructionText}>
        {isCheckIn
          ? 'Presiona el botón para registrar tu ingreso'
          : 'Presiona el botón para registrar tu salida'}
      </Text>

      {/* Placeholder visual del botón de acción (se conectará a cámara en Fase 2) */}
      <View
        style={[
          styles.actionPlaceholder,
          { backgroundColor: isCheckIn ? Colors.checkIn : Colors.checkOut },
        ]}
      >
        <Ionicons
          name={isCheckIn ? 'log-in-outline' : 'log-out-outline'}
          size={48}
          color={Colors.textLight}
        />
        <Text style={styles.actionText}>
          {isCheckIn ? 'INGRESO' : 'SALIDA'}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },

  // ── Loading ──
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.textSecondary,
  },

  // ── No vinculado ──
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

  // ── Vinculado ──
  greetingText: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginBottom: 40,
    textAlign: 'center',
  },
  actionPlaceholder: {
    width: 160,
    height: 160,
    borderRadius: 80,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 6,
  },
  actionText: {
    color: Colors.textLight,
    fontSize: 18,
    fontWeight: '800',
    marginTop: 6,
    letterSpacing: 1,
  },
});
