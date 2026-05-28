'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, MapPin, Users, Clock } from 'lucide-react';

interface Disaster {
  id: string;
  type: string;
  location: string;
  latitude: number;
  longitude: number;
  severity: string;
  status: string;
  affected_people: number;
  created_at: string;
}

const getSeverityColor = (severity: string) => {
  const colors = {
    low: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
    medium: 'bg-yellow-500/10 text-yellow-300 border-yellow-500/20',
    high: 'bg-orange-500/10 text-orange-300 border-orange-500/20',
    critical: 'bg-red-500/10 text-red-300 border-red-500/20',
  };
  return colors[severity as keyof typeof colors] || colors.low;
};

const getStatusIcon = (status: string) => {
  if (status === 'active') return '🔴';
  if (status === 'monitoring') return '🟡';
  return '🟢';
};

export default function DisasterStatusOverview() {
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDisasters = async () => {
      try {
        // Fetch real-time NDMA data first
        const ndmaRes = await fetch('/api/ndma?limit=10');
        if (ndmaRes.ok) {
          const ndmaData = await ndmaRes.json();
          if (ndmaData.data && ndmaData.data.length > 0) {
            console.log('[v0] DisasterStatusOverview: Fetched NDMA data', ndmaData.data.length);
            // Map NDMA data to Disaster interface
            const mappedNdmaDisasters = ndmaData.data.map((item: any) => ({
              id: item.id,
              type: item.type || 'Disaster',
              location: item.source || 'India',
              latitude: 20.5937, // Default India center
              longitude: 78.9629,
              severity: item.severity?.toLowerCase() || 'medium',
              status: item.status || 'active',
              affected_people: 0,
              created_at: item.published_at || new Date().toISOString(),
            }));
            setDisasters(mappedNdmaDisasters);
            setLoading(false);
            return;
          }
        }

        // Fallback to database disasters if NDMA API doesn't return data
        const supabase = createClient();
        const { data, error } = await supabase
          .from('disasters')
          .select('*')
          .order('created_at', { ascending: false })
          .limit(10);

        if (!error && data) {
          console.log('[v0] DisasterStatusOverview: Fetched database disasters', data.length);
          setDisasters(data);
        }
      } catch (error) {
        console.error('[v0] DisasterStatusOverview: Error fetching data', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDisasters();

    // Subscribe to realtime updates
    const supabase = createClient();
    const channel = supabase
      .channel('disasters_channel')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'disasters' },
        () => {
          fetchDisasters();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="h-40 bg-gray-200 dark:bg-slate-800/50 border-gray-300 dark:border-slate-700/50 animate-pulse" />
        ))}
      </div>
    );
  }

  const activeDisasters = disasters.filter(d => d.status === 'active').length;
  const totalAffected = disasters.reduce((sum, d) => sum + (d.affected_people || 0), 0);
  const criticalCount = disasters.filter(d => d.severity === 'critical').length;

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-900/5 border-red-200 dark:border-red-500/20 hover:border-red-300 dark:hover:border-red-500/40 transition-all">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-400 mb-2">Active Disasters</p>
                <p className="text-3xl font-bold text-red-600 dark:text-red-300">{activeDisasters}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-red-400 dark:text-red-500/50" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-900/5 border-orange-200 dark:border-orange-500/20 hover:border-orange-300 dark:hover:border-orange-500/40 transition-all">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-400 mb-2">Critical Events</p>
                <p className="text-3xl font-bold text-orange-600 dark:text-orange-300">{criticalCount}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-orange-400 dark:text-orange-500/50" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-900/5 border-blue-200 dark:border-blue-500/20 hover:border-blue-300 dark:hover:border-blue-500/40 transition-all">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-400 mb-2">Total Affected</p>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-300">{totalAffected.toLocaleString()}</p>
              </div>
              <Users className="w-10 h-10 text-blue-400 dark:text-blue-500/50" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100 dark:from-cyan-900/20 dark:to-cyan-900/5 border-cyan-200 dark:border-cyan-500/20 hover:border-cyan-300 dark:hover:border-cyan-500/40 transition-all">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-400 mb-2">Total Events</p>
                <p className="text-3xl font-bold text-cyan-600 dark:text-cyan-300">{disasters.length}</p>
              </div>
              <Clock className="w-10 h-10 text-cyan-400 dark:text-cyan-500/50" />
            </div>
          </div>
        </Card>
      </div>

      {/* Disasters List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {disasters.length > 0 ? (
          disasters.map(disaster => (
            <Card key={disaster.id} className="bg-gray-50 dark:bg-slate-800/50 border-gray-200 dark:border-slate-700/50 hover:border-gray-300 dark:hover:border-slate-600/50 transition-all hover:shadow-lg dark:hover:shadow-blue-500/10">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{getStatusIcon(disaster.status)}</span>
                      <h3 className="font-semibold text-lg text-gray-900 dark:text-white capitalize">{disaster.type}</h3>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      {disaster.location}
                    </p>
                  </div>
                  <Badge className={`${getSeverityColor(disaster.severity)} border`}>
                    {disaster.severity?.toUpperCase()}
                  </Badge>
                </div>

                <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">{disaster.description || 'No description available'}</p>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600 dark:text-gray-500">Affected People</p>
                    <p className="text-lg font-semibold text-cyan-600 dark:text-cyan-300">{disaster.affected_people?.toLocaleString() || 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-600 dark:text-gray-500">Status</p>
                    <p className="text-lg font-semibold text-green-600 dark:text-green-300 capitalize">{disaster.status}</p>
                  </div>
                </div>

                <div className="mt-4 text-xs text-gray-500 dark:text-gray-500">
                  {new Date(disaster.created_at).toLocaleDateString()} at {new Date(disaster.created_at).toLocaleTimeString()}
                </div>
              </div>
            </Card>
          ))
        ) : (
          <Card className="col-span-2 bg-gray-50 dark:bg-slate-800/50 border-gray-200 dark:border-slate-700/50 p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400">No active disasters to display</p>
          </Card>
        )}
      </div>
    </div>
  );
}
