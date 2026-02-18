import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

const sampleDisasters = [
  {
    type: 'Earthquake',
    location: 'San Francisco, California',
    latitude: 37.7749,
    longitude: -122.4194,
    severity: 'critical',
    status: 'active',
    description: 'Major earthquake detected with magnitude 7.2. Emergency response initiated.',
    affected_people: 50000,
  },
  {
    type: 'Flood',
    location: 'Houston, Texas',
    latitude: 29.7604,
    longitude: -95.3698,
    severity: 'high',
    status: 'active',
    description: 'Severe flooding in downtown area. Evacuation underway.',
    affected_people: 35000,
  },
  {
    type: 'Wildfire',
    location: 'Los Angeles, California',
    latitude: 34.0522,
    longitude: -118.2437,
    severity: 'high',
    status: 'monitoring',
    description: 'Fast-moving wildfire threatening residential areas.',
    affected_people: 25000,
  },
  {
    type: 'Tornado',
    location: 'Oklahoma City, Oklahoma',
    latitude: 35.4676,
    longitude: -97.5164,
    severity: 'critical',
    status: 'active',
    description: 'EF5 tornado reported. Widespread damage and casualties.',
    affected_people: 15000,
  },
  {
    type: 'Hurricane',
    location: 'Miami, Florida',
    latitude: 25.7617,
    longitude: -80.1918,
    severity: 'high',
    status: 'monitoring',
    description: 'Category 4 hurricane approaching coast.',
    affected_people: 80000,
  },
  {
    type: 'Landslide',
    location: 'Seattle, Washington',
    latitude: 47.6062,
    longitude: -122.3321,
    severity: 'medium',
    status: 'resolved',
    description: 'Mudslide blocked major highway. Cleared.',
    affected_people: 5000,
  },
  {
    type: 'Blizzard',
    location: 'Denver, Colorado',
    latitude: 39.7392,
    longitude: -104.9903,
    severity: 'medium',
    status: 'monitoring',
    description: 'Heavy snow storm causing transportation disruptions.',
    affected_people: 45000,
  },
  {
    type: 'Tsunami',
    location: 'Honolulu, Hawaii',
    latitude: 21.3099,
    longitude: -157.8581,
    severity: 'high',
    status: 'active',
    description: 'Tsunami warning issued following earthquake.',
    affected_people: 20000,
  },
];

async function seedData() {
  try {
    console.log('Seeding database with sample disaster data...');

    // Insert disasters
    const { data: disasterData, error: disasterError } = await supabase
      .from('disasters')
      .insert(sampleDisasters)
      .select();

    if (disasterError) {
      console.error('Error inserting disasters:', disasterError);
      return;
    }

    console.log(`Successfully inserted ${disasterData.length} disaster records`);

    // Insert statistics for each disaster
    const statisticsData = [];
    for (const disaster of disasterData) {
      const stats = [
        {
          disaster_id: disaster.id,
          metric_name: 'response_teams',
          metric_value: Math.floor(Math.random() * 50) + 10,
          metric_unit: 'teams',
        },
        {
          disaster_id: disaster.id,
          metric_name: 'emergency_calls',
          metric_value: Math.floor(Math.random() * 5000) + 1000,
          metric_unit: 'calls',
        },
        {
          disaster_id: disaster.id,
          metric_name: 'casualties',
          metric_value: Math.floor(Math.random() * 500),
          metric_unit: 'people',
        },
        {
          disaster_id: disaster.id,
          metric_name: 'shelters_opened',
          metric_value: Math.floor(Math.random() * 100) + 5,
          metric_unit: 'shelters',
        },
        {
          disaster_id: disaster.id,
          metric_name: 'area_affected',
          metric_value: Math.floor(Math.random() * 500) + 10,
          metric_unit: 'sq_km',
        },
      ];
      statisticsData.push(...stats);
    }

    const { data: statsResult, error: statsError } = await supabase
      .from('disaster_statistics')
      .insert(statisticsData);

    if (statsError) {
      console.error('Error inserting statistics:', statsError);
      return;
    }

    console.log(`Successfully inserted ${statisticsData.length} statistics records`);
    console.log('Database seeding completed!');
  } catch (error) {
    console.error('Error seeding database:', error);
    process.exit(1);
  }
}

seedData();
