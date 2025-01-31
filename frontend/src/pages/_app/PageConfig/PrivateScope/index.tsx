import { FC, ReactElement } from 'react';

interface PrivateScopeProps {
  children: ReactElement;
}

const PrivateScope: FC<PrivateScopeProps> = ({ children }) =>
  // useEffect(() => {
  //   socketService.connect();

  //   return () => socketService.disconnect();
  // }, []);

  children;
export default PrivateScope;
