import { FC } from 'react';
import { AspectRatio, BackgroundImage, Box, Button, Group, Image, Overlay, Stack, Text, Title } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';

import Icon, { IconType } from 'components/Icon';

import { useRouter } from 'next/router';
import { RoutePath } from 'routes';
import classes from './index.module.css';

const greenStyleSettings = {
  textColor: 'text.8',
  backgroundMobileSrc: '/images/green-course-preview-background.svg',
  backgroundDesktopSrc: '/images/green-course-preview-background-desktop.svg',
  color: '#7FDFD5',
};

const blueStyleSettings = {
  textColor: 'secondaryBlue.5',
  backgroundMobileSrc: '/images/blue-course-preview-background.svg',
  backgroundDesktopSrc: '/images/blue-course-preview-background-desktop.svg',
  color: '#79CEE7',
};

const getPreviewStyle = (index: number) => (index % 2 === 0 ? greenStyleSettings : blueStyleSettings);

const mobileSizes = {
  containerWidth: '320px',
  containerHeight: '430px',
  imageHeight: '169px',
  imageWidth: '100%',
};

const desktopSizes = {
  containerWidth: '608px',
  containerHeight: '430px',
  imageHeight: '174px',
  imageWidth: '305px',
};

interface CoursePreviewProps {
  index: number;
}

const CoursePreview: FC<CoursePreviewProps> = ({ index }) => {
  const isMobile = useMediaQuery('(max-width: 400px)');
  const sizes = isMobile ? mobileSizes : desktopSizes;
  const router = useRouter();

  const styles = getPreviewStyle(index);

  const marginTop = () => {
    if (isMobile) {
      return index ? '-50px' : 0;
    }
    return index && index !== 1 ? '-30px' : 0;
  };

  return (
    <Box w="100%" maw={sizes.containerWidth} h={431} mt={marginTop()}>
      <BackgroundImage
        src={isMobile ? styles.backgroundMobileSrc : styles.backgroundDesktopSrc}
        px={14}
        pt={31}
        pb={59}
        h={sizes.containerHeight}
        w="100%"
      >
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

          <Group className={classes.group}>
            <AspectRatio ratio={16 / 9} w={sizes.imageWidth} pos="relative" mt={13} h={sizes.imageHeight}>
              <Image src="/images/course-image.png" alt="Demo" radius={20} h={sizes.imageHeight} />
              <Overlay color={styles.color} backgroundOpacity={0.35} radius={20} />
            </AspectRatio>

            <Button
              variant="outline-bottom"
              h={24}
              rightSection={<Icon type={IconType.Arrow} color="inherit" size={20} />}
              onClick={() => router.push(`${RoutePath.Courses}/new`)}
            >
              View course
            </Button>
          </Group>
        </Stack>
      </BackgroundImage>
    </Box>
  );
};
export default CoursePreview;
