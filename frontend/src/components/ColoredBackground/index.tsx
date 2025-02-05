import { Box, Paper } from '@mantine/core';
import { ReactNode } from 'react';

import clsx from 'clsx';
import classes from './index.module.css';

type ColoredPaperProps = {
  children: ReactNode;
  rightTopOffset?: { w: number; h: number };
  leftBottomOffset?: { w: number; h: number };
  childrenClassName?: string;
};

const ColoredPaper = ({ children, rightTopOffset, leftBottomOffset, childrenClassName }: ColoredPaperProps) => (
  <Paper className={classes.root}>
    <Box className={clsx(classes.children, childrenClassName)}>{children}</Box>
    <Box
      className={classes.leftTopBox}
      w={rightTopOffset ? `calc(100% - ${rightTopOffset.w}px` : '0px'}
      h={rightTopOffset ? `${rightTopOffset.h}px` : '0px'}
    />

    <Box className={classes.body} />

    <Box
      className={classes.rightBottomBox}
      w={leftBottomOffset ? `calc(100% - ${leftBottomOffset.w}px` : '0px'}
      h={leftBottomOffset ? `${leftBottomOffset.h}px` : '0px'}
    />
  </Paper>
);

export default ColoredPaper;
