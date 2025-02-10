import { FC, ReactNode } from 'react';
import {
  ActionIcon,
  Box,
  Button,
  ButtonProps,
  FloatingPosition,
  Group,
  Popover as PopoverMantine,
  Stack,
  Tooltip,
  PopoverProps as MantinePopoverProps,
} from '@mantine/core';

import Icon, { IconType } from 'components/Icon';

import { useDisclosure } from '@mantine/hooks';
import classes from './index.module.css';

type PopoverProps = {
  children: ReactNode;
  target: ReactNode;
  variant?: 'top-right' | 'bottom-right';
  position?: FloatingPosition;
  tooltip?: string;
  buttonProps?: Omit<ButtonProps, 'children'>;
  floatingSizes?: { w: number; h: number; offset?: number };
  onOpen?: MantinePopoverProps['onOpen'];
  onClose?: MantinePopoverProps['onClose'];
};

const Popover: FC<PopoverProps> = ({
  children,
  target,
  position = 'bottom-end',
  tooltip,
  buttonProps,
  floatingSizes,
  onClose,
  onOpen,
}) => {
  const [opened, { close, toggle }] = useDisclosure(false);

  return (
    <PopoverMantine
      position={position}
      opened={opened}
      offset={floatingSizes ? floatingSizes.offset || -floatingSizes.h : undefined}
      onOpen={onOpen}
      onClose={onClose}
    >
      <PopoverMantine.Target>
        <Tooltip label={tooltip} disabled={!tooltip} withArrow position="top" arrowSize={15} multiline>
          <Button variant="transparent" p={0} onClick={toggle} {...buttonProps}>
            {target}
          </Button>
        </Tooltip>
      </PopoverMantine.Target>

      <PopoverMantine.Dropdown
        autoFocus={opened}
        p={0}
        className={classes.content}
        mod={{ variant: position }}
        onBlur={close}
      >
        <Group justify="space-between" gap={0}>
          <Box className={classes.header} h={floatingSizes?.h || 0}>
            <ActionIcon className={classes.closeButton} variant="transparent" onClick={close}>
              <Icon type={IconType.CircleX} color="back" size={45} />
            </ActionIcon>
          </Box>

          {position === 'bottom-end' && <Box w={floatingSizes?.w || 0} onClick={close} h={floatingSizes?.h || 0} />}
        </Group>

        <Box className={classes.body}>
          <Stack pt={32} px={20} align="center">
            {children}
          </Stack>
        </Box>

        {position === 'top-end' && (
          <Group justify="flex-end" pos="relative" gap={0}>
            <Box className={classes.footer} h={floatingSizes?.h || 0} />

            <Box pt={20} w={floatingSizes?.w || 0} onClick={close} h={floatingSizes?.h || 0} />
          </Group>
        )}
      </PopoverMantine.Dropdown>
    </PopoverMantine>
  );
};

export default Popover;
