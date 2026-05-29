import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { trajectory_id, method } = await request.json();

    // Call Python backend audit service
    const backendUrl = process.env.LLM_BACKEND_URL || 'http://localhost:8000';
    
    try {
      const auditResponse = await fetch(`${backendUrl}/api/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trajectory_id, method }),
      });

      const auditData = await auditResponse.json();
      return NextResponse.json(auditData);
    } catch (error) {
      console.error('Error calling LLM backend audit:', error);
      return NextResponse.json(
        { error: 'LLM backend audit is currently unavailable.' },
        { status: 503 }
      );
    }
  } catch (error) {
    console.error('API Error in Next.js audit route:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
