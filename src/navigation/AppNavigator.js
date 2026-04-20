import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { AttendanceScreen, ScheduleScreen } from '../screens';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();

export default function AppNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Asistencia') {
            iconName = focused ? 'finger-print' : 'finger-print-outline';
          } else if (route.name === 'Mi Horario') {
            iconName = focused ? 'calendar' : 'calendar-outline';
          }

          return <Ionicons name={iconName} size={size + 4} color={color} />;
        },
        tabBarActiveTintColor: Colors.tabActive,
        tabBarInactiveTintColor: Colors.tabInactive,
        tabBarStyle: {
          backgroundColor: Colors.tabBar,
          borderTopColor: Colors.tabBarBorder,
          borderTopWidth: 1,
          height: 70,
          paddingBottom: 10,
          paddingTop: 8,
          elevation: 8,
          shadowColor: Colors.shadow,
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.1,
          shadowRadius: 4,
        },
        tabBarLabelStyle: {
          fontSize: 13,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: Colors.background,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 1,
          borderBottomColor: Colors.tabBarBorder,
        },
        headerTitleStyle: {
          fontSize: 20,
          fontWeight: '700',
          color: Colors.textPrimary,
        },
        headerTitleAlign: 'center',
      })}
    >
      <Tab.Screen name="Asistencia" component={AttendanceScreen} />
      <Tab.Screen name="Mi Horario" component={ScheduleScreen} />
    </Tab.Navigator>
  );
}
