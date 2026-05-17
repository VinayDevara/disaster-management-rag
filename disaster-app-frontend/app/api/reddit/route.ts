// // // // // import { NextResponse } from 'next/server';

// // // // // const KEYWORDS = [
// // // // //   'earthquake',
// // // // //   'flood',
// // // // //   'cyclone',
// // // // //   'storm',
// // // // //   'wildfire',
// // // // //   'landslide',
// // // // //   'evacuation',
// // // // //   'rescue',
// // // // // ];

// // // // // const SUBREDDITS = ['worldnews', 'news', 'india'];

// // // // // export async function GET() {
// // // // //   try {
// // // // //     const allPosts: any[] = [];

// // // // //     for (const subreddit of SUBREDDITS) {
// // // // //       const url = `https://www.reddit.com/r/${subreddit}/new.json?limit=20`;

// // // // //       const res = await fetch(url, {
// // // // //         headers: {
// // // // //           'User-Agent': 'Mozilla/5.0',
// // // // //           'Accept': 'application/json',
// // // // //         },
// // // // //         cache: 'no-store',
// // // // //       });

// // // // //       const text = await res.text();

// // // // //       if (!res.ok) {
// // // // //         console.error(`Reddit fetch failed for ${subreddit}:`, res.status, text);
// // // // //         continue;
// // // // //       }

// // // // //       let data;
// // // // //       try {
// // // // //         data = JSON.parse(text);
// // // // //       } catch (parseError) {
// // // // //         console.error(`Invalid JSON from ${subreddit}:`, text.slice(0, 300));
// // // // //         continue;
// // // // //       }

// // // // //       const posts = (data?.data?.children || []).map((item: any) => item.data);
// // // // //       allPosts.push(...posts);
// // // // //     }

// // // // //     const filteredPosts = allPosts
// // // // //       .filter((post: any) => {
// // // // //         const text = `${post.title || ''} ${post.selftext || ''}`.toLowerCase();
// // // // //         return KEYWORDS.some((keyword) => text.includes(keyword));
// // // // //       })
// // // // //       .map((post: any) => ({
// // // // //         id: post.id,
// // // // //         title: post.title,
// // // // //         subreddit: post.subreddit,
// // // // //         score: post.score,
// // // // //         created_utc: post.created_utc,
// // // // //         url: `https://www.reddit.com${post.permalink}`,
// // // // //       }))
// // // // //       .sort((a, b) => b.created_utc - a.created_utc)
// // // // //       .slice(0, 12);

// // // // //     return NextResponse.json(filteredPosts);
// // // // //   } catch (error: any) {
// // // // //     console.error('Route error:', error);
// // // // //     return NextResponse.json(
// // // // //       { error: error.message || 'Failed to fetch Reddit posts' },
// // // // //       { status: 500 }
// // // // //     );
// // // // //   }
// // // // // }
// // import { NextResponse } from 'next/server';

// // const DISASTER_KEYWORDS = [
// //   'earthquake',
// //   'flood',
// //   'flooding',
// //   'cyclone',
// //   'hurricane',
// //   'typhoon',
// //   'storm',
// //   'wildfire',
// //   'forest fire',
// //   'landslide',
// //   'tsunami',
// //   'evacuation',
// //   'rescue',
// //   'rainfall',
// //   'weather warning',
// //   'heatwave',
// //   'disaster',
// //   'severe weather',
// //   'monsoon',
// // ];

// // const EXCLUDE_KEYWORDS = [
// //   'wife',
// //   'husband',
// //   'celebrity',
// //   'actor',
// //   'actress',
// //   'tv',
// //   'show',
// //   'movie',
// //   'gladiators',
// //   'football',
// //   'cricket',
// //   'tennis',
// //   'abuse',
// //   'dating',
// //   'fashion',
// //   'music',
// //   'album',
// //   'box office',
// // ];

// // export async function GET() {
// //   try {
// //     const apiKey = process.env.GNEWS_API_KEY;

// //     if (!apiKey) {
// //       return NextResponse.json(
// //         { error: 'Missing GNEWS_API_KEY in .env.local' },
// //         { status: 500 }
// //       );
// //     }

// //     const query = encodeURIComponent(
// //       '(earthquake OR flood OR flooding OR cyclone OR hurricane OR typhoon OR storm OR wildfire OR landslide OR tsunami OR evacuation OR rescue OR rainfall OR weather warning OR heatwave OR disaster)'
// //     );

// //     const url = `https://gnews.io/api/v4/search?q=${query}&lang=en&max=30&apikey=${apiKey}`;

// //     const res = await fetch(url, { cache: 'no-store' });
// //     const data = await res.json();

// //     if (!res.ok) {
// //       return NextResponse.json(
// //         { error: data?.errors?.[0] || data?.message || 'Failed to fetch news' },
// //         { status: res.status }
// //       );
// //     }

// //     const filtered = (data.articles || []).filter((article: any) => {
// //       const text = `${article.title || ''} ${article.description || ''}`.toLowerCase();

// //       const hasDisasterKeyword = DISASTER_KEYWORDS.some((keyword) =>
// //         text.includes(keyword)
// //       );

// //       const hasExcludedKeyword = EXCLUDE_KEYWORDS.some((keyword) =>
// //         text.includes(keyword)
// //       );

// //       return hasDisasterKeyword && !hasExcludedKeyword;
// //     });

// //     const articles = filtered.slice(0, 10).map((article: any, index: number) => ({
// //     id: article.url || String(index),
// //     title: article.title || 'Untitled article',
// //     subreddit: article.source?.name || 'News',
// //     score: 1,
// //     created_utc: article.publishedAt
// //         ? Math.floor(new Date(article.publishedAt).getTime() / 1000)
// //         : Math.floor(Date.now() / 1000),
// //     url: article.url || '#',
// //     image: article.image || '',
// //     }));

// //     return NextResponse.json(articles);
// //   } catch (error: any) {
// //     return NextResponse.json(
// //       { error: error.message || 'Failed to fetch news' },
// //       { status: 500 }
// //     );
// //   }
// // }import { NextResponse } from 'next/server';

const DISASTER_KEYWORDS = [
  'earthquake',
  'flood',
  'flooding',
  'cyclone',
  'hurricane',
  'typhoon',
  'storm',
  'wildfire',
  'forest fire',
  'landslide',
  'tsunami',
  'evacuation',
  'rescue',
  'rainfall',
  'weather warning',
  'heatwave',
  'disaster',
  'severe weather',
  'monsoon',
  'cloudburst',
];

const INDIA_KEYWORDS = [
  'india',
  'indian',
  'delhi',
  'mumbai',
  'kolkata',
  'chennai',
  'hyderabad',
  'assam',
  'odisha',
  'maharashtra',
  'kerala',
  'tamil nadu',
  'gujarat',
  'rajasthan',
  'uttarakhand',
  'himachal',
  'andhra',
  'telangana',
  'karnataka',
  'bengaluru',
  'bangalore',
];

const KARNATAKA_KEYWORDS = [
  'karnataka',
  'bengaluru',
  'bangalore',
  'mysuru',
  'mangalore',
  'udupi',
  'hubli',
  'belagavi',
  'shivamogga',
  'kodagu',
  'coorg',
  'dakshina kannada',
  'uttara kannada',
  'hassan',
  'chikkamagaluru',
  'mandya',
  'tumakuru',
  'ballari',
  'raichur',
  'kalaburagi',
  'bidar',
];

const EXCLUDE_KEYWORDS = [
  'wife',
  'husband',
  'celebrity',
  'actor',
  'actress',
  'tv',
  'show',
  'movie',
  'football',
  'cricket score',
  'tennis',
  'dating',
  'fashion',
  'music',
  'album',
  'box office',
  'iphone',
  'android',
  'laptop',
  'stocks',
  'share market',
];

export async function GET(request: Request) {
  try {
    const apiKey = process.env.GNEWS_API_KEY;

    if (!apiKey) {
      return Response.json(
        { error: 'Missing GNEWS_API_KEY in .env.local' },
        { status: 500 }
      );
    }

    const { searchParams } = new URL(request.url);
    const region = searchParams.get('region') || 'india';

    // Keep API query broad and stable
    const query = encodeURIComponent(
      'earthquake OR flood OR cyclone OR storm OR wildfire OR landslide OR tsunami OR rainfall OR weather warning OR heatwave OR disaster'
    );

    const url = `https://gnews.io/api/v4/search?q=${query}&lang=en&max=50&apikey=${apiKey}`;

    // Cache the GNews response for 30 minutes (1800 seconds) to avoid rate limits.
    // The query is global; region filtering happens locally below.
    const res = await fetch(url, { next: { revalidate: 1800 } });
    const data = await res.json();

    if (!res.ok) {
      return Response.json(
        { error: data?.errors?.[0] || data?.message || 'Failed to fetch news' },
        { status: res.status }
      );
    }

    const filtered = (data.articles || []).filter((article: any) => {
      const text = `${article.title || ''} ${article.description || ''}`.toLowerCase();

      const hasDisasterKeyword = DISASTER_KEYWORDS.some((keyword) =>
        text.includes(keyword)
      );

      const hasExcludedKeyword = EXCLUDE_KEYWORDS.some((keyword) =>
        text.includes(keyword)
      );

      if (!hasDisasterKeyword || hasExcludedKeyword) {
        return false;
      }

      if (region === 'karnataka') {
        return KARNATAKA_KEYWORDS.some((keyword) => text.includes(keyword));
      }

      if (region === 'india') {
        return INDIA_KEYWORDS.some((keyword) => text.includes(keyword));
      }

      if (region !== 'global') {
        // Dynamic region based on geolocation state/city (e.g. "surathkal,karnataka")
        const localKeywords = region.toLowerCase().split(',');
        
        // If it's a dynamic location, check if it contains any of the location keywords (city or state)
        return localKeywords.some(keyword => {
          const kw = keyword.trim();
          return kw.length > 0 && (text.includes(kw) || text.includes(kw.split(' ')[0]));
        });
      }

      return true; // global
    });

    const articles = filtered.slice(0, 10).map((article: any, index: number) => ({
      id: article.url || String(index),
      title: article.title || 'Untitled article',
      source: article.source?.name || 'News',
      created_utc: article.publishedAt
        ? Math.floor(new Date(article.publishedAt).getTime() / 1000)
        : Math.floor(Date.now() / 1000),
      url: article.url || '#',
      image: article.image || '',
      description: article.description || '',
    }));

    return Response.json(articles);
  } catch (error: any) {
    return Response.json(
      { error: error.message || 'Failed to fetch news' },
      { status: 500 }
    );
  }
}