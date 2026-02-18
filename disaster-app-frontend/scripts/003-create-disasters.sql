-- Create disasters table
CREATE TABLE IF NOT EXISTS public.disasters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL,
  location TEXT NOT NULL,
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'monitoring')),
  description TEXT,
  affected_people INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable Row Level Security
ALTER TABLE public.disasters ENABLE ROW LEVEL SECURITY;

-- Anyone can view active disasters
CREATE POLICY "Anyone can view disasters" ON public.disasters 
  FOR SELECT USING (true);

-- Create disaster_statistics table
CREATE TABLE IF NOT EXISTS public.disaster_statistics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disaster_id UUID NOT NULL REFERENCES public.disasters(id) ON DELETE CASCADE,
  metric_name TEXT NOT NULL,
  metric_value DECIMAL(15, 2),
  metric_unit TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable Row Level Security
ALTER TABLE public.disaster_statistics ENABLE ROW LEVEL SECURITY;

-- Anyone can view statistics
CREATE POLICY "Anyone can view statistics" ON public.disaster_statistics 
  FOR SELECT USING (true);

-- Create indexes for performance
CREATE INDEX idx_disasters_status ON public.disasters(status);
CREATE INDEX idx_disasters_type ON public.disasters(type);
CREATE INDEX idx_disasters_created_at ON public.disasters(created_at DESC);
CREATE INDEX idx_disaster_stats_disaster_id ON public.disaster_statistics(disaster_id);
