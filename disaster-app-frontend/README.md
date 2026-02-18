# Disaster Management Dashboard

A modern, real-time disaster management system with AI-powered chat assistance, real-time status monitoring, and advanced analytics.

## Features

### Real-Time Monitoring
- Live disaster event tracking
- Real-time status updates
- Multi-location monitoring
- Severity classification (Low, Medium, High, Critical)

### AI-Powered Chat Assistant
- Natural language queries about disasters
- Historical chat storage
- Per-user chat history saved to database
- Integration with your LLM backend

### Advanced Analytics
- Disaster type distribution (Pie charts)
- Severity analysis
- Location heat maps
- Time-series trends
- People affected metrics
- Response metrics

### User Management
- Secure authentication with Supabase
- Email verification
- Per-user data isolation
- Session management

### Modern UI/UX
- Dark theme optimized for emergency situations
- Responsive design
- Real-time updates
- Smooth animations and transitions
- Interactive data visualizations

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript
- **Styling**: Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Charts**: Recharts
- **UI Components**: shadcn/ui
- **Backend**: Your Python LLM service

## Getting Started

### Prerequisites

- Node.js 18+
- Supabase project
- Vercel Blob (optional, for file storage)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Set up environment variables (.env.local):
   ```
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_key
   SUPABASE_JWT_SECRET=your_jwt_secret
   POSTGRES_URL=your_postgres_url
   POSTGRES_URL_NON_POOLING=your_postgres_url_non_pooling
   POSTGRES_USER=your_postgres_user
   POSTGRES_PASSWORD=your_postgres_password
   POSTGRES_DATABASE=your_postgres_database
   POSTGRES_HOST=your_postgres_host
   LLM_BACKEND_URL=http://localhost:8000  # Your Python backend URL
   ```

### Database Setup

1. Run migrations to create tables:
   ```bash
   # The migrations are located in scripts/
   # Run them in Supabase SQL Editor or using psql
   ```

2. (Optional) Seed sample data:
   ```bash
   node scripts/seed-data.js
   ```

### Running the Development Server

```bash
pnpm dev
```

Visit `http://localhost:3000` to see your application.

## Project Structure

```
├── app/
│   ├── api/
│   │   ├── chat/          # Chat endpoint
│   │   └── disasters/     # Disasters CRUD
│   ├── auth/
│   │   ├── login/         # Login page
│   │   ├── sign-up/       # Registration page
│   │   └── error/         # Auth error page
│   ├── dashboard/         # Main dashboard page
│   ├── globals.css        # Global styles & animations
│   └── layout.tsx         # Root layout
├── components/
│   ├── DisasterStatusOverview.tsx    # Disaster status cards
│   ├── AdvancedVisualizations.tsx    # Charts & analytics
│   ├── ChatInterface.tsx             # Chat component
│   ├── ChatHistorySidebar.tsx        # Chat history sidebar
│   ├── TopNavigation.tsx             # Navigation bar
│   ├── DisasterAlert.tsx             # Alert notifications
│   └── ui/                           # shadcn UI components
├── lib/
│   ├── supabase/
│   │   ├── client.ts      # Browser client
│   │   ├── server.ts      # Server client
│   │   └── proxy.ts       # Middleware proxy
│   └── utils.ts           # Utility functions
├── scripts/
│   ├── 001-create-profiles.sql       # Create profiles table
│   ├── 002-create-chat-history.sql   # Create chat history table
│   ├── 003-create-disasters.sql      # Create disasters table
│   └── seed-data.js                   # Sample data seeder
└── middleware.ts          # Next.js middleware for auth
```

## Database Schema

### profiles
- `id` (UUID, PK) - References auth.users
- `username` (TEXT, UNIQUE)
- `full_name` (TEXT)
- `avatar_url` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### chat_history
- `id` (UUID, PK)
- `user_id` (UUID, FK) - References profiles
- `title` (TEXT)
- `messages` (JSONB) - Array of message objects
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### disasters
- `id` (UUID, PK)
- `type` (TEXT) - Earthquake, Flood, Wildfire, etc.
- `location` (TEXT)
- `latitude` (DECIMAL)
- `longitude` (DECIMAL)
- `severity` (TEXT) - low, medium, high, critical
- `status` (TEXT) - active, resolved, monitoring
- `description` (TEXT)
- `affected_people` (INTEGER)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### disaster_statistics
- `id` (UUID, PK)
- `disaster_id` (UUID, FK) - References disasters
- `metric_name` (TEXT)
- `metric_value` (DECIMAL)
- `metric_unit` (TEXT)
- `created_at` (TIMESTAMP)

## API Endpoints

### GET /api/chat
Get chat history

### POST /api/chat
Send message to chat (integrates with LLM backend)

### GET /api/disasters
List all disasters (supports filtering)

### POST /api/disasters
Create a new disaster record

## Authentication Flow

1. User signs up with email/password
2. Verification email is sent
3. User verifies email
4. User logs in
5. Session is created and stored
6. User can access protected routes

## LLM Backend Integration

The chat feature integrates with a Python backend. Update `LLM_BACKEND_URL` to point to your service.

Expected API:
```
POST /chat
{
  "query": "What disasters are active?"
}

Response:
{
  "response": "There are currently 5 active disasters..."
}
```

## Customization

### Adding New Disaster Types
Update the disasters table with new types and add corresponding icons/colors in `DisasterStatusOverview.tsx`.

### Theming
Modify CSS variables in `app/globals.css` under `:root` to customize colors.

### Adding New Charts
Use Recharts components in `AdvancedVisualizations.tsx` to add new visualizations.

## Deployment

### Vercel Deployment

1. Push your code to GitHub
2. Connect your GitHub repository to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy

### Self-Hosted

1. Build: `pnpm build`
2. Start: `pnpm start`
3. Ensure environment variables are set

## Security Considerations

- All database queries use Row Level Security (RLS)
- User data is isolated per user
- Passwords are hashed by Supabase
- Authentication tokens are secure HTTP-only cookies
- API endpoints validate user authentication

## Performance

- Realtime subscriptions for live updates
- Optimized database queries with indexes
- Client-side caching with SWR
- Responsive images and lazy loading

## Troubleshooting

### Chat not working
- Ensure `LLM_BACKEND_URL` is correctly set
- Check backend service is running
- Verify API endpoint format

### Authentication issues
- Check Supabase URL and keys are correct
- Verify email confirmation is enabled
- Clear browser cookies and retry

### Database migration errors
- Ensure RLS is enabled on tables
- Check foreign key references
- Verify user has proper permissions

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in Supabase dashboard
3. Verify environment variables are set correctly

## License

MIT License - Feel free to use this project as a template for your disaster management systems.

## Contributing

Contributions are welcome! Please submit pull requests to improve the application.

---

Built with Next.js, Supabase, and modern web technologies for effective disaster management and emergency response coordination.
