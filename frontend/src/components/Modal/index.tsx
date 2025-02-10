import { FC, ReactNode, useState } from 'react';
import { Modal as MantineModal, ActionIcon, Center } from '@mantine/core';

import Icon, { IconType } from 'components/Icon';
import classes from './index.module.css';

type ModalProps = {
  children: ReactNode;
  opened: boolean;
  onClose: () => void;
};

const Modal: FC<ModalProps> = ({ children, opened, onClose }) => {
  const [open, setOpen] = useState(opened);

  return (
    <MantineModal
      opened={open}
      onClose={onClose}
      withCloseButton={false}
      size="xl"
      h="668px"
      classNames={{
        content: classes.content,
        body: classes.body,
        root: classes.root,
      }}
      yOffset={41}
      overlayProps={{
        backgroundOpacity: 0.55,
        blur: 3,
      }}
    >
      <ActionIcon variant="transparent" w={45} h={45} onClick={() => setOpen(false)}>
        <Icon type={IconType.CircleX} color="back" size={45} />
      </ActionIcon>

      <Center h="100%">{children}</Center>
    </MantineModal>
  );
};

export default Modal;
