import Joi from "joi";

export const emailSchema = Joi.object({
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      "string.empty": "errMessage.email.empty",
      "string.email": "errMessage.email.valid",
      "any.required": "errMessage.email.required",
    }),
});
