import { Box, Paper } from '@mantine/core';
import { ReactNode } from 'react';

import clsx from 'clsx';
import classes from './index.module.css';

type ColoredPaperProps = {
  children: ReactNode;
  rightTopOffset?: { w: number; h: number };
  leftTopOffset?: { w: number; h: number };
  leftBottomOffset?: { w: number; h: number };
  childrenClassName?: string;
  color?: 'main' | 'secondarySkyBlue' | 'glass';
};

const ColoredPaper = ({
  children,
  rightTopOffset,
  leftBottomOffset,
  leftTopOffset,
  color = 'main',
  childrenClassName,
}: ColoredPaperProps) => (
  <Paper
    className={clsx(classes.root, {
      [classes.secondarySkyBlue]: color === 'secondarySkyBlue',
      [classes.glass]: color === 'glass',
    })}
  >
    <Box className={clsx(classes.children, childrenClassName)}>{children}</Box>
    <Box
      className={clsx({ [classes.leftTopBox]: !!rightTopOffset })}
      w={rightTopOffset ? `calc(100% - ${rightTopOffset.w}px` : '0px'}
      h={rightTopOffset ? `${rightTopOffset.h}px` : '0px'}
    />
    <Box
      className={clsx({ [classes.rightTopBox]: !!leftTopOffset })}
      w={leftTopOffset ? `calc(100% - ${leftTopOffset.w}px` : '0px'}
      h={leftTopOffset ? `${leftTopOffset.h}px` : '0px'}
    />

    <Box className={clsx(classes.body, { [classes.borderTopRight]: !!leftTopOffset })} />

    <Box
      className={classes.rightBottomBox}
      w={leftBottomOffset ? `calc(100% - ${leftBottomOffset.w}px` : '0px'}
      h={leftBottomOffset ? `${leftBottomOffset.h}px` : '0px'}
    />
  </Paper>
);

export default ColoredPaper;
