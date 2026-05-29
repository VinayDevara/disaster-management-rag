// 'use client';

// import { useEffect, useState } from 'react';

// type NewsPost = {
//   id: string;
//   title: string;
//   source: string;
//   created_utc: number;
//   url: string;
//   image?: string;
//   description?: string;
// };

// type RegionType = 'india' | 'karnataka' | 'global';

// export default function SocialSignalsPanel() {
//   const [posts, setPosts] = useState<NewsPost[]>([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState('');
//   const [regionFilter, setRegionFilter] = useState<RegionType>('india');

//   useEffect(() => {
//     const fetchPosts = async () => {
//       try {
//         setLoading(true);
//         setError('');

//         const res = await fetch(`/api/reddit?region=${regionFilter}`);
//         const data = await res.json();

//         if (!res.ok) {
//           throw new Error(data.error || 'Failed to fetch posts');
//         }

//         setPosts(data);
//       } catch (err: any) {
//         setError(err.message || 'Something went wrong');
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchPosts();
//   }, [regionFilter]);

//   const formatTime = (createdUtc: number) => {
//     return new Date(createdUtc * 1000).toLocaleString([], {
//       day: '2-digit',
//       month: 'short',
//       hour: '2-digit',
//       minute: '2-digit',
//     });
//   };

//   const getSeverity = (title: string) => {
//     const text = title.toLowerCase();

//     if (
//       text.includes('death') ||
//       text.includes('deaths') ||
//       text.includes('killed') ||
//       text.includes('critical') ||
//       text.includes('massive') ||
//       text.includes('devastating')
//     ) {
//       return 'CRITICAL';
//     }

//     if (
//       text.includes('flood') ||
//       text.includes('earthquake') ||
//       text.includes('cyclone') ||
//       text.includes('wildfire') ||
//       text.includes('landslide') ||
//       text.includes('tsunami') ||
//       text.includes('hurricane') ||
//       text.includes('typhoon')
//     ) {
//       return 'HIGH';
//     }

//     return 'MEDIUM';
//   };

//   const getSeverityClasses = (title: string) => {
//     const severity = getSeverity(title);

//     if (severity === 'CRITICAL') {
//       return 'bg-red-600/90 text-white border border-red-400/40';
//     }

//     if (severity === 'HIGH') {
//       return 'bg-orange-500/90 text-white border border-orange-300/40';
//     }

//     return 'bg-yellow-400/90 text-black border border-yellow-200/40';
//   };

//   const getRegionButtonClasses = (value: RegionType) => {
//     return regionFilter === value
//       ? 'bg-blue-500 text-white border-blue-400'
//       : 'bg-slate-900/70 text-slate-300 border-slate-700 hover:border-blue-400/40 hover:text-white';
//   };

//   return (
//     <div className="rounded-3xl border border-slate-800/80 bg-slate-950/40 backdrop-blur-sm p-6 shadow-[0_0_30px_rgba(0,0,0,0.25)]">
//       <div className="flex flex-col gap-4 mb-6 lg:flex-row lg:items-center lg:justify-between">
//        <div>
//       <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
//         Live Disaster & Weather Signals
//       </h3>
//       <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
//         Region-filtered disaster and weather news for situational awareness
//       </p>
//     </div>

//         <div className="flex flex-wrap gap-3">
//           <button
//             type="button"
//             onClick={() => setRegionFilter('india')}
//             className={`px-4 py-2 rounded-full border text-sm font-medium transition ${getRegionButtonClasses(
//               'india'
//             )}`}
//           >
//             India
//           </button>
//           <button
//             type="button"
//             onClick={() => setRegionFilter('karnataka')}
//             className={`px-4 py-2 rounded-full border text-sm font-medium transition ${getRegionButtonClasses(
//               'karnataka'
//             )}`}
//           >
//             Karnataka
//           </button>
//           <button
//             type="button"
//             onClick={() => setRegionFilter('global')}
//             className={`px-4 py-2 rounded-full border text-sm font-medium transition ${getRegionButtonClasses(
//               'global'
//             )}`}
//           >
//             Global
//           </button>
//         </div>
//       </div>

//       {loading && (
//         <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
//           {[1, 2, 3, 4].map((item) => (
//             <div
//               key={item}
//               className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden animate-pulse"
//             >
//               <div className="h-44 bg-slate-800" />
//               <div className="p-4 space-y-3">
//                 <div className="h-4 bg-slate-800 rounded w-3/4" />
//                 <div className="h-4 bg-slate-800 rounded w-full" />
//                 <div className="h-4 bg-slate-800 rounded w-2/3" />
//               </div>
//             </div>
//           ))}
//         </div>
//       )}

//       {!loading && error && (
//         <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
//           {error}
//         </div>
//       )}

//       {!loading && !error && posts.length === 0 && (
//         <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-slate-400">
//           No disaster-related news found for this region.
//         </div>
//       )}

//       {!loading && !error && posts.length > 0 && (
//         <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
//           {posts.map((post) => (
//             <a
//               key={post.id}
//               href={post.url}
//               target="_blank"
//               rel="noreferrer"
//               className="group rounded-2xl overflow-hidden border border-slate-800 bg-slate-900/80 hover:bg-slate-900 transition-all duration-300 hover:border-blue-500/40 hover:shadow-[0_0_24px_rgba(59,130,246,0.12)]"
//             >
//               <div className="relative w-full h-52 bg-slate-800 overflow-hidden">
//                 {post.image ? (
//                   <img
//                     src={post.image}
//                     alt={post.title}
//                     className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
//                   />
//                 ) : (
//                   <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
//                     No image available
//                   </div>
//                 )}

//                 <div className="absolute top-3 right-3">
//                   <span
//                     className={`text-xs font-semibold px-3 py-1 rounded-full backdrop-blur-sm ${getSeverityClasses(
//                       post.title
//                     )}`}
//                   >
//                     {getSeverity(post.title)}
//                   </span>
//                 </div>
//               </div>

//               <div className="p-4">
//                 <div className="flex items-center gap-3 text-xs text-slate-400 mb-3">
//                   <span className="truncate max-w-[140px]">{post.source}</span>
//                   <span className="w-1 h-1 rounded-full bg-slate-500" />
//                   <span>{formatTime(post.created_utc)}</span>
//                 </div>

//                 <h4 className="text-white font-semibold text-lg leading-snug line-clamp-2 group-hover:text-blue-300 transition-colors">
//                   {post.title}
//                 </h4>

//                 {post.description && (
//                   <p className="mt-2 text-sm text-slate-400 line-clamp-2">
//                     {post.description}
//                   </p>
//                 )}

//                 <div className="mt-4 flex items-center justify-between">
//                   <span className="text-sm text-slate-500">
//                     {regionFilter === 'karnataka'
//                       ? 'Karnataka focus'
//                       : regionFilter === 'india'
//                       ? 'India focus'
//                       : 'Global feed'}
//                   </span>
//                   <span className="text-blue-400 group-hover:text-blue-300 text-sm font-medium">
//                     Read more →
//                   </span>
//                 </div>
//               </div>
//             </a>
//           ))}
//         </div>
//       )}
//     </div>
//   );
// }
'use client';

import { useEffect, useState } from 'react';

type NewsPost = {
  id: string;
  title: string;
  source: string;
  created_utc: number;
  url: string;
  image?: string;
  description?: string;
};

type RegionType = 'current location' | 'india' | 'global';
type DetectedRegionType = 'india' | 'global';

export default function SocialSignalsPanel() {
  const [posts, setPosts] = useState<NewsPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [regionFilter, setRegionFilter] = useState<RegionType>('current location');
  const [detectedRegion, setDetectedRegion] = useState<DetectedRegionType>('india');
  const [locationStatus, setLocationStatus] = useState('Detecting your location...');

  useEffect(() => {
    if (!navigator.geolocation) {
      setDetectedRegion('india');
      setLocationStatus('Geolocation not supported. Showing India news.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
          );

          if (!res.ok) {
            throw new Error('Failed to reverse geocode location');
          }

          const data = await res.json();
          const country = data.address?.country?.toLowerCase() || '';

          if (country.includes('india')) {
            setDetectedRegion('india');
            setLocationStatus('Showing news based on your current location in India.');
          } else {
            setDetectedRegion('global');
            setLocationStatus('Showing global news based on your current location.');
          }
        } catch (err) {
          console.error('Reverse geocoding failed:', err);
          setDetectedRegion('india');
          setLocationStatus('Could not detect exact region. Showing India news.');
        }
      },
      (err) => {
        console.warn('Geolocation permission not available or denied:', err.message || `Code: ${err.code}`);
        setDetectedRegion('india');
        setLocationStatus('Location permission denied. Showing India news.');
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000,
      }
    );
  }, []);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        setLoading(true);
        setError('');

        const effectiveRegion =
          regionFilter === 'current location' ? detectedRegion : regionFilter;

        const res = await fetch(`/api/reddit?region=${effectiveRegion}`);
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.error || 'Failed to fetch posts');
        }

        setPosts(data);
      } catch (err: any) {
        setError(err.message || 'Something went wrong');
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, [regionFilter, detectedRegion]);

  const formatTime = (createdUtc: number) => {
    return new Date(createdUtc * 1000).toLocaleString([], {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getSeverity = (title: string) => {
    const text = title.toLowerCase();

    if (
      text.includes('death') ||
      text.includes('deaths') ||
      text.includes('killed') ||
      text.includes('critical') ||
      text.includes('massive') ||
      text.includes('devastating')
    ) {
      return 'CRITICAL';
    }

    if (
      text.includes('flood') ||
      text.includes('earthquake') ||
      text.includes('cyclone') ||
      text.includes('wildfire') ||
      text.includes('landslide') ||
      text.includes('tsunami') ||
      text.includes('hurricane') ||
      text.includes('typhoon')
    ) {
      return 'HIGH';
    }

    return 'MEDIUM';
  };

  const getSeverityClasses = (title: string) => {
    const severity = getSeverity(title);

    if (severity === 'CRITICAL') {
      return 'bg-red-600/90 text-white border border-red-400/40';
    }

    if (severity === 'HIGH') {
      return 'bg-orange-500/90 text-white border border-orange-300/40';
    }

    return 'bg-yellow-400/90 text-black border border-yellow-200/40';
  };

  const getRegionButtonClasses = (value: RegionType) => {
    return regionFilter === value
      ? 'bg-blue-500 text-white border-blue-400'
      : 'bg-slate-900/70 text-slate-300 border-slate-700 hover:border-blue-400/40 hover:text-white';
  };

  const getRegionLabel = () => {
    if (regionFilter === 'current location') {
      return detectedRegion === 'india'
        ? 'Current location • India'
        : 'Current location • Global';
    }

    if (regionFilter === 'india') {
      return 'India focus';
    }

    return 'Global feed';
  };

  return (
    <div className="rounded-3xl border border-slate-800/80 bg-slate-950/40 backdrop-blur-sm p-6 shadow-[0_0_30px_rgba(0,0,0,0.25)]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
            Live Disaster & Weather Signals
          </h3>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Region-filtered disaster and weather news for situational awareness
          </p>

          {regionFilter === 'current location' && (
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              {locationStatus}
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setRegionFilter('current location')}
            className={`rounded-full border px-4 py-2 text-sm font-medium transition ${getRegionButtonClasses(
              'current location'
            )}`}
          >
            Current Location
          </button>

          <button
            type="button"
            onClick={() => setRegionFilter('india')}
            className={`rounded-full border px-4 py-2 text-sm font-medium transition ${getRegionButtonClasses(
              'india'
            )}`}
          >
            India
          </button>

          <button
            type="button"
            onClick={() => setRegionFilter('global')}
            className={`rounded-full border px-4 py-2 text-sm font-medium transition ${getRegionButtonClasses(
              'global'
            )}`}
          >
            Global
          </button>
        </div>
      </div>

      {loading && (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {[1, 2, 3, 4].map((item) => (
            <div
              key={item}
              className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 animate-pulse"
            >
              <div className="h-44 bg-slate-800" />
              <div className="space-y-3 p-4">
                <div className="h-4 w-3/4 rounded bg-slate-800" />
                <div className="h-4 w-full rounded bg-slate-800" />
                <div className="h-4 w-2/3 rounded bg-slate-800" />
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
          {error}
        </div>
      )}

      {!loading && !error && posts.length === 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-slate-400">
          No disaster-related news found for this region.
        </div>
      )}

      {!loading && !error && posts.length > 0 && (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {posts.map((post) => (
            <a
              key={post.id}
              href={post.url}
              target="_blank"
              rel="noreferrer"
              className="group overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 transition-all duration-300 hover:border-blue-500/40 hover:bg-slate-900 hover:shadow-[0_0_24px_rgba(59,130,246,0.12)]"
            >
              <div className="relative h-52 w-full overflow-hidden bg-slate-800">
                {post.image ? (
                  <img
                    src={post.image}
                    alt={post.title}
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-sm text-slate-500">
                    No image available
                  </div>
                )}

                <div className="absolute right-3 top-3">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold backdrop-blur-sm ${getSeverityClasses(
                      post.title
                    )}`}
                  >
                    {getSeverity(post.title)}
                  </span>
                </div>
              </div>

              <div className="p-4">
                <div className="mb-3 flex items-center gap-3 text-xs text-slate-400">
                  <span className="max-w-[140px] truncate">{post.source}</span>
                  <span className="h-1 w-1 rounded-full bg-slate-500" />
                  <span>{formatTime(post.created_utc)}</span>
                </div>

                <h4 className="line-clamp-2 text-lg font-semibold leading-snug text-white transition-colors group-hover:text-blue-300">
                  {post.title}
                </h4>

                {post.description && (
                  <p className="mt-2 line-clamp-2 text-sm text-slate-400">
                    {post.description}
                  </p>
                )}

                <div className="mt-4 flex items-center justify-between">
                  <span className="text-sm text-slate-500">{getRegionLabel()}</span>
                  <span className="text-sm font-medium text-blue-400 group-hover:text-blue-300">
                    Read more →
                  </span>
                </div>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}