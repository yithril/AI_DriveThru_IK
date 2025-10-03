# AI Drive-Thru Frontend

A Next.js frontend for the AI-powered drive-thru ordering system.

## Quick Start

1. **Copy environment variables:**
   ```bash
   cp env.example .env.local
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

## Environment Variables

Create a `.env.local` file with:

```env
# Restaurant Configuration
NEXT_PUBLIC_RESTAURANT_ID=1
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Features

- **Two-Panel Layout**: Order management (left) + Menu display (right)
- **Restaurant Theming**: Automatic branding from API data
- **Order Management**: Add/remove items with quantity controls
- **Car Control**: "New Car" / "Car Arrived" workflow
- **Error Handling**: 404 page, error boundary, API error states
- **Responsive Design**: Optimized for drive-thru displays

## API Integration

The app automatically fetches restaurant data from your backend API:
- Restaurant info (name, colors, logo)
- Menu categories (sorted alphabetically)
- Menu items with prices, descriptions, images, tags

## Development

- **Theme Provider**: Fetches restaurant data immediately on app load
- **Caching**: 5-minute cache to avoid repeated API calls
- **Error Boundaries**: Graceful error handling throughout the app
- **TypeScript**: Full type safety with restaurant and menu types