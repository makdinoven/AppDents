export interface SignUpRequest {
  email: string;
}

export interface SignUpResponse {
  access_token: string;
  token_type?: string;
  id?: number;
  email?: string;
  role?: string;
  balance?: number;
}

export interface LoginType {
  email: string;
  password: string;
}

export interface ChangePasswordType {
  email: string;
}
export interface EnterEmailType {
  email: string;
}

export interface ResetPasswordType {
  password: string;
}

export interface PaymentType {
  email: string;
  name: string;
  password: string;
}

export interface OrderDescriptionType {
  description: string;
}
