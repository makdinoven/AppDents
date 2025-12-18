export interface ChangePasswordType {
  email: string;
}

export interface ResetPasswordType {
  password: string;
}

export interface ResetPasswordDTO {
  password: string;
  id: number;
}

export interface ChangePasswordDTO {
  email: string;
  language: string;
}
