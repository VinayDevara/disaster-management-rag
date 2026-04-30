'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { User, Mail, Calendar } from 'lucide-react';

interface Profile {
  id: string;
  username: string;
  full_name: string;
  avatar_url: string;
  created_at: string;
}

export default function UserProfile() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (user) {
        const { data } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', user.id)
          .single();

        if (data) {
          setProfile(data);
          setFullName(data.full_name || '');
        }
      }
      setLoading(false);
    };

    fetchProfile();
  }, []);

  const handleUpdateProfile = async () => {
    if (!profile) return;

    const supabase = createClient();
    const { error } = await supabase
      .from('profiles')
      .update({ full_name: fullName })
      .eq('id', profile.id);

    if (!error) {
      setProfile({ ...profile, full_name: fullName });
      setEditing(false);
    }
  };

  if (loading) {
    return <div className="text-gray-400">Loading profile...</div>;
  }

  if (!profile) {
    return <div className="text-gray-400">Profile not found</div>;
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700/50 p-6 max-w-md">
      <div className="space-y-6">
        {/* Avatar */}
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
            <User className="w-8 h-8 text-white" />
          </div>
        </div>

        {/* Username */}
        <div>
          <p className="text-sm text-gray-400 mb-2">Email</p>
          <div className="flex items-center gap-2 p-3 bg-slate-700/30 rounded-lg border border-slate-600">
            <Mail className="w-4 h-4 text-blue-400" />
            <p className="text-white text-sm font-medium">{profile.username}</p>
          </div>
        </div>

        {/* Full Name */}
        <div>
          <Label className="text-gray-200 mb-2 block">Full Name</Label>
          {editing ? (
            <Input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="bg-slate-700/50 border-slate-600 text-white placeholder-gray-400"
            />
          ) : (
            <div className="p-3 bg-slate-700/30 rounded-lg border border-slate-600">
              <p className="text-white">{fullName || 'Not set'}</p>
            </div>
          )}
        </div>

        {/* Member Since */}
        <div>
          <p className="text-sm text-gray-400 mb-2">Member Since</p>
          <div className="flex items-center gap-2 p-3 bg-slate-700/30 rounded-lg border border-slate-600">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <p className="text-white text-sm">
              {new Date(profile.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>
        </div>

        {/* Edit Button */}
        <div className="flex gap-2">
          {editing ? (
            <>
              <Button
                onClick={handleUpdateProfile}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                Save Changes
              </Button>
              <Button
                onClick={() => {
                  setEditing(false);
                  setFullName(profile.full_name || '');
                }}
                variant="outline"
                className="flex-1 border-slate-600 text-gray-400 hover:bg-slate-700"
              >
                Cancel
              </Button>
            </>
          ) : (
            <Button
              onClick={() => setEditing(true)}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            >
              Edit Profile
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
