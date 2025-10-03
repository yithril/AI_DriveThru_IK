export interface Restaurant {
  id: number;
  name: string;
  primary_color: string;
  secondary_color: string;
  phone?: string;
  address?: string;
  logo_url?: string;
}

export interface MenuItem {
  id: number;
  name: string;
  price: number;
  description?: string;
  image_url?: string;
  sort_order: number;
  restaurant_id?: number;
  tags: Array<{
    name: string;
    color: string;
  }>;
}

export interface MenuCategory {
  id: number;
  name: string;
  description?: string;
  sort_order: number;
  items: MenuItem[];
}

export interface RestaurantMenuResponse {
  restaurant: Restaurant;
  menu: MenuCategory[];
  total_items: number;
}

export interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  surfaceHover: string;
  text: {
    primary: string;
    secondary: string;
    muted: string;
    accent: string;
  };
  border: {
    primary: string;
    secondary: string;
  };
  button: {
    primary: string;
    primaryHover: string;
    secondary: string;
    secondaryHover: string;
  };
  error?: {
    background: string;
    text: string;
    border: string;
  };
}
