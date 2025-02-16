import { FC, useLayoutEffect, useState } from "react";
import { Box, Stack, Title } from "@mantine/core";
import { useDebouncedValue, useInputState, useSetState } from "@mantine/hooks";
import cx from "clsx";

import Icon, { IconType } from "components/Icon";
import Popover from "components/Popover";
import classes from "./index.module.css";

interface FilterProps {
  setParams: ReturnType<typeof useSetState>[1];
}

const filterButtons: { text: string; value: string }[] = [
  { text: "all courses", value: "allCourses" },
  { text: "gnathology", value: "gnathology" },
  { text: "pediatric dentistry", value: "pediatricDentistry" },
  { text: "orthodontics", value: "orthodontics" },
  { text: "orthopedics", value: "orthopedics" },
  { text: "periodontology", value: "periodontology" },
  { text: "restoration", value: "restoration" },
  { text: "technicians", value: "technicians" },
  { text: "management", value: "management" },
  { text: "surgery", value: "surgery" },
  { text: "endodontics", value: "endodontics" },
];

const Filter: FC<FilterProps> = ({ setParams }) => {
  const [isPopoverOpened, setIsPopoverOpened] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState(
    filterButtons[0]?.value || "",
  );
  const [search] = useInputState("");
  const [debouncedSearch] = useDebouncedValue(search, 500);

  useLayoutEffect(() => {
    setParams({ searchValue: debouncedSearch });
  }, [debouncedSearch, setParams]);

  return (
    <Popover
      target={
        <Title order={3} c="text.8">
          <Icon
            size={28}
            type={isPopoverOpened ? IconType.FilledFilter : IconType.Filter}
            color="main"
          />
        </Title>
      }
      onOpen={() => setIsPopoverOpened(true)}
      onClose={() => setIsPopoverOpened(false)}
      floatingSizes={{ w: 43, h: 53 }}
    >
      <Stack className={classes.stack} w="100%">
        {filterButtons.map((btn, index) => (
          <Box
            key={btn.value}
            className={cx(classes.menuLabel, {
              [classes.menuLabelSelected]: selectedFilter === btn.value,
            })}
            onClick={() => setSelectedFilter(btn.value)}
          >
            <Title order={3}>{btn.text}</Title>
          </Box>
        ))}
      </Stack>
    </Popover>
  );
};
export default Filter;
