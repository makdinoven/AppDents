import Joi from "joi";

export const loginSchema = Joi.object({
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      "string.empty": "error.email.empty",
      "string.email": "error.email.valid",
      "any.required": "error.email.required",
    }),

  password: Joi.string().required().messages({
    "string.empty": "error.password.empty",
    "any.required": "error.password.required",
  }),
});
