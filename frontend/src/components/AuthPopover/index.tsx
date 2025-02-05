import ResetPasswordModal from 'components/ResetPasswordModal';
import SignInModal from 'components/SignInModal';
import SignUpModal from 'components/SignUpModal';
import { useState } from 'react';

export enum SCREEN {
  LOGIN = 'login',
  SIGN_UP = 'sign-up',
  RESET_PASSWORD = 'reset-password',
}

const AuthPopover = () => {
  const [screen, setScreen] = useState(SCREEN.LOGIN);

  switch (screen) {
    case SCREEN.SIGN_UP:
      return <SignUpModal setScreen={setScreen} />;
    case SCREEN.RESET_PASSWORD:
      return <ResetPasswordModal />;
    case SCREEN.LOGIN:
    default:
      return <SignInModal setScreen={setScreen} />;
  }
};

export default AuthPopover;
