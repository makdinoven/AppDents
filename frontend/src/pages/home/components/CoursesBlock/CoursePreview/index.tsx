import { FC } from 'react';
import { AspectRatio, BackgroundImage, Box, Button, Image, Overlay, Stack, Text, Title } from '@mantine/core';
import { useDebouncedValue, useInputState } from '@mantine/hooks';

import Icon, { IconType } from 'components/Icon';

const greenStyleSettings = {
  textColor: 'text.8',
  backgroundSrc: '/images/green-course-preview-background.svg',
  color: 'main.3',
};

const blueStyleSettings = {
  textColor: 'secondaryBlue.5',
  backgroundSrc: '/images/blue-course-preview-background.svg',
  color: 'secondarySkyBlue.4',
};

const getPreviewStyle = (index: number) => (index % 2 === 0 ? greenStyleSettings : blueStyleSettings);

interface CoursePreviewProps {
  index: number;
}

const CoursePreview: FC<CoursePreviewProps> = ({ index }) => {
  const [search, setSearch] = useInputState('');

  const [debouncedSearch] = useDebouncedValue(search, 500);

  const styles = getPreviewStyle(index);

  return (
    <Box w="320px" maw={500} h={431} mt={index ? '-30px' : 0}>
      <BackgroundImage src={styles.backgroundSrc} px={14} pt={31} pb={59} w="320px">
        <Stack gap={0}>
          <Stack w="90%" align="flex-start" gap={5}>
            <Title order={4}>Teg</Title>

            <Text size="xl" c={styles.textColor}>
              Damon 2.0 How to treat all common malocclusions
            </Text>

            <Text size="md" fz={14}>
              By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.
            </Text>
          </Stack>

          <AspectRatio ratio={16 / 9} mx="auto" w="100%" pos="relative" mt={13} mb={15} h="169px">
            <Image src="/images/course-image.png" alt="Demo" radius={20} h={169} />
            <Overlay color={styles.color} backgroundOpacity={0.35} radius={20} />
          </AspectRatio>

          <Button variant="outline-bottom" h={24} rightSection={<Icon type={IconType.Arrow} color="inherit" />}>
            View course
          </Button>
        </Stack>
      </BackgroundImage>
    </Box>
  );
};
export default CoursePreview;
