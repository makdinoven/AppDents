import { Button, Text } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import Icon, { IconType } from 'components/Icon';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';

type BackButtonProps = {
  onClick: () => void;
};

const BackButton = ({ onClick }: BackButtonProps) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  return (
    <Button
      variant="transparent"
      onClick={onClick}
      leftSection={<Icon type={IconType.ChevronCompactLeft} size={isMobile ? 23 : 35} />}
    >
      <Text size="xl" c="text.8">
        Back
      </Text>
    </Button>
  );
};

export default BackButton;
