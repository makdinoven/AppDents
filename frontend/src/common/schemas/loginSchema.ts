import Joi from "joi";

export const loginSchema = Joi.object({
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      "string.empty": "errMessage.email.empty",
      "string.email": "errMessage.email.valid",
      "any.required": "errMessage.email.required",
    }),

  password: Joi.string().required().messages({
    "string.empty": "errMessage.password.empty",
    "any.required": "errMessage.password.required",
  }),
});
