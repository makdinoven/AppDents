export interface SignUpType {
  id: number;
  email: string;
  password: string;
  role: string;
}

export interface LoginType {
  email: string;
  password: string;
}

export interface ChangePasswordType {
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
