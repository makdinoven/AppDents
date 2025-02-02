import { Input } from '@mantine/core';

import classes from './index.module.css';

export default Input.extend({
  defaultProps: {
    size: 'md',
  },
  classNames: {
    input: classes.input,
  },
});
