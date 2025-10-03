from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "restaurants" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "logo_url" VARCHAR(255),
    "primary_color" VARCHAR(7) NOT NULL DEFAULT '#FF6B35',
    "secondary_color" VARCHAR(7) NOT NULL DEFAULT '#F7931E',
    "description" TEXT,
    "address" VARCHAR(255),
    "phone" VARCHAR(20),
    "hours" VARCHAR(100),
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "restaurants"."name" IS 'Restaurant name - required, max 100 characters';
COMMENT ON COLUMN "restaurants"."logo_url" IS 'URL to restaurant logo image';
COMMENT ON COLUMN "restaurants"."primary_color" IS 'Primary brand color in hex format';
COMMENT ON COLUMN "restaurants"."secondary_color" IS 'Secondary brand color in hex format';
COMMENT ON COLUMN "restaurants"."description" IS 'Restaurant description';
COMMENT ON COLUMN "restaurants"."address" IS 'Restaurant address';
COMMENT ON COLUMN "restaurants"."phone" IS 'Restaurant phone number';
COMMENT ON COLUMN "restaurants"."hours" IS 'Restaurant operating hours';
COMMENT ON COLUMN "restaurants"."is_active" IS 'Whether the restaurant is active';
COMMENT ON COLUMN "restaurants"."created_at" IS 'When the restaurant was created';
COMMENT ON COLUMN "restaurants"."updated_at" IS 'When the restaurant was last updated';
COMMENT ON TABLE "restaurants" IS 'Restaurant information and branding';
CREATE TABLE IF NOT EXISTS "categories" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "display_order" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "restaurant_id" INT NOT NULL REFERENCES "restaurants" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "categories"."name" IS 'Category name - required, max 100 characters';
COMMENT ON COLUMN "categories"."description" IS 'Category description';
COMMENT ON COLUMN "categories"."display_order" IS 'Order for displaying categories';
COMMENT ON COLUMN "categories"."is_active" IS 'Whether the category is active';
COMMENT ON COLUMN "categories"."created_at" IS 'When the category was created';
COMMENT ON COLUMN "categories"."updated_at" IS 'When the category was last updated';
COMMENT ON COLUMN "categories"."restaurant_id" IS 'Reference to restaurant';
COMMENT ON TABLE "categories" IS 'Menu categories for organizing items';
CREATE TABLE IF NOT EXISTS "ingredients" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "is_allergen" BOOL NOT NULL DEFAULT False,
    "allergen_type" VARCHAR(50),
    "is_optional" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "restaurant_id" INT NOT NULL REFERENCES "restaurants" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "ingredients"."name" IS 'Ingredient name - required, max 100 characters';
COMMENT ON COLUMN "ingredients"."description" IS 'Ingredient description';
COMMENT ON COLUMN "ingredients"."is_allergen" IS 'Whether this ingredient is an allergen';
COMMENT ON COLUMN "ingredients"."allergen_type" IS 'Type of allergen (e.g., ''dairy'', ''nuts'', ''gluten'')';
COMMENT ON COLUMN "ingredients"."is_optional" IS 'Whether this ingredient is optional in menu items';
COMMENT ON COLUMN "ingredients"."created_at" IS 'When the ingredient was created';
COMMENT ON COLUMN "ingredients"."updated_at" IS 'When the ingredient was last updated';
COMMENT ON COLUMN "ingredients"."restaurant_id" IS 'Reference to restaurant';
COMMENT ON TABLE "ingredients" IS 'Ingredients for menu items';
CREATE TABLE IF NOT EXISTS "menu_items" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "price" DECIMAL(10,2) NOT NULL,
    "image_url" VARCHAR(255),
    "is_available" BOOL NOT NULL DEFAULT True,
    "is_upsell" BOOL NOT NULL DEFAULT False,
    "is_special" BOOL NOT NULL DEFAULT False,
    "prep_time_minutes" INT NOT NULL DEFAULT 5,
    "display_order" INT NOT NULL DEFAULT 0,
    "size" VARCHAR(11) NOT NULL DEFAULT 'regular',
    "available_sizes" JSONB NOT NULL,
    "modifiable_ingredients" JSONB NOT NULL,
    "max_quantity" INT NOT NULL DEFAULT 10,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "category_id" INT NOT NULL REFERENCES "categories" ("id") ON DELETE CASCADE,
    "restaurant_id" INT NOT NULL REFERENCES "restaurants" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "menu_items"."name" IS 'Menu item name - required, max 100 characters';
COMMENT ON COLUMN "menu_items"."description" IS 'Menu item description';
COMMENT ON COLUMN "menu_items"."price" IS 'Menu item price - required, max 999999.99';
COMMENT ON COLUMN "menu_items"."image_url" IS 'URL to menu item image';
COMMENT ON COLUMN "menu_items"."is_available" IS 'Whether the menu item is available for ordering';
COMMENT ON COLUMN "menu_items"."is_upsell" IS 'Whether this item should be suggested for upselling';
COMMENT ON COLUMN "menu_items"."is_special" IS 'Whether this item is a special/featured item';
COMMENT ON COLUMN "menu_items"."prep_time_minutes" IS 'Estimated preparation time in minutes';
COMMENT ON COLUMN "menu_items"."display_order" IS 'Order for displaying menu items within category';
COMMENT ON COLUMN "menu_items"."size" IS 'Size of the menu item (small, medium, large, etc.)';
COMMENT ON COLUMN "menu_items"."available_sizes" IS 'List of available sizes for this item (e.g., [''small'', ''medium'', ''large''])';
COMMENT ON COLUMN "menu_items"."modifiable_ingredients" IS 'List of ingredient names that can be modified (added/removed/extra)';
COMMENT ON COLUMN "menu_items"."max_quantity" IS 'Maximum quantity allowed for this item';
COMMENT ON COLUMN "menu_items"."created_at" IS 'When the menu item was created';
COMMENT ON COLUMN "menu_items"."updated_at" IS 'When the menu item was last updated';
COMMENT ON COLUMN "menu_items"."category_id" IS 'Reference to category';
COMMENT ON COLUMN "menu_items"."restaurant_id" IS 'Reference to restaurant';
COMMENT ON TABLE "menu_items" IS 'Menu items with pricing and availability';
CREATE TABLE IF NOT EXISTS "menu_item_ingredients" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "quantity" DECIMAL(8,2) NOT NULL,
    "unit" VARCHAR(20) NOT NULL,
    "is_optional" BOOL NOT NULL DEFAULT False,
    "additional_cost" DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ingredient_id" INT NOT NULL REFERENCES "ingredients" ("id") ON DELETE CASCADE,
    "menu_item_id" INT NOT NULL REFERENCES "menu_items" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_menu_item_i_menu_it_7990c3" UNIQUE ("menu_item_id", "ingredient_id")
);
COMMENT ON COLUMN "menu_item_ingredients"."quantity" IS 'Quantity of ingredient (e.g., 1.0, 2.5)';
COMMENT ON COLUMN "menu_item_ingredients"."unit" IS 'Unit of measurement (pieces, oz, cups, lbs, etc.)';
COMMENT ON COLUMN "menu_item_ingredients"."is_optional" IS 'Whether this ingredient is optional (e.g., ''extra cheese'')';
COMMENT ON COLUMN "menu_item_ingredients"."additional_cost" IS 'Additional cost when adding extra of this ingredient';
COMMENT ON COLUMN "menu_item_ingredients"."created_at" IS 'When the menu item ingredient was created';
COMMENT ON COLUMN "menu_item_ingredients"."ingredient_id" IS 'Reference to ingredient';
COMMENT ON COLUMN "menu_item_ingredients"."menu_item_id" IS 'Reference to menu item';
COMMENT ON TABLE "menu_item_ingredients" IS 'Many-to-many relationship between menu items and ingredients';
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "orders" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "customer_name" VARCHAR(100),
    "customer_phone" VARCHAR(20),
    "status" VARCHAR(9) NOT NULL DEFAULT 'pending',
    "subtotal" DECIMAL(10,2) NOT NULL,
    "tax_amount" DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    "total_amount" DECIMAL(10,2) NOT NULL,
    "special_instructions" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "restaurant_id" INT NOT NULL REFERENCES "restaurants" ("id") ON DELETE CASCADE,
    "user_id" INT REFERENCES "users" ("id") ON DELETE SET NULL
);
COMMENT ON COLUMN "orders"."customer_name" IS 'Customer name - optional for anonymous orders';
COMMENT ON COLUMN "orders"."customer_phone" IS 'Customer phone number - optional';
COMMENT ON COLUMN "orders"."status" IS 'Current order status';
COMMENT ON COLUMN "orders"."subtotal" IS 'Subtotal before tax';
COMMENT ON COLUMN "orders"."tax_amount" IS 'Tax amount';
COMMENT ON COLUMN "orders"."total_amount" IS 'Total amount including tax';
COMMENT ON COLUMN "orders"."special_instructions" IS 'Special instructions for the order';
COMMENT ON COLUMN "orders"."created_at" IS 'When the order was created';
COMMENT ON COLUMN "orders"."updated_at" IS 'When the order was last updated';
COMMENT ON COLUMN "orders"."restaurant_id" IS 'Reference to restaurant';
COMMENT ON COLUMN "orders"."user_id" IS 'Reference to registered user - optional';
COMMENT ON TABLE "orders" IS 'Customer orders with status and pricing';
CREATE TABLE IF NOT EXISTS "order_items" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "quantity" INT NOT NULL,
    "unit_price" DECIMAL(10,2) NOT NULL,
    "total_price" DECIMAL(10,2) NOT NULL,
    "special_instructions" TEXT,
    "size" VARCHAR(11) NOT NULL DEFAULT 'regular',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "menu_item_id" INT NOT NULL REFERENCES "menu_items" ("id") ON DELETE CASCADE,
    "order_id" INT NOT NULL REFERENCES "orders" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "order_items"."quantity" IS 'Quantity of the item - max 10 per item';
COMMENT ON COLUMN "order_items"."unit_price" IS 'Unit price at time of order';
COMMENT ON COLUMN "order_items"."total_price" IS 'Total price for this line item';
COMMENT ON COLUMN "order_items"."special_instructions" IS 'Special instructions for this item';
COMMENT ON COLUMN "order_items"."size" IS 'Size of the ordered item (can be different from menu item default)';
COMMENT ON COLUMN "order_items"."created_at" IS 'When the order item was created';
COMMENT ON COLUMN "order_items"."updated_at" IS 'When the order item was last updated';
COMMENT ON COLUMN "order_items"."menu_item_id" IS 'Reference to menu item';
COMMENT ON COLUMN "order_items"."order_id" IS 'Reference to order';
COMMENT ON TABLE "order_items" IS 'Individual items within orders';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
