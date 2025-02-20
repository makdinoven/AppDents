import { Box, Paper } from '@mantine/core';
import { ReactNode } from 'react';

import clsx from 'clsx';
import classes from './index.module.css';

type ColoredPaperProps = {
  children: ReactNode;
  header?: ReactNode;
  rightTopOffset?: { w: number; h: number };
  leftTopOffset?: { w: number; h: number };
  leftBottomOffset?: { w: number; h: number };
  childrenClassName?: string;
  headerClassName?: string;
  color?: 'main' | 'secondarySkyBlue' | 'glass';
};

const ColoredPaper = ({
  header,
  children,
  rightTopOffset,
  leftBottomOffset,
  leftTopOffset,
  color = 'main',
  childrenClassName,
  headerClassName,
}: ColoredPaperProps) => (
  <Paper
    className={clsx(classes.root, {
      [classes.secondarySkyBlue]: color === 'secondarySkyBlue',
      [classes.glass]: color === 'glass',
      [classes.rightTop]: Boolean(rightTopOffset),
      [classes.leftBottom]: Boolean(leftBottomOffset),
      [classes.leftTop]: Boolean(leftTopOffset),
    })}
  >
    <Box className={clsx(classes.header, headerClassName)}>{header}</Box>

    {rightTopOffset && (
      <Box
        className={clsx({ [classes.leftTopBox]: !!rightTopOffset })}
        w={`calc(100% - ${rightTopOffset.w}px`}
        h={`${rightTopOffset.h}px`}
      />
    )}

    {leftTopOffset && (
      <Box
        className={clsx({ [classes.rightTopBox]: !!leftTopOffset })}
        w={`calc(100% - ${leftTopOffset.w}px`}
        h={`${leftTopOffset.h}px`}
      />
    )}

    <Box
      className={clsx(
        classes.body,
        {
          [classes.borderTopRight]: !!leftTopOffset,
          [classes.borderTopLeft]: !!rightTopOffset,
          [classes.borderBottomRight]: !!leftBottomOffset,
        },
        childrenClassName,
      )}
    >
      {children}
    </Box>

    {leftBottomOffset && (
      <Box className={classes.rightBottomBox} w={`calc(100% - ${leftBottomOffset.w}px`} h={`${leftBottomOffset.h}px`} />
    )}
  </Paper>
);

export default ColoredPaper;
