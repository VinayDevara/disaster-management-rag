# Quick Start Guide - Disaster Management Dashboard

## 5-Minute Setup

### Step 1: Start the Application
```bash
pnpm dev
```
Visit `http://localhost:3000`

### Step 2: Create Your Account
1. Click "Create one" on login page
2. Enter email and password
3. Verify email (check spam folder if needed)
4. Log back in

### Step 3: See Sample Data
```bash
# In another terminal, seed the database
node scripts/seed-data.js
```

Refresh your browser - you'll see:
- 8 disaster events
- Status cards with real-time counts
- Interactive charts and visualizations
- Sample analytics data

### Step 4: Try the Chat
1. Go to "AI Assistant" section
2. Type: "What disasters are currently active?"
3. See the response (works even if backend isn't connected)

### Step 5: Explore Features
- **Sidebar**: View chat history
- **Dashboard**: See real-time disaster status
- **Charts**: Interactive data visualizations
- **Status Cards**: Quick disaster overview

## What You're Looking At

### Dashboard Layout
```
┌─ Navigation Bar (Logo, Alerts, Sign Out) ──────────────────┐
├─────────────────────────────────────────────────────────────┤
│ Sidebar (Chat History) │  Main Content (Responsive)         │
│                        │                                     │
│ • New Chat            │ ➤ Disaster Status Overview          │
│ • Past Chats          │   (4 status cards)                  │
│ • Delete Chat         │                                     │
│                        │ ➤ Analytics & Insights              │
│                        │   (6 interactive charts)            │
│                        │                                     │
│                        │ ➤ AI Assistant                      │
│                        │   (Chat interface)                  │
└─────────────────────────────────────────────────────────────┘
```

## Key Pages

| Page | URL | Purpose |
|------|-----|---------|
| Login | `/auth/login` | User authentication |
| Sign Up | `/auth/sign-up` | Create new account |
| Dashboard | `/dashboard` | Main application |
| API Docs | `/api/chat`, `/api/disasters` | Backend integration |

## Important Files

**For configuration:**
- `.env.local` - Environment variables
- `package.json` - Dependencies

**For customization:**
- `app/globals.css` - Colors and animations
- `components/DisasterStatusOverview.tsx` - Status display
- `components/AdvancedVisualizations.tsx` - Charts

**For data:**
- `scripts/seed-data.js` - Sample data
- `scripts/001-*.sql` - Database schema

## Common Tasks

### Add More Disasters
Using Supabase dashboard:
1. Go to `public.disasters` table
2. Click "Insert new row"
3. Fill in: type, location, severity, status, etc.
4. Refresh dashboard to see updates

### Connect Your LLM Backend
1. Update `LLM_BACKEND_URL` in `.env.local`
2. Ensure backend is running
3. Test chat functionality

### Change Dashboard Colors
Edit `app/globals.css`:
```css
:root {
  --primary: 219 99% 50%;        /* Blue */
  --secondary: 180 91% 55%;      /* Cyan */
  /* ... other variables ... */
}
```

### Add New Chart
Edit `components/AdvancedVisualizations.tsx`:
```tsx
// Add new state
const [newData, setNewData] = useState([]);

// Add new Card with chart
<Card className="...">
  <ResponsiveContainer width="100%" height={300}>
    <BarChart data={newData}>
      {/* Chart components */}
    </BarChart>
  </ResponsiveContainer>
</Card>
```

## Testing Scenarios

### Scenario 1: Fresh Start
1. Sign up with new email
2. Verify email
3. Log in
4. See empty dashboard
5. Use seed script to populate data

### Scenario 2: With Sample Data
```bash
node scripts/seed-data.js
```
- See 8 different disaster types
- Multiple severity levels
- Different locations
- Real data in charts

### Scenario 3: Chat Testing
Type these queries:
- "What earthquakes are active?"
- "How many people are affected?"
- "List all critical disasters"
- "What's happening in California?"

## Troubleshooting Quick Fixes

### Dashboard shows "No active disasters"
✓ Run: `node scripts/seed-data.js`

### Login not working
✓ Check Supabase URL and keys in `.env.local`

### Chat returning error
✓ Check `LLM_BACKEND_URL` is correct
✓ Ensure backend service is running

### Charts not displaying
✓ Refresh browser
✓ Clear browser cache
✓ Check console for errors

### Database errors
✓ Verify migrations were run in order
✓ Check Supabase project is active
✓ Verify credentials in `.env.local`

## Next Steps

1. **Connect Backend**: Update `LLM_BACKEND_URL`
2. **Add Real Data**: Replace sample disasters
3. **Customize Brand**: Update colors and logo
4. **Deploy**: Push to GitHub → Vercel
5. **Monitor**: Set up error tracking

## Learning Resources

- **Next.js**: nextjs.org/docs
- **Supabase**: supabase.com/docs
- **Tailwind**: tailwindcss.com/docs
- **Recharts**: recharts.org/

## Key Code Snippets

### Fetch disasters
```typescript
const { data } = await supabase
  .from('disasters')
  .select('*')
  .eq('status', 'active');
```

### Send chat message
```typescript
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: 'User query',
    sessionId: 'chat-id',
    userId: 'user-id'
  })
});
```

### Get user info
```typescript
const { data: { user } } = await supabase.auth.getUser();
```

## Performance Tips

- Keep disasters table under 10,000 records for best performance
- Archive old disasters periodically
- Use indexes for frequently filtered columns
- Cache chart data when possible

## Security Reminders

✓ Never expose `SUPABASE_SERVICE_ROLE_KEY` in client code
✓ Use Row Level Security (RLS) on all tables
✓ Validate all user inputs on backend
✓ Use HTTPS in production
✓ Keep dependencies updated

---

**You're all set!** Start the dev server and explore the application.

For detailed docs, see README.md and IMPLEMENTATION_SUMMARY.md
