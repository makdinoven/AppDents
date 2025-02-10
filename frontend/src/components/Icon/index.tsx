import React, { FC, SVGProps } from 'react';
import cx from 'clsx';

import {
  SearchIcon,
  FilterIcon,
  CircleArrowIcon,
  FilledFilterIcon,
  CircleXIcon,
  DialogIcon,
  ArrowIcon,
  ChevronCompactLeftIcon,
  CircleArrowThinIcon,
} from 'public/icons';

import classes from './index.module.css';

export enum IconType {
  Search = 'search',
  Filter = 'filter',
  FilledFilter = 'filled-filter',
  CircleArrow = 'circle-arrow',
  Arrow = 'arrow',
  CircleX = 'circle-x',
  Dialog = 'dialog',
  ChevronCompactLeft = 'chevron-compact-left',
  CircleArrowThin = 'circle-arrow-thin',
}

interface IconProps extends SVGProps<SVGSVGElement> {
  type: IconType;
  color?: 'primary' | 'secondary-gray' | 'main' | 'back' | 'inherit' | 'green';
  width?: number;
  height?: number;
  size?: number;
  className?: string;
}

const Icon: FC<IconProps> = ({ type, className, size = 16, width, height, color = 'primary', ...otherProps }) => {
  const iconProps = {
    ...otherProps,
    width: width || size,
    height: height || size,
    className: cx(
      classes.icon,
      {
        [classes.primary]: color === 'primary',
        [classes.secondary]: color === 'secondary-gray',
        [classes.main]: color === 'main',
        [classes.back]: color === 'back',
        [classes.inherit]: color === 'inherit',
        [classes.green]: color === 'green',
      },
      className,
    ),
  };

  switch (type) {
    case IconType.Search:
      return <SearchIcon {...iconProps} />;

    case IconType.Filter:
      return <FilterIcon {...iconProps} />;

    case IconType.FilledFilter:
      return <FilledFilterIcon {...iconProps} />;

    case IconType.CircleArrow:
      return <CircleArrowIcon {...iconProps} />;

    case IconType.CircleX:
      return <CircleXIcon {...iconProps} />;

    case IconType.Dialog:
      return <DialogIcon {...iconProps} />;

    case IconType.Arrow:
      return <ArrowIcon {...iconProps} />;

    case IconType.ChevronCompactLeft:
      return <ChevronCompactLeftIcon {...iconProps} />;

    case IconType.CircleArrowThin:
      return <CircleArrowThinIcon {...iconProps} />;

    default:
      return null;
  }
};

export default Icon;
