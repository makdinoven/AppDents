import { FC, useLayoutEffect } from 'react';
import { TextInput } from '@mantine/core';
import { useDebouncedValue, useInputState, useSetState } from '@mantine/hooks';

import Icon, { IconType } from 'components/Icon';
import classes from './index.module.css';

interface SearchProps {
  setParams: ReturnType<typeof useSetState>[1];
}

const Search: FC<SearchProps> = ({ setParams }) => {
  const [search, setSearch] = useInputState('');

  const [debouncedSearch] = useDebouncedValue(search, 500);

  useLayoutEffect(() => {
    setParams({ searchValue: debouncedSearch });
  }, [debouncedSearch, setParams]);

  return (
    <TextInput
      flex={1}
      miw={255}
      maw="100%"
      size="xs"
      variant="dark"
      value={search}
      onChange={setSearch}
      placeholder="Search courses..."
      classNames={{
        wrapper: classes.wrapper,
        input: classes.input,
      }}
      rightSection={<Icon size={16} type={IconType.Search} color="secondary-gray" />}
    />
  );
};
export default Search;
