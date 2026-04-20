import React, { useMemo } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme';

// ── Datos mock de horario semanal ──────────────────────────────
const MOCK_SCHEDULE = {
  defaultStart: '08:00 AM',
  defaultEnd: '05:00 PM',
  // Días no laborales (0=Domingo, 6=Sábado)
  daysOff: [0, 6],
};

/**
 * Genera los próximos N días laborales a partir de hoy.
 */
function getNextWorkDays(count = 5) {
  const days = [];
  const now = new Date();
  let cursor = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  while (days.length < count) {
    const dayOfWeek = cursor.getDay();
    if (!MOCK_SCHEDULE.daysOff.includes(dayOfWeek)) {
      days.push({
        id: cursor.toISOString(),
        date: new Date(cursor),
        dayOfWeek,
        start: MOCK_SCHEDULE.defaultStart,
        end: MOCK_SCHEDULE.defaultEnd,
      });
    }
    cursor.setDate(cursor.getDate() + 1);
  }

  return days;
}

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
  const workDays = useMemo(() => getNextWorkDays(5), []);

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
