import { FileRejection } from '@mantine/dropzone';
import { showNotification } from '@mantine/notifications';

import { ApiError } from 'types';

type ValidationErrors = {
  [name: string]: string[] | string;
};

interface ErrorData {
  errors?: ValidationErrors;
  detail: string;
}

export const handleApiError = (
  e: ApiError,
  // setError?: UseFormSetError<TFieldValues>,
) => {
  const data = e.data as ErrorData;

  if (!data?.errors && !data.detail) return;

  showNotification({
    title: 'Error',
    message: data.detail,
    color: 'red',
  });
};

enum ErrorCode {
  FileInvalidType = 'file-invalid-type',
  FileTooLarge = 'file-too-large',
}

export const handleDropzoneError = (fileRejections: FileRejection[]) => {
  fileRejections.forEach((fileRejection) => {
    const { errors } = fileRejection;

    errors.forEach((error) => {
      let { message } = error;

      switch (error.code) {
        case ErrorCode.FileTooLarge: {
          const [maxSizeInBytes] = message.split(' ').slice(-2);
          // fix it
          const maxSizeInMb = Number(maxSizeInBytes);

          message = `Maximum file size allowed is ${maxSizeInMb} MB.`;
          break;
        }

        case ErrorCode.FileInvalidType: {
          const [fileFormats] = message.split(' ').slice(-1);

          const fileExtensions = fileFormats.split(',').map((format) => `.${format.split('/')[1]}`);

          if (fileExtensions.length === 1) {
            message = `Only ${fileExtensions[0]} file type is allowed.`;
            break;
          }

          message = `Allowed file types are ${fileExtensions.join(', ')}.`;
          break;
        }
        default:
          break;
      }

      showNotification({
        title: 'Error',
        message,
        color: 'red',
      });
    });
  });
};
