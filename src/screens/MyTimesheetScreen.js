import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme';
import { getEmployeeSummary } from '../services/api';
import { getDeviceToken } from '../utils/storage';

export default function MyTimesheetScreen({ onClose }) {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = await getDeviceToken();
      const data = await getEmployeeSummary(token);
      setSummary(data);
    } catch (err) {
      console.error('[MyTimesheet] Error loading summary:', err);
      setError('No se pudo cargar el resumen. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const renderDayItem = ({ item }) => {
    const dateObj = new Date(item.date);
    const dayName = dateObj.toLocaleDateString('es-ES', { weekday: 'long' });
    const dayNum = dateObj.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });

    let statusColor = Colors.textSecondary;
    if (item.status === 'Completo') statusColor = Colors.success;
    if (item.status === 'Horas Extra') statusColor = Colors.todayAccent;
    if (item.status === 'Incompleto') statusColor = Colors.warning;
    if (item.status === 'Falta') statusColor = Colors.error;
    if (item.status === 'Justificado') statusColor = '#6f42c1'; // Purple

    return (
      <View style={styles.dayItem}>
        <View style={styles.dayInfo}>
          <Text style={styles.dayName}>{dayName.charAt(0).toUpperCase() + dayName.slice(1)} {dayNum}</Text>
          <Text style={[styles.dayStatus, { color: statusColor }]}>{item.status}</Text>
        </View>
        <View style={styles.dayStats}>
          <Text style={styles.workedHours}>{item.worked_hours}h</Text>
          {item.overtime_minutes > 0 && (
            <Text style={styles.extraText}>+{Math.round(item.overtime_minutes / 60 * 10) / 10}h extra</Text>
          )}
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={Colors.todayAccent} />
        <Text style={styles.loadingText}>Cargando resumen...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Ionicons name="alert-circle-outline" size={48} color={Colors.error} />
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadSummary}>
          <Text style={styles.retryButtonText}>Reintentar</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.closeLink} onPress={onClose}>
          <Text style={styles.closeLinkText}>Cerrar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Mi Resumen Semanal</Text>
        <TouchableOpacity onPress={onClose}>
          <Ionicons name="close" size={28} color={Colors.textPrimary} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Summary Cards */}
        <View style={styles.summaryRow}>
          <View style={[styles.summaryCard, { borderLeftColor: Colors.success }]}>
            <Text style={styles.summaryLabel}>Horas Regulares</Text>
            <Text style={styles.summaryValue}>{summary.total_regular_hours}h</Text>
          </View>
          <View style={[styles.summaryCard, { borderLeftColor: Colors.todayAccent }]}>
            <Text style={styles.summaryLabel}>Horas Extra</Text>
            <Text style={styles.summaryValue}>{summary.total_overtime_hours}h</Text>
          </View>
        </View>

        {/* History List */}
        <Text style={styles.sectionTitle}>Últimos 7 Días</Text>
        {summary.days.length > 0 ? (
          summary.days.map((day, index) => (
            <React.Fragment key={day.date}>
              {renderDayItem({ item: day })}
              {index < summary.days.length - 1 && <View style={styles.separator} />}
            </React.Fragment>
          ))
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No hay registros procesados aún.</Text>
          </View>
        )}
      </ScrollView>

      {/* Footer Button */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.closeButton} onPress={onClose}>
          <Text style={styles.closeButtonText}>VOLVER AL MARCADOR</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.surfaceLight,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingHorizontal: 20,
    paddingBottom: 15,
    backgroundColor: Colors.cardBackground,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  scrollContent: {
    padding: 20,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  summaryCard: {
    flex: 0.48,
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  summaryLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 12,
  },
  dayItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  dayInfo: {
    flex: 1,
  },
  dayName: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  dayStatus: {
    fontSize: 13,
    marginTop: 2,
    fontWeight: '500',
  },
  dayStats: {
    alignItems: 'flex-end',
  },
  workedHours: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  extraText: {
    fontSize: 11,
    color: Colors.todayAccent,
    fontWeight: '600',
  },
  separator: {
    height: 1,
    backgroundColor: Colors.border,
    opacity: 0.5,
  },
  footer: {
    padding: 20,
    backgroundColor: Colors.cardBackground,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  closeButton: {
    backgroundColor: Colors.textPrimary, // Navy-ish or Dark
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
  },
  closeButtonText: {
    color: Colors.textLight,
    fontWeight: '700',
    fontSize: 14,
    letterSpacing: 1,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: Colors.textSecondary,
  },
  errorText: {
    fontSize: 15,
    color: Colors.textPrimary,
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: Colors.todayAccent,
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: Colors.textLight,
    fontWeight: '600',
  },
  closeLink: {
    marginTop: 15,
  },
  closeLinkText: {
    color: Colors.textSecondary,
    fontSize: 14,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    color: Colors.textSecondary,
    fontStyle: 'italic',
  }
});
