/**
 * Order-related type definitions
 */

export interface LineItem {
  menu_item_id: number;
  name: string;
  price: number;
  quantity: number;
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
