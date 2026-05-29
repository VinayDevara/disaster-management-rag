import { createClient } from '@/lib/supabase/server';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { message, sessionId, userId } = await request.json();

    // Validate input
    if (!message || !userId) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Call your Python backend LLM service
    // Replace with your actual backend URL
    const backendUrl = process.env.LLM_BACKEND_URL || 'http://localhost:8000';
    
    try {
      const llmResponse = await fetch(`${backendUrl}/api/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: message }),
});

const llmData = await llmResponse.json();
const finalResponse = llmData.final_response || {};
const response = finalResponse.unified_response || finalResponse.answer || llmData.answer || 'No response received';
const trajectory_id = llmData.trajectory_id;

      // Save to chat history if sessionId provided
      if (sessionId) {
        const supabase = await createClient();
        const { data: chatData } = await supabase
          .from('chat_history')
          .select('messages')
          .eq('id', sessionId)
          .single();

        const messages = chatData?.messages || [];
        messages.push({
          role: 'user',
          content: message,
          timestamp: new Date().toISOString(),
        });
        messages.push({
          role: 'assistant',
          content: response,
          timestamp: new Date().toISOString(),
          trajectory_id: trajectory_id,
        });

        await supabase
          .from('chat_history')
          .update({
            messages,
            updated_at: new Date().toISOString(),
          })
          .eq('id', sessionId);
      }

      return NextResponse.json({ response, trajectory_id });
    } catch (error) {
      console.error('Error calling LLM backend:', error);
      // Fallback response if backend is unavailable
      const fallbackResponse = `I received your query: "${message}". 
        
The disaster management system is processing your request. Currently, the LLM backend is being initialized. Please try again shortly or contact support for real-time disaster information.

In the meantime, you can view the current disaster status in the dashboard above.`;

      return NextResponse.json({ response: fallbackResponse });
    }
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
