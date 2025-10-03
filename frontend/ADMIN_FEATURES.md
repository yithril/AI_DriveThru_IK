# Admin Section Features & Menu

## Overview
The Admin section is completely separate from the customer drive-thru interface. It does **not** use the `DataContext` or tenant-specific logic that the drive-thru section uses.

## Layout Architecture

### Customer (Drive-Thru) Layout
- **Route:** `/(customer)` 
- **Contexts:** DataProvider, ThemeProvider, SessionProvider, SpeakerProvider, OrderProvider
- **Purpose:** Voice-enabled ordering interface for customers
- **Features:** AI voice processing, real-time order management, restaurant theming

### Admin Layout
- **Route:** `/admin`
- **Contexts:** None (uses direct API calls via `apiClient`)
- **Purpose:** Restaurant management and configuration
- **Features:** CRUD operations for all restaurant data

---

## Current Admin Menu Structure

### 🏠 Dashboard (`/admin`)
- Overview statistics
- Quick actions
- Recent activity

### 🏪 Restaurants (`/admin/restaurants`)
**Features:**
- List all restaurants
- Create new restaurant
- Edit restaurant details
- Delete restaurant
- Configure branding (colors, logo)

**Data managed:**
- Name, description, address, phone, hours
- Primary and secondary colors
- Logo URL
- Active status

### 🍔 Menu Items (`/admin/menu-items`)
**Features:**
- List all menu items
- Filter by category
- Create new menu item
- Edit menu item details
- Delete menu item
- Upload item images
- Manage ingredients per item

**Data managed:**
- Name, description, price
- Category assignment
- Image URL
- Availability status
- Special/upsell flags
- Prep time
- Display order

### 📝 Menu Item Ingredients (`/admin/menu-items/[id]/ingredients`)
**Features:**
- View all ingredients for a menu item
- Add ingredients to menu item
- Specify quantity and unit
- Mark as optional
- Set additional cost
- Remove ingredients

### 🥗 Ingredients (`/admin/ingredients`)
**Features:**
- List all ingredients
- Search ingredients
- Filter by allergens
- Create new ingredient
- Edit ingredient details
- Delete ingredient
- Track unit costs

**Data managed:**
- Name, description
- Allergen information
- Allergen type (dairy, gluten, nuts, etc.)
- Unit cost

### 📂 Categories (`/admin/categories`)
**Features:**
- List all categories
- Create new category
- Edit category details
- Delete category
- Reorder categories

**Data managed:**
- Name, description
- Display order
- Active status

### 📤 Import Data (`/admin/import`)
**Features:**
- Bulk import menu data
- CSV/JSON upload
- Data validation
- Preview before import
- Error reporting

---

## API Integration

All admin endpoints are now properly namespaced under `/api/admin/*`:

| Frontend Path | Backend Endpoint |
|--------------|------------------|
| Restaurants | `/api/admin/restaurants` |
| Menu Items | `/api/admin/menu-items` |
| Ingredients | `/api/admin/ingredients` |
| Categories | `/api/admin/categories` |
| File Upload | `/api/admin/upload/image` |

---

## Next Steps for Building Admin Features

### 1. Dashboard Page (`/admin/page.tsx`)
```typescript
// TODO: Build dashboard with:
// - Restaurant count
// - Menu items count
// - Recent orders
// - Quick links to common actions
```

### 2. Restaurants Page (`/admin/restaurants/page.tsx`)
```typescript
// TODO: Build restaurant management with:
// - DataTable with restaurants
// - Create/Edit modal
// - Color picker for branding
// - Logo upload
// - Delete confirmation
```

### 3. Enhanced Menu Items Page
```typescript
// TODO: Improve with:
// - Image preview
// - Drag-and-drop reordering
// - Quick toggle for availability
// - Batch operations
// - Category filter
```

### 4. Categories Page (`/admin/categories/page.tsx`)
```typescript
// TODO: Build with:
// - Sortable list
// - Inline editing
// - Display order management
// - Active/inactive toggle
```

### 5. Analytics & Reports (New)
```typescript
// TODO: Create analytics section:
// - Sales by item
// - Popular items
// - Order patterns by time
// - Revenue reports
// - Customer insights
```

---

## Component Patterns to Use

### Data Fetching
```typescript
import { apiClient } from '@/lib/api';

// In your component
const [data, setData] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  async function fetchData() {
    try {
      const restaurantId = 1; // Get from context or route
      const result = await apiClient.getMenuItems(restaurantId);
      setData(result);
    } catch (error) {
      console.error('Failed to fetch:', error);
    } finally {
      setLoading(false);
    }
  }
  fetchData();
}, []);
```

### Creating Records
```typescript
const handleCreate = async (formData) => {
  try {
    const result = await apiClient.createMenuItem({
      name: formData.name,
      description: formData.description,
      price: formData.price,
      category_id: formData.categoryId,
      restaurant_id: restaurantId,
      // ... other fields
    });
    
    // Refresh list or add to state
    setItems([...items, result]);
  } catch (error) {
    console.error('Create failed:', error);
  }
};
```

### Updating Records
```typescript
const handleUpdate = async (itemId, updates) => {
  try {
    const result = await apiClient.updateMenuItem(itemId, updates);
    
    // Update in state
    setItems(items.map(item => 
      item.id === itemId ? result : item
    ));
  } catch (error) {
    console.error('Update failed:', error);
  }
};
```

### Deleting Records
```typescript
const handleDelete = async (itemId) => {
  if (!confirm('Are you sure?')) return;
  
  try {
    await apiClient.deleteMenuItem(itemId);
    
    // Remove from state
    setItems(items.filter(item => item.id !== itemId));
  } catch (error) {
    console.error('Delete failed:', error);
  }
};
```

### Image Upload
```typescript
const handleImageUpload = async (file: File) => {
  try {
    const result = await apiClient.uploadImage(file, restaurantId);
    
    // Use result.data.image_url for the menu item
    return result.data.image_url;
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

---

## UI Component Libraries

Consider using these for rapid development:
- **shadcn/ui** - Pre-built, customizable components
- **Radix UI** - Accessible component primitives
- **React Table** - For data tables
- **React Hook Form** - For forms
- **Zod** - For validation

---

## State Management

Currently using local component state. Consider adding:
- **Zustand** - Lightweight state management (if needed)
- **React Query** - For server state management (recommended)

Example with React Query:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function MenuItemsList() {
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ['menuItems', restaurantId],
    queryFn: () => apiClient.getMenuItems(restaurantId),
  });
  
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteMenuItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['menuItems']);
    },
  });
  
  // ... rest of component
}
```

---

## Security Notes

⚠️ **Important:** Before production:
1. Add authentication middleware
2. Implement role-based access control
3. Add CSRF protection
4. Validate all inputs
5. Rate limit API calls
6. Add audit logging
7. Secure file uploads
8. Add API authentication tokens

---

## Testing Strategy

1. **Unit Tests:** Test API client functions
2. **Integration Tests:** Test full CRUD workflows
3. **E2E Tests:** Test admin user flows with Playwright
4. **API Tests:** Test backend endpoints directly

---

## Performance Considerations

- Implement pagination for large lists
- Add search/filter debouncing
- Use optimistic updates for better UX
- Cache frequently accessed data
- Lazy load images
- Use React.memo for expensive renders
- Implement virtual scrolling for long lists

