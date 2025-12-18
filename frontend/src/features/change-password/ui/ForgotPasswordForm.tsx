import Form from "@/shared/components/Modals/modules/Form/Form.tsx";
import Input from "@/shared/components/ui/Inputs/Input/Input.tsx";
import Button from "@/shared/components/ui/Button/Button.tsx";
import { useForgotPasswordForm } from "../model/useForgotPasswordForm.tsx";
import { ReactNode } from "react";

type Props = {
  bottomSlot?: (err: any) => ReactNode;
  onSuccess?: () => void;
};

export const ForgotPasswordForm = ({ bottomSlot, onSuccess }: Props) => {
  const { register, handleSubmit, errors, loading, error, onSubmit } =
    useForgotPasswordForm({ onSuccess });

  return (
    <>
      <Form handleSubmit={handleSubmit(onSubmit)}>
        <Input
          id="email"
          placeholder="Email"
          error={errors.email?.message}
          {...register("email")}
        />
        <Button loading={loading} text="Reset" type="submit" />
      </Form>
      {bottomSlot && bottomSlot(error)}
    </>
  );
};
