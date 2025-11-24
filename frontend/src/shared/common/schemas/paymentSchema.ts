import Joi from "joi";

export const paymentSchema = Joi.object({
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      "string.empty": "error.email.empty",
      "string.email": "error.email.valid",
      "any.required": "error.email.required",
    }),
  name: Joi.any().optional(),
  password: Joi.any().optional(),
});
