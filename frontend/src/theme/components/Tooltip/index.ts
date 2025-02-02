import { Tooltip } from '@mantine/core';

import classes from './index.module.css';

export default Tooltip.extend({
  defaultProps: {},
  classNames: {
    tooltip: classes.tooltip,
  },
});
