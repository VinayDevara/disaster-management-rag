import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function setupDatabase() {
  try {
    console.log('Setting up database...');

    // Create profiles table
    const { error: profilesError } = await supabase.rpc('exec', {
      sql: `
        CREATE TABLE IF NOT EXISTS profiles (
          id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
          username TEXT UNIQUE NOT NULL,
          full_name TEXT,
          avatar_url TEXT,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "Users can view their own profile" ON profiles
          FOR SELECT USING (auth.uid() = id);

        CREATE POLICY "Users can update their own profile" ON profiles
          FOR UPDATE USING (auth.uid() = id);

        CREATE POLICY "Users can insert their own profile" ON profiles
          FOR INSERT WITH CHECK (auth.uid() = id);
      `
    });

    // Create chat_history table
    const { error: chatError } = await supabase.rpc('exec', {
      sql: `
        CREATE TABLE IF NOT EXISTS chat_history (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
          title TEXT NOT NULL,
          messages JSONB DEFAULT '[]',
          created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "Users can view their own chat history" ON chat_history
          FOR SELECT USING (auth.uid() = user_id);

        CREATE POLICY "Users can create chat history" ON chat_history
          FOR INSERT WITH CHECK (auth.uid() = user_id);

        CREATE POLICY "Users can update their own chat history" ON chat_history
          FOR UPDATE USING (auth.uid() = user_id);

        CREATE POLICY "Users can delete their own chat history" ON chat_history
          FOR DELETE USING (auth.uid() = user_id);
      `
    });

    // Create disasters table
    const { error: disastersError } = await supabase.rpc('exec', {
      sql: `
        CREATE TABLE IF NOT EXISTS disasters (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          type TEXT NOT NULL,
          location TEXT NOT NULL,
          latitude DECIMAL(10, 8),
          longitude DECIMAL(11, 8),
          severity TEXT,
          status TEXT DEFAULT 'active',
          description TEXT,
          affected_people INTEGER,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        ALTER TABLE disasters ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "Anyone can view disasters" ON disasters FOR SELECT USING (true);
      `
    });

    // Create disaster_statistics table
    const { error: statsError } = await supabase.rpc('exec', {
      sql: `
        CREATE TABLE IF NOT EXISTS disaster_statistics (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          disaster_id UUID NOT NULL REFERENCES disasters(id) ON DELETE CASCADE,
          metric_name TEXT NOT NULL,
          metric_value DECIMAL(15, 2),
          created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        ALTER TABLE disaster_statistics ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "Anyone can view statistics" ON disaster_statistics FOR SELECT USING (true);
      `
    });

    console.log('Database setup completed!');
  } catch (error) {
    console.error('Error setting up database:', error);
    process.exit(1);
  }
}

setupDatabase();
