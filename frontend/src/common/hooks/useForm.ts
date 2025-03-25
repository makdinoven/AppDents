import { useState, ChangeEvent, FormEvent } from "react";
import Joi from "joi";

interface UseFormProps<T> {
  validationSchema: Joi.ObjectSchema | undefined;
  onSubmit: (values: T) => void;
}

export const useForm = <T extends Record<string, any>>({
  validationSchema,
  onSubmit,
}: UseFormProps<T>) => {
  const [values, setValues] = useState<T>({} as T);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setValues((prevValues) => ({ ...prevValues, [name]: value }));
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!validationSchema) {
      setErrors({});
      return onSubmit(values);
    }

    const trimmedValues = Object.keys(values).reduce(
      (acc, key) => ({
        ...acc,
        [key]: values[key]?.trim(),
      }),
      {} as T,
    );

    const { error } = validationSchema.validate(trimmedValues, {
      abortEarly: false,
    });

    if (error) {
      const newErrors: Partial<Record<keyof T, string>> = {};
      error.details.forEach((detail) => {
        newErrors[detail.path[0] as keyof T] = detail.message;
      });
      setErrors(newErrors);
    } else {
      setErrors({});
      onSubmit(trimmedValues);
    }
  };

  return { values, errors, handleChange, handleSubmit };
};
