import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme';
import { getDeviceToken } from '../utils/storage';
import { fetchWeeklySchedule } from '../services/api';

// ── Helpers de formato ─────────────────────────────────────────
const DAY_NAMES = [
  'Domingo', 'Lunes', 'Martes', 'Miércoles',
  'Jueves', 'Viernes', 'Sábado',
];

const MONTH_NAMES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

function formatDateLabel(date) {
  const dayName = DAY_NAMES[date.getDay()];
  const day = date.getDate();
  const month = MONTH_NAMES[date.getMonth()];
  return { dayName, fullDate: `${day} de ${month}` };
}

function isToday(date) {
  const now = new Date();
  return (
    date.getDate() === now.getDate() &&
    date.getMonth() === now.getMonth() &&
    date.getFullYear() === now.getFullYear()
  );
}

/**
 * Genera los próximos N días laborales combinando fechas reales
 * con los horarios recibidos del backend.
 * @param {Array} apiSchedule - Horario semanal del backend [{day_of_week, start_time, end_time}]
 * @param {number} count - Cantidad de días a generar
 */
function getNextWorkDays(apiSchedule, count = 5) {
  // Convertir schedule del backend en un mapa day_of_week → horario
  // Backend usa 0=Lunes … 4=Viernes; JS usa 0=Domingo … 6=Sábado
  // Mapeo: backend_day → js_day:  0→1, 1→2, 2→3, 3→4, 4→5
  const scheduleMap = {};
  apiSchedule.forEach((s) => {
    const jsDay = s.day_of_week + 1; // backend 0=Lunes → JS 1=Lunes
    scheduleMap[jsDay] = {
      start: formatTime(s.start_time),
      end: formatTime(s.end_time),
    };
  });

  const days = [];
  const now = new Date();
  let cursor = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  while (days.length < count) {
    const jsDay = cursor.getDay();
    if (scheduleMap[jsDay]) {
      days.push({
        id: cursor.toISOString(),
        date: new Date(cursor),
        dayOfWeek: jsDay,
        start: scheduleMap[jsDay].start,
        end: scheduleMap[jsDay].end,
      });
    }
    cursor.setDate(cursor.getDate() + 1);
  }

  return days;
}

/**
 * Convierte "08:00" → "08:00 AM", "17:00" → "05:00 PM"
 */
function formatTime(timeStr) {
  if (!timeStr) return timeStr;
  const [h, m] = timeStr.split(':').map(Number);
  const suffix = h >= 12 ? 'PM' : 'AM';
  const hour12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${String(hour12).padStart(2, '0')}:${String(m).padStart(2, '0')} ${suffix}`;
}

// ── Componente de tarjeta de día ───────────────────────────────
function DayCard({ item }) {
  const today = isToday(item.date);
  const { dayName, fullDate } = formatDateLabel(item.date);

  return (
    <View style={[styles.card, today && styles.cardToday]}>
      {/* Indicador lateral */}
      <View style={[styles.cardStripe, today && styles.cardStripeToday]} />

      <View style={styles.cardContent}>
        {/* Encabezado: Día de la semana + badge "Hoy" */}
        <View style={styles.cardHeader}>
          <Text style={[styles.dayName, today && styles.dayNameToday]}>
            {dayName}
          </Text>
          {today && (
            <View style={styles.todayBadge}>
              <Text style={styles.todayBadgeText}>HOY</Text>
            </View>
          )}
        </View>

        {/* Fecha completa */}
        <Text style={[styles.fullDate, today && styles.fullDateToday]}>
          {fullDate}
        </Text>

        {/* Horario */}
        <View style={styles.timeRow}>
          <Ionicons
            name="time-outline"
            size={18}
            color={today ? Colors.todayAccent : Colors.textSecondary}
          />
          <Text style={[styles.timeText, today && styles.timeTextToday]}>
            {item.start} — {item.end}
          </Text>
        </View>
      </View>
    </View>
  );
}

// ── Pantalla principal ─────────────────────────────────────────
export default function ScheduleScreen() {
  const [workDays, setWorkDays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSchedule = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = await getDeviceToken();
      if (!token) {
        setWorkDays([]);
        setError('Dispositivo no vinculado');
        return;
      }

      const result = await fetchWeeklySchedule(token);

      if (result.error) {
        setError('No se pudo cargar el horario');
        setWorkDays([]);
        return;
      }

      const days = getNextWorkDays(result.schedule || [], 5);
      setWorkDays(days);
    } catch (err) {
      console.error('[Schedule] Error cargando horario:', err);
      setError('Error de conexión');
      setWorkDays([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSchedule();
  }, [loadSchedule]);

  if (loading) {
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color={Colors.todayAccent} />
        <Text style={styles.loadingText}>Cargando horario...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centeredContainer}>
        <Ionicons name="cloud-offline-outline" size={48} color={Colors.textSecondary} />
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Título de sección */}
      <View style={styles.sectionHeader}>
        <Ionicons name="calendar-outline" size={22} color={Colors.textSecondary} />
        <Text style={styles.sectionTitle}>Próximos días laborales</Text>
      </View>

      <FlatList
        data={workDays}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <DayCard item={item} />}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
      />
    </View>
  );
}

// ── Estilos ────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.surface,
  },
  centeredContainer: {
    flex: 1,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.textSecondary,
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 8,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  listContent: {
    padding: 16,
    paddingTop: 8,
  },

  // ─ Tarjeta ─
  card: {
    flexDirection: 'row',
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: Colors.shadow,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 8,
      },
      android: { elevation: 3 },
      web: {
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      },
    }),
  },
  cardToday: {
    backgroundColor: Colors.todayBackground,
    borderWidth: 1.5,
    borderColor: Colors.todayBorder,
  },

  // ─ Franja lateral decorativa ─
  cardStripe: {
    width: 5,
    backgroundColor: Colors.border,
  },
  cardStripeToday: {
    backgroundColor: Colors.todayAccent,
  },

  cardContent: {
    flex: 1,
    padding: 18,
    paddingLeft: 16,
  },

  // ─ Encabezado ─
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  dayName: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  dayNameToday: {
    color: Colors.todayAccent,
  },

  // ─ Badge "HOY" ─
  todayBadge: {
    marginLeft: 10,
    backgroundColor: Colors.todayAccent,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  todayBadgeText: {
    color: Colors.textLight,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
  },

  // ─ Fecha ─
  fullDate: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginBottom: 10,
  },
  fullDateToday: {
    color: Colors.todayAccent,
    fontWeight: '500',
  },

  // ─ Horario ─
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  timeText: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.textPrimary,
    letterSpacing: 0.3,
  },
  timeTextToday: {
    color: Colors.todayAccent,
  },
});
