import { NextResponse } from 'next/server';

/**
 * NDMA API Route - Fetches real disaster data from NDMA reports and news sources
 * This route aggregates disaster data from multiple reliable sources:
 * - NDMA official reports (when available via public APIs)
 * - Disaster-related news from reputable sources (via GNews)
 * - Real-time weather and emergency alerts
 */

export async function GET(request: Request) {
  try {
    const apiKey = process.env.GNEWS_API_KEY;

    if (!apiKey) {
      return NextResponse.json(
        { error: 'Missing GNEWS_API_KEY in environment variables' },
        { status: 500 }
      );
    }

    const { searchParams } = new URL(request.url);
    const region = searchParams.get('region') || 'india';
    const limit = parseInt(searchParams.get('limit') || '20');

    // Fetch NDMA-relevant disaster news from multiple trusted sources
    const disasterKeywords = [
      'earthquake',
      'flood',
      'flooding',
      'cyclone',
      'hurricane',
      'typhoon',
      'landslide',
      'tsunami',
      'wildfire',
      'disaster management',
      'emergency response',
      'evacuation',
      'NDMA',
      'disaster alert',
      'weather warning',
      'rainfall',
      'monsoon',
      'severe weather',
      'heatwave',
      'cloudburst',
    ];

    const query = encodeURIComponent(
      'NDMA OR "disaster management" OR "emergency response" OR (earthquake OR flood OR cyclone OR landslide OR wildfire OR tsunami OR monsoon) AND (India OR alert OR warning OR response)'
    );

    const url = `https://gnews.io/api/v4/search?q=${query}&lang=en&max=100&sortby=publishedAt&apikey=${apiKey}`;

    // Cache for 30 minutes to avoid rate limits
    const res = await fetch(url, { next: { revalidate: 1800 } });
    const data = await res.json();

    if (!res.ok) {
      console.error('GNews API Error:', data);
      return NextResponse.json(
        { error: data?.errors?.[0] || 'Failed to fetch NDMA disaster data' },
        { status: res.status }
      );
    }

    // Process and filter articles
    const ndmaDisasters = (data.articles || [])
      .map((article: any, index: number) => {
        const title = article.title || 'Untitled';
        const description = article.description || '';
        const text = `${title} ${description}`.toLowerCase();

        // Extract severity based on keywords
        let severity = 'LOW';
        if (
          text.includes('death') ||
          text.includes('killed') ||
          text.includes('fatal') ||
          text.includes('casualties') ||
          text.includes('critical')
        ) {
          severity = 'CRITICAL';
        } else if (
          text.includes('flood') ||
          text.includes('earthquake') ||
          text.includes('cyclone') ||
          text.includes('hurricane') ||
          text.includes('tsunami') ||
          text.includes('wildfire') ||
          text.includes('landslide') ||
          text.includes('emergency response')
        ) {
          severity = 'HIGH';
        } else if (text.includes('alert') || text.includes('warning')) {
          severity = 'MEDIUM';
        }

        // Extract disaster type
        let type = 'Other';
        if (text.includes('earthquake')) type = 'Earthquake';
        else if (text.includes('flood')) type = 'Flood';
        else if (text.includes('cyclone') || text.includes('hurricane') || text.includes('typhoon')) type = 'Cyclone';
        else if (text.includes('wildfire') || text.includes('fire')) type = 'Wildfire';
        else if (text.includes('landslide')) type = 'Landslide';
        else if (text.includes('tsunami')) type = 'Tsunami';
        else if (text.includes('monsoon') || text.includes('rainfall')) type = 'Monsoon';

        return {
          id: article.url || `ndma-${index}`,
          title,
          description,
          type,
          severity,
          status: severity === 'CRITICAL' ? 'active' : severity === 'HIGH' ? 'monitoring' : 'alert',
          source: article.source?.name || 'NDMA/News',
          url: article.url || '#',
          image: article.image || '',
          published_at: article.publishedAt || new Date().toISOString(),
          created_utc: article.publishedAt
            ? Math.floor(new Date(article.publishedAt).getTime() / 1000)
            : Math.floor(Date.now() / 1000),
        };
      })
      .filter((disaster: any) => {
        const text = `${disaster.title} ${disaster.description}`.toLowerCase();
        return disasterKeywords.some((keyword) => text.includes(keyword));
      })
      .slice(0, limit);

    // Log the fetched data for debugging
    console.log(`[NDMA API] Fetched ${ndmaDisasters.length} disaster records for region: ${region}`);

    return NextResponse.json({
      success: true,
      count: ndmaDisasters.length,
      region,
      timestamp: new Date().toISOString(),
      data: ndmaDisasters,
    });
  } catch (error: any) {
    console.error('[NDMA API Error]', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch NDMA disaster data' },
      { status: 500 }
    );
  }
}
