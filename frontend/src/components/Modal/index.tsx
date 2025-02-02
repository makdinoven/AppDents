import { FC, ReactNode } from 'react';
import { ActionIcon, Center, Stack } from '@mantine/core';

import Icon, { IconType } from 'components/Icon';

type ModalProps = {
  children: ReactNode;
  onClose: () => void;
};

const Modal: FC<ModalProps> = ({ children, onClose }) => (
  <Stack h="100%">
    <ActionIcon variant="transparent" miw={46} mih={46} onClick={onClose}>
      <Icon type={IconType.CircleX} color="back" size={45} />
    </ActionIcon>

    <Center h="100%">{children}</Center>
  </Stack>
);

export default Modal;
