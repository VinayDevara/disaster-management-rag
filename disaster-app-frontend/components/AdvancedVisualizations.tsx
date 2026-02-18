'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { Card } from '@/components/ui/card';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DisasterStats {
  type: string;
  count: number;
  severity: string;
  affected: number;
}

interface TimeSeriesData {
  date: string;
  events: number;
  affected: number;
}

const COLORS = ['#3b82f6', '#ef4444', '#f97316', '#eab308', '#10b981', '#06b6d4', '#8b5cf6', '#ec4899'];

export default function AdvancedVisualizations() {
  const [disasterTypes, setDisasterTypes] = useState([]);
  const [severityData, setSeverityData] = useState([]);
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [locationData, setLocationData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      const supabase = createClient();

      // Fetch disaster types count
      const { data: disasterTypeData } = await supabase
        .from('disasters')
        .select('type')
        .order('created_at', { ascending: false });

      if (disasterTypeData) {
        const typeCount = disasterTypeData.reduce((acc, d) => {
          const existing = acc.find(item => item.name === d.type);
          if (existing) {
            existing.value++;
          } else {
            acc.push({ name: d.type, value: 1 });
          }
          return acc;
        }, [] as any[]);
        setDisasterTypes(typeCount);
      }

      // Fetch severity distribution
      const { data: severityDataRaw } = await supabase
        .from('disasters')
        .select('severity');

      if (severityDataRaw) {
        const severityCount = severityDataRaw.reduce((acc, d) => {
          const existing = acc.find(item => item.name === d.severity);
          if (existing) {
            existing.value++;
          } else {
            acc.push({ name: d.severity || 'Unknown', value: 1 });
          }
          return acc;
        }, [] as any[]);
        setSeverityData(severityCount);
      }

      // Fetch location distribution
      const { data: locationDataRaw } = await supabase
        .from('disasters')
        .select('location')
        .order('created_at', { ascending: false })
        .limit(10);

      if (locationDataRaw) {
        const locCount = locationDataRaw.reduce((acc, d) => {
          const existing = acc.find(item => item.name === d.location);
          if (existing) {
            existing.count++;
          } else {
            acc.push({ name: d.location, count: 1 });
          }
          return acc;
        }, [] as any[]);
        setLocationData(locCount.slice(0, 8));
      }

      // Generate time series data (mock data with last 30 days)
      const mockTimeSeries = Array.from({ length: 30 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (29 - i));
        return {
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          events: Math.floor(Math.random() * 15) + 2,
          affected: Math.floor(Math.random() * 5000) + 500,
        };
      });
      setTimeSeriesData(mockTimeSeries);

      setLoading(false);
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="h-80 bg-slate-800/50 border-slate-700/50 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Disaster Types Pie Chart */}
      <Card className="bg-slate-800/50 border-slate-700/50 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Disasters by Type</h3>
        {disasterTypes.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={disasterTypes}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {disasterTypes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center text-gray-400">
            No data available
          </div>
        )}
      </Card>

      {/* Severity Distribution Pie Chart */}
      <Card className="bg-slate-800/50 border-slate-700/50 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Severity Distribution</h3>
        {severityData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {severityData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.name === 'critical'
                        ? '#ef4444'
                        : entry.name === 'high'
                          ? '#f97316'
                          : entry.name === 'medium'
                            ? '#eab308'
                            : '#10b981'
                    }
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center text-gray-400">
            No data available
          </div>
        )}
      </Card>

      {/* Events Over Time */}
      <Card className="bg-slate-800/50 border-slate-700/50 p-6 lg:col-span-2">
        <h3 className="text-lg font-semibold text-white mb-4">Events Trend (Last 30 Days)</h3>
        {timeSeriesData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timeSeriesData}>
              <defs>
                <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="date" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Area
                type="monotone"
                dataKey="events"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorEvents)"
                name="Events"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center text-gray-400">
            No data available
          </div>
        )}
      </Card>

      {/* Top Affected Locations Bar Chart */}
      <Card className="bg-slate-800/50 border-slate-700/50 p-6 lg:col-span-2">
        <h3 className="text-lg font-semibold text-white mb-4">Most Affected Locations</h3>
        {locationData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={locationData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="name" stroke="#94a3b8" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="count" fill="#06b6d4" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center text-gray-400">
            No data available
          </div>
        )}
      </Card>

      {/* People Affected Trend */}
      <Card className="bg-slate-800/50 border-slate-700/50 p-6 lg:col-span-2">
        <h3 className="text-lg font-semibold text-white mb-4">People Affected Trend</h3>
        {timeSeriesData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeSeriesData}>
              <defs>
                <linearGradient id="colorAffected" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="date" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="affected"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                name="People Affected"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center text-gray-400">
            No data available
          </div>
        )}
      </Card>
    </div>
  );
}
