export type TransactionType =
  | {
      type: "referralCashback";
      amount: number | null;
      created_at: string | null;
      from_user: number | null;
    }
  | {
      type: "internalPurchase";
      amount: number | null;
      created_at: string | null;
      reason: string | null;
      courses: number[];
    }
  | {
      type: "adminAdjust";
      amount: number | null;
      created_at: string | null;
      reason: string | null;
    };
