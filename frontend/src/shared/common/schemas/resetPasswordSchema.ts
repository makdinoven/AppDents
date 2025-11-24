import Joi from "joi";

export const resetPasswordSchema = Joi.object({
  password: Joi.string().required().messages({
    "string.empty": "error.password.empty",
    "any.required": "error.password.required",
  }),
});
