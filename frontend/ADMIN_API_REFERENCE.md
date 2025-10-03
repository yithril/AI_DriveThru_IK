# Admin API Reference

This document outlines all available API endpoints for the Admin section of AI DriveThru.

## Base URL
- Development: `http://localhost:8000`
- Production: Set via `NEXT_PUBLIC_API_BASE_URL` environment variable

## Authentication
Currently no authentication is implemented. This should be added before production deployment.

---

## Restaurants API

### Get All Restaurants
```http
GET /api/admin/restaurants
```

**Response:**
```typescript
{
  restaurants: Restaurant[];
  total_count: number;
}
```

### Get Restaurant by ID
```http
GET /api/admin/restaurants/{restaurant_id}
```

### Create Restaurant
```http
POST /api/admin/restaurants
Content-Type: application/json

{
  name: string;
  description?: string;
  address?: string;
  phone?: string;
  hours?: string;
  primary_color?: string;    // Default: "#FF6B35"
  secondary_color?: string;  // Default: "#004E89"
  is_active?: boolean;       // Default: true
}
```

### Update Restaurant
```http
PUT /api/admin/restaurants/{restaurant_id}
Content-Type: application/json

{
  name?: string;
  description?: string;
  address?: string;
  phone?: string;
  hours?: string;
  primary_color?: string;
  secondary_color?: string;
  is_active?: boolean;
}
```

### Delete Restaurant
```http
DELETE /api/admin/restaurants/{restaurant_id}
```

---

## Menu Items API

### Get Menu Items
```http
GET /api/admin/menu-items?restaurant_id={restaurant_id}&category_id={category_id}&available_only={true|false}
```

**Query Parameters:**
- `restaurant_id` (required): Filter by restaurant
- `category_id` (optional): Filter by category
- `available_only` (optional, default: true): Only show available items

### Get Menu Item by ID
```http
GET /api/admin/menu-items/{menu_item_id}
```

### Create Menu Item
```http
POST /api/admin/menu-items
Content-Type: application/json

{
  name: string;
  description?: string;
  price: number;
  category_id: number;
  restaurant_id: number;
  image_url?: string;
  is_available?: boolean;      // Default: true
  is_upsell?: boolean;         // Default: false
  is_special?: boolean;        // Default: false
  prep_time_minutes?: number;  // Default: 5
  display_order?: number;      // Default: 0
}
```

### Update Menu Item
```http
PUT /api/admin/menu-items/{menu_item_id}
Content-Type: application/json

{
  name?: string;
  description?: string;
  price?: number;
  category_id?: number;
  image_url?: string;
  is_available?: boolean;
  is_upsell?: boolean;
  is_special?: boolean;
  prep_time_minutes?: number;
  display_order?: number;
}
```

### Delete Menu Item
```http
DELETE /api/admin/menu-items/{menu_item_id}
```

### Get Menu Item Ingredients
```http
GET /api/admin/menu-items/{menu_item_id}/ingredients
```

### Add Ingredient to Menu Item
```http
POST /api/admin/menu-items/{menu_item_id}/ingredients
Content-Type: application/json

{
  ingredient_id: number;
  quantity: number;
  unit?: string;              // Default: "unit"
  is_optional?: boolean;      // Default: false
  additional_cost?: number;   // Default: 0
}
```

### Remove Ingredient from Menu Item
```http
DELETE /api/admin/menu-items/{menu_item_id}/ingredients/{ingredient_id}
```

---

## Ingredients API

### Get Ingredients
```http
GET /api/admin/ingredients?restaurant_id={restaurant_id}&search={search}&allergen_only={true|false}
```

**Query Parameters:**
- `restaurant_id` (required): Filter by restaurant
- `search` (optional): Search by name
- `allergen_only` (optional): Only show allergens

### Get Ingredient by ID
```http
GET /api/admin/ingredients/{ingredient_id}
```

### Create Ingredient
```http
POST /api/admin/ingredients
Content-Type: application/json

{
  name: string;
  description?: string;
  restaurant_id: number;
  is_allergen?: boolean;      // Default: false
  allergen_type?: string;     // e.g., "dairy", "gluten", "nuts"
  unit_cost: number;
}
```

### Update Ingredient
```http
PUT /api/admin/ingredients/{ingredient_id}
Content-Type: application/json

{
  name?: string;
  description?: string;
  is_allergen?: boolean;
  allergen_type?: string;
  unit_cost?: number;
}
```

### Delete Ingredient
```http
DELETE /api/admin/ingredients/{ingredient_id}
```

---

## Categories API

### Get Categories
```http
GET /api/admin/categories?restaurant_id={restaurant_id}
```

### Get Category by ID
```http
GET /api/admin/categories/{category_id}
```

### Create Category
```http
POST /api/admin/categories
Content-Type: application/json

{
  name: string;
  description?: string;
  restaurant_id: number;
  display_order?: number;  // Default: 0
  is_active?: boolean;     // Default: true
}
```

### Update Category
```http
PUT /api/admin/categories/{category_id}
Content-Type: application/json

{
  name?: string;
  description?: string;
  display_order?: number;
  is_active?: boolean;
}
```

### Delete Category
```http
DELETE /api/admin/categories/{category_id}
```

---

## File Upload API

### Upload Image
```http
POST /api/admin/upload/image
Content-Type: multipart/form-data

file: File (image)
restaurant_id: number
```

**Response:**
```typescript
{
  success: boolean;
  message: string;
  data: {
    file_id: string;
    image_url: string;
    original_name: string;
    size: number;
    content_type: string;
  }
}
```

### Upload Generic File
```http
POST /api/admin/upload/upload
Content-Type: multipart/form-data

file: File
restaurant_id: number
file_type: string  // "images", "audio", "documents", etc.
```

### Delete File
```http
DELETE /api/admin/upload/delete?s3_key={s3_key}
```

### List Files
```http
GET /api/admin/upload/list?restaurant_id={restaurant_id}&file_type={file_type}
```

---

## Customer-Facing APIs (Non-Admin)

These endpoints are used by the drive-thru customer interface and should NOT be prefixed with `/admin`:

### Voice Processing
```http
POST /api/ai/process-audio
Content-Type: multipart/form-data

audio_file: File
session_id: string
restaurant_id: number
language: string  // Default: "en"
```

### Restaurant Menu (Customer View)
```http
GET /api/restaurants/{restaurant_id}/menu
```

### Session Management
```http
POST /api/sessions/new-car
POST /api/sessions/next-car
GET /api/sessions/current
GET /api/sessions/current-order
```

---

## Common Response Formats

### Success Response
```typescript
{
  success: true;
  data: T;
  message?: string;
}
```

### Error Response
```typescript
{
  success: false;
  error: string;
  detail?: string;
}
```

---

## Admin Feature Roadmap

### Current Features ✅
- ✅ Restaurant Management (CRUD)
- ✅ Menu Item Management (CRUD)
- ✅ Ingredient Management (CRUD)
- ✅ Category Management (CRUD)
- ✅ Menu Item-Ingredient Relationships
- ✅ Image Upload
- ✅ Data Import

### Planned Features 🚧
- [ ] User Authentication & Authorization
- [ ] Role-Based Access Control (Super Admin, Restaurant Admin, Staff)
- [ ] Order History & Analytics
- [ ] Real-time Order Monitoring
- [ ] Inventory Management
- [ ] Sales Reports & Dashboard
- [ ] Customer Feedback & Ratings
- [ ] Menu Item Analytics (Popular items, order patterns)
- [ ] Bulk Operations (Import/Export)
- [ ] Multi-restaurant Support
- [ ] A/B Testing for Menu Items
- [ ] Promotional Management
- [ ] Staff Management
- [ ] Shift Scheduling

### Future Enhancements 💡
- Webhooks for external integrations
- GraphQL API option
- API versioning
- Rate limiting
- Audit logs
- Backup & restore functionality
- Multi-language support for menu items
- Nutritional information management
- Allergen tracking & warnings

