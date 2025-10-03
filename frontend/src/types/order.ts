/**
 * Order-related type definitions
 */

export interface LineItem {
  id: string;
  menu_item_id: number;
  name: string;
  price: number;
  quantity: number;
  additional_cost?: number;
  additional_costs?: { name: string; cost: number }[];
  modifier_costs?: { ingredient_id: number; ingredient_name: string; action: string; cost: number }[];
  total_price?: number;
  customizations?: string[];
  size?: string;
  special_instructions?: string;
}

export interface OrderState {
  line_items: LineItem[];
  last_mentioned_item_ref?: string;
  totals: {
    subtotal?: number;
    tax?: number;
    total?: number;
  };
}

export interface ConversationEntry {
  role: string;
  content: string;
  timestamp: string;
}

export interface SessionData {
  id: string;
  restaurant_id: number;
  customer_name?: string;
  created_at: string;
  updated_at: string;
  conversation_state: string;
  conversation_history: ConversationEntry[];
  conversation_context: {
    turn_counter: number;
    last_action_uuid?: string;
    thinking_since?: string;
    timeout_at?: string;
    expectation: string;
  };
  order_state: OrderState;
}
