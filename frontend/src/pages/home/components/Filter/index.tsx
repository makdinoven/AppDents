import { FC, useLayoutEffect, useState } from 'react';
import { ActionIcon, Menu, Text } from '@mantine/core';
import { useDebouncedValue, useInputState, useSetState } from '@mantine/hooks';
import cx from 'clsx';

import Icon, { IconType } from 'components/Icon';
import classes from './index.module.css';

interface FilterProps {
  setParams: ReturnType<typeof useSetState>[1];
}

const Filter: FC<FilterProps> = ({ setParams }) => {
  const [opened, setOpened] = useState(false);
  const [search] = useInputState('');

  const [debouncedSearch] = useDebouncedValue(search, 500);

  useLayoutEffect(() => {
    setParams({ searchValue: debouncedSearch });
  }, [debouncedSearch, setParams]);

  return (
    <Menu shadow="md" width={200} floatingStrategy="absolute" opened={opened} onChange={setOpened}>
      <Menu.Target>
        <ActionIcon variant="transparent">
          <Icon size={28} type={opened ? IconType.FilledFilter : IconType.Filter} color="main" />
        </ActionIcon>
      </Menu.Target>

      <Menu.Dropdown w="96vw" bg="main.3">
        <ActionIcon variant="transparent" w={45} h={45}>
          <Icon type={IconType.CircleX} color="back" size={45} />
        </ActionIcon>

        {Array.from({ length: 5 }).map((_, index) => (
          <Menu.Item
            // eslint-disable-next-line react/no-array-index-key
            key={index}
            classNames={{
              itemLabel: cx(classes.menuLabel, { [classes.menuLabelSelected]: !index }),
            }}
          >
            <Text size="md">Text {`${index}`}</Text>
          </Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  );
};
export default Filter;
