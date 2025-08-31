export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'staff';
  is_active: boolean;
  created_at: string;
}

export interface Account {
  id: number;
  user_id: number;
  ebay_username: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface OrderStatus {
  id: number;
  csv_data_id: number;
  status: 'pending' | 'processing' | 'shipped' | 'completed';
  updated_by: number;
  updated_at: string;
}

export interface OrderNote {
  id: number;
  order_id: number;
  note: string;
  created_by: number;
  created_at: string;
}

export interface Order {
  id: number;
  item_id: string;
  csv_row: Record<string, any>;
  order_status?: OrderStatus;
  account_id: number;
  created_at: string;
  notes?: OrderNote[];
}

export interface Listing {
  id: number;
  item_id: string;
  csv_row: Record<string, any>;
  account_id: number;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}