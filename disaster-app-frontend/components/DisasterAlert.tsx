'use client';

import { AlertTriangle, Bell, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useState, useEffect } from 'react';

interface Alert {
  id: string;
  type: 'critical' | 'high' | 'medium' | 'info';
  title: string;
  message: string;
  duration?: number;
}

export function DisasterAlert({ alert, onClose }: { alert: Alert; onClose: () => void }) {
  useEffect(() => {
    if (alert.duration) {
      const timer = setTimeout(onClose, alert.duration);
      return () => clearTimeout(timer);
    }
  }, [alert, onClose]);

  const bgColors = {
    critical: 'bg-red-500/10 border-red-500/30',
    high: 'bg-orange-500/10 border-orange-500/30',
    medium: 'bg-yellow-500/10 border-yellow-500/30',
    info: 'bg-blue-500/10 border-blue-500/30',
  };

  const textColors = {
    critical: 'text-red-300',
    high: 'text-orange-300',
    medium: 'text-yellow-300',
    info: 'text-blue-300',
  };

  const iconColors = {
    critical: 'text-red-400',
    high: 'text-orange-400',
    medium: 'text-yellow-400',
    info: 'text-blue-400',
  };

  return (
    <div className={`flex gap-3 p-4 border rounded-lg ${bgColors[alert.type]} animate-slide-in-top`}>
      <div className="flex-shrink-0 mt-0.5">
        {alert.type === 'critical' ? (
          <AlertTriangle className={`w-5 h-5 ${iconColors[alert.type]}`} />
        ) : (
          <Bell className={`w-5 h-5 ${iconColors[alert.type]}`} />
        )}
      </div>
      <div className="flex-1">
        <h4 className={`font-semibold text-sm ${textColors[alert.type]}`}>{alert.title}</h4>
        <p className={`text-xs ${textColors[alert.type]} opacity-80 mt-0.5`}>{alert.message}</p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={onClose}
        className={`flex-shrink-0 ${textColors[alert.type]} hover:${bgColors[alert.type]}`}
      >
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
}

export function AlertContainer() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const removeAlert = (id: string) => {
    setAlerts(alerts => alerts.filter(a => a.id !== id));
  };

  return (
    <div className="fixed bottom-4 right-4 space-y-2 w-96 max-h-96 overflow-y-auto z-50">
      {alerts.map(alert => (
        <DisasterAlert key={alert.id} alert={alert} onClose={() => removeAlert(alert.id)} />
      ))}
    </div>
  );
}
