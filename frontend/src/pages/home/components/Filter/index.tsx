import { FC, useLayoutEffect, useState } from 'react';
import { Box, Stack, Title } from '@mantine/core';
import { useDebouncedValue, useInputState, useSetState } from '@mantine/hooks';
import cx from 'clsx';

import Icon, { IconType } from 'components/Icon';
import Popover from 'components/Popover';
import classes from './index.module.css';

interface FilterProps {
  setParams: ReturnType<typeof useSetState>[1];
}

const Filter: FC<FilterProps> = ({ setParams }) => {
  const [isPopoverOpened, setIsPopoverOpened] = useState(false);
  const [search] = useInputState('');

  const [debouncedSearch] = useDebouncedValue(search, 500);

  useLayoutEffect(() => {
    setParams({ searchValue: debouncedSearch });
  }, [debouncedSearch, setParams]);

  return (
    <Popover
      target={
        <Title order={3} c="text.8">
          <Icon size={28} type={isPopoverOpened ? IconType.FilledFilter : IconType.Filter} color="main" />
        </Title>
      }
      onOpen={() => setIsPopoverOpened(true)}
      onClose={() => setIsPopoverOpened(false)}
      floatingSizes={{ w: 43, h: 43 }}
    >
      <Stack w="100%">
        {Array.from({ length: 5 }).map((_, index) => (
          <Box
            // eslint-disable-next-line react/no-array-index-key
            key={index}
            className={cx(classes.menuLabel, { [classes.menuLabelSelected]: !index })}
          >
            <Title order={3}>Text {`${index}`}</Title>
          </Box>
        ))}
      </Stack>
    </Popover>
  );
};
export default Filter;
