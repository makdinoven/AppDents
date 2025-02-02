import { ActionIcon } from '@mantine/core';

import classes from './index.module.css';

export default ActionIcon.extend({
  defaultProps: {
    size: 'md',
  },
  classNames: {
    root: classes.root,
  },
});
